"""Shared graph state and the Finding record.

`findings` and `degraded_agents` use `operator.add` reducers so the three
specialist agents can run in parallel and each append its own contribution
without clobbering the others.
"""
import operator
from typing import Annotated, Any, Optional, TypedDict


class Finding(TypedDict):
    """A single review observation produced by a specialist agent."""

    agent: str          # which specialist produced it: quality | security | test_gap
    path: str           # file path within the repo
    line: int           # line number the comment targets
    side: str           # "RIGHT" (added/changed) or "LEFT" (removed) — GitHub review side
    symbol: str         # enclosing function/class name (human-readable location)
    severity: str       # critical | high | medium | low
    title: str          # concise headline (<= ~8 words)
    problem: str        # concise reframed feedback: what's wrong and why
    suggestion: str     # concrete suggested fix (may include a short snippet)
    confidence: str     # verifier confidence: high | medium | low | "" (unverified)
    draft_comment: str  # composed markdown body to post (derived from the above)
    in_hunk: bool       # whether `line` falls inside a diff hunk (postable inline)


class Hunk(TypedDict):
    """One @@ hunk from a unified diff, with resolved line ranges."""

    old_start: int
    old_count: int
    new_start: int
    new_count: int
    header: str
    added_lines: list[int]    # new-file (RIGHT) line numbers that were added
    removed_lines: list[int]  # old-file (LEFT) line numbers that were removed


class ReviewState(TypedDict, total=False):
    """End-to-end state for one PR review run (one thread_id)."""

    pr_url: str
    diff: str
    pr_meta: dict[str, Any]            # owner, repo, number, head_sha, title, ...
    hunks: dict[str, list[Hunk]]       # path -> hunks (for inline-postability checks)
    context: dict[str, Any]

    findings: Annotated[list[Finding], operator.add]   # raw union from all agents
    degraded_agents: Annotated[list[str], operator.add]

    consolidated: list[Finding]          # deduped, hunk-validated, verified, ranked
    suppressed: list[Finding]            # filtered out by the verifier as likely FPs
    refinements: dict[str, str]          # "path|line|side" -> regenerated comment
    decision: Optional[dict[str, Any]]   # human gate result, e.g. {"action": "approve"}
    posted: bool
