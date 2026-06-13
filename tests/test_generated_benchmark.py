from __future__ import annotations

from rpl.agent_engine.planner import RuleBasedPlanner
from rpl.eval.benchmarks import generate_recovery_bench


def test_generated_benchmark_has_distinct_structured_tasks() -> None:
    tasks = generate_recovery_bench(train_per_type=2, test_per_type=1, clean_per_type=1)
    goals = [task.goal for task in tasks]

    assert len(tasks) == 15
    assert len(set(goals)) == len(goals)
    assert any(task.expected_error_type == "missing_field" for task in tasks)


def test_rule_based_planner_accepts_structured_task() -> None:
    task = generate_recovery_bench(train_per_type=1, test_per_type=0, clean_per_type=0)[0]

    steps = RuleBasedPlanner().plan(task.goal, [])

    assert len(steps) == 1
    assert steps[0].tool_name == "math_calc"
    assert steps[0].params is not None
    assert "expression" in steps[0].params
