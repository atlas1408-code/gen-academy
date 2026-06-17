"""FastAPI app driving the review loop.

  POST /review              {pr_url}            -> start a run to the interrupt
  GET  /run/{run_id}                            -> current findings + status
  POST /run/{run_id}/decision {action, ...}     -> resume the graph

Each request rebuilds the graph on a Postgres-backed checkpointer, so state is
durable and the API is stateless between calls.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from langgraph.types import Command

from app.graph import build_graph, open_pg_checkpointer
from app.tools.github import GitHubError

app = FastAPI(title="Code Review Agent")
_STATIC = Path(__file__).parent / "static"


class ReviewRequest(BaseModel):
    pr_url: str


class DecisionRequest(BaseModel):
    action: str                       # approve | refine | reject
    rejected: list[int] = []          # finding indices to drop (approve)
    refine: list[dict] = []           # [{"index": int, "instruction": str}]


def _config(run_id: str) -> dict:
    return {"configurable": {"thread_id": run_id}}


def _state_response(run_id: str, snap) -> dict:
    values = snap.values or {}
    nxt = snap.next or ()
    if values.get("posted"):
        status = "posted"
    elif "human_gate" in nxt:
        status = "awaiting_approval"
    elif not nxt:
        status = "ended"
    else:
        status = "running"
    return {
        "run_id": run_id,
        "status": status,
        "interrupted": bool(nxt),
        "pr_url": values.get("pr_url"),
        "degraded_agents": values.get("degraded_agents", []),
        "findings": values.get("consolidated", []),
        "suppressed": values.get("suppressed", []),
        "posted": bool(values.get("posted", False)),
    }


@app.get("/")
def index() -> FileResponse:
    return FileResponse(_STATIC / "index.html")


@app.post("/review")
def start_review(req: ReviewRequest) -> dict:
    run_id = uuid.uuid4().hex[:12]
    cfg = _config(run_id)
    try:
        with open_pg_checkpointer() as cp:
            graph = build_graph(cp)
            graph.invoke({"pr_url": req.pr_url}, cfg)
            snap = graph.get_state(cfg)
    except GitHubError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return _state_response(run_id, snap)


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


@app.get("/review/stream")
def review_stream(pr_url: str) -> StreamingResponse:
    """Server-Sent Events: live per-agent progress, then the final findings.

    Emits {type:'meta'|'progress'|'done'|'error'}. Progress payloads are the
    custom events the graph nodes write (stage/agent updates)."""
    run_id = uuid.uuid4().hex[:12]
    cfg = _config(run_id)

    def gen():
        yield _sse({"type": "meta", "run_id": run_id})
        try:
            with open_pg_checkpointer() as cp:
                graph = build_graph(cp)
                for chunk in graph.stream({"pr_url": pr_url}, cfg, stream_mode="custom"):
                    yield _sse({"type": "progress", **chunk})
                snap = graph.get_state(cfg)
            yield _sse({"type": "done", **_state_response(run_id, snap)})
        except GitHubError as exc:
            yield _sse({"type": "error", "detail": str(exc)})
        except Exception as exc:  # surface unexpected failures to the UI
            yield _sse({"type": "error", "detail": f"{type(exc).__name__}: {exc}"})

    return StreamingResponse(gen(), media_type="text/event-stream")


@app.get("/run/{run_id}")
def get_run(run_id: str) -> dict:
    with open_pg_checkpointer() as cp:
        snap = build_graph(cp).get_state(_config(run_id))
    if not snap.values:
        raise HTTPException(status_code=404, detail=f"No run {run_id!r}")
    return _state_response(run_id, snap)


@app.post("/run/{run_id}/decision")
def decide(run_id: str, req: DecisionRequest) -> dict:
    cfg = _config(run_id)
    resume = {"action": req.action, "rejected": req.rejected, "refine": req.refine}
    with open_pg_checkpointer() as cp:
        graph = build_graph(cp)
        if not graph.get_state(cfg).values:
            raise HTTPException(status_code=404, detail=f"No run {run_id!r}")
        graph.invoke(Command(resume=resume), cfg)
        snap = graph.get_state(cfg)
    return _state_response(run_id, snap)
