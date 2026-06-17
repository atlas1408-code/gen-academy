"""verify node (improvement #2) — cut false positives.

Re-checks each consolidated finding against the actual diff with an independent
verifier model, assigns a confidence, and partitions findings into:
  - consolidated: kept (valid + high/medium confidence) — these get surfaced/posted
  - suppressed:   filtered out as likely false positives — kept visible, never posted

One batched verifier call per run. Fails OPEN: if the verifier errors or returns
nothing for a finding, that finding is kept (we never lose a finding to a verifier
hiccup), just marked with unknown confidence.
"""
from __future__ import annotations

from langchain_core.runnables import RunnableConfig

from app.db import repo
from app.models import get_verifier
from app.progress import emit
from app.state import ReviewState
from app.tools.json_repair import call_agent_with_repair

_SYSTEM = (
    "You are a strict verifier whose job is to REDUCE false positives from an "
    "automated code reviewer. For each finding decide whether it is a real, "
    "actionable issue clearly grounded in the diff. Reject hallucinations (claims "
    "about code that is not in the diff), misreadings, pure style nitpicks, and "
    "trivial comments. Be conservative with confidence."
)

# Keep a finding only if it's judged valid AND confidence is high/medium.
_KEEP_CONFIDENCE = {"high", "medium"}


def _prompt(findings: list[dict], diff: str) -> str:
    lines = []
    for i, f in enumerate(findings):
        lines.append(
            f"[{i}] [{f.get('severity')}] {f.get('path')}:{f.get('line')} — "
            f"{f.get('title')}\n"
            f"    problem: {f.get('problem')}\n"
            f"    suggestion: {f.get('suggestion')}"
        )
    return (
        f"## Diff under review\n```diff\n{diff}\n```\n\n"
        f"## Findings to verify (by index)\n" + "\n".join(lines) + "\n\n"
        "For EACH finding, decide if it is a real, actionable issue grounded in "
        "the diff. Return ONLY JSON:\n"
        '{"verdicts": [{"index": int, "verdict": "valid"|"invalid", '
        '"confidence": "high"|"medium"|"low", "reason": str}]}'
    )


def verify(state: ReviewState, config: RunnableConfig) -> dict:
    findings = list(state.get("consolidated", []))
    if not findings:
        return {"suppressed": []}

    emit({"stage": "verify", "status": "running", "n": len(findings)})

    result = call_agent_with_repair(
        get_verifier(), _prompt(findings, state.get("diff", "")),
        "verifier", system=_SYSTEM, max_retries=1,
    )

    verdicts: dict[int, dict] = {}
    if result.ok and isinstance(result.data.get("verdicts"), list):
        for v in result.data["verdicts"]:
            if isinstance(v, dict) and isinstance(v.get("index"), int):
                verdicts[v["index"]] = v

    kept: list[dict] = []
    suppressed: list[dict] = []
    for i, f in enumerate(findings):
        v = verdicts.get(i)
        if v is None:
            # fail open: no verdict for this finding -> keep it, unknown confidence
            f["confidence"] = f.get("confidence") or "unverified"
            kept.append(f)
            continue
        conf = str(v.get("confidence", "")).lower()
        f["confidence"] = conf or "low"
        if v.get("verdict") == "valid" and conf in _KEEP_CONFIDENCE:
            kept.append(f)
        else:
            f["suppress_reason"] = v.get("reason", "")
            suppressed.append(f)

    run_id = config["configurable"]["thread_id"]
    repo.replace_findings(run_id, kept)  # DB reflects what will actually be surfaced

    print(f"[verify] kept {len(kept)} / suppressed {len(suppressed)} "
          f"(verifier {'ok' if result.ok else 'FAILED -> fail-open'})")
    emit({"stage": "verify", "status": "done",
          "kept": len(kept), "suppressed": len(suppressed)})

    return {"consolidated": kept, "suppressed": suppressed}
