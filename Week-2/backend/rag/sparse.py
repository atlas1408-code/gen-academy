"""BM25 sparse encoder for hybrid retrieval (PLAN.md §8.3, Phase 2c).

Dense embeddings capture meaning but can miss exact technical terms; BM25 sparse
vectors recover them (the jargon-recovery half of the hybrid story). We fit a
BM25 model over the ingested chunk texts and persist its IDF params so query
time uses the same statistics.

Pinecone hybrid convention: store raw dense (unit-normalized) + raw sparse
vectors; apply the dense/sparse weighting (alpha) to the QUERY vectors only, so
score = alpha * cosine + (1 - alpha) * bm25.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pinecone_text.sparse import BM25Encoder

from .config import ROOT

_PARAMS = ROOT / "backend" / "bm25_params.json"


def fit_bm25(texts: list[str]) -> BM25Encoder:
    """Fit BM25 over the corpus and persist params for query-time reuse."""
    enc = BM25Encoder()
    enc.fit(texts)
    enc.dump(str(_PARAMS))
    return enc


@lru_cache(maxsize=1)
def load_bm25() -> BM25Encoder:
    if not _PARAMS.exists():
        raise RuntimeError(
            "bm25_params.json missing — run ingestion first to fit the BM25 model."
        )
    enc = BM25Encoder()
    enc.load(str(_PARAMS))
    return enc


def encode_doc(enc: BM25Encoder, text: str) -> dict:
    """Sparse vector for a stored chunk: {'indices': [...], 'values': [...]}."""
    return enc.encode_documents(text)


def encode_query(text: str) -> dict:
    return load_bm25().encode_queries(text)


def scale_sparse(sparse: dict, factor: float) -> dict:
    return {"indices": sparse["indices"],
            "values": [v * factor for v in sparse["values"]]}
