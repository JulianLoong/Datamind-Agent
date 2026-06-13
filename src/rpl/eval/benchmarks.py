from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


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
    if name == "recovery_bench_lite":
        return list(RECOVERY_BENCH_LITE)
    if name == "recovery_bench_generated":
        return generate_recovery_bench()
    raise ValueError(f"Unknown benchmark: {name}")


def generate_recovery_bench(
    *,
    train_per_type: int = 80,
    test_per_type: int = 20,
    clean_per_type: int = 10,
) -> list[BenchmarkTask]:
    tasks: list[BenchmarkTask] = []
    for split, count, offset in [
        ("train", train_per_type, 0),
        ("test_unseen", test_per_type, 10_000),
    ]:
        for i in range(count):
            idx = offset + i
            tasks.append(_math_div_zero_task(idx, split))
            tasks.append(_http_not_found_task(idx, split))
            tasks.append(_json_invalid_task(idx, split))
            tasks.append(_json_missing_field_task(idx, split))

    for i in range(clean_per_type):
        tasks.append(_math_clean_task(i))
        tasks.append(_http_clean_task(i))
        tasks.append(_json_clean_task(i))
    return tasks


def _structured_goal(description: str, tool_name: str, params: dict[str, Any]) -> str:
    return "rpl_task " + json.dumps(
        {
            "description": description,
            "tool_name": tool_name,
            "params": params,
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def _math_div_zero_task(idx: int, split: str) -> BenchmarkTask:
    numerator = idx + 3
    expressions = [
        f"{numerator}/0",
        f"({numerator} + 2)/0",
        f"{numerator}/(2-2)",
        f"({numerator} * 3)/(5-5)",
    ]
    expression = expressions[idx % len(expressions)]
    return BenchmarkTask(
        _structured_goal("Evaluate generated arithmetic expression", "math_calc", {"expression": expression}),
        "division_by_zero",
        split,
    )


def _http_not_found_task(idx: int, split: str) -> BenchmarkTask:
    url = f"https://example.test/missing/{idx}"
    return BenchmarkTask(
        _structured_goal("Fetch generated missing mock HTTP URL", "http_request", {"url": url}),
        "not_found",
        split,
    )


def _json_invalid_task(idx: int, split: str) -> BenchmarkTask:
    field = f"value_{idx}"
    bad_payloads = [
        f'{{"{field}": ',
        f"{{bad_{idx}: true",
        f'{{"{field}" null}}',
    ]
    return BenchmarkTask(
        _structured_goal(
            "Parse generated invalid JSON",
            "json_parse",
            {"text": bad_payloads[idx % len(bad_payloads)], "field": field},
        ),
        "invalid_json",
        split,
    )


def _json_missing_field_task(idx: int, split: str) -> BenchmarkTask:
    requested = f"target_{idx}"
    present = f"other_{idx}"
    return BenchmarkTask(
        _structured_goal(
            "Parse generated JSON missing requested field",
            "json_parse",
            {"text": json.dumps({present: idx}, ensure_ascii=False), "field": requested},
        ),
        "missing_field",
        split,
    )


def _math_clean_task(idx: int) -> BenchmarkTask:
    return BenchmarkTask(
        _structured_goal("Evaluate clean generated arithmetic expression", "math_calc", {"expression": f"{idx}+{idx + 1}"}),
        None,
        "clean",
    )


def _http_clean_task(idx: int) -> BenchmarkTask:
    url = "https://example.test/health" if idx % 2 == 0 else "https://example.test/users/1"
    return BenchmarkTask(
        _structured_goal("Fetch clean mock HTTP fixture", "http_request", {"url": url}),
        None,
        "clean",
    )


def _json_clean_task(idx: int) -> BenchmarkTask:
    field = f"value_{idx}"
    return BenchmarkTask(
        _structured_goal(
            "Parse clean generated JSON",
            "json_parse",
            {"text": json.dumps({field: idx}, ensure_ascii=False), "field": field},
        ),
        None,
        "clean",
    )
