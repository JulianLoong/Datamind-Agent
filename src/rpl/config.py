from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover - exercised in minimal environments
    yaml = None


@dataclass(frozen=True)
class PathSettings:
    trajectory_db: str = "data/trajectories.db"


@dataclass(frozen=True)
class AgentSettings:
    max_steps: int = 20
    max_retries_per_step: int = 3


@dataclass(frozen=True)
class RecoverySettings:
    candidate_count: int = 3
    default_selector: str = "first"
    selector: str = "default"


@dataclass(frozen=True)
class LLMSettings:
    provider: str = "fake"


@dataclass(frozen=True)
class ToolSettings:
    random_seed: int | None = 42
    configs: dict[str, dict[str, Any]] = field(default_factory=dict)


@dataclass(frozen=True)
class Settings:
    paths: PathSettings = field(default_factory=PathSettings)
    agent: AgentSettings = field(default_factory=AgentSettings)
    recovery: RecoverySettings = field(default_factory=RecoverySettings)
    llm: LLMSettings = field(default_factory=LLMSettings)
    tools: ToolSettings = field(default_factory=ToolSettings)


def _default_config() -> dict[str, Any]:
    return {
        "paths": {"trajectory_db": "data/trajectories.db"},
        "agent": {"max_steps": 20, "max_retries_per_step": 3},
        "recovery": {"candidate_count": 3, "default_selector": "first", "selector": "default"},
        "llm": {"provider": "fake"},
        "tools": {
            "random_seed": 42,
            "json_parse": {"error_rate": 0.0, "error_types": ["invalid_json", "missing_field"]},
            "math_calc": {
                "error_rate": 0.0,
                "error_types": ["division_by_zero", "invalid_expression"],
            },
            "file_read": {
                "error_rate": 0.0,
                "error_types": ["file_not_found", "permission_denied"],
                "sandbox_dir": "data/sandbox",
            },
            "http_request": {
                "error_rate": 0.0,
                "error_types": ["timeout", "not_found", "invalid_response"],
            },
        },
    }


def _load_yaml_or_default(config_path: Path) -> dict[str, Any]:
    if yaml is None or not config_path.exists():
        return _default_config()
    return yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}


def load_settings(path: str | Path = "config/default.yaml") -> Settings:
    config_path = Path(path)
    data = _load_yaml_or_default(config_path)

    tools_data = data.get("tools", {}) or {}
    random_seed = tools_data.get("random_seed", 42)
    tool_configs = {key: value for key, value in tools_data.items() if key != "random_seed"}

    return Settings(
        paths=PathSettings(**(data.get("paths", {}) or {})),
        agent=AgentSettings(**(data.get("agent", {}) or {})),
        recovery=RecoverySettings(**(data.get("recovery", {}) or {})),
        llm=LLMSettings(**(data.get("llm", {}) or {})),
        tools=ToolSettings(random_seed=random_seed, configs=tool_configs),
    )
