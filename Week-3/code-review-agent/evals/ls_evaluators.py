"""LangSmith evaluators for the code-review agent.

`judged_metrics` is the LLM-as-judge evaluator: it scores every finding the
agent produced with the INDEPENDENT judge (evals/judge.py, a different model
family than any reviewer) and emits precision, recall, and false-positive count
in one pass — so the judge is called once per finding, not once per metric.

The remaining evaluators are code-based and read straight off the target's
output (no model calls): latency, cost (tokens), and degraded-agent count.

Each evaluator takes (run, example):
  run.outputs      = review_target(...) return value
  example.outputs  = {"expected": [known issues]}
"""
from __future__ import annotations

from evals.judge import judge_finding


def judged_metrics(run, example) -> dict:
    """LLM-as-judge: precision + recall + FP count for one PR."""
    outputs = run.outputs or {}
    findings = outputs.get("findings", []) or []
    diff = outputs.get("diff", "") or ""
    expected = (example.outputs or {}).get("expected", []) or []

    valid = invalid = uncertain = 0
    matched: set[str] = set()
    for f in findings:
        vd = judge_finding(f, diff, expected)
        if vd.verdict == "valid":
            valid += 1
            if vd.matched_known_id:
                matched.add(vd.matched_known_id)
        elif vd.verdict == "invalid":
            invalid += 1
        else:
            uncertain += 1

    results = [
        {"key": "n_findings", "score": len(findings)},
        {"key": "n_valid", "score": valid},
        {"key": "fp_count", "score": invalid},
    ]

    denom = valid + invalid
    if denom:
        results.append({"key": "precision", "score": valid / denom})

    if expected:
        caught = sum(1 for k in expected if k.get("id") in matched)
        results.append({
            "key": "recall",
            "score": caught / len(expected),
            "comment": f"caught {caught}/{len(expected)} known issues",
        })

    return {"results": results}


def latency(run, example) -> dict:
    """Code-based: end-to-end review latency in seconds."""
    return {"key": "latency_s", "score": (run.outputs or {}).get("latency_s", 0)}


def cost_tokens(run, example) -> dict:
    """Code-based: agent token usage for this PR (cost proxy)."""
    return {"key": "agent_tokens", "score": (run.outputs or {}).get("tokens", 0)}


def degraded_count(run, example) -> dict:
    """Code-based: how many specialist agents degraded (resilience signal)."""
    d = (run.outputs or {}).get("degraded", []) or []
    return {"key": "degraded_count", "score": len(d), "comment": ",".join(d) or "none"}


ALL_EVALUATORS = [judged_metrics, latency, cost_tokens, degraded_count]
