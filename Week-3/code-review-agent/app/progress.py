"""Emit live progress events onto LangGraph's custom stream.

Nodes call `emit(...)`; when the graph is run via `.stream(stream_mode="custom")`
the payloads are forwarded to the caller (the SSE endpoint). When run via plain
`.invoke()` there is no writer, so `emit` is a safe no-op.
"""
from typing import Any


def emit(payload: dict[str, Any]) -> None:
    try:
        from langgraph.config import get_stream_writer

        writer = get_stream_writer()
        if writer:
            writer(payload)
    except Exception:
        pass  # not in a streaming context — ignore
