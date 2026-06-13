from __future__ import annotations

import asyncio

from rpl.runtime import build_runtime


if __name__ == "__main__":
    runtime = build_runtime()
    result = asyncio.run(runtime.executor.run_task("calculate math divide by zero"))
    print(result)
