from __future__ import annotations

import uuid

from rpl.agent_engine.planner import Planner
from rpl.agent_engine.step import Step, StepStatus, TaskResult
from rpl.recovery.pipeline import RecoveryPipeline
from rpl.tools.registry import ToolRegistry
from rpl.trajectory.collector import TrajectoryCollector


class Executor:
    def __init__(
        self,
        registry: ToolRegistry,
        planner: Planner,
        recovery_pipeline: RecoveryPipeline,
        collector: TrajectoryCollector,
    ) -> None:
        self.registry = registry
        self.planner = planner
        self.recovery_pipeline = recovery_pipeline
        self.collector = collector

    async def run_task(
        self,
        task_goal: str,
        *,
        max_steps: int = 20,
        max_retries_per_step: int = 3,
    ) -> TaskResult:
        task_id = str(uuid.uuid4())
        steps = self.planner.plan(task_goal, self.registry.list_tools())[:max_steps]
        total_tokens = 0
        total_latency_ms = 0.0
        recovery_tokens = 0
        recovery_latency_ms = 0.0
        task_status = "success"

        for step in steps:
            self.collector.on_step_start(step)
            success = await self._execute_step_with_recovery(
                step,
                steps[: step.index],
                task_goal,
                max_retries_per_step=max_retries_per_step,
            )
            self.collector.on_step_end(step)
            if step.result is not None:
                total_tokens += step.result.tokens_used
                total_latency_ms += step.result.latency_ms
            for attempt in step.recovery_attempts:
                recovery_tokens += attempt.candidate_tokens
                recovery_latency_ms += attempt.candidate_latency_ms
            if not success:
                task_status = "failed"
                break

        result = TaskResult(
            task_id=task_id,
            goal=task_goal,
            status=task_status,
            steps=steps,
            total_tokens=total_tokens,
            total_latency_ms=total_latency_ms,
            recovery_tokens=recovery_tokens,
            recovery_latency_ms=recovery_latency_ms,
        )
        self.collector.on_task_end(result)
        return result

    async def _execute_step_with_recovery(
        self,
        step: Step,
        history: list[Step],
        task_goal: str,
        *,
        max_retries_per_step: int,
    ) -> bool:
        pending_recovery = None
        for attempt_no in range(max_retries_per_step + 1):
            step.status = StepStatus.RUNNING
            result = self.registry.execute(step.tool_name or "", step.params or {})
            step.result = result
            self.collector.on_tool_call(step, step.tool_name or "", step.params or {}, result)

            if pending_recovery is not None:
                pending_recovery.final_result = result
                pending_recovery.outcome = StepStatus.SUCCESS if result.success else StepStatus.FAILED
                pending_recovery = None

            if result.success:
                step.status = StepStatus.SUCCESS
                return True

            step.status = StepStatus.FAILED
            if attempt_no >= max_retries_per_step:
                return False

            step.status = StepStatus.RECOVERING
            recovery_attempt = await self.recovery_pipeline.recover(step, history, task_goal)
            chosen = recovery_attempt.candidates[recovery_attempt.chosen_index]
            step.recovery_attempts.append(recovery_attempt)
            self.collector.on_recovery(step, recovery_attempt)
            if chosen.tool_name is None:
                recovery_attempt.outcome = StepStatus.FAILED
                recovery_attempt.final_result = result
                step.status = StepStatus.FAILED
                return False
            step.tool_name = chosen.tool_name
            step.params = chosen.tool_params or {}
            pending_recovery = recovery_attempt

        return False
