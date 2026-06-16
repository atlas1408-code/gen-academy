"""Robust JSON extraction for LLM agent output.

`call_agent_with_repair` invokes a model, tries to parse JSON from the reply,
and on failure feeds the bad output back with a repair instruction and retries.
Token usage is accumulated across attempts. It returns an AgentResult and never
raises on a parse/model failure — callers decide how to degrade.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


@dataclass
class AgentResult:
    data: dict[str, Any] | None          # parsed JSON, or None if never parsed
    prompt_tokens: int = 0
    completion_tokens: int = 0
    attempts: int = 0
    raw: str = ""
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.data is not None


def extract_json(text: str) -> dict[str, Any] | None:
    """Pull a JSON object out of an LLM reply (handles fences / surrounding prose)."""
    if not text:
        return None
    candidates: list[str] = []
    if m := _FENCE_RE.search(text):
        candidates.append(m.group(1).strip())
    # Greedy span from first '{' to last '}'.
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        candidates.append(text[start : end + 1])
    candidates.append(text.strip())

    for cand in candidates:
        try:
            parsed = json.loads(cand)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, TypeError):
            continue
    return None


def _usage(resp) -> tuple[int, int]:
    u = getattr(resp, "usage_metadata", None) or {}
    return int(u.get("input_tokens", 0)), int(u.get("output_tokens", 0))


def call_agent_with_repair(
    llm, prompt: str, agent_name: str, system: str = "", max_retries: int = 2
) -> AgentResult:
    """Invoke `llm`, parse JSON, repairing up to `max_retries` times."""
    messages: list = []
    if system:
        messages.append(SystemMessage(content=system))
    messages.append(HumanMessage(content=prompt))

    result = AgentResult(data=None)
    for attempt in range(max_retries + 1):
        result.attempts = attempt + 1
        try:
            resp = llm.invoke(messages)
        except Exception as exc:  # network/model error — degrade, don't crash
            result.errors.append(f"invoke error: {type(exc).__name__}: {exc}")
            break

        pt, ct = _usage(resp)
        result.prompt_tokens += pt
        result.completion_tokens += ct
        text = resp.content if isinstance(resp.content, str) else str(resp.content)
        result.raw = text

        if (parsed := extract_json(text)) is not None:
            result.data = parsed
            return result

        result.errors.append(f"attempt {attempt + 1}: unparseable JSON")
        if attempt < max_retries:
            messages.append(AIMessage(content=text))
            messages.append(HumanMessage(content=(
                "Your previous response was not valid JSON. Respond with ONLY a "
                "single JSON object matching the requested schema — no prose, no "
                "markdown fences."
            )))

    return result
