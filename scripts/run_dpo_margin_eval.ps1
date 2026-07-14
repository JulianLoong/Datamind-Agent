param(
    [string]$BaseModel = "Qwen/Qwen2.5-0.5B-Instruct",
    [string]$AdapterPath = "data/pm_checkpoints/dpo_pm_outcomes",
    [string]$Pairs = "data/pref_pairs_outcomes/val.jsonl",
    [double]$GiveUpPenalty = -5.0,
    [int]$BootstrapSamples = 10000,
    [string]$PairwiseOut = "data/eval/dpo_pairwise_margin.json",
    [string]$ControlledOut = "data/eval/dpo_controlled_smoke.json"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$PairwiseScript = Join-Path $RepoRoot "scripts\eval_dpo_margin.py"
$ControlledScript = Join-Path $RepoRoot "scripts\run_dpo_controlled_smoke.py"

if (-not (Test-Path $Python)) {
    throw "Project Python was not found at $Python."
}

$env:PYTHONPATH = Join-Path $RepoRoot "src"

& $Python $PairwiseScript `
    --pairs $Pairs `
    --base-model $BaseModel `
    --adapter $AdapterPath `
    --give-up-penalty $GiveUpPenalty `
    --bootstrap-samples $BootstrapSamples `
    --out $PairwiseOut

& $Python $ControlledScript `
    --base-model $BaseModel `
    --adapter $AdapterPath `
    --give-up-penalty $GiveUpPenalty `
    --out $ControlledOut
