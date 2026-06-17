"""Deterministic static-analysis signals (improvement #3).

Runs ruff on the changed file content and returns structured findings. We enable
ruff's pyflakes/pycodestyle (E/F/W), bugbear (B), flake8-bandit security rules
(S), comprehensions (C4) and simplify (SIM) — so a single fast tool grounds both
the quality and security agents (e.g. S608 hardcoded-SQL, B006 mutable default,
E722 bare except). Fails open: if ruff isn't available or errors, returns [].
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

_SELECT = "E,F,W,B,S,C4,SIM"


def _ruff_bin() -> str | None:
    cand = Path(sys.executable).with_name("ruff")
    return str(cand) if cand.exists() else shutil.which("ruff")


def run_ruff(path: str, source: str) -> list[dict]:
    """Return ruff findings for one file's source, or [] on any failure."""
    if not path.endswith(".py") or not source:
        return []
    ruff = _ruff_bin()
    if not ruff:
        return []
    try:
        proc = subprocess.run(
            [ruff, "check", "--select", _SELECT, "--output-format", "json",
             "--stdin-filename", path, "-"],
            input=source, capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    try:
        items = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError:
        return []

    out: list[dict] = []
    for it in items:
        loc = it.get("location") or {}
        out.append({
            "tool": "ruff",
            "code": it.get("code"),
            "line": loc.get("row"),
            "message": (it.get("message") or "").strip(),
        })
    return out


def signals_on_lines(signals: list[dict], lines: set[int]) -> list[dict]:
    """Keep only signals on the given (changed) lines; if none match, keep all."""
    scoped = [s for s in signals if s.get("line") in lines]
    return scoped or signals
