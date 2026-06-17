"""human_gate node — pauses for human approval, finalizes the decision.

Uses LangGraph's `interrupt(...)`: the graph stops here and surfaces the payload;
it resumes via `Command(resume=<decision>)`.

Decision shape:
  {"action": "approve", "rejected": [<finding index>, ...]}   # rejected are dropped
  {"action": "reject"}                                          # post nothing
  {"action": "refine", "refine": [{"index": i, "instruction": "..."}]}

Refine regenerates the named comment(s) via the consolidate model, stores the new
text in a `refinements` overlay (keyed "path|line|side"), and routes back through
consolidate -> gate so the human sees the updated comment before approving.
"""
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import interrupt

from app.db import repo
from app.models import get_model
from app.state import ReviewState


def _finding_key(f: dict) -> str:
    return f"{f['path']}|{f['line']}|{f['side']}"


def _regenerate_suggestion(problem: str, original: str, instruction: str) -> str:
    llm = get_model("consolidate")
    prompt = (
        "Rewrite the suggested fix for a code-review finding per the instruction. "
        "Keep it concise and actionable. Return ONLY the rewritten suggestion text "
        "(no preamble, no markdown headers).\n\n"
        f"Problem being addressed:\n{problem}\n\n"
        f"Original suggestion:\n{original}\n\n"
        f"Instruction:\n{instruction}"
    )
    resp = llm.invoke([HumanMessage(content=prompt)])
    text = resp.content if isinstance(resp.content, str) else str(resp.content)
    return text.strip() or original


def human_gate(state: ReviewState, config: RunnableConfig) -> dict:
    findings = state.get("consolidated", state.get("findings", []))
    payload = {
        "type": "approval_request",
        "pr_url": state.get("pr_url"),
        "summary": f"{len(findings)} finding(s) ready for review",
        "findings": findings,
        "suppressed": state.get("suppressed", []),
        "degraded_agents": state.get("degraded_agents", []),
    }
    decision = interrupt(payload)
    action = (decision or {}).get("action", "unknown")
    print(f"[human_gate] resumed with action={action}")

    run_id = config["configurable"]["thread_id"]
    repo.record_approval(run_id, action, edits=decision)

    if action == "refine":
        refinements = dict(state.get("refinements", {}))
        for item in (decision or {}).get("refine", []):
            idx = item.get("index")
            if idx is None or not (0 <= idx < len(findings)):
                continue
            f = findings[idx]
            new_text = _regenerate_suggestion(
                f.get("problem", ""), f.get("suggestion", ""),
                item.get("instruction", ""),
            )
            refinements[_finding_key(f)] = new_text
            print(f"[human_gate] refined suggestion for {f['path']}:{f['line']}")
        return {"decision": decision, "refinements": refinements}

    return {"decision": decision}


def route_after_gate(state: ReviewState) -> str:
    """approve -> post_comments; refine -> consolidate (loop); reject/else -> END."""
    action = (state.get("decision") or {}).get("action")
    if action == "approve":
        return "post_comments"
    if action == "refine":
        return "consolidate"
    return "__end__"
