param(
    [string]$LlmModel = "deepseek-chat",
    [string]$LlmBaseUrl = "https://api.deepseek.com",
    [string]$LlmApiKey = $env:DEEPSEEK_API_KEY,
    [string]$LlmCache = "data/eval/real_llm_smoke_v1_candidates.jsonl",
    [string]$DpoBaseModel = "Qwen/Qwen2.5-0.5B-Instruct",
    [string]$DpoAdapterPath = "data/pm_checkpoints/dpo_pm_outcomes",
    [double]$GiveUpPenalty = -5.0,
    [string]$Out = "data/eval/real_llm_smoke_v1.json"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$Script = Join-Path $RepoRoot "scripts\run_real_llm_smoke.py"

if (-not (Test-Path $Python)) {
    throw "Project Python was not found at $Python."
}
if ([string]::IsNullOrWhiteSpace($LlmApiKey)) {
    throw "Missing API key. Pass -LlmApiKey or set DEEPSEEK_API_KEY."
}

$env:PYTHONPATH = Join-Path $RepoRoot "src"
& $Python $Script `
    --llm-model $LlmModel `
    --llm-base-url $LlmBaseUrl `
    --llm-api-key $LlmApiKey `
    --llm-cache $LlmCache `
    --dpo-base-model $DpoBaseModel `
    --dpo-adapter $DpoAdapterPath `
    --give-up-penalty $GiveUpPenalty `
    --out $Out
