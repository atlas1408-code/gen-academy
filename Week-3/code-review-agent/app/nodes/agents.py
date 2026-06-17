"""Specialist agent nodes — real Nebius calls (Phase 4).

A node factory produces three specialists (quality, security, test_gap). Each
builds a prompt from the diff + tree-sitter context, calls the model through the
JSON-repair helper, and EITHER appends findings OR appends its name to
`degraded_agents`. A node never raises — agent failures degrade the run.
"""
from __future__ import annotations

from typing import Any

from langchain_core.runnables import RunnableConfig

from app.config import MODELS
from app.db import repo
from app.format import compose_comment
from app.models import get_model
from app.progress import emit
from app.state import Finding, ReviewState
from app.tools.json_repair import call_agent_with_repair

_VALID_SEVERITY = {"critical", "high", "medium", "low"}

_ROLE = {
    "quality": "Reviews readability, duplication, dead code, error handling, "
               "naming, and mutable defaults.",
    "security": "Hunts injection, hardcoded secrets, unsafe deserialization, "
                "SSRF, path traversal, and data exposure.",
    "test_gap": "Flags new or changed public code shipped without tests.",
}

_SYSTEM = {
    "quality": (
        "You are a senior code reviewer focused strictly on CODE QUALITY: "
        "readability, duplication, dead code, error handling, naming, mutable "
        "default arguments, and maintainability. Ignore security and test "
        "coverage — other reviewers handle those."
    ),
    "security": (
        "You are an application security reviewer. Focus strictly on SECURITY "
        "vulnerabilities: injection (SQL/command), hardcoded secrets/credentials, "
        "unsafe deserialization, SSRF, path traversal, and data exposure. Ignore "
        "style and test coverage."
    ),
    "test_gap": (
        "You are a test-coverage reviewer. Focus strictly on TEST GAPS: new or "
        "changed public functions/branches that ship without corresponding tests. "
        "Use the provided context (whether a matching test file exists) to judge. "
        "Ignore style and security."
    ),
}

_SCHEMA_INSTRUCTIONS = (
    "Return ONLY a single JSON object, no prose or markdown, with this schema:\n"
    '{"findings": [{\n'
    '  "path": str, "line": int, "side": "RIGHT"|"LEFT",\n'
    '  "symbol": str,            // enclosing function/class name, or "" if none\n'
    '  "severity": "critical"|"high"|"medium"|"low",\n'
    '  "title": str,             // a concise headline, <= ~8 words\n'
    '  "problem": str,           // 1-2 sentences: what is wrong and why it matters\n'
    '  "suggestion": str         // a concrete fix; a short code snippet is welcome\n'
    "}]}\n"
    "- `line` is a line number in the file being reviewed; `side` is RIGHT for "
    "added/changed lines, LEFT for removed lines.\n"
    "- Set `symbol` from the provided code context (the enclosing function/class).\n"
    "- Be concise and specific. If you find no issues in your area, return "
    '{"findings": []}.'
)


def _review_targets(state: ReviewState) -> list[str]:
    """Short 'what it's looking at' lines: each changed file + its symbols."""
    out: list[str] = []
    for path, blob in (state.get("context") or {}).items():
        syms = ", ".join(
            e["name"] for e in blob.get("enclosing", []) if e.get("name")
        )
        out.append(f"{path} · {syms}" if syms else path)
    return out or ["the PR diff"]


def _build_prompt(state: ReviewState) -> str:
    context = state.get("context", {})
    ctx_lines = []
    for path, blob in context.items():
        enclosing = ", ".join(
            f"{e['kind']} {e['name']}()" for e in blob.get("enclosing", [])
        ) or "n/a"
        test = blob.get("matching_test") or "none"
        ctx_lines.append(
            f"- {path} [{blob.get('language')}]: enclosing={enclosing}; "
            f"imports={blob.get('imports', [])}; matching_test_path={test}"
        )
    context_text = "\n".join(ctx_lines) if ctx_lines else "(no context)"

    return (
        f"Review the following pull request diff.\n\n"
        f"## Code context (per changed file)\n{context_text}\n\n"
        f"## Unified diff\n```diff\n{state.get('diff', '')}\n```\n\n"
        f"{_SCHEMA_INSTRUCTIONS}"
    )


def _coerce_findings(agent_name: str, data: dict[str, Any]) -> list[Finding]:
    out: list[Finding] = []
    for item in data.get("findings", []) or []:
        if not isinstance(item, dict):
            continue
        severity = str(item.get("severity", "")).lower()
        if severity not in _VALID_SEVERITY:
            severity = "medium"
        side = str(item.get("side", "RIGHT")).upper()
        side = side if side in {"RIGHT", "LEFT"} else "RIGHT"
        try:
            line = int(item.get("line", 0))
        except (TypeError, ValueError):
            line = 0
        f = Finding(
            agent=agent_name,
            path=str(item.get("path", "")),
            line=line,
            side=side,
            symbol=str(item.get("symbol", "")).strip(),
            severity=severity,
            title=str(item.get("title", "")).strip(),
            # fall back to legacy `rationale` if a model still emits it
            problem=str(item.get("problem", item.get("rationale", ""))).strip(),
            suggestion=str(item.get("suggestion", "")).strip(),
            confidence="",   # set by the verify node (#2)
            draft_comment="",
            in_hunk=False,  # consolidate (Phase 5) computes the real value
        )
        f["draft_comment"] = compose_comment(f)
        out.append(f)
    return out


def make_agent_node(agent_name: str):
    """Return a graph node function for the named specialist agent."""

    def _node(state: ReviewState, config: RunnableConfig) -> dict:
        run_id = config["configurable"]["thread_id"]
        model_name = MODELS[agent_name]
        emit({"agent": agent_name, "event": "started", "role": _ROLE[agent_name]})
        for target in _review_targets(state):
            emit({"agent": agent_name, "event": "reviewing", "target": target})
        emit({"agent": agent_name, "event": "model", "model": model_name})

        llm = get_model(agent_name)
        result = call_agent_with_repair(
            llm, _build_prompt(state), agent_name, system=_SYSTEM[agent_name]
        )
        repo.record_token_usage(
            run_id, agent_name, result.prompt_tokens, result.completion_tokens
        )

        if not result.ok:
            print(f"[agent:{agent_name}] DEGRADED after {result.attempts} attempt(s): "
                  f"{result.errors[-1] if result.errors else 'unknown'}")
            emit({"agent": agent_name, "event": "degraded",
                  "tokens": result.prompt_tokens + result.completion_tokens})
            return {"degraded_agents": [agent_name]}

        findings = _coerce_findings(agent_name, result.data)
        print(f"[agent:{agent_name}] {len(findings)} finding(s) "
              f"(tokens in/out={result.prompt_tokens}/{result.completion_tokens})")
        emit({"agent": agent_name, "event": "done", "count": len(findings),
              "tokens": result.prompt_tokens + result.completion_tokens})
        return {"findings": findings}

    _node.__name__ = f"{agent_name}_agent"
    return _node
