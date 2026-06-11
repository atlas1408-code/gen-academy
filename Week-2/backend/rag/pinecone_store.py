"""Pinecone index management + LlamaIndex vector store (PLAN.md §3, §7).

`ensure_index()` creates the serverless index with the EXACT embedding
dimension and metric from config if it doesn't exist yet — the dimension must
match the embedding model or upserts fail (§8.1).
"""
from __future__ import annotations

import math
import time
from functools import lru_cache

from pinecone import Pinecone, ServerlessSpec

from .config import load_settings


def l2_normalize(vec: list[float]) -> list[float]:
    """Unit-normalize so dotproduct == cosine on this index."""
    n = math.sqrt(sum(x * x for x in vec))
    return [x / n for x in vec] if n else vec


@lru_cache(maxsize=1)
def get_client() -> Pinecone:
    return Pinecone(api_key=load_settings().pinecone_api_key)


def ensure_index():
    """Create the index if missing; return the index handle. Idempotent."""
    s = load_settings()
    pc = get_client()
    existing = {ix["name"] for ix in pc.list_indexes()}
    if s.pinecone_index not in existing:
        pc.create_index(
            name=s.pinecone_index,
            dimension=s.embed_dim,
            metric=s.pinecone_metric,
            spec=ServerlessSpec(cloud=s.pinecone_cloud, region=s.pinecone_region),
        )
        # Wait until ready before returning.
        while not pc.describe_index(s.pinecone_index).status["ready"]:
            time.sleep(1)
    return pc.Index(s.pinecone_index)


def recreate_index():
    """Delete the index if it exists, then create it fresh with the configured
    metric. Needed for the cosine→dotproduct switch when enabling hybrid (§10).
    """
    s = load_settings()
    pc = get_client()
    if s.pinecone_index in {ix["name"] for ix in pc.list_indexes()}:
        pc.delete_index(s.pinecone_index)
        while s.pinecone_index in {ix["name"] for ix in pc.list_indexes()}:
            time.sleep(1)
    return ensure_index()


def get_vector_store():
    """LlamaIndex PineconeVectorStore over the ensured index."""
    from llama_index.vector_stores.pinecone import PineconeVectorStore

    return PineconeVectorStore(pinecone_index=ensure_index())
