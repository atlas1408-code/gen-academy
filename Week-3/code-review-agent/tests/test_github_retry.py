"""GitHub fetch resilience: 5xx retried then surfaced cleanly; 404 is permanent."""
import httpx
import pytest

from app.tools import github
from app.tools.github import GitHubError

_ACCEPT = "application/vnd.github+json"


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    monkeypatch.setattr(github.time, "sleep", lambda *_a, **_k: None)


def _client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_500_then_success_is_retried():
    calls = {"n": 0}

    def handler(_req):
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(500, text="server error")
        return httpx.Response(200, json={"ok": True})

    resp = github._get(_client(handler), "https://api.github.com/x", _ACCEPT)
    assert resp.status_code == 200
    assert calls["n"] == 2  # retried once


def test_persistent_500_surfaces_clean_error():
    calls = {"n": 0}

    def handler(_req):
        calls["n"] += 1
        return httpx.Response(500, text="down")

    with pytest.raises(GitHubError) as exc:
        github._get(_client(handler), "https://api.github.com/x", _ACCEPT)
    assert exc.value.status == 500
    assert calls["n"] == github._MAX_RETRIES  # exhausted retries


def test_rate_limit_then_success_is_retried():
    calls = {"n": 0}

    def handler(_req):
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(
                403, text="API rate limit exceeded",
                headers={"X-RateLimit-Remaining": "0", "Retry-After": "1"},
            )
        return httpx.Response(200, json={"ok": True})

    resp = github._get(_client(handler), "https://api.github.com/x", _ACCEPT)
    assert resp.status_code == 200 and calls["n"] == 2


def test_404_is_permanent_no_retry():
    calls = {"n": 0}

    def handler(_req):
        calls["n"] += 1
        return httpx.Response(404, text="not found")

    with pytest.raises(GitHubError):
        github._get(_client(handler), "https://api.github.com/x", _ACCEPT)
    assert calls["n"] == 1  # not retried
