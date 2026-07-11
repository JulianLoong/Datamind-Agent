from __future__ import annotations

import asyncio
import json
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

from rpl.agent_engine.executor import Executor
from rpl.agent_engine.planner import RuleBasedPlanner
from rpl.eval.baselines import build_baseline
from rpl.eval.benchmarks import BenchmarkTask, get_benchmark
from rpl.eval.metrics import (
    TaskEvalRecord,
    summarize_records,
    summarize_records_by_failure_family,
    summarize_records_by_failure_type,
    summarize_records_by_split,
    task_record,
)
from rpl.llm import CachedLLMClient
from rpl.recovery import (
    CandidateDedup,
    CandidateGenerator,
    CandidateValidator,
    ErrorContextBuilder,
    RecoveryPipeline,
)
from rpl.recovery.candidate_gen import build_llm_client
from rpl.tools.builtin import build_builtin_registry
from rpl.trajectory.collector import TrajectoryCollector
from rpl.trajectory.store import TrajectoryStore


async def run_eval(
    *,
    benchmark_name: str = "recovery_bench_lite",
    baseline_names: list[str] | None = None,
    pm_path: str | None = None,
    pm_paths: dict[str, str] | None = None,
    memory_db_path: str | None = None,
    llm_provider: str | None = None,
    llm_model: str | None = None,
    llm_base_url: str | None = None,
    llm_api_key: str | None = None,
    llm_max_tokens: int = 512,
    llm_cache_path: str | Path | None = None,
    splits: list[str] | None = None,
    max_tasks: int = 0,
    repeats: int = 5,
    candidate_count: int = 3,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    tasks = get_benchmark(benchmark_name)
    tasks = _filter_tasks(tasks, splits=splits, max_tasks=max_tasks)
    baseline_names = baseline_names or ["no_recovery", "first", "random"]
    all_records: list[TaskEvalRecord] = []
    summaries: dict[str, dict[str, float | int | str]] = {}
    baseline_configs: dict[str, dict[str, int]] = {}

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        shared_llm_client = build_llm_client(
            provider=llm_provider or "fake",
            model=llm_model,
            base_url=llm_base_url,
            api_key=llm_api_key,
        )
        if llm_cache_path is not None:
            shared_llm_client = CachedLLMClient(
                shared_llm_client,
                cache_path=llm_cache_path,
                namespace=json.dumps(
                    {
                        "provider": llm_provider or "fake",
                        "model": llm_model,
                        "base_url": llm_base_url,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                ),
            )
        for baseline_name in baseline_names:
            baseline_pm_path = _resolve_pm_path(
                baseline_name,
                default_pm_path=pm_path,
                pm_paths=pm_paths,
            )
            spec = build_baseline(
                baseline_name,
                pm_path=baseline_pm_path,
                memory_db_path=memory_db_path,
                llm_client=shared_llm_client,
            )
            baseline_configs[spec.name] = {
                "max_retries_per_step": spec.max_retries_per_step,
                "candidate_count": spec.candidate_count,
            }
            records = await _run_baseline(
                spec_name=spec.name,
                tasks=tasks,
                repeats=repeats,
                max_retries_per_step=spec.max_retries_per_step,
                selector=spec.selector,
                db_path=tmp_path / f"{spec.name}.db",
                llm_client=shared_llm_client,
                llm_max_tokens=llm_max_tokens,
                candidate_count=spec.candidate_count
                if spec.candidate_count is not None
                else candidate_count,
            )
            all_records.extend(records)
            summaries[spec.name] = summarize_records(records)

    report = {
        "benchmark": benchmark_name,
        "repeats": repeats,
        "splits": splits or [],
        "max_tasks": max_tasks,
        "task_count": len(tasks),
        "llm_cache_path": str(llm_cache_path) if llm_cache_path is not None else None,
        "baseline_configs": baseline_configs,
        "summaries": summaries,
        "split_summaries": {
            baseline: summarize_records_by_split(
                [record for record in all_records if record.baseline == baseline]
            )
            for baseline in summaries
        },
        "failure_type_summaries": {
            baseline: summarize_records_by_failure_type(
                [record for record in all_records if record.baseline == baseline]
            )
            for baseline in summaries
        },
        "failure_family_summaries": {
            baseline: summarize_records_by_failure_family(
                [record for record in all_records if record.baseline == baseline]
            )
            for baseline in summaries
        },
        "records": [asdict(record) for record in all_records],
    }
    if output_path is not None:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


async def _run_baseline(
    *,
    spec_name: str,
    tasks: list[BenchmarkTask],
    repeats: int,
    max_retries_per_step: int,
    selector,
    db_path: Path,
    llm_client,
    llm_max_tokens: int = 512,
    candidate_count: int = 3,
) -> list[TaskEvalRecord]:
    registry = build_builtin_registry()
    store = TrajectoryStore(db_path)
    executor = Executor(
        registry,
        RuleBasedPlanner(),
        RecoveryPipeline(
            ErrorContextBuilder(),
            CandidateGenerator(
                llm_client,
                max_tokens=llm_max_tokens,
                tool_specs=registry.list_tools(),
            ),
            CandidateDedup(),
            selector,
            candidate_count=candidate_count,
            validator=CandidateValidator(registry),
        ),
        TrajectoryCollector(store),
    )

    records: list[TaskEvalRecord] = []
    for _ in range(repeats):
        for task in tasks:
            result = await executor.run_task(
                task.goal,
                max_steps=20,
                max_retries_per_step=max_retries_per_step,
            )
            records.append(
                task_record(
                    baseline=spec_name,
                    goal=task.goal,
                    split=task.split,
                    expected_error_type=task.expected_error_type,
                    failure_family=task.failure_family,
                    result=result,
                )
            )
    return records


def run_eval_sync(**kwargs: Any) -> dict[str, Any]:
    return asyncio.run(run_eval(**kwargs))


def parse_pm_path_items(items: list[str] | None) -> dict[str, str]:
    paths: dict[str, str] = {}
    for item in items or []:
        if "=" not in item:
            raise ValueError(f"Invalid PM path item {item!r}; expected baseline=path")
        baseline, path = item.split("=", 1)
        baseline = baseline.strip()
        path = path.strip()
        if not baseline or not path:
            raise ValueError(f"Invalid PM path item {item!r}; expected baseline=path")
        paths[baseline] = path
    return paths


def _filter_tasks(
    tasks: list[BenchmarkTask],
    *,
    splits: list[str] | None = None,
    max_tasks: int = 0,
) -> list[BenchmarkTask]:
    filtered = list(tasks)
    if splits:
        split_filter = set(splits)
        filtered = [task for task in filtered if task.split in split_filter]
    if max_tasks > 0:
        filtered = filtered[:max_tasks]
    return filtered


def _resolve_pm_path(
    baseline_name: str,
    *,
    default_pm_path: str | None,
    pm_paths: dict[str, str] | None,
) -> str | None:
    if not pm_paths:
        return default_pm_path
    if baseline_name in pm_paths:
        return pm_paths[baseline_name]
    base_name = baseline_name.rsplit("_r", 1)[0] if "_r" in baseline_name else baseline_name
    return pm_paths.get(base_name, default_pm_path)
