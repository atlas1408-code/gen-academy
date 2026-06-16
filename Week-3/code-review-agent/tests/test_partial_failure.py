"""One agent failing must not sink the run — the others still produce a review.

Hermetic: GitHub I/O, the models, and the DB repo are all stubbed, so this runs
with no network and no Postgres.
"""
import pytest

import app.nodes.agents as agents_mod
import app.nodes.consolidate as consolidate_mod
import app.nodes.fetch_pr as fetch_mod
from app.db import repo

_DIFF = """\
diff --git a/app/search.py b/app/search.py
new file mode 100644
--- /dev/null
+++ b/app/search.py
@@ -0,0 +1,3 @@
+def search_notes(owner, term):
+    return owner + term
+# end
"""

def _good(line: int) -> str:
    return (
        f'{{"findings":[{{"path":"app/search.py","line":{line},"side":"RIGHT",'
        f'"severity":"medium","rationale":"r","draft_comment":"c"}}]}}'
    )


_GARBAGE = "here are the issues (no json)"


class _Resp:
    def __init__(self, c):
        self.content = c
        self.usage_metadata = {"input_tokens": 1, "output_tokens": 1}


class _LLM:
    def __init__(self, c):
        self._c = c

    def invoke(self, _m):
        return _Resp(self._c)


@pytest.fixture()
def stubbed(monkeypatch):
    # No DB.
    for fn in ("upsert_run", "record_token_usage", "replace_findings",
               "set_run_status", "record_approval"):
        monkeypatch.setattr(repo, fn, lambda *a, **k: None)
    # No network in fetch_pr / build_context.
    monkeypatch.setattr(
        fetch_mod.github, "fetch_pr",
        lambda _url: ({"owner": "o", "repo": "r", "number": 1,
                       "head_sha": "deadbeef", "title": "t"}, _DIFF),
    )
    import app.nodes.build_context as bc_mod
    monkeypatch.setattr(bc_mod.github, "fetch_file_at", lambda *a, **k: None)
    # security degrades (garbage), the other two succeed.
    fakes = {"quality": _LLM(_good(2)), "security": _LLM(_GARBAGE),
             "test_gap": _LLM(_good(3))}
    monkeypatch.setattr(agents_mod, "get_model", lambda a: fakes[a])


def test_one_agent_degrades_others_still_review(stubbed):
    from app.graph import build_graph

    graph = build_graph()  # InMemorySaver
    cfg = {"configurable": {"thread_id": "test-partial"}}
    res = graph.invoke({"pr_url": "https://github.com/o/r/pull/1"}, cfg)

    # Reached the human gate (run did not crash).
    assert "__interrupt__" in res
    payload = res["__interrupt__"][0].value

    assert payload["degraded_agents"] == ["security"]
    agents_with_findings = {f["agent"] for f in payload["findings"]}
    assert "security" not in agents_with_findings
    assert {"quality", "test_gap"}.issubset(agents_with_findings)
    assert len(payload["findings"]) >= 2
