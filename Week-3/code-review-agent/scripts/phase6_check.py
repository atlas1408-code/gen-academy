"""Phase 6 acceptance: gated, safe write.

Runs the full graph twice against eval-target-repo PR #1 with deterministic fake
agents (no token cost), proving:
  1. Approve posts real comments — inline where in-hunk, general otherwise.
  2. One rejected finding is dropped (not posted).
  3. Re-approving the same run posts ZERO duplicates (idempotency ledger).

Cleans up the comments it creates so the eval PR stays tidy.
"""
import httpx

from app.config import NEBIUS_BASE_URL  # noqa: F401 (ensures .env is loaded)
from app.db import repo
from app.db.repo import DATABASE_URL
from app.graph import build_graph, open_pg_checkpointer
from app.tools import github
from langgraph.types import Command

import os
import psycopg

PR_URL = "https://github.com/atlas1408-code/eval-target-repo/pull/1"
OWNER, REPO, NUMBER = "atlas1408-code", "eval-target-repo", 1


class _Resp:
    def __init__(self, content):
        self.content = content
        self.usage_metadata = {"input_tokens": 5, "output_tokens": 5}


class _LLM:
    def __init__(self, content):
        self._c = content

    def invoke(self, _m):
        return _Resp(self._c)


def _good(line, sev, rat, comment):
    return (
        f'{{"findings":[{{"path":"app/search.py","line":{line},"side":"RIGHT",'
        f'"severity":"{sev}","rationale":"{rat}","draft_comment":"{comment}"}}]}}'
    )


_FAKES = {
    "security": _LLM(_good(15, "critical", "SQL injection", "Use a parameterized query.")),
    "quality":  _LLM(_good(8, "medium", "hardcoded token", "Move the token to env.")),
    "test_gap": _LLM(_good(999, "low", "no test", "Add a unit test for search_notes.")),
}


def _run(thread_id: str, decision: dict) -> dict:
    cfg = {"configurable": {"thread_id": thread_id}}
    with open_pg_checkpointer() as cp:
        g = build_graph(cp)
        res = g.invoke({"pr_url": PR_URL}, cfg)
        consolidated = res["__interrupt__"][0].value["findings"]
        print(f"  consolidated order: "
              f"{[(i, f['severity'], f['line'], f['in_hunk']) for i, f in enumerate(consolidated)]}")
        g.invoke(Command(resume=decision), cfg)
    return consolidated


def _ledger_rows(head_sha):
    with psycopg.connect(DATABASE_URL) as conn:
        cur = conn.execute(
            "SELECT path, line, comment_type, github_comment_id FROM posted_comments "
            "WHERE head_sha=%s ORDER BY line", (head_sha,))
        return cur.fetchall()


def _cleanup(head_sha, token):
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    with httpx.Client(timeout=30) as c:
        for path, line, ctype, cid in _ledger_rows(head_sha):
            if not cid:
                continue
            url = (f"https://api.github.com/repos/{OWNER}/{REPO}/pulls/comments/{cid}"
                   if ctype == "inline" else
                   f"https://api.github.com/repos/{OWNER}/{REPO}/issues/comments/{cid}")
            c.delete(url, headers=headers)
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute("DELETE FROM posted_comments WHERE head_sha=%s", (head_sha,))
        conn.commit()


def main():
    import app.nodes.agents as agents
    agents.get_model = lambda a: _FAKES[a]

    repo.init_app_tables()
    pr_meta, _ = github.fetch_pr(PR_URL)
    head_sha = pr_meta["head_sha"]
    token = os.environ["GITHUB_TOKEN"]
    _cleanup(head_sha, token)  # start clean (rerunnable)

    # severity order -> [critical(15), medium(8), low(999)]; reject the medium (idx 1).
    decision = {"action": "approve", "rejected": [1]}

    print("=== RUN 1 (approve, reject idx 1) ===")
    _run("phase6-e2e-1", decision)
    rows1 = _ledger_rows(head_sha)
    print(f"  ledger after run 1: {rows1}")

    print("\n=== RUN 2 (same decision -> idempotent) ===")
    _run("phase6-e2e-2", decision)
    rows2 = _ledger_rows(head_sha)
    print(f"  ledger after run 2: {rows2}")

    types = sorted(r[2] for r in rows1)
    lines = sorted(r[1] for r in rows1)
    assert len(rows1) == 2, f"expected 2 posted, got {len(rows1)}"
    assert types == ["general", "inline"], types          # inline + general
    assert lines == [15, 999], lines                       # line 8 (rejected) absent
    assert len(rows2) == 2, f"re-approve changed ledger: {rows2}"  # no duplicates

    print("\nPASS: inline+general posted; rejected finding dropped; re-approve "
          "added 0 duplicates.")
    _cleanup(head_sha, token)
    print("Cleaned up test comments.")


if __name__ == "__main__":
    main()
