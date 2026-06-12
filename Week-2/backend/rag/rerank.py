"""Hosted cross-encoder reranking via Pinecone Inference (PLAN.md §10).

After hybrid retrieval returns the top-k by similarity, a cross-encoder re-scores
each (question, chunk) pair for true relevance and keeps the best `top_n`. This
sharpens ranking and — because the rerank score separates "actually answers it"
from "merely on-topic" far better than a similarity cutoff — gives a cleaner
refusal signal. Uses the existing Pinecone key; no extra infra.
"""
from __future__ import annotations

from .config import load_settings
from .pinecone_store import get_client


def rerank(query: str, sources: list, top_n: int) -> list:
    """Return the top_n sources reordered by cross-encoder relevance, each with
    `.rerank_score` set. Falls back to the input order if reranking is empty."""
    if not sources:
        return []
    s = load_settings()
    docs = [{"id": str(i), "text": src.text} for i, src in enumerate(sources)]
    res = get_client().inference.rerank(
        model=s.rerank_model,
        query=query,
        documents=docs,
        top_n=min(top_n, len(docs)),
        rank_fields=["text"],
        return_documents=False,
    )
    out = []
    for d in res.data:
        src = sources[d.index]
        src.rerank_score = float(d.score)
        out.append(src)
    return out
