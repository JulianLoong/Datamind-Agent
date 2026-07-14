from __future__ import annotations

import json

import pytest

from rpl.agent_engine.step import Step
from rpl.eval.real_llm_smoke import (
    _build_episode_registry,
    _semantic_success,
    build_real_llm_smoke_prompt,
    real_llm_smoke_episodes,
    run_real_llm_smoke,
)
from rpl.llm import LLMClient, LLMRequest, LLMResponse
from rpl.pref_model.model import PrefModel
from rpl.recovery.context_builder import ErrorContextBuilder
from rpl.recovery.types import Candidate


class EpisodeLLMClient(LLMClient):
    def __init__(self, responses: dict[str, str]) -> None:
        self.responses = responses
        self.calls: list[LLMRequest] = []

    async def complete(self, request: LLMRequest) -> LLMResponse:
        self.calls.append(request)
        episode_id = next(
            line.removeprefix("Episode ID: ")
            for line in request.prompt.splitlines()
            if line.startswith("Episode ID: ")
        )
        return LLMResponse(self.responses[episode_id], tokens_used=11)


class RepairFirstModel(PrefModel):
    def score(self, error_context, candidate) -> float:
        if candidate.action.startswith("repair_"):
            return 10.0
        if candidate.tool_name is None and (
            "No alternative" in error_context.task_goal
            or "no replacement" in error_context.task_goal
        ):
            return 9.0
        if candidate.action == "retry_same_tool":
            return -2.0
        if candidate.tool_name is None:
            return -10.0
        return 0.0


def _candidate_response(episode) -> str:
    if not episode.recoverable:
        candidates = [
            {
                "reasoning": "The declared resources cannot satisfy the task.",
                "action": "give_up",
                "tool_name": None,
                "tool_params": None,
            }
            for _ in range(3)
        ]
    else:
        assert episode.oracle_call is not None
        candidates = [
            {
                "reasoning": "Use the task-provided recovery constraint.",
                "action": f"repair_{episode.id}",
                "tool_name": episode.oracle_call.tool_name,
                "tool_params": episode.oracle_call.params,
            },
            {
                "reasoning": "No other declared repair is better.",
                "action": "give_up",
                "tool_name": None,
                "tool_params": None,
            },
            {
                "reasoning": "A duplicate conservative stop plan.",
                "action": "give_up",
                "tool_name": None,
                "tool_params": None,
            },
        ]
    return json.dumps({"candidates": candidates})


def test_real_llm_smoke_episodes_have_valid_initial_failures_and_oracles(tmp_path) -> None:
    episodes = real_llm_smoke_episodes()

    assert len(episodes) == 10
    assert sum(episode.recoverable for episode in episodes) == 8
    assert sum(not episode.recoverable for episode in episodes) == 2

    for episode in episodes:
        registry = _build_episode_registry(episode, tmp_path / episode.id)
        initial = registry.execute(episode.initial_call.tool_name, episode.initial_call.params)
        assert initial.success is False
        assert initial.error_type == episode.expected_error_type
        if episode.recoverable:
            assert episode.oracle_call is not None
            result = registry.execute(episode.oracle_call.tool_name, episode.oracle_call.params)
            candidate = Candidate(
                "oracle test only",
                "oracle_test",
                episode.oracle_call.tool_name,
                episode.oracle_call.params,
                "oracle test only",
            )
            assert _semantic_success(episode, candidate, result)
        else:
            assert episode.oracle_call is None
            assert episode.expected_tool_name is None


def test_real_llm_smoke_prompt_exposes_resources_but_not_hidden_oracle(tmp_path) -> None:
    episode = next(
        item for item in real_llm_smoke_episodes() if item.id == "file_missing_primary_with_backup"
    )
    registry = _build_episode_registry(episode, tmp_path)
    result = registry.execute(episode.initial_call.tool_name, episode.initial_call.params)
    step = Step(
        0,
        episode.task_goal,
        episode.initial_call.tool_name,
        episode.initial_call.params,
        result=result,
    )
    ctx = ErrorContextBuilder().build(step, [], episode.task_goal)
    prompt = build_real_llm_smoke_prompt(episode, ctx, registry.list_tools(), candidate_count=3)

    assert "config/backup.json" in prompt
    assert "Never invent a file path or URL" in prompt
    assert '"candidates"' in prompt
    assert "oracle_call" not in prompt
    assert "expected_result" not in prompt


@pytest.mark.asyncio
async def test_real_llm_smoke_separates_coverage_from_selector_ranking() -> None:
    episodes = real_llm_smoke_episodes()
    client = EpisodeLLMClient({episode.id: _candidate_response(episode) for episode in episodes})

    report = await run_real_llm_smoke(
        llm_client=client,
        pref_models={"dpo_pm": RepairFirstModel()},
        episodes=episodes,
    )

    assert report["task_count"] == 10
    assert report["generator_summary"]["parse_success_rate"] == 1.0
    assert report["generator_summary"]["candidate_coverage_at_k"] == 1.0
    assert report["generator_summary"]["hallucinated_resource_rate"] == 0.0
    assert report["selector_summaries"]["dpo_pm"]["top1_success_given_coverage"] == 1.0
    assert report["selector_summaries"]["dpo_pm"]["abstention_accuracy"] == 1.0
    assert (
        report["selector_summaries"]["fixed_order"]["avg_tool_calls"]
        > report["selector_summaries"]["dpo_pm"]["avg_tool_calls"]
    )
    for episode in report["episodes"]:
        fingerprints = {
            result["candidate_pool_fingerprint"] for result in episode["selectors"].values()
        }
        assert fingerprints == {episode["candidate_pool_fingerprint"]}


@pytest.mark.asyncio
async def test_real_llm_parse_failure_does_not_add_error_specific_repair() -> None:
    episode = real_llm_smoke_episodes()[0]
    client = EpisodeLLMClient({episode.id: "not-json"})

    report = await run_real_llm_smoke(llm_client=client, episodes=[episode])

    record = report["episodes"][0]
    assert record["parse_success"] is False
    assert record["llm_candidate_count"] == 0
    assert record["llm_coverage"] is False
    assert [item["source"] for item in record["candidates"]] == [
        "system_control",
        "system_control",
    ]
    assert not any(
        item["candidate"]["action"] == "avoid_zero_division" for item in record["candidates"]
    )


@pytest.mark.asyncio
async def test_hallucinated_file_is_valid_but_not_semantically_successful() -> None:
    episode = next(
        item for item in real_llm_smoke_episodes() if item.id == "file_missing_without_discovery"
    )
    response = json.dumps(
        {
            "candidates": [
                {
                    "reasoning": "Guess a conventional fixture filename.",
                    "action": "read_guessed_file",
                    "tool_name": "file_read",
                    "tool_params": {"path": "fixtures.json"},
                }
            ]
        }
    )
    client = EpisodeLLMClient({episode.id: response})

    report = await run_real_llm_smoke(llm_client=client, episodes=[episode], candidate_count=1)

    candidate = report["episodes"][0]["candidates"][0]
    assert candidate["valid"] is True
    assert candidate["tool_result"]["error_type"] == "file_not_found"
    assert candidate["semantic_success"] is False
    assert candidate["hallucinated_resource"] is True
    assert report["generator_summary"]["hallucinated_resource_rate"] == 1.0


@pytest.mark.asyncio
async def test_give_up_counts_as_decision_not_tool_call() -> None:
    episode = next(
        item
        for item in real_llm_smoke_episodes()
        if item.id == "http_deleted_resource_without_alternative"
    )
    client = EpisodeLLMClient({episode.id: _candidate_response(episode)})

    report = await run_real_llm_smoke(
        llm_client=client,
        pref_models={"dpo_pm": RepairFirstModel()},
        episodes=[episode],
    )

    result = report["episodes"][0]["selectors"]["dpo_pm"]
    assert result["top1_give_up"] is True
    assert result["recovery_decisions"] == 1
    assert result["tool_calls"] == 0
