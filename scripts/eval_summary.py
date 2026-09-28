#!/usr/bin/env python3
"""Render a claude plugin eval aggregate-result.json as a markdown summary."""

import datetime
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")


def fmt(n):
    return f"{n:.2f}" if isinstance(n, (int, float)) else "-"


def render(result):
    generated = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Weekly eval results (with/without plugin)",
        "",
        f"Generated {generated} · Claude Code {result.get('claudeVersion', '?')}"
        f" · cost ${fmt(result.get('costUsd'))}"
        f" · {round(result.get('durationSeconds', 0))}s",
        "",
    ]

    if result.get("partial"):
        lines += [f"**Partial run:** {result.get('partialReason', 'unknown reason')}", ""]

    agg = result.get("aggregates", {})
    lines += [
        f"Suite score: **{fmt(agg.get('overallScore'))}** · "
        f"mean Δ **{fmt(agg.get('meanDelta'))}** · "
        f"{agg.get('casesPassed', '?')}/{agg.get('casesTotal', '?')} cases at threshold",
        "",
        "| Case | With | W/out | Δ |",
        "| --- | --- | --- | --- |",
    ]

    for case in sorted(result.get("cases", []), key=lambda c: c.get("name", "")):
        case_agg = case.get("aggregates", {})
        score = case_agg.get("score")
        delta = case_agg.get("delta")
        without = score - delta if isinstance(score, (int, float)) and isinstance(delta, (int, float)) else None
        lines.append(f"| {case.get('name', '?')} | {fmt(score)} | {fmt(without)} | {fmt(delta)} |")

    lines.append("")
    return "\n".join(lines)


def main():
    if len(sys.argv) != 2:
        print("usage: eval_summary.py <aggregate-result.json>", file=sys.stderr)
        sys.exit(1)

    with open(sys.argv[1], encoding="utf-8") as f:
        result = json.load(f)

    print(render(result))


if __name__ == "__main__":
    main()
