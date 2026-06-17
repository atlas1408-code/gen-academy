"""Phase 4 acceptance #2: one agent returns garbage -> it degrades, others still review.

Deterministic (no network): patches the per-agent model so `security` always
emits unparseable text while `quality` and `test_gap` return valid JSON.
"""
from app.db import repo
from app.graph import build_graph


class _FakeResp:
    def __init__(self, content):
        self.content = content
        self.usage_metadata = {"input_tokens": 10, "output_tokens": 5}


class _FakeLLM:
    def __init__(self, content):
        self._content = content

    def invoke(self, _messages):
        return _FakeResp(self._content)


def _good(line: int) -> str:
    return (
        f'{{"findings":[{{"path":"app/search.py","line":{line},"side":"RIGHT",'
        f'"severity":"medium","rationale":"r","draft_comment":"c"}}]}}'
    )


_GARBAGE = "Sure! Here are the issues I found: (no JSON here, just prose)."

# Distinct lines so the two good agents don't dedupe into one another.
_FAKES = {
    "quality": _FakeLLM(_good(2)),
    "security": _FakeLLM(_GARBAGE),   # <- will fail to parse -> degrade
    "test_gap": _FakeLLM(_good(3)),
}


def main() -> None:
    import app.nodes.agents as agents
    import app.nodes.verify as verify
    agents.get_model = lambda agent: _FAKES[agent]   # monkeypatch
    verify.get_verifier = lambda: _FakeLLM('{"verdicts": []}')  # fail-open, no network

    repo.init_app_tables()
    cfg = {"configurable": {"thread_id": "phase4-degrade"}}
    graph = build_graph()  # InMemorySaver is fine here
    res = graph.invoke(
        {"pr_url": "https://github.com/atlas1408-code/eval-target-repo/pull/1"}, cfg
    )
    payload = res["__interrupt__"][0].value
    findings = payload["findings"]
    degraded = payload["degraded_agents"]
    agents_with_findings = sorted({f["agent"] for f in findings})

    print(f"\ndegraded_agents      = {degraded}")
    print(f"agents with findings = {agents_with_findings}")
    print(f"total findings       = {len(findings)}")

    assert degraded == ["security"], f"expected security degraded, got {degraded}"
    assert "security" not in agents_with_findings
    assert {"quality", "test_gap"}.issubset(set(agents_with_findings))
    print("\nPASS: security degraded; quality + test_gap still produced a review.")


if __name__ == "__main__":
    main()
