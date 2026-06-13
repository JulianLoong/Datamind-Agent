from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from rpl.agent_engine.step import RecoveryAttempt, Step, TaskResult
from rpl.tools.base import ToolResult


def _json_default(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "value"):
        return value.value
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def to_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=_json_default)


def from_json(value: str | None, default: Any = None) -> Any:
    if value is None:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


class TrajectoryStore:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    goal TEXT NOT NULL,
                    status TEXT NOT NULL,
                    total_tokens INTEGER DEFAULT 0,
                    total_latency_ms REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS steps (
                    id TEXT PRIMARY KEY,
                    task_id TEXT REFERENCES tasks(id),
                    step_index INTEGER NOT NULL,
                    description TEXT,
                    tool_name TEXT,
                    params_json TEXT,
                    status TEXT NOT NULL,
                    result_json TEXT,
                    tokens_used INTEGER DEFAULT 0,
                    latency_ms REAL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS recovery_attempts (
                    id TEXT PRIMARY KEY,
                    step_id TEXT REFERENCES steps(id),
                    error_context_json TEXT,
                    candidates_json TEXT NOT NULL,
                    chosen_index INTEGER NOT NULL,
                    chosen_candidate_json TEXT,
                    outcome TEXT NOT NULL,
                    initial_result_json TEXT,
                    final_result_json TEXT,
                    pm_scores_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            self._ensure_recovery_columns(conn)

    def _ensure_recovery_columns(self, conn: sqlite3.Connection) -> None:
        existing = {
            row["name"] for row in conn.execute("PRAGMA table_info(recovery_attempts)").fetchall()
        }
        columns = {
            "error_context_json": "TEXT",
            "chosen_candidate_json": "TEXT",
            "initial_result_json": "TEXT",
            "final_result_json": "TEXT",
        }
        for column, column_type in columns.items():
            if column not in existing:
                conn.execute(f"ALTER TABLE recovery_attempts ADD COLUMN {column} {column_type}")

    def save_task(self, result: TaskResult) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO tasks (id, goal, status, total_tokens, total_latency_ms)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    result.task_id,
                    result.goal,
                    result.status,
                    result.total_tokens,
                    result.total_latency_ms,
                ),
            )
            for step in result.steps:
                self.save_step(conn, result.task_id, step)

    def save_step(self, conn: sqlite3.Connection, task_id: str, step: Step) -> None:
        step_id = f"{task_id}:{step.index}"
        result = step.result or ToolResult(success=False, error_type="not_executed")
        conn.execute(
            """
            INSERT OR REPLACE INTO steps (
                id, task_id, step_index, description, tool_name, params_json, status,
                result_json, tokens_used, latency_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                step_id,
                task_id,
                step.index,
                step.description,
                step.tool_name,
                to_json(step.params or {}),
                step.status.value,
                to_json(result),
                result.tokens_used,
                result.latency_ms,
            ),
        )
        for idx, attempt in enumerate(step.recovery_attempts):
            self.save_recovery_attempt(conn, step_id, idx, attempt)

    def save_recovery_attempt(
        self,
        conn: sqlite3.Connection,
        step_id: str,
        attempt_index: int,
        attempt: RecoveryAttempt,
    ) -> None:
        chosen_candidate = None
        if 0 <= attempt.chosen_index < len(attempt.candidates):
            chosen_candidate = attempt.candidates[attempt.chosen_index]
        conn.execute(
            """
            INSERT OR REPLACE INTO recovery_attempts (
                id, step_id, error_context_json, candidates_json, chosen_index,
                chosen_candidate_json, outcome, initial_result_json, final_result_json, pm_scores_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"{step_id}:recovery:{attempt_index}",
                step_id,
                to_json(attempt.error_context) if attempt.error_context is not None else None,
                to_json(attempt.candidates),
                attempt.chosen_index,
                to_json(chosen_candidate) if chosen_candidate is not None else None,
                attempt.outcome.value,
                to_json(attempt.initial_result) if attempt.initial_result is not None else None,
                to_json(attempt.final_result) if attempt.final_result is not None else None,
                to_json(attempt.pm_scores) if attempt.pm_scores is not None else None,
            ),
        )

    def query_failures(self, error_type: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        sql = "SELECT * FROM steps WHERE status = 'failed'"
        params: list[Any] = []
        if error_type is not None:
            sql += " AND result_json LIKE ?"
            params.append(f'%"error_type": "{error_type}"%')
        sql += " ORDER BY rowid DESC LIMIT ?"
        params.append(limit)
        with self.connect() as conn:
            return [dict(row) for row in conn.execute(sql, params).fetchall()]

    def query_recovery_attempts(self, task_id: str | None = None) -> list[dict[str, Any]]:
        sql = "SELECT ra.* FROM recovery_attempts ra"
        params: list[Any] = []
        if task_id is not None:
            sql += " JOIN steps s ON ra.step_id = s.id WHERE s.task_id = ?"
            params.append(task_id)
        sql += " ORDER BY ra.created_at ASC"
        with self.connect() as conn:
            return [dict(row) for row in conn.execute(sql, params).fetchall()]

    def query_recovery_attempts_with_context(self, limit: int = 1000) -> list[dict[str, Any]]:
        sql = """
        SELECT
            t.id AS task_id,
            t.goal AS task_goal,
            t.status AS task_status,
            s.id AS step_id,
            s.step_index,
            s.description AS step_description,
            s.tool_name AS final_tool_name,
            s.params_json AS final_params_json,
            s.status AS step_status,
            s.result_json AS step_result_json,
            ra.*
        FROM recovery_attempts ra
        JOIN steps s ON ra.step_id = s.id
        JOIN tasks t ON s.task_id = t.id
        ORDER BY ra.created_at DESC
        LIMIT ?
        """
        with self.connect() as conn:
            return [dict(row) for row in conn.execute(sql, [limit]).fetchall()]
