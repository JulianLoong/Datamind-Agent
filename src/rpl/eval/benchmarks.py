from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BenchmarkTask:
    goal: str
    expected_error_type: str | None = None
    split: str = "test"
    failure_family: str | None = None
    metadata: dict[str, Any] | None = None


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


RECOVERY_BENCH_LITE: list[BenchmarkTask] = [
    BenchmarkTask(
        _structured_goal("Parse invalid JSON", "json_parse", {"text": '{"a":}', "field": "a"}),
        "invalid_json",
        "train",
    ),
    BenchmarkTask(
        _structured_goal("Parse JSON missing field", "json_parse", {"text": '{"other": 1}', "field": "target"}),
        "missing_field",
        "train",
    ),
    BenchmarkTask(
        _structured_goal("Evaluate math with wrong type", "math_calc", {"expression": 42}),
        "validation_error",
        "train",
    ),
    BenchmarkTask(
        _structured_goal("Parse malformed JSON variant", "json_parse", {"text": "{broken: true}", "field": "broken"}),
        "invalid_json",
        "test_seen",
    ),
    BenchmarkTask(
        _structured_goal("Parse JSON missing other field", "json_parse", {"text": '{"x": 2}', "field": "y"}),
        "missing_field",
        "test_seen",
    ),
    BenchmarkTask(
        _structured_goal(
            "Fetch HTTP with wrong method",
            "http_request",
            {"url": "https://example.test/health", "method": "POST"},
        ),
        "validation_error",
        "test_seen",
    ),
    BenchmarkTask(
        _structured_goal("Evaluate clean math", "math_calc", {"expression": "1+1"}),
        None,
        "clean",
    ),
    BenchmarkTask(
        _structured_goal("Fetch clean HTTP", "http_request", {"url": "https://example.test/health"}),
        None,
        "clean",
    ),
    BenchmarkTask(
        _structured_goal("Parse clean JSON", "json_parse", {"text": '{"v": 1}', "field": "v"}),
        None,
        "clean",
    ),
]


def get_benchmark(name: str = "recovery_bench_lite") -> list[BenchmarkTask]:
    if name == "recovery_bench_lite":
        return list(RECOVERY_BENCH_LITE)
    if name == "recovery_bench_generated":
        return generate_recovery_bench()
    if name == "recovery_gym":
        return generate_recovery_gym()
    raise ValueError(f"Unknown benchmark: {name}")


def generate_recovery_gym(
    *,
    train_per_family: int = 12,
    test_per_family: int = 4,
    clean_per_tool: int = 4,
) -> list[BenchmarkTask]:
    """Build executable recovery episodes with explicit generalization splits.

    Two failure families are covered:
    - ``malformed_input``: recoverable JSON syntax errors.
    - ``schema_error``: parameter validation failures (wrong type, wrong enum, extra property).

    Each error message returned by the registry is information-dense enough that a real LLM
    can infer the correct repair action from the prompt alone (no hidden internal state).
    """

    tasks: list[BenchmarkTask] = []
    for i in range(train_per_family):
        tasks.extend(_recovery_gym_family_tasks(i, "seen_template_unseen_params", offset=0))
    for i in range(test_per_family):
        tasks.extend(_recovery_gym_family_tasks(i, "seen_tool_new_error_message", offset=10_000))
        tasks.extend(_recovery_gym_new_tool_same_family_tasks(i, offset=20_000))

    for i in range(clean_per_tool):
        tasks.extend(
            [
                _math_clean_task(i),
                _http_clean_task(i),
                _json_clean_task(i),
            ]
        )
    return tasks


def _recovery_gym_family_tasks(idx: int, split: str, *, offset: int) -> list[BenchmarkTask]:
    item = offset + idx
    return [
        _gym_json_malformed_input_task(item, split),
        _gym_json_schema_task(item, split),
        _gym_http_schema_task(item, split),
        _gym_extra_property_task(item, split),
    ]


def _recovery_gym_new_tool_same_family_tasks(idx: int, *, offset: int) -> list[BenchmarkTask]:
    item = offset + idx
    return [
        _gym_math_wrong_type_task(item, "new_tool_same_family"),
    ]


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
            tasks.append(_json_invalid_task(idx, split))
            tasks.append(_json_missing_field_task(idx, split))
            tasks.append(_math_wrong_type_task(idx, split))
            tasks.append(_http_wrong_method_task(idx, split))
            tasks.append(_json_extra_property_task(idx, split))

    for i in range(clean_per_type):
        tasks.append(_math_clean_task(i))
        tasks.append(_http_clean_task(i))
        tasks.append(_json_clean_task(i))
    return tasks


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


def _math_wrong_type_task(idx: int, split: str) -> BenchmarkTask:
    return BenchmarkTask(
        _structured_goal(
            "Evaluate arithmetic expression with wrong type",
            "math_calc",
            {"expression": idx},
        ),
        "validation_error",
        split,
    )


def _http_wrong_method_task(idx: int, split: str) -> BenchmarkTask:
    methods = ["POST", "PUT", "DELETE"]
    urls = ["https://example.test/health", "https://example.test/users/1"]
    return BenchmarkTask(
        _structured_goal(
            "Fetch HTTP fixture with unsupported method",
            "http_request",
            {"url": urls[idx % len(urls)], "method": methods[idx % len(methods)]},
        ),
        "validation_error",
        split,
    )


def _json_extra_property_task(idx: int, split: str) -> BenchmarkTask:
    field = f"value_{idx}"
    return BenchmarkTask(
        _structured_goal(
            "Parse JSON with unexpected parameter",
            "json_parse",
            {"text": json.dumps({field: idx}), "field": field, "bogus": "extra"},
        ),
        "validation_error",
        split,
    )


def _math_clean_task(idx: int) -> BenchmarkTask:
    return BenchmarkTask(
        _structured_goal(
            "Evaluate clean generated arithmetic expression",
            "math_calc",
            {"expression": f"{idx}+{idx + 1}"},
        ),
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


def _gym_task(
    *,
    description: str,
    tool_name: str,
    params: dict[str, Any],
    expected_error_type: str,
    split: str,
    failure_family: str,
    idx: int,
) -> BenchmarkTask:
    return BenchmarkTask(
        _structured_goal(description, tool_name, params),
        expected_error_type,
        split,
        failure_family,
        {
            "gym": "recovery_gym",
            "idx": idx,
            "tool_name": tool_name,
            "description": description,
        },
    )


def _gym_json_malformed_input_task(idx: int, split: str) -> BenchmarkTask:
    field = f"value_{idx}"
    payloads = [
        f'{{"{field}": ',
        f"{{broken_{idx}: true",
        f'{{"{field}" null}}',
    ]
    return _gym_task(
        description="Parse malformed JSON payload",
        tool_name="json_parse",
        params={"text": payloads[idx % len(payloads)], "field": field},
        expected_error_type="invalid_json",
        split=split,
        failure_family="malformed_input",
        idx=idx,
    )


def _gym_json_schema_task(idx: int, split: str) -> BenchmarkTask:
    return _gym_task(
        description="Parse JSON with wrong parameter type",
        tool_name="json_parse",
        params={"text": {"value": idx}},
        expected_error_type="validation_error",
        split=split,
        failure_family="schema_error",
        idx=idx,
    )


def _gym_http_schema_task(idx: int, split: str) -> BenchmarkTask:
    methods = ["POST", "PUT", "DELETE"]
    urls = ["https://example.test/health", "https://example.test/users/1"]
    return _gym_task(
        description="Fetch HTTP fixture with unsupported method",
        tool_name="http_request",
        params={"url": urls[idx % len(urls)], "method": methods[idx % len(methods)]},
        expected_error_type="validation_error",
        split=split,
        failure_family="schema_error",
        idx=idx,
    )


def _gym_extra_property_task(idx: int, split: str) -> BenchmarkTask:
    field = f"value_{idx}"
    return _gym_task(
        description="Parse JSON with unexpected parameter",
        tool_name="json_parse",
        params={"text": json.dumps({field: idx}), "field": field, "bogus": "extra"},
        expected_error_type="validation_error",
        split=split,
        failure_family="schema_error",
        idx=idx,
    )


def _gym_math_wrong_type_task(idx: int, split: str) -> BenchmarkTask:
    return _gym_task(
        description="Evaluate arithmetic expression with wrong type",
        tool_name="math_calc",
        params={"expression": idx},
        expected_error_type="validation_error",
        split=split,
        failure_family="schema_error",
        idx=idx,
    )
