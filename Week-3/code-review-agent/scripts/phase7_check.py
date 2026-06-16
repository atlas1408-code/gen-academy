"""Phase 7 acceptance: full loop via the HTTP API.

Drives the FastAPI app with TestClient (same ASGI app the browser hits), using
deterministic fake agents so it's fast and free. Proves:
  paste URL -> POST /review -> GET /run -> POST /decision approve -> posted.
Then a second approve confirms idempotency. Cleans up posted comments.
"""
import os

import httpx
import psycopg
from fastapi.testclient import TestClient

import app.nodes.agents as agents
from app.db.repo import DATABASE_URL
from app.tools import github

PR_URL = "https://github.com/atlas1408-code/eval-target-repo/pull/1"
OWNER, REPO = "atlas1408-code", "eval-target-repo"


class _Resp:
    def __init__(self, c): self.content = c; self.usage_metadata = {"input_tokens": 5, "output_tokens": 5}
class _LLM:
    def __init__(self, c): self._c = c
    def invoke(self, _m): return _Resp(self._c)
def _good(line, sev, comment):
    return (f'{{"findings":[{{"path":"app/search.py","line":{line},"side":"RIGHT",'
            f'"severity":"{sev}","rationale":"r","draft_comment":"{comment}"}}]}}')


_FAKES = {
    "security": _LLM(_good(15, "critical", "Use a parameterized query.")),
    "quality":  _LLM(_good(8, "medium", "Move token to env.")),
    "test_gap": _LLM(_good(999, "low", "Add a test.")),
}


def _ledger(head_sha):
    with psycopg.connect(DATABASE_URL) as conn:
        return conn.execute(
            "SELECT path,line,comment_type,github_comment_id FROM posted_comments "
            "WHERE head_sha=%s ORDER BY line", (head_sha,)).fetchall()


def _cleanup(head_sha, token):
    h = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    with httpx.Client(timeout=30) as c:
        for _p, _l, ctype, cid in _ledger(head_sha):
            if not cid: continue
            url = (f"https://api.github.com/repos/{OWNER}/{REPO}/pulls/comments/{cid}"
                   if ctype == "inline" else
                   f"https://api.github.com/repos/{OWNER}/{REPO}/issues/comments/{cid}")
            c.delete(url, headers=h)
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute("DELETE FROM posted_comments WHERE head_sha=%s", (head_sha,)); conn.commit()


def main():
    agents.get_model = lambda a: _FAKES[a]
    from app.api.server import app
    client = TestClient(app)

    head_sha = github.fetch_pr(PR_URL)[0]["head_sha"]
    token = os.environ["GITHUB_TOKEN"]
    _cleanup(head_sha, token)

    print("GET /  ->", client.get("/").status_code, "(serves index.html)")

    print("\nPOST /review …")
    r = client.post("/review", json={"pr_url": PR_URL}).json()
    run_id = r["run_id"]
    print(f"  run_id={run_id} status={r['status']} findings={len(r['findings'])}")
    assert r["status"] == "awaiting_approval"
    assert len(r["findings"]) == 3

    print("GET /run/{id} …")
    g = client.get(f"/run/{run_id}").json()
    assert g["status"] == "awaiting_approval" and len(g["findings"]) == 3

    # severity order -> [critical(15), medium(8), low(999)]; reject the medium.
    print("\nPOST /run/{id}/decision approve (reject idx 1) …")
    d = client.post(f"/run/{run_id}/decision",
                    json={"action": "approve", "rejected": [1]}).json()
    print(f"  status={d['status']} posted={d['posted']}")
    assert d["status"] == "posted" and d["posted"] is True

    rows = _ledger(head_sha)
    print(f"  ledger: {[(p, l, t) for p, l, t, _ in rows]}")
    assert sorted(x[2] for x in rows) == ["general", "inline"]   # inline + general
    assert sorted(x[1] for x in rows) == [15, 999]               # line 8 rejected

    print("\nGET /run/{id} on unknown id ->", client.get("/run/nope").status_code)
    assert client.get("/run/nope").status_code == 404

    print("\nPASS: browser loop works end to end (paste -> review -> approve -> posted).")
    _cleanup(head_sha, token)
    print("Cleaned up test comments.")


if __name__ == "__main__":
    main()
