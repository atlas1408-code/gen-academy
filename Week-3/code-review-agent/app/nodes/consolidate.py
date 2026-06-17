"""consolidate node (Phase 5).

Takes the raw union of agent findings and produces a clean, postable set:
  1. validate `in_hunk` for each finding against the parsed diff hunks
  2. dedupe by (path, line, side) — merge agents, union rationales, keep the
     highest severity
  3. sort by severity (critical -> low)
The result is written to `consolidated` (last-write-wins) and persisted. The raw
`findings` key keeps the per-agent union (it has an additive reducer).
"""
from langchain_core.runnables import RunnableConfig

from app.db import repo
from app.format import compose_comment
from app.progress import emit
from app.state import Finding, ReviewState
from app.tools import github

_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _merge_group(group: list[Finding]) -> Finding:
    """Merge findings that share (path, line, side) into one (keep highest severity)."""
    top = min(group, key=lambda f: _SEVERITY_ORDER.get(f["severity"], 99))
    agents = "+".join(sorted({f["agent"] for f in group}))
    problems = " | ".join(
        dict.fromkeys(f.get("problem", "") for f in group if f.get("problem"))
    )
    # a group is deterministic if any member is — keeps it exempt from suppression
    source = ("deterministic"
              if any(f.get("source") == "deterministic" for f in group)
              else top.get("source", ""))
    return Finding(
        agent=agents,
        path=top["path"],
        line=top["line"],
        side=top["side"],
        symbol=top.get("symbol", ""),
        severity=top["severity"],
        title=top.get("title", ""),
        problem=problems or top.get("problem", ""),
        suggestion=top.get("suggestion", ""),
        source=source,
        confidence=top.get("confidence", ""),
        draft_comment=top.get("draft_comment", ""),
        in_hunk=top["in_hunk"],
    )


def consolidate(state: ReviewState, config: RunnableConfig) -> dict:
    hunks = state.get("hunks", {})
    raw = list(state.get("findings", []))

    # 1. hunk validation
    for f in raw:
        f["in_hunk"] = github.finding_in_hunk(f, hunks)

    # 2. dedupe by (path, line, side)
    groups: dict[tuple, list[Finding]] = {}
    for f in raw:
        groups.setdefault((f["path"], f["line"], f["side"]), []).append(f)
    merged = [_merge_group(g) for g in groups.values()]

    # 3. apply any human refinements (regenerated suggestions from a refine loop),
    #    then (re)compose the postable comment from the structured fields
    refinements = state.get("refinements", {})
    for f in merged:
        key = f"{f['path']}|{f['line']}|{f['side']}"
        if key in refinements:
            f["suggestion"] = refinements[key]
        f["draft_comment"] = compose_comment(f)

    # 4. severity rank
    merged.sort(key=lambda f: _SEVERITY_ORDER.get(f["severity"], 99))

    agents_seen = sorted({f["agent"] for f in raw})
    n_inline = sum(1 for f in merged if f["in_hunk"])
    print(f"[consolidate] {len(raw)} raw -> {len(merged)} after dedupe "
          f"(from {agents_seen}); {n_inline} inline-postable")
    if state.get("degraded_agents"):
        print(f"[consolidate] degraded agents: {state['degraded_agents']}")

    run_id = config["configurable"]["thread_id"]
    repo.upsert_run(run_id, state.get("pr_url"), status="awaiting_approval")
    repo.replace_findings(run_id, merged)

    emit({"stage": "consolidate", "status": "done", "count": len(merged)})
    return {"consolidated": merged}
