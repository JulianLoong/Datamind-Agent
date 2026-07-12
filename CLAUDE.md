# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DataMindAgent RPL (Recovery Preference Learning) is a research prototype for training a DPO-trained Preference Model (`DPO_PM`) that ranks recovery candidates when an AI agent's tool calls fail. The system implements a complete pipeline: trajectory collection, preference-pair extraction, DPO training, and controlled evaluation against multiple baselines.

This is a thesis-focused research project. `DPO_PM` is the target model. `lightweight_pm` (dependency-free pairwise ranker) and `memory_lightweight_pm` (retrieval-augmented) are baselines, not the final method. `mock_pm` is a rule-based oracle for debugging/cold-start only.

## Commands

### Environment

The project uses a local venv at `.venv\`. Python >=3.10 required. The core package has zero runtime dependencies; DPO training dependencies (torch, transformers, peft, trl, bitsandbytes) are imported lazily only by DPO scripts/model code.

```bash
# Install dev dependencies (pytest, ruff)
pip install -e ".[dev]"

# Install DPO training deps (only on CUDA machine, only for DPO path)
pip install torch transformers datasets accelerate peft trl bitsandbytes
```

### Running Tests

```bash
# Full suite
.venv\Scripts\python.exe -m pytest

# Single test file / single test
.venv\Scripts\python.exe -m pytest tests/test_candidate_gen.py
.venv\Scripts\python.exe -m pytest tests/test_candidate_gen.py::test_specific_name -v
```

`tests/conftest.py` automatically inserts `src/` onto `sys.path`, so no `PYTHONPATH` manipulation is needed for tests. `asyncio_mode = "auto"` is set in `pyproject.toml`.

### Linting

```bash
.venv\Scripts\python.exe -m ruff check src tests scripts
.venv\Scripts\python.exe -m ruff format src tests scripts
```

Ruff config: line-length 100, rules `E,F,I,UP,B`, target py310.

### Core Scripts

All scripts require `PYTHONPATH=src` (bash) or are run via the installed `rpl-agent` entry point. On Windows PowerShell use `$env:PYTHONPATH = "src"`.

```bash
# Run the agent on a task
PYTHONPATH=src python3 scripts/run_agent.py "calculate math"

# Lightweight baseline loop (fast, no GPU)
PYTHONPATH=src python3 scripts/cold_start.py --selector mock_pm --repeats 10 --export
PYTHONPATH=src python3 scripts/train_pm.py --train data/pref_pairs/train.jsonl --val data/pref_pairs/val.jsonl --out data/pm_checkpoints/lightweight_pm.json
PYTHONPATH=src python3 scripts/run_eval.py --baselines first random lightweight_pm --pm-path data/pm_checkpoints/lightweight_pm.json --repeats 5 --out data/eval/recovery_bench_lite.json

# Generated benchmark (thesis-scale)
PYTHONPATH=src python3 scripts/collect_benchmark_data.py --benchmark recovery_bench_generated --splits train --db data/generated_trajectories.db --out-dir data/pref_pairs_generated
PYTHONPATH=src python3 scripts/export_dpo_data.py --train data/pref_pairs_generated/train.jsonl --val data/pref_pairs_generated/val.jsonl --out-train data/dpo_generated/train.jsonl --out-val data/dpo_generated/val.jsonl

# DPO training (CUDA only)
PYTHONPATH=src python3 scripts/train_dpo_pm.py --base-model Qwen/Qwen2.5-0.5B-Instruct --train data/pref_pairs_outcomes/train.jsonl --val data/pref_pairs_outcomes/val.jsonl --work-dir data/dpo_outcomes --out data/pm_checkpoints/dpo_pm_outcomes --use-4bit --bf16 --gradient-checkpointing
```

### Eval CLI conventions

- `--baselines` accepts names with optional `_r<N>` retry suffix (e.g. `dpo_pm_r3` = dpo_pm with 3 retries).
- `--pm-paths baseline=path` lets each baseline use a different checkpoint. DPO paths use `base_model::adapter_path` format (e.g. `Qwen/Qwen2.5-0.5B-Instruct::data/pm_checkpoints/dpo_pm_outcomes`).
- Real-LLM eval uses `run_real_llm_eval.py`; the PowerShell wrapper `run_real_llm_dpo_pm_eval.ps1` pins to `.venv\Scripts\python.exe` and verifies DPO deps. Malformed real-LLM candidates halt eval by default; `--allow-candidate-fallback` is diagnostic only.

## Architecture

### Package layout

Source lives under `src/rpl/` (installed as package `rpl`). Key submodules:

- **`agent_engine/`** — `Executor` runs the task loop: plan step → call tool → on failure, invoke `RecoveryPipeline` → retry. `RuleBasedPlanner`/`StaticPlanner` produce steps. `step.py` defines `Step`, `StepStatus`, `TaskResult`, `RecoveryAttempt`.
- **`recovery/`** — The core research artifact. `RecoveryPipeline` (pipeline.py) orchestrates: `ErrorContextBuilder` → `CandidateGenerator` → `CandidateDedup` → `CandidateValidator` → `RecoverySelector`. Selectors live in `selector.py`: `DefaultSelector` (first/random), `PMSelector` (wraps any PrefModel), `MemoryPriorSelector`, `LLMSelfSelector`.
- **`tools/`** — `BaseTool` abstract class, `ToolRegistry` with parameter validation. `builtin/` has deterministic tools (json_parse, math_calc, file_read, http_request) with configurable `error_rate` and `error_types` for reproducible failure injection.
- **`llm/`** — `LLMClient` interface. `FakeLLMClient` is deterministic (keeps the pipeline fully local/reproducible). `OpenAICompatibleLLMClient` for real LLMs. `CachedLLMClient` wraps another client for eval consistency.
- **`pref_model/`** — `PrefModel` interface, `MockPrefModel` (oracle), `LightweightPrefModel` (dependency-free ranker), `DPOPrefModel` (LoRA adapter scoring; torch imported lazily).
- **`pref_data/`** — Preference-pair extraction from recovery trajectories. `extractor.py` (DPO pairs), `multi_candidate.py` (outcome-ranked collection), `quality.py` (filtering), `dpo_data.py` (DPO format export).
- **`eval/`** — `runner.py` (`run_eval` orchestrator), `benchmarks.py` (task sets: `recovery_bench_lite`, `recovery_bench_generated`, `recovery_gym`), `baselines.py` (build_baseline selector assembly), `metrics.py` (success/attempt/token accounting + `recovery_trace`), `report.py` (JSON+Markdown output).
- **`trajectory/`** — `TrajectoryStore` is SQLite-backed persistence for tasks/steps/recovery attempts. `TrajectoryCollector` writes during execution.
- **`experience/`** — `ExperienceMemory` retrieval-based prior for successful recovery patterns (ablation baseline).
- **`runtime.py`** — `build_runtime()` assembles all components from `config/default.yaml` (dependency injection root). `main.py` is the CLI entry (`rpl-agent`).

### Key data flow

1. **Execution**: `Executor` calls a tool via `ToolRegistry`; on failure, builds an `ErrorContext`, generates recovery candidates, filters/dedups/validates, and a `Selector` picks one.
2. **Data collection**: Recovery attempts are stored in `TrajectoryStore` (SQLite). `pref_data/extractor.py` reads these to emit DPO-style preference pairs (`PreferencePair`: chosen/rejected candidate under a shared error-context prompt).
3. **Training**: `train_pm.py` (lightweight, dependency-free) or `train_dpo_pm.py` (QLoRA DPO, GPU). The thesis-facing checkpoint is `data/pm_checkpoints/dpo_pm_outcomes` trained from outcome-ranked pairs in `data/pref_pairs_outcomes/`.
4. **Evaluation**: `run_eval.py` builds benchmarks, assembles baselines via `build_baseline()`, runs the executor with each selector, and emits metrics. Real-LLM eval reuses one candidate cache across selectors for fair comparison.

### Config

`config/default.yaml` sets trajectory DB path, agent limits (`max_steps=20`, `max_retries_per_step=3`), recovery defaults (`candidate_count=3`, `default_selector=first`), LLM provider (`fake` by default), and per-tool error rates/types. Override via `build_runtime(config_path, selector_name=..., pm_path=...)`.

### Evaluation record

Recent eval records include a `recovery_trace` field (generated candidates, selected index, PM scores, initial/final tool results) to support failure analysis instead of relying on aggregate metrics alone.

## Repository Conventions

- DPO/PyTorch dependencies must stay lazily imported — only inside `pref_model/dpo.py`, the DPO training scripts, and `DPOPrefModel` construction. The lightweight loop and tests must run in a venv with no torch installed.
- Built-in tools are intentionally deterministic with injectable error rates. Do not add real network/filesystem side effects to `tools/builtin/`; add realistic tools as new `BaseTool` subclasses instead.
- `FakeLLMClient` is the default for reproducibility. Real-LLM eval is opt-in via `provider=openai_compatible` or the `run_real_llm_eval.py` script.
- Eval report artifacts under `data/eval/` are checked in (both `.json` and `.md`). Preference-pair datasets under `data/pref_pairs*/` and checkpoints under `data/pm_checkpoints/` are also committed.
- The repo contains Chinese-language planning/thesis docs (`*.md` at repo root). These track research direction and experiment status; treat them as authoritative for project intent alongside `README.md`.

## Model naming for reports

Use `dpo_pm_r3` in reports for multi-round DPO_PM evaluation with a three-retry budget. Baseline names map to `BaselineSpec` in `eval/baselines.py`; `_r<N>` suffix overrides `max_retries_per_step`.
