from __future__ import annotations


def summary_markdown(report: dict) -> str:
    lines = [
        f"# {report['benchmark']} Results",
        "",
        f"repeats: {report['repeats']}",
        "",
        "Note: controlled synthetic benchmarks validate the recovery pipeline and ranking behavior; "
        "split-level results should be used when discussing generalization.",
        "",
        "| baseline | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for baseline, summary in report["summaries"].items():
        lines.append(
            "| {baseline} | {success:.3f} | {recovery:.3f} | {attempts:.3f} | {recovered_attempts:.3f} | {calls:.3f} |".format(
                baseline=baseline,
                success=summary["success_rate"],
                recovery=summary["recovery_success_rate"],
                attempts=summary["avg_recovery_attempts"],
                recovered_attempts=summary["avg_recovery_attempts_on_recovered"],
                calls=summary["avg_tool_calls"],
            )
        )

    _append_grouped_table(
        lines,
        title_prefix="Split",
        grouped=report.get("split_summaries", {}),
        attempts_key="avg_recovery_attempts",
        calls_key="avg_tool_calls",
    )
    _append_grouped_table(
        lines,
        title_prefix="Failure Type",
        grouped=report.get("failure_type_summaries", {}),
        attempts_key="avg_recovery_attempts_on_failure_tasks",
        calls_key="avg_tool_calls_on_failure_tasks",
    )
    _append_grouped_table(
        lines,
        title_prefix="Failure Family",
        grouped=report.get("failure_family_summaries", {}),
        attempts_key="avg_recovery_attempts_on_failure_tasks",
        calls_key="avg_tool_calls_on_failure_tasks",
    )
    return "\n".join(lines) + "\n"


def _append_grouped_table(
    lines: list[str],
    *,
    title_prefix: str,
    grouped: dict,
    attempts_key: str,
    calls_key: str,
) -> None:
    group_names = sorted({group for summaries in grouped.values() for group in summaries})
    for group_name in group_names:
        lines.extend(
            [
                "",
                f"## {title_prefix}: {group_name}",
                "",
                "| baseline | tasks | success_rate | recovery_success_rate | avg_recovery_attempts | avg_recovery_attempts_on_recovered | avg_tool_calls |",
                "|---|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for baseline, summaries in grouped.items():
            summary = summaries.get(group_name)
            if summary is None:
                continue
            lines.append(
                "| {baseline} | {tasks} | {success:.3f} | {recovery:.3f} | {attempts:.3f} | {recovered_attempts:.3f} | {calls:.3f} |".format(
                    baseline=baseline,
                    tasks=summary["tasks"],
                    success=summary["success_rate"],
                    recovery=summary["recovery_success_rate"],
                    attempts=summary[attempts_key],
                    recovered_attempts=summary["avg_recovery_attempts_on_recovered"],
                    calls=summary[calls_key],
                )
            )
