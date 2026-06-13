from __future__ import annotations

import argparse
import asyncio

from rpl.runtime import build_runtime


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the RPL prototype agent.")
    parser.add_argument("task", nargs="?", default="calculate math", help="Task goal for the agent")
    parser.add_argument("--config", default="config/default.yaml", help="Path to YAML config")
    args = parser.parse_args()

    runtime = build_runtime(args.config)
    result = asyncio.run(
        runtime.executor.run_task(
            args.task,
            max_steps=runtime.settings.agent.max_steps,
            max_retries_per_step=runtime.settings.agent.max_retries_per_step,
        )
    )
    print(f"task_id={result.task_id}")
    print(f"status={result.status}")
    for step in result.steps:
        print(f"step[{step.index}] {step.status.value}: {step.tool_name} {step.params} -> {step.result}")


if __name__ == "__main__":
    main()
