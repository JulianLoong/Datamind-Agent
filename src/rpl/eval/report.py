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
        "| baseline | failure_tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |",
        "|---|---:|---:|---:|---:|",
    ]
    for baseline, summary in report["summaries"].items():
        lines.append(
            "| {baseline} | {failure_tasks} | {recovery:.3f} | {attempts:.3f} | {total_tokens:.3f} |".format(
                baseline=baseline,
                failure_tasks=summary["failure_tasks"],
                recovery=summary["recovery_success_rate"],
                attempts=summary["avg_recovery_attempts"],
                total_tokens=summary["avg_total_recovery_tokens"],
            )
        )

    _append_grouped_table(
        lines,
        title_prefix="Split",
        grouped=report.get("split_summaries", {}),
    )
    _append_grouped_table(
        lines,
        title_prefix="Failure Type",
        grouped=report.get("failure_type_summaries", {}),
    )
    _append_grouped_table(
        lines,
        title_prefix="Failure Family",
        grouped=report.get("failure_family_summaries", {}),
    )
    return "\n".join(lines) + "\n"


def _append_grouped_table(
    lines: list[str],
    *,
    title_prefix: str,
    grouped: dict,
) -> None:
    group_names = sorted({group for summaries in grouped.values() for group in summaries})
    for group_name in group_names:
        lines.extend(
            [
                "",
                f"## {title_prefix}: {group_name}",
                "",
                "| baseline | tasks | recovery_success_rate | avg_recovery_attempts | avg_total_recovery_tokens |",
                "|---|---:|---:|---:|---:|",
            ]
        )
        for baseline, summaries in grouped.items():
            summary = summaries.get(group_name)
            if summary is None:
                continue
            lines.append(
                "| {baseline} | {tasks} | {recovery:.3f} | {attempts:.3f} | {total_tokens:.3f} |".format(
                    baseline=baseline,
                    tasks=summary["tasks"],
                    recovery=summary["recovery_success_rate"],
                    attempts=summary["avg_recovery_attempts"],
                    total_tokens=summary["avg_total_recovery_tokens"],
                )
            )
