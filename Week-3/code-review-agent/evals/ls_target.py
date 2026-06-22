"""LangSmith target: run the agent on one PR to the human-gate interrupt.

Read-only — never approves or posts. Returns the produced findings plus the
diff, degraded agents, latency, and agent token count so the evaluators can
score precision/recall (judge), latency, and cost.

Each call uses a unique thread_id: the Postgres checkpointer + additive
`findings` reducer would otherwise leak a previous run's findings into this one.
"""
from __future__ import annotations

import time
import uuid

import psycopg

from app.db.repo import DATABASE_URL
from app.graph import build_graph, open_pg_checkpointer


def _agent_tokens(run_id: str) -> int:
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            row = conn.execute(
                "SELECT COALESCE(SUM(total_tokens), 0) FROM token_usage "
                "WHERE run_id = %s",
                (run_id,),
            ).fetchone()
        return int(row[0]) if row else 0
    except Exception:
        return 0


def review_target(inputs: dict) -> dict:
    """LangSmith target fn. inputs = {"pr_url": str, "name": str}."""
    name = inputs.get("name", "pr")
    run_id = f"lseval-{name}-{uuid.uuid4().hex[:8]}"
    cfg = {"configurable": {"thread_id": run_id}}

    t0 = time.perf_counter()
    with open_pg_checkpointer() as cp:
        graph = build_graph(cp)
        graph.invoke({"pr_url": inputs["pr_url"]}, cfg)
        snap = graph.get_state(cfg)
    latency_s = round(time.perf_counter() - t0, 2)

    v = snap.values or {}
    return {
        "findings": v.get("consolidated", []),
        "suppressed": v.get("suppressed", []),
        "diff": v.get("diff", ""),
        "degraded": v.get("degraded_agents", []),
        "latency_s": latency_s,
        "tokens": _agent_tokens(run_id),
        "run_id": run_id,
    }
