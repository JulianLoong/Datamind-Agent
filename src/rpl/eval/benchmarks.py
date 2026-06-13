from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BenchmarkTask:
    goal: str
    expected_error_type: str | None = None
    split: str = "test"


RECOVERY_BENCH_LITE: list[BenchmarkTask] = [
    BenchmarkTask("calculate math divide by zero", "division_by_zero", "train"),
    BenchmarkTask("fetch missing http", "not_found", "train"),
    BenchmarkTask("parse invalid json", "invalid_json", "train"),
    BenchmarkTask("calculate math divide by zero case 2", "division_by_zero", "test_seen"),
    BenchmarkTask("fetch missing http 404", "not_found", "test_seen"),
    BenchmarkTask("parse bad json", "invalid_json", "test_seen"),
    BenchmarkTask("calculate math", None, "clean"),
    BenchmarkTask("fetch http", None, "clean"),
    BenchmarkTask("parse json", None, "clean"),
]


def get_benchmark(name: str = "recovery_bench_lite") -> list[BenchmarkTask]:
    if name != "recovery_bench_lite":
        raise ValueError(f"Unknown benchmark: {name}")
    return list(RECOVERY_BENCH_LITE)
