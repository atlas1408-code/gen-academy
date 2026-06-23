"""GitHub read access: PR metadata, raw diff, file contents, and hunk parsing.

Reads are autonomous (Phase 3). Writes (posting comments) come in Phase 6.
A GITHUB_TOKEN is optional for reads but raises the rate limit when present.
"""
from __future__ import annotations

import os
import re
import time

import httpx

from app.state import Hunk

API_ROOT = "https://api.github.com"
_PR_URL_RE = re.compile(r"github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)")
_HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")

_MAX_RETRIES = 4
_BACKOFF_BASE = 1.5
# Cap any single backoff sleep. GitHub's rate-limit reset can be minutes away;
# without this cap a single rate-limited call blocks the whole run for minutes.
# Capping fails fast instead, letting callers degrade / fail open.
_MAX_BACKOFF = 30.0


class GitHubError(RuntimeError):
    """Unrecoverable, run-level GitHub failure (e.g. PR not found)."""

    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


class RateLimitError(GitHubError):
    """Rate-limited after exhausting retries. Distinct from a 404 so callers
    that scan many files (repo_index) can abort early instead of grinding
    through every file behind the limit."""


def parse_pr_url(pr_url: str) -> tuple[str, str, int]:
    m = _PR_URL_RE.search(pr_url)
    if not m:
        raise GitHubError(f"Not a valid GitHub PR URL: {pr_url!r}")
    return m["owner"], m["repo"], int(m["number"])


def _headers(accept: str) -> dict[str, str]:
    h = {"Accept": accept, "X-GitHub-Api-Version": "2022-11-28"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _get(client: httpx.Client, url: str, accept: str) -> httpx.Response:
    """GET with retry/backoff on 5xx and rate-limit, respecting Retry-After."""
    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            resp = client.get(url, headers=_headers(accept))
        except httpx.TransportError as exc:  # network blip
            last_exc = exc
            time.sleep(_BACKOFF_BASE ** attempt)
            continue

        if resp.status_code == 404:
            raise GitHubError(f"Not found: {url}")
        if resp.status_code < 400:
            return resp

        # Rate limit (403/429 with remaining 0) or transient 5xx -> back off.
        rate_limited = resp.status_code in (403, 429) and (
            resp.headers.get("X-RateLimit-Remaining") == "0"
            or "rate limit" in resp.text.lower()
        )
        if resp.status_code >= 500 or rate_limited:
            if attempt < _MAX_RETRIES - 1:
                time.sleep(_retry_after_seconds(resp, attempt))
                continue
            if rate_limited:
                raise RateLimitError(
                    f"GitHub rate limit for {url}", resp.status_code
                )
        # Other 4xx (or retries exhausted) -> permanent.
        raise GitHubError(
            f"GitHub {resp.status_code} for {url}: {resp.text[:200]}", resp.status_code
        )

    raise GitHubError(f"GitHub request failed after retries: {url} ({last_exc})")


def _post(client: httpx.Client, url: str, payload: dict) -> httpx.Response:
    """POST with retry/backoff on 5xx; 4xx raise a status-bearing GitHubError."""
    accept = "application/vnd.github+json"
    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            resp = client.post(url, headers=_headers(accept), json=payload)
        except httpx.TransportError as exc:
            last_exc = exc
            time.sleep(_BACKOFF_BASE ** attempt)
            continue
        if resp.status_code < 400:
            return resp
        if resp.status_code >= 500 and attempt < _MAX_RETRIES - 1:
            time.sleep(_retry_after_seconds(resp, attempt))
            continue
        raise GitHubError(
            f"GitHub {resp.status_code} for POST {url}: {resp.text[:300]}",
            resp.status_code,
        )
    raise GitHubError(f"GitHub POST failed after retries: {url} ({last_exc})")


def post_inline_comment(
    owner: str, repo: str, number: int, *,
    body: str, commit_id: str, path: str, line: int, side: str = "RIGHT",
) -> dict:
    """Post a single inline review comment on a PR line. Raises on 422 if the
    line is not part of the diff (caller should fall back to a general comment)."""
    url = f"{API_ROOT}/repos/{owner}/{repo}/pulls/{number}/comments"
    payload = {
        "body": body, "commit_id": commit_id,
        "path": path, "line": line, "side": side.upper(),
    }
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        return _post(client, url, payload).json()


def post_general_comment(owner: str, repo: str, number: int, body: str) -> dict:
    """Post a general (issue) comment on the PR conversation."""
    url = f"{API_ROOT}/repos/{owner}/{repo}/issues/{number}/comments"
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        return _post(client, url, {"body": body}).json()


def _retry_after_seconds(resp: httpx.Response, attempt: int) -> float:
    if (ra := resp.headers.get("Retry-After")) and ra.isdigit():
        return min(float(ra), _MAX_BACKOFF)
    if reset := resp.headers.get("X-RateLimit-Reset"):
        try:
            return min(max(0.0, float(reset) - time.time()), _MAX_BACKOFF)
        except ValueError:
            pass
    return _BACKOFF_BASE ** attempt


def fetch_pr(pr_url: str) -> tuple[dict, str]:
    """Return (pr_meta, raw_diff) for a PR URL."""
    owner, repo, number = parse_pr_url(pr_url)
    base = f"{API_ROOT}/repos/{owner}/{repo}/pulls/{number}"
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        meta_resp = _get(client, base, "application/vnd.github+json")
        diff_resp = _get(client, base, "application/vnd.github.v3.diff")

    meta = meta_resp.json()
    pr_meta = {
        "owner": owner,
        "repo": repo,
        "number": number,
        "title": meta.get("title"),
        "body": meta.get("body") or "",
        "head_sha": meta.get("head", {}).get("sha"),
        "base_sha": meta.get("base", {}).get("sha"),
        "state": meta.get("state"),
    }
    return pr_meta, diff_resp.text


_LINK_RE = re.compile(
    r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)", re.IGNORECASE
)


def parse_linked_issues(text: str) -> list[int]:
    """Extract issue numbers from 'fixes #12' / 'closes #7' style references."""
    seen: list[int] = []
    for m in _LINK_RE.finditer(text or ""):
        n = int(m.group(1))
        if n not in seen:
            seen.append(n)
    return seen


def fetch_issue(owner: str, repo: str, number: int) -> dict | None:
    """Fetch a linked issue's title/body, or None if unavailable."""
    url = f"{API_ROOT}/repos/{owner}/{repo}/issues/{number}"
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        try:
            resp = _get(client, url, "application/vnd.github+json")
        except GitHubError:
            return None
    d = resp.json()
    return {"number": number, "title": d.get("title"), "body": d.get("body") or ""}


def fetch_tree(owner: str, repo: str, ref: str) -> list[str]:
    """Return all blob (file) paths in the repo at a ref, or [] on failure."""
    url = f"{API_ROOT}/repos/{owner}/{repo}/git/trees/{ref}?recursive=1"
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        try:
            resp = _get(client, url, "application/vnd.github+json")
        except GitHubError:
            return []
    return [t["path"] for t in resp.json().get("tree", []) if t.get("type") == "blob"]


def fetch_file_at(owner: str, repo: str, path: str, ref: str) -> str | None:
    """Fetch raw file content at a ref, or None if it doesn't exist there."""
    url = f"{API_ROOT}/repos/{owner}/{repo}/contents/{path}?ref={ref}"
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        try:
            resp = _get(client, url, "application/vnd.github.raw")
        except RateLimitError:
            raise  # let scanners (repo_index) abort early instead of grinding on
        except GitHubError:
            return None  # benign: file absent at this ref
    return resp.text


def parse_diff(diff_text: str) -> dict[str, list[Hunk]]:
    """Parse a unified diff into {path: [Hunk, ...]} keyed by new-file path."""
    hunks: dict[str, list[Hunk]] = {}
    cur_path: str | None = None
    cur: Hunk | None = None
    new_line = old_line = 0

    for line in diff_text.splitlines():
        if line.startswith("+++ "):
            target = line[4:].strip()
            cur_path = None if target == "/dev/null" else target[2:] if target.startswith("b/") else target
            cur = None
            continue

        if line.startswith("@@"):
            m = _HUNK_RE.match(line)
            if not m or cur_path is None:
                continue
            old_start = int(m.group(1))
            old_count = int(m.group(2) or 1)
            new_start = int(m.group(3))
            new_count = int(m.group(4) or 1)
            cur = Hunk(
                old_start=old_start, old_count=old_count,
                new_start=new_start, new_count=new_count,
                header=line, added_lines=[], removed_lines=[],
            )
            hunks.setdefault(cur_path, []).append(cur)
            new_line, old_line = new_start, old_start
            continue

        if cur is None:
            continue
        if line.startswith("\\"):  # "\ No newline at end of file"
            continue
        if line.startswith("+"):
            cur["added_lines"].append(new_line)
            new_line += 1
        elif line.startswith("-"):
            cur["removed_lines"].append(old_line)
            old_line += 1
        else:  # context line
            new_line += 1
            old_line += 1

    return hunks


def line_in_hunk(path: str, line: int, side: str, hunks: dict[str, list[Hunk]]) -> bool:
    """True if (path, line, side) falls within a changed range of some hunk.

    Used to decide inline (postable) vs. general comment placement.
    """
    for h in hunks.get(path, []):
        if side.upper() == "LEFT":
            if h["old_start"] <= line < h["old_start"] + h["old_count"]:
                return True
        else:  # RIGHT
            if h["new_start"] <= line < h["new_start"] + h["new_count"]:
                return True
    return False


def finding_in_hunk(finding: dict, hunks: dict[str, list[Hunk]]) -> bool:
    """line_in_hunk for a Finding dict (path/line/side)."""
    return line_in_hunk(
        finding.get("path", ""),
        int(finding.get("line", 0)),
        finding.get("side", "RIGHT"),
        hunks,
    )
