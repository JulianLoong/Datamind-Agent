from __future__ import annotations

import hashlib
import json
import random
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from statistics import mean
from typing import Any

from rpl.agent_engine.step import Step
from rpl.llm import LLMClient, LLMRequest
from rpl.pref_model.model import PrefModel
from rpl.recovery.candidate_gen import CandidateParseError, parse_candidates
from rpl.recovery.context_builder import ErrorContextBuilder
from rpl.recovery.types import Candidate, ErrorContext
from rpl.recovery.validator import CandidateValidator
from rpl.tools.base import ToolResult
from rpl.tools.builtin import FileReadTool, HttpRequestTool, JsonParseTool, MathCalcTool
from rpl.tools.registry import ToolRegistry


@dataclass(frozen=True)
class SmokeCall:
    tool_name: str
    params: dict[str, Any]


@dataclass(frozen=True)
class RealLLMSmokeEpisode:
    id: str
    category: str
    task_goal: str
    initial_call: SmokeCall
    expected_error_type: str
    recoverable: bool
    expected_tool_name: str | None = None
    expected_result: Any = None
    oracle_call: SmokeCall | None = None
    sandbox_files: dict[str, str] = field(default_factory=dict)
    http_fixtures: dict[str, Any] = field(default_factory=dict)
    declared_file_paths: tuple[str, ...] = ()
    declared_http_urls: tuple[str, ...] = ()


@dataclass(frozen=True)
class CandidateAudit:
    index: int
    source: str
    candidate: Candidate
    valid: bool
    validation_reason: str
    tool_result: ToolResult | None
    semantic_success: bool
    hallucinated_resource: bool


def real_llm_smoke_episodes() -> list[RealLLMSmokeEpisode]:
    health_url = "https://example.test/health"
    users_url = "https://example.test/users/1"
    health_result = {"status_code": 200, "body": {"status": "ok"}}
    return [
        RealLLMSmokeEpisode(
            id="math_zero_denominator_policy",
            category="math",
            task_goal=(
                "Compute the ratio 12/denominator. The denominator is incorrectly zero. "
                "The task policy explicitly requires using denominator=1 when it is zero."
            ),
            initial_call=SmokeCall("math_calc", {"expression": "12/0"}),
            expected_error_type="division_by_zero",
            recoverable=True,
            expected_tool_name="math_calc",
            expected_result=12.0,
            oracle_call=SmokeCall("math_calc", {"expression": "12/1"}),
        ),
        RealLLMSmokeEpisode(
            id="math_malformed_explicit_expression",
            category="math",
            task_goal=(
                "Calculate 8 + 2. The current math expression is malformed; recover by submitting "
                "a syntactically valid expression for exactly that calculation."
            ),
            initial_call=SmokeCall("math_calc", {"expression": "(8 + 2"}),
            expected_error_type="invalid_expression",
            recoverable=True,
            expected_tool_name="math_calc",
            expected_result=10.0,
            oracle_call=SmokeCall("math_calc", {"expression": "8 + 2"}),
        ),
        RealLLMSmokeEpisode(
            id="json_malformed_known_value",
            category="json",
            task_goal=(
                "Extract user_id from the supplied JSON payload. The intended payload contains "
                "user_id=7 but is missing its closing brace; repair only the JSON syntax."
            ),
            initial_call=SmokeCall("json_parse", {"text": '{"user_id": 7', "field": "user_id"}),
            expected_error_type="invalid_json",
            recoverable=True,
            expected_tool_name="json_parse",
            expected_result=7,
            oracle_call=SmokeCall("json_parse", {"text": '{"user_id": 7}', "field": "user_id"}),
        ),
        RealLLMSmokeEpisode(
            id="json_missing_field_default",
            category="json",
            task_goal=(
                "Extract country from the JSON object. If country is absent, the task policy says "
                "to add country with the string value unknown before parsing."
            ),
            initial_call=SmokeCall("json_parse", {"text": '{"name": "Ada"}', "field": "country"}),
            expected_error_type="missing_field",
            recoverable=True,
            expected_tool_name="json_parse",
            expected_result="unknown",
            oracle_call=SmokeCall(
                "json_parse",
                {"text": '{"name": "Ada", "country": "unknown"}', "field": "country"},
            ),
        ),
        RealLLMSmokeEpisode(
            id="http_wrong_method",
            category="http",
            task_goal=(
                f"Fetch the service health document from {health_url}. The endpoint is read-only; "
                "use a method allowed by the provided tool schema. Allowed URL: " + health_url
            ),
            initial_call=SmokeCall("http_request", {"url": health_url, "method": "POST"}),
            expected_error_type="validation_error",
            recoverable=True,
            expected_tool_name="http_request",
            expected_result=health_result,
            oracle_call=SmokeCall("http_request", {"url": health_url, "method": "GET"}),
            http_fixtures={health_url: {"status": "ok"}, users_url: {"id": 1, "name": "Ada"}},
            declared_http_urls=(health_url, users_url),
        ),
        RealLLMSmokeEpisode(
            id="http_wrong_endpoint_catalog",
            category="http",
            task_goal=(
                "Fetch the service health document. The requested /status endpoint is unavailable. "
                f"The complete allowed endpoint catalog is [{health_url}, {users_url}]."
            ),
            initial_call=SmokeCall("http_request", {"url": "https://example.test/status"}),
            expected_error_type="not_found",
            recoverable=True,
            expected_tool_name="http_request",
            expected_result=health_result,
            oracle_call=SmokeCall("http_request", {"url": health_url}),
            http_fixtures={health_url: {"status": "ok"}, users_url: {"id": 1, "name": "Ada"}},
            declared_http_urls=("https://example.test/status", health_url, users_url),
        ),
        RealLLMSmokeEpisode(
            id="file_missing_primary_with_backup",
            category="file",
            task_goal=(
                "Read the application configuration. config/current.json is unavailable and the "
                "declared fallback is config/backup.json. Allowed sandbox paths: "
                "[config/current.json, config/backup.json]."
            ),
            initial_call=SmokeCall("file_read", {"path": "config/current.json"}),
            expected_error_type="file_not_found",
            recoverable=True,
            expected_tool_name="file_read",
            expected_result='{"mode":"safe"}',
            oracle_call=SmokeCall("file_read", {"path": "config/backup.json"}),
            sandbox_files={"config/backup.json": '{"mode":"safe"}'},
            declared_file_paths=("config/current.json", "config/backup.json"),
        ),
        RealLLMSmokeEpisode(
            id="file_escape_with_safe_copy",
            category="file",
            task_goal=(
                "Read the public notice. The current path escapes the sandbox. An authorized copy "
                "is available at public/notice.txt. Allowed sandbox path: [public/notice.txt]."
            ),
            initial_call=SmokeCall("file_read", {"path": "../notice.txt"}),
            expected_error_type="permission_denied",
            recoverable=True,
            expected_tool_name="file_read",
            expected_result="public notice",
            oracle_call=SmokeCall("file_read", {"path": "public/notice.txt"}),
            sandbox_files={"public/notice.txt": "public notice"},
            declared_file_paths=("../notice.txt", "public/notice.txt"),
        ),
        RealLLMSmokeEpisode(
            id="file_missing_without_discovery",
            category="unrecoverable_file",
            task_goal=(
                "Read reports/final.txt. No alternative path, directory listing, search tool, or "
                "replacement content is available. Do not guess filenames."
            ),
            initial_call=SmokeCall("file_read", {"path": "reports/final.txt"}),
            expected_error_type="file_not_found",
            recoverable=False,
            declared_file_paths=("reports/final.txt",),
        ),
        RealLLMSmokeEpisode(
            id="http_deleted_resource_without_alternative",
            category="unrecoverable_http",
            task_goal=(
                "Fetch the deleted order resource at https://example.test/orders/404. There is no "
                "replacement order endpoint. The only other declared endpoint is the unrelated "
                f"service health endpoint {health_url}; do not substitute unrelated data."
            ),
            initial_call=SmokeCall("http_request", {"url": "https://example.test/orders/404"}),
            expected_error_type="not_found",
            recoverable=False,
            http_fixtures={health_url: {"status": "ok"}},
            declared_http_urls=("https://example.test/orders/404", health_url),
        ),
    ]


def build_real_llm_smoke_prompt(
    episode: RealLLMSmokeEpisode,
    ctx: ErrorContext,
    tools: list[Any],
    *,
    candidate_count: int,
) -> str:
    tool_specs = [
        {"name": tool.name, "description": tool.description, "schema": tool.schema}
        for tool in sorted(tools, key=lambda item: item.name)
    ]
    resources = {
        "allowed_file_paths": list(episode.declared_file_paths),
        "allowed_http_urls": list(episode.declared_http_urls),
    }
    return (
        "You are an agent recovery expert. Generate distinct executable recovery plans.\n"
        f"Episode ID: {episode.id}\n"
        f"Candidate Count: {candidate_count}\n"
        f"Task Goal: {ctx.task_goal}\n"
        f"Current Step: {ctx.step_description}\n"
        f"Failed Tool: {ctx.tool_name}\n"
        f"Tool Params: {json.dumps(ctx.tool_params, ensure_ascii=False)}\n"
        f"Error Type: {ctx.error_type}\n"
        f"Error Message: {ctx.error_message}\n"
        f"Available Tools JSON: {json.dumps(tool_specs, ensure_ascii=False, sort_keys=True)}\n"
        f"Declared Resources JSON: {json.dumps(resources, ensure_ascii=False, sort_keys=True)}\n"
        "Never invent a file path or URL that is not declared above. Do not substitute unrelated "
        "resources merely to make a tool call succeed. If the task cannot be completed from the "
        "declared information, return a give_up plan. Do not include unchanged retries; the system "
        "adds retry and give_up controls separately. Return JSON only in this exact wrapper shape: "
        '{"candidates":[{"reasoning":"...","action":"...","tool_name":"... or null",'
        '"tool_params":{}}]}.'
    )


async def run_real_llm_smoke(
    *,
    llm_client: LLMClient,
    pref_models: dict[str, PrefModel] | None = None,
    provider: str = "openai_compatible",
    model: str = "deepseek-chat",
    base_url: str = "https://api.deepseek.com",
    cache_path: str | None = None,
    candidate_count: int = 3,
    random_seed: int = 17,
    episodes: list[RealLLMSmokeEpisode] | None = None,
) -> dict[str, Any]:
    episodes = episodes or real_llm_smoke_episodes()
    pref_models = pref_models or {}
    episode_records: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix="rpl-real-llm-smoke-") as tmp:
        tmp_root = Path(tmp)
        for episode in episodes:
            record = await _evaluate_episode(
                episode,
                llm_client=llm_client,
                pref_models=pref_models,
                candidate_count=candidate_count,
                random_seed=random_seed,
                tmp_root=tmp_root,
            )
            episode_records.append(record)

    return {
        "benchmark": "real_llm_smoke_v1",
        "positioning": "supplementary smoke test",
        "provider": provider,
        "model": model,
        "base_url": base_url,
        "cache_path": cache_path,
        "candidate_count": candidate_count,
        "task_count": len(episodes),
        "recoverable_tasks": sum(1 for episode in episodes if episode.recoverable),
        "unrecoverable_tasks": sum(1 for episode in episodes if not episode.recoverable),
        "generator_summary": _summarize_generator(episode_records),
        "selector_summaries": _summarize_selectors(episode_records),
        "episodes": episode_records,
    }


async def _evaluate_episode(
    episode: RealLLMSmokeEpisode,
    *,
    llm_client: LLMClient,
    pref_models: dict[str, PrefModel],
    candidate_count: int,
    random_seed: int,
    tmp_root: Path,
) -> dict[str, Any]:
    registry = _build_episode_registry(episode, tmp_root / episode.id / "initial")
    initial_result = registry.execute(episode.initial_call.tool_name, episode.initial_call.params)
    if initial_result.success or initial_result.error_type != episode.expected_error_type:
        raise ValueError(
            f"Episode {episode.id} produced {initial_result.error_type!r}, expected "
            f"{episode.expected_error_type!r}"
        )
    step = Step(
        index=0,
        description=episode.task_goal,
        tool_name=episode.initial_call.tool_name,
        params=dict(episode.initial_call.params),
        result=initial_result,
    )
    ctx = ErrorContextBuilder().build(step, [], episode.task_goal)
    prompt = build_real_llm_smoke_prompt(
        episode, ctx, registry.list_tools(), candidate_count=candidate_count
    )
    request = LLMRequest(prompt=prompt, temperature=0.2, max_tokens=768)
    response = await llm_client.complete(request)
    cache_hit = bool(getattr(llm_client, "last_cache_hit", False))
    cache_key = getattr(llm_client, "last_cache_key", None)

    parse_success = True
    parse_error = ""
    try:
        llm_candidates = parse_candidates(response.text)[:candidate_count]
    except CandidateParseError as exc:
        parse_success = False
        parse_error = str(exc)
        llm_candidates = []

    controls = _system_control_candidates(episode)
    sourced_candidates = [(candidate, "llm_generated") for candidate in llm_candidates]
    sourced_candidates.extend((candidate, "system_control") for candidate in controls)
    audits = [
        _audit_candidate(
            episode,
            candidate,
            source=source,
            index=index,
            tmp_root=tmp_root / episode.id / "audit",
        )
        for index, (candidate, source) in enumerate(sourced_candidates)
    ]
    valid_audits = [audit for audit in audits if audit.valid]
    pool_fingerprint = _pool_fingerprint(audits)

    selector_orders: dict[str, list[CandidateAudit]] = {
        "fixed_order": _fixed_order(valid_audits),
        "random": _random_order(valid_audits, seed=_stable_seed(episode.id, random_seed)),
    }
    for name, pref_model in pref_models.items():
        selector_orders[name] = _preference_order(valid_audits, pref_model, ctx)

    selector_results = {
        name: _execute_order(
            episode,
            order,
            tmp_root=tmp_root / episode.id / "selectors" / name,
            pool_fingerprint=pool_fingerprint,
        )
        for name, order in selector_orders.items()
    }
    llm_audits = [audit for audit in audits if audit.source == "llm_generated"]
    return {
        "id": episode.id,
        "category": episode.category,
        "task_goal": episode.task_goal,
        "recoverable": episode.recoverable,
        "initial_call": asdict(episode.initial_call),
        "expected_error_type": episode.expected_error_type,
        "initial_result": asdict(initial_result),
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "cache_key": cache_key,
        "cache_hit": cache_hit,
        "generation_tokens": response.tokens_used,
        "raw_response": response.text,
        "parse_success": parse_success,
        "parse_error": parse_error,
        "candidate_pool_fingerprint": pool_fingerprint,
        "llm_candidate_count": len(llm_audits),
        "llm_schema_valid_count": sum(1 for audit in llm_audits if audit.valid),
        "llm_semantic_success_count": sum(1 for audit in llm_audits if audit.semantic_success),
        "llm_coverage": any(audit.semantic_success for audit in llm_audits),
        "llm_hallucinated_resource_count": sum(
            1 for audit in llm_audits if audit.hallucinated_resource
        ),
        "candidates": [_audit_to_dict(audit) for audit in audits],
        "selectors": selector_results,
    }


def _system_control_candidates(episode: RealLLMSmokeEpisode) -> list[Candidate]:
    return [
        Candidate(
            reasoning="Retry the failed tool once with unchanged parameters.",
            action="retry_same_tool",
            tool_name=episode.initial_call.tool_name,
            tool_params=dict(episode.initial_call.params),
            raw_text="system_control:retry_same_tool",
        ),
        Candidate(
            reasoning="Stop because no bounded recovery should be attempted.",
            action="give_up",
            tool_name=None,
            tool_params=None,
            raw_text="system_control:give_up",
        ),
    ]


def _audit_candidate(
    episode: RealLLMSmokeEpisode,
    candidate: Candidate,
    *,
    source: str,
    index: int,
    tmp_root: Path,
) -> CandidateAudit:
    registry = _build_episode_registry(episode, tmp_root / str(index))
    validation = CandidateValidator(registry).validate(candidate)
    result: ToolResult | None = None
    if validation.valid and candidate.tool_name is not None:
        result = registry.execute(candidate.tool_name, candidate.tool_params or {})
    return CandidateAudit(
        index=index,
        source=source,
        candidate=candidate,
        valid=validation.valid,
        validation_reason=validation.reason,
        tool_result=result,
        semantic_success=_semantic_success(episode, candidate, result),
        hallucinated_resource=_hallucinated_resource(episode, candidate),
    )


def _semantic_success(
    episode: RealLLMSmokeEpisode,
    candidate: Candidate,
    result: ToolResult | None,
) -> bool:
    return bool(
        episode.recoverable
        and result is not None
        and result.success
        and candidate.tool_name == episode.expected_tool_name
        and result.data == episode.expected_result
    )


def _hallucinated_resource(
    episode: RealLLMSmokeEpisode,
    candidate: Candidate,
) -> bool:
    params = candidate.tool_params or {}
    if candidate.tool_name == "file_read":
        path = params.get("path")
        return isinstance(path, str) and path not in episode.declared_file_paths
    if candidate.tool_name == "http_request":
        url = params.get("url")
        return isinstance(url, str) and url not in episode.declared_http_urls
    return False


def _fixed_order(audits: list[CandidateAudit]) -> list[CandidateAudit]:
    retries = [audit for audit in audits if audit.candidate.action == "retry_same_tool"]
    repairs = [
        audit
        for audit in audits
        if audit.candidate.tool_name is not None and audit.candidate.action != "retry_same_tool"
    ]
    give_ups = [audit for audit in audits if audit.candidate.tool_name is None]
    return retries + repairs + give_ups


def _random_order(audits: list[CandidateAudit], *, seed: int) -> list[CandidateAudit]:
    ordered = list(audits)
    random.Random(seed).shuffle(ordered)
    return ordered


def _preference_order(
    audits: list[CandidateAudit], pref_model: PrefModel, ctx: ErrorContext
) -> list[CandidateAudit]:
    ranked = pref_model.rank(ctx, [audit.candidate for audit in audits])
    return [audits[index] for index, _ in ranked]


def _execute_order(
    episode: RealLLMSmokeEpisode,
    order: list[CandidateAudit],
    *,
    tmp_root: Path,
    pool_fingerprint: str,
) -> dict[str, Any]:
    attempts = 0
    tool_calls = 0
    recovered = False
    selected_give_up = False
    trace: list[dict[str, Any]] = []
    first_success_rank = next(
        (rank for rank, audit in enumerate(order, start=1) if audit.semantic_success), None
    )
    for rank, audit in enumerate(order, start=1):
        attempts += 1
        candidate = audit.candidate
        if candidate.tool_name is None:
            selected_give_up = True
            trace.append(
                {"rank": rank, "candidate_index": audit.index, "give_up": True, "result": None}
            )
            break
        registry = _build_episode_registry(episode, tmp_root / str(rank))
        result = registry.execute(candidate.tool_name, candidate.tool_params or {})
        tool_calls += 1
        success = _semantic_success(episode, candidate, result)
        trace.append(
            {
                "rank": rank,
                "candidate_index": audit.index,
                "give_up": False,
                "result": asdict(result),
                "semantic_success": success,
            }
        )
        if success:
            recovered = True
            break
    return {
        "candidate_pool_fingerprint": pool_fingerprint,
        "ordered_candidate_indices": [audit.index for audit in order],
        "top1_semantic_success": bool(order and order[0].semantic_success),
        "top1_give_up": bool(order and order[0].candidate.tool_name is None),
        "first_success_rank": first_success_rank,
        "recovered": recovered,
        "recovery_decisions": attempts,
        "tool_calls": tool_calls,
        "selected_give_up": selected_give_up,
        "trace": trace,
    }


def _build_episode_registry(episode: RealLLMSmokeEpisode, root: Path) -> ToolRegistry:
    sandbox = root / "sandbox"
    sandbox.mkdir(parents=True, exist_ok=True)
    for relative_path, content in episode.sandbox_files.items():
        target = sandbox / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    registry = ToolRegistry()
    registry.register(JsonParseTool())
    registry.register(MathCalcTool())
    registry.register(FileReadTool(sandbox_dir=sandbox))
    registry.register(HttpRequestTool(fixtures=episode.http_fixtures or None))
    return registry


def _pool_fingerprint(audits: list[CandidateAudit]) -> str:
    payload = [
        {
            "source": audit.source,
            "candidate": asdict(audit.candidate),
            "valid": audit.valid,
        }
        for audit in audits
    ]
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _stable_seed(episode_id: str, seed: int) -> int:
    digest = hashlib.sha256(f"{seed}:{episode_id}".encode()).hexdigest()
    return int(digest[:16], 16)


def _audit_to_dict(audit: CandidateAudit) -> dict[str, Any]:
    return {
        "index": audit.index,
        "source": audit.source,
        "candidate": asdict(audit.candidate),
        "valid": audit.valid,
        "validation_reason": audit.validation_reason,
        "tool_result": asdict(audit.tool_result) if audit.tool_result is not None else None,
        "semantic_success": audit.semantic_success,
        "hallucinated_resource": audit.hallucinated_resource,
    }


def _summarize_generator(records: list[dict[str, Any]]) -> dict[str, Any]:
    recoverable = [record for record in records if record["recoverable"]]
    llm_candidates = sum(record["llm_candidate_count"] for record in records)
    valid_candidates = sum(record["llm_schema_valid_count"] for record in records)
    hallucinated = sum(record["llm_hallucinated_resource_count"] for record in records)
    return {
        "parse_success_rate": _rate(
            sum(record["parse_success"] for record in records), len(records)
        ),
        "schema_valid_candidate_rate": _rate(valid_candidates, llm_candidates),
        "candidate_coverage_at_k": _rate(
            sum(record["llm_coverage"] for record in recoverable), len(recoverable)
        ),
        "hallucinated_resource_rate": _rate(hallucinated, llm_candidates),
        "candidate_generation_tokens": sum(record["generation_tokens"] for record in records),
        "api_tokens_this_run": sum(
            record["generation_tokens"] for record in records if not record["cache_hit"]
        ),
        "cache_hits": sum(record["cache_hit"] for record in records),
        "parsed_llm_candidates": llm_candidates,
    }


def _summarize_selectors(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    names = sorted({name for record in records for name in record["selectors"]})
    summaries: dict[str, dict[str, Any]] = {}
    for name in names:
        covered = [record for record in records if record["recoverable"] and record["llm_coverage"]]
        recoverable = [record for record in records if record["recoverable"]]
        unrecoverable = [record for record in records if not record["recoverable"]]
        results = [record["selectors"][name] for record in records]
        first_ranks = [
            record["selectors"][name]["first_success_rank"]
            for record in covered
            if record["selectors"][name]["first_success_rank"] is not None
        ]
        summaries[name] = {
            "top1_success_given_coverage": _rate(
                sum(record["selectors"][name]["top1_semantic_success"] for record in covered),
                len(covered),
            ),
            "recovery_success_rate": _rate(
                sum(record["selectors"][name]["recovered"] for record in recoverable),
                len(recoverable),
            ),
            "mean_first_success_rank_given_coverage": mean(first_ranks) if first_ranks else 0.0,
            "abstention_accuracy": _rate(
                sum(record["selectors"][name]["top1_give_up"] for record in unrecoverable),
                len(unrecoverable),
            ),
            "avg_recovery_decisions": mean(result["recovery_decisions"] for result in results)
            if results
            else 0.0,
            "avg_tool_calls": mean(result["tool_calls"] for result in results) if results else 0.0,
            "covered_recoverable_cases": len(covered),
        }
    return summaries


def real_llm_smoke_markdown(report: dict[str, Any]) -> str:
    generator = report["generator_summary"]
    lines = [
        "# real_llm_smoke_v1 Results",
        "",
        "Positioning: supplementary smoke test; not a statistical main result.",
        "",
        f"Provider: `{report['provider']}`",
        f"Model: `{report['model']}`",
        f"Tasks: {report['task_count']} ({report['recoverable_tasks']} recoverable, "
        f"{report['unrecoverable_tasks']} unrecoverable)",
        "",
        "## Candidate Generation",
        "",
        "| parse success | schema-valid candidates | coverage@K | "
        "hallucinated resources | tokens | cache hits |",
        "|---:|---:|---:|---:|---:|---:|",
        (
            "| {parse:.3f} | {valid:.3f} | {coverage:.3f} | {hallucination:.3f} | "
            "{tokens} | {hits} |"
        ).format(
            parse=generator["parse_success_rate"],
            valid=generator["schema_valid_candidate_rate"],
            coverage=generator["candidate_coverage_at_k"],
            hallucination=generator["hallucinated_resource_rate"],
            tokens=generator["candidate_generation_tokens"],
            hits=generator["cache_hits"],
        ),
        "",
        "## Selector Results",
        "",
        "| selector | top1 success given coverage | recovery success | first success rank | "
        "abstention | decisions | tool calls |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name, summary in report["selector_summaries"].items():
        lines.append(
            (
                "| {name} | {top1:.3f} | {recovery:.3f} | {rank:.3f} | "
                "{abstention:.3f} | {decisions:.3f} | {calls:.3f} |"
            ).format(
                name=name,
                top1=summary["top1_success_given_coverage"],
                recovery=summary["recovery_success_rate"],
                rank=summary["mean_first_success_rank_given_coverage"],
                abstention=summary["abstention_accuracy"],
                decisions=summary["avg_recovery_decisions"],
                calls=summary["avg_tool_calls"],
            )
        )
    lines.extend(["", "## Per-Episode Audit", ""])
    for episode in report["episodes"]:
        lines.append(
            f"- `{episode['id']}`: parse={episode['parse_success']}, "
            f"llm_candidates={episode['llm_candidate_count']}, "
            f"coverage={episode['llm_coverage']}, "
            f"hallucinated={episode['llm_hallucinated_resource_count']}"
        )
    return "\n".join(lines) + "\n"


def _rate(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0
