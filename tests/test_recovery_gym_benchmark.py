from __future__ import annotations

from rpl.agent_engine.planner import RuleBasedPlanner
from rpl.eval.benchmarks import generate_recovery_gym, get_benchmark
from rpl.tools.builtin import build_builtin_registry


def test_recovery_gym_has_family_and_generalization_splits() -> None:
    tasks = generate_recovery_gym(train_per_family=2, test_per_family=1, clean_per_tool=1)
    splits = {task.split for task in tasks}
    families = {task.failure_family for task in tasks if task.failure_family is not None}

    assert "seen_template_unseen_params" in splits
    assert "seen_tool_new_error_message" in splits
    assert "new_tool_same_family" in splits
    assert "clean" in splits
    assert {"schema_error", "malformed_input"} <= families
    assert len({task.goal for task in tasks}) == len(tasks)


def test_recovery_gym_is_available_by_name() -> None:
    tasks = get_benchmark("recovery_gym")

    assert tasks
    assert any(task.failure_family == "schema_error" for task in tasks)


def test_recovery_gym_clean_tasks_execute_successfully() -> None:
    registry = build_builtin_registry()
    planner = RuleBasedPlanner()
    clean_tasks = [task for task in generate_recovery_gym(clean_per_tool=1) if task.split == "clean"]

    assert clean_tasks
    for task in clean_tasks:
        step = planner.plan(task.goal, registry.list_tools())[0]
        result = registry.execute(step.tool_name or "", step.params or {})
        assert result.success is True
