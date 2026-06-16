"""Run the agent over the eval PRs and report a hit rate vs. expected findings.

Runs each PR to the human-gate interrupt (read-only — never approves/posts),
matches produced findings against the expected set in prs.yaml, and writes a
markdown report. Target reference: 8 of 10 (per the build plan).

    python -m evals.run_eval
"""
import os
from datetime import datetime, timezone
from pathlib import Path

import yaml

from app.graph import build_graph, open_pg_checkpointer

_HERE = Path(__file__).parent
_REPORT = _HERE / "last_report.md"


def _basename(path: str) -> str:
    return path.rsplit("/", 1)[-1]


def _produced_findings(pr_url: str, run_id: str) -> tuple[list[dict], list[str]]:
    """Run one PR to the interrupt; return (raw findings union, degraded agents)."""
    cfg = {"configurable": {"thread_id": run_id}}
    with open_pg_checkpointer() as cp:
        graph = build_graph(cp)
        graph.invoke({"pr_url": pr_url}, cfg)
        snap = graph.get_state(cfg)
    values = snap.values or {}
    return values.get("findings", []), values.get("degraded_agents", [])


def _is_caught(expected: dict, produced: list[dict]) -> dict | None:
    """Return the matching produced finding (or None) for an expected issue."""
    want_file = _basename(expected["path"])
    keywords = [k.lower() for k in expected["keywords"]]
    for f in produced:
        if _basename(f.get("path", "")) != want_file:
            continue
        hay = " ".join(str(f.get(k, "")) for k in
                       ("title", "problem", "suggestion", "draft_comment")).lower()
        if any(k in hay for k in keywords):
            return f
    return None


def main() -> None:
    spec = yaml.safe_load((_HERE / "prs.yaml").read_text())
    lines: list[str] = []
    total_expected = total_caught = total_findings = 0

    print("Running eval over", len(spec["prs"]), "PRs (this makes real model calls)…\n")
    for pr in spec["prs"]:
        run_id = f"eval-{pr['name']}"
        produced, degraded = _produced_findings(pr["url"], run_id)
        total_findings += len(produced)

        pr_caught = 0
        rows = []
        for exp in pr["expected"]:
            match = _is_caught(exp, produced)
            caught = match is not None
            pr_caught += caught
            who = match["agent"] if match else "—"
            rows.append((exp["id"], caught, who))

        total_expected += len(pr["expected"])
        total_caught += pr_caught
        deg = f"  (degraded: {', '.join(degraded)})" if degraded else ""
        header = (f"### {pr['name']}: {pr_caught}/{len(pr['expected'])} caught"
                  f"  ·  {len(produced)} findings produced{deg}")
        print(header)
        lines.append(header)
        for fid, caught, who in rows:
            mark = "✅" if caught else "❌"
            row = f"- {mark} `{fid}`" + (f" — caught by {who}" if caught else " — MISSED")
            print("  " + row)
            lines.append(row)
        print()
        lines.append("")

    rate = (total_caught / total_expected * 100) if total_expected else 0
    summary = (f"## Eval summary: {total_caught}/{total_expected} expected issues "
               f"caught ({rate:.0f}%)  ·  {total_findings} total findings  ·  "
               f"target 8/10")
    print(summary)

    report = (f"# Eval report — {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}\n\n"
              + summary + "\n\n" + "\n".join(lines) + "\n")
    _REPORT.write_text(report)
    print(f"\nWrote {_REPORT.relative_to(_HERE.parent)}")


if __name__ == "__main__":
    main()
