"""Run the agent over the eval PRs and report PRECISION and RECALL.

For each PR: run the agent to the interrupt (read-only — never approves/posts),
then have an INDEPENDENT judge (evals/judge.py) label every produced finding as
valid / invalid / uncertain and match valid ones to known issues. From that we
compute recall, precision, F1, false-positives-per-PR, a false-positive
taxonomy, and per-agent precision. Results are written to a markdown report, a
per-run artifact (for human spot-checking), and an append-only ledger.

    python -m evals.run_eval
"""
from __future__ import annotations

import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import psycopg
import yaml

from app import config
from app.config import JUDGE_MODEL, MODELS
from app.db.repo import DATABASE_URL
from app.graph import build_graph, open_pg_checkpointer
from evals.judge import judge_finding

_HERE = Path(__file__).parent
_REPORT = _HERE / "last_report.md"
_LEDGER = _HERE / "results_ledger.jsonl"
_LASTRUN = _HERE / "last_run.json"


def _run_pr(pr: dict, run_id: str) -> tuple[list[dict], str, list[str]]:
    # Unique thread_id per run: the Postgres checkpointer + additive `findings`
    # reducer would otherwise leak a previous run's findings into this one.
    cfg = {"configurable": {"thread_id": run_id}}
    with open_pg_checkpointer() as cp:
        graph = build_graph(cp)
        graph.invoke({"pr_url": pr["url"]}, cfg)
        snap = graph.get_state(cfg)
    v = snap.values or {}
    return v.get("consolidated", []), v.get("diff", ""), v.get("degraded_agents", [])


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True
        ).strip()
    except Exception:
        return "unknown"


def _agent_token_totals(run_ids: list[str]) -> dict[str, int]:
    with psycopg.connect(DATABASE_URL) as conn:
        rows = conn.execute(
            "SELECT agent, SUM(total_tokens) FROM token_usage "
            "WHERE run_id = ANY(%s) GROUP BY agent",
            (run_ids,),
        ).fetchall()
    return {a: int(t) for a, t in rows}


def main() -> None:
    spec = yaml.safe_load((_HERE / "prs.yaml").read_text())
    thr = spec.get("thresholds", {})
    prs = spec["prs"]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    run_ids: list[str] = []

    records: list[dict] = []                 # per-finding, for last_run.json
    agent_stats: dict[str, Counter] = defaultdict(Counter)
    fp_types: Counter = Counter()
    cat_expected, cat_caught = Counter(), Counter()
    tot_valid = tot_invalid = tot_uncertain = 0
    tot_expected = tot_caught = 0
    fp_per_pr: list[int] = []
    judge_tokens = 0
    pr_rows: list[dict] = []

    config.log_tracing_status()
    print(f"Eval over {len(prs)} PRs · judge = {JUDGE_MODEL}\n")
    for pr in prs:
        run_id = f"eval-{pr['name']}-{stamp}"
        run_ids.append(run_id)
        findings, diff, degraded = _run_pr(pr, run_id)
        expected = pr.get("expected") or []
        matched: set[str] = set()
        v = i = u = 0

        for f in findings:
            vd = judge_finding(f, diff, expected)
            judge_tokens += vd.tokens
            records.append({
                "pr": pr["name"], "agent": f.get("agent"),
                "path": f.get("path"), "line": f.get("line"),
                "severity": f.get("severity"), "title": f.get("title"),
                "problem": f.get("problem"), "suggestion": f.get("suggestion"),
                "verdict": vd.verdict, "fp_type": vd.fp_type,
                "matched_known_id": vd.matched_known_id, "judge_rationale": vd.rationale,
            })
            for a in str(f.get("agent", "")).split("+"):
                agent_stats[a][vd.verdict] += 1
            if vd.verdict == "valid":
                v += 1
                if vd.matched_known_id:
                    matched.add(vd.matched_known_id)
            elif vd.verdict == "invalid":
                i += 1
                fp_types[vd.fp_type or "unspecified"] += 1
            else:
                u += 1

        tot_valid += v; tot_invalid += i; tot_uncertain += u
        fp_per_pr.append(i)
        caught = sum(1 for k in expected if k["id"] in matched)
        if expected:
            tot_expected += len(expected); tot_caught += caught
        for k in expected:
            cat_expected[k["category"]] += 1
            if k["id"] in matched:
                cat_caught[k["category"]] += 1

        pr_rows.append({"name": pr["name"], "n": len(findings), "valid": v,
                        "invalid": i, "uncertain": u, "caught": caught,
                        "expected": len(expected), "degraded": degraded})
        deg = f" · degraded={degraded}" if degraded else ""
        print(f"  {pr['name']:<26} findings={len(findings):>2} "
              f"valid={v} invalid={i} uncertain={u} "
              f"recall={caught}/{len(expected)}{deg}")

    recall = tot_caught / tot_expected if tot_expected else 0.0
    precision = tot_valid / (tot_valid + tot_invalid) if (tot_valid + tot_invalid) else None
    f1 = (2 * precision * recall / (precision + recall)
          if precision and (precision + recall) else 0.0)
    avg_fp = sum(fp_per_pr) / len(fp_per_pr) if fp_per_pr else 0.0

    # threshold pass/fail
    checks = {
        "recall_overall": (recall, thr.get("recall_overall"), recall >= thr.get("recall_overall", 0)),
        "precision_overall": (precision or 0, thr.get("precision_overall"),
                              (precision or 0) >= thr.get("precision_overall", 0)),
        "max_fp_per_pr": (avg_fp, thr.get("max_fp_per_pr"), avg_fp <= thr.get("max_fp_per_pr", 1e9)),
    }
    passed = all(c[2] for c in checks.values())

    agent_tokens = _agent_token_totals(run_ids)

    # ---------- report ----------
    L: list[str] = []
    pct = lambda x: f"{x*100:.0f}%" if x is not None else "n/a"
    L.append(f"# Eval report — {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}")
    L.append("")
    L.append(f"**{'PASS' if passed else 'FAIL'}** · "
             f"recall {pct(recall)} · precision {pct(precision)} · "
             f"F1 {f1*100:.0f}% · {avg_fp:.1f} false positives/PR")
    L.append("")
    L.append(f"- models: {', '.join(sorted(set(MODELS.values())))}")
    L.append(f"- judge: {JUDGE_MODEL}")
    L.append(f"- findings judged: valid={tot_valid} invalid={tot_invalid} uncertain={tot_uncertain}")
    L.append("")
    L.append("## Thresholds")
    L.append("| metric | value | target | |")
    L.append("|---|---|---|---|")
    L.append(f"| recall | {pct(recall)} | ≥{pct(thr.get('recall_overall'))} | {'✅' if checks['recall_overall'][2] else '❌'} |")
    L.append(f"| precision | {pct(precision)} | ≥{pct(thr.get('precision_overall'))} | {'✅' if checks['precision_overall'][2] else '❌'} |")
    L.append(f"| FP/PR | {avg_fp:.1f} | ≤{thr.get('max_fp_per_pr')} | {'✅' if checks['max_fp_per_pr'][2] else '❌'} |")
    L.append("")
    L.append("## Recall by category")
    L.append("| category | caught / expected |")
    L.append("|---|---|")
    for cat in sorted(cat_expected):
        L.append(f"| {cat} | {cat_caught[cat]}/{cat_expected[cat]} |")
    L.append("")
    L.append("## Precision by agent (raw)")
    L.append("| agent | valid | invalid | uncertain | precision |")
    L.append("|---|---|---|---|---|")
    for a in sorted(agent_stats):
        s = agent_stats[a]
        denom = s["valid"] + s["invalid"]
        p = f"{s['valid']/denom*100:.0f}%" if denom else "n/a"
        L.append(f"| {a} | {s['valid']} | {s['invalid']} | {s['uncertain']} | {p} |")
    L.append("")
    L.append("## False-positive taxonomy")
    if fp_types:
        L.append("| type | count |")
        L.append("|---|---|")
        for t, c in fp_types.most_common():
            L.append(f"| {t} | {c} |")
    else:
        L.append("_(no false positives)_")
    L.append("")
    L.append("## Per-PR")
    L.append("| PR | findings | valid | invalid | recall | degraded |")
    L.append("|---|---|---|---|---|---|")
    for r in pr_rows:
        rec = f"{r['caught']}/{r['expected']}" if r["expected"] else "— (precision only)"
        L.append(f"| {r['name']} | {r['n']} | {r['valid']} | {r['invalid']} | {rec} | {','.join(r['degraded']) or '—'} |")
    L.append("")
    L.append("## Cost (tokens)")
    L.append(f"- agent tokens (this eval): {sum(agent_tokens.values())} "
             f"({', '.join(f'{a}={t}' for a, t in sorted(agent_tokens.items()))})")
    L.append(f"- judge tokens: {judge_tokens}")

    report = "\n".join(L) + "\n"
    _REPORT.write_text(report)
    _LASTRUN.write_text(json.dumps(records, indent=2))

    ledger_row = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "commit": _git_commit(), "judge": JUDGE_MODEL,
        "recall": round(recall, 3), "precision": round(precision, 3) if precision else None,
        "f1": round(f1, 3), "fp_per_pr": round(avg_fp, 2),
        "valid": tot_valid, "invalid": tot_invalid, "uncertain": tot_uncertain,
        "passed": passed,
    }
    with _LEDGER.open("a") as fh:
        fh.write(json.dumps(ledger_row) + "\n")

    print("\n" + report)
    print(f"Wrote {_REPORT.name}, {_LASTRUN.name}; appended to {_LEDGER.name}")
    print(f"\n{'PASS ✅' if passed else 'FAIL ❌'}")


if __name__ == "__main__":
    main()
