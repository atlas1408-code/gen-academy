"""FastAPI app exposing the glass-box pipeline (PLAN.md §3, §7.2, Phase 3).

Endpoints:
  GET /status            — corpus + index + config snapshot (JSON)
  GET /ingest?force=…    — SSE stream of ingestion StepEvents over the corpus dir
  GET /query?q=…         — SSE stream of query StepEvents (embed→retrieve→generate)

Both streams emit `text/event-stream`. The path operations are sync `def` so
FastAPI runs them (and the blocking Nebius/Pinecone calls inside the generators)
in a threadpool, keeping the event loop free.
"""
from __future__ import annotations

from collections.abc import Iterator

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from rag.config import load_settings
from rag.events import StepEvent
from rag.ingest import _MANIFEST, ingest_corpus_stream
from rag.pinecone_store import ensure_index
from rag.query import query_stream

app = FastAPI(title="RAG Simulator — Glass-Box API")

# React/Vite dev server origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_SSE_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no",
                "Connection": "keep-alive"}


def _sse(events: Iterator[StepEvent]) -> StreamingResponse:
    def gen():
        for ev in events:
            yield ev.to_sse()
    return StreamingResponse(gen(), media_type="text/event-stream", headers=_SSE_HEADERS)


@app.get("/status")
def status() -> dict:
    s = load_settings()
    import json
    manifest = json.loads(_MANIFEST.read_text()) if _MANIFEST.exists() else {}
    try:
        stats = ensure_index().describe_index_stats()
        index = {"metric": s.pinecone_metric, "dimension": s.embed_dim,
                 "vector_count": stats.get("total_vector_count", 0)}
    except Exception as e:  # network/index issues shouldn't 500 the status page
        index = {"error": str(e)}
    return {
        "models": {"embed": s.nebius_embed_model, "llm": s.nebius_llm_model},
        "retrieval": {"top_k": s.top_k, "hybrid_alpha": s.hybrid_alpha,
                      "similarity_cutoff": s.similarity_cutoff},
        "index": index,
        "manifest": manifest,
    }


@app.get("/ingest")
def ingest(force: bool = Query(False)) -> StreamingResponse:
    s = load_settings()
    return _sse(ingest_corpus_stream(s.transcripts_dir, force=force))


@app.get("/query")
def query(q: str = Query(..., min_length=1)) -> StreamingResponse:
    return _sse(query_stream(q))
