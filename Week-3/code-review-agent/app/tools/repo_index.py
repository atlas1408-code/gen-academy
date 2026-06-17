"""Repo-aware context (improvement #2, lite — no vector DB).

Given the symbols changed in a PR, find where they are referenced *elsewhere* in
the repository so the agents can reason about blast radius (e.g. a signature
change that affects other call sites). Bounded and fail-open: lists the repo tree
in one call, then scans a capped number of source files for the symbols.
"""
from __future__ import annotations

import re
from pathlib import Path

from app.tools import github

_CODE_EXT = {".py"}                 # v1 is Python-only (matches tree-sitter/ruff)
_MAX_FILES = 40                     # cap files scanned (cost/latency guard)
_MAX_REFS_PER_SYMBOL = 6


_MAX_TEST_FILES = 25


def is_test_file(path: str) -> bool:
    """Heuristic for a Python test file across common layouts."""
    if not path.endswith(".py"):
        return False
    base = path.rsplit("/", 1)[-1]
    return (base.startswith("test_") or base.endswith("_test.py")
            or "/tests/" in f"/{path}" or "/test/" in f"/{path}")


def load_test_corpus(owner: str, repo: str, ref: str) -> str | None:
    """Concatenated contents of the repo's test files (capped), or None if the
    tree can't be read / there are no test files (so callers stay conservative)."""
    if not (owner and repo and ref):
        return None
    paths = [p for p in github.fetch_tree(owner, repo, ref) if is_test_file(p)]
    paths = paths[:_MAX_TEST_FILES]
    if not paths:
        return None
    parts = [s for p in paths if (s := github.fetch_file_at(owner, repo, p, ref))]
    return "\n".join(parts) if parts else None


def find_references(
    owner: str, repo: str, ref: str, symbols: list[str], exclude_paths: set[str],
) -> dict[str, list[dict]]:
    """Return {symbol: [{path, line, snippet}, ...]} for cross-file usages."""
    symbols = [s for s in symbols if s and len(s) >= 3]  # skip noisy short names
    if not symbols or not ref:
        return {}

    paths = [
        p for p in github.fetch_tree(owner, repo, ref)
        if Path(p).suffix in _CODE_EXT and p not in exclude_paths
    ][:_MAX_FILES]

    patterns = {s: re.compile(rf"\b{re.escape(s)}\b") for s in symbols}
    refs: dict[str, list[dict]] = {s: [] for s in symbols}

    for path in paths:
        src = github.fetch_file_at(owner, repo, path, ref)
        if not src:
            continue
        for lineno, line in enumerate(src.splitlines(), 1):
            for s, pat in patterns.items():
                if len(refs[s]) < _MAX_REFS_PER_SYMBOL and pat.search(line):
                    refs[s].append(
                        {"path": path, "line": lineno, "snippet": line.strip()[:120]}
                    )

    return {s: v for s, v in refs.items() if v}
