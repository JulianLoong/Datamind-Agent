param(
    [string]$Benchmark = "recovery_bench_lite",
    [string[]]$Baselines = @("fixed_retry", "dpo_pm_r3"),
    [string]$DpoBaseModel = "Qwen/Qwen2.5-0.5B-Instruct",
    [string]$DpoAdapterPath = "data/pm_checkpoints/dpo_pm_outcomes",
    [string]$LlmProvider = "openai_compatible",
    [Parameter(Mandatory = $true)]
    [string]$LlmModel,
    [Parameter(Mandatory = $true)]
    [string]$LlmBaseUrl,
    [string]$LlmApiKey = $env:DEEPSEEK_API_KEY,
    [int]$LlmMaxTokens = 512,
    [string]$LlmCache = "data/eval/real_llm_deepseek_candidates_v3.jsonl",
    [int]$MaxTasks = 8,
    [int]$Repeats = 1,
    [string]$Out = "data/eval/real_llm_deepseek_dpo_pm_r3_smoke.json",
    [string[]]$Splits = @()
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$EvalScript = Join-Path $RepoRoot "scripts\run_real_llm_eval.py"
$SrcPath = Join-Path $RepoRoot "src"

if (-not (Test-Path $Python)) {
    throw "Project Python was not found at $Python. Create or restore .venv before running DPO_PM evals."
}

if ([string]::IsNullOrWhiteSpace($LlmApiKey)) {
    throw "Missing LLM API key. Pass -LlmApiKey or set DEEPSEEK_API_KEY in this shell."
}

$env:PYTHONPATH = $SrcPath

& $Python -c "import sys, torch, transformers, peft; print('using python:', sys.executable); print('torch:', torch.__version__); print('transformers:', transformers.__version__); print('peft:', peft.__version__)"

$pmPathItems = @()
foreach ($baseline in $Baselines) {
    $baseName = if ($baseline -match "^(.*)_r\d+$") { $Matches[1] } else { $baseline }
    if ($baseName -eq "dpo_pm") {
        $pmPathItems += "$baseline=$DpoBaseModel::$DpoAdapterPath"
    }
}
if ($pmPathItems.Count -eq 0) {
    $pmPathItems += "dpo_pm=$DpoBaseModel::$DpoAdapterPath"
}
$evalArgs = @(
    $EvalScript,
    "--benchmark", $Benchmark,
    "--baselines"
) + $Baselines + @(
    "--pm-paths"
) + $pmPathItems + @(
    "--llm-provider", $LlmProvider,
    "--llm-model", $LlmModel,
    "--llm-base-url", $LlmBaseUrl,
    "--llm-api-key", $LlmApiKey,
    "--llm-max-tokens", "$LlmMaxTokens",
    "--llm-cache", $LlmCache,
    "--max-tasks", "$MaxTasks",
    "--repeats", "$Repeats",
    "--out", $Out
)

if ($Splits.Count -gt 0) {
    $evalArgs += @("--splits") + $Splits
}

& $Python @evalArgs
