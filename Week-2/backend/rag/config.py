"""Central config: loads .env once and exposes typed settings + tunables.

Every other module imports `settings` from here. Keeps env-var names in one
place so the Pinecone index dimension and the embedding model can never drift
apart (see PLAN.md §7, §9).
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Repo root = Week-2/ (this file is at Week-2/backend/rag/config.py)
ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


def _req(name: str) -> str:
    val = os.getenv(name, "").strip()
    if not val:
        raise RuntimeError(
            f"Missing required env var {name!r}. "
            f"Copy .env.example to .env and fill it in."
        )
    return val


def _get(name: str, default: str) -> str:
    return os.getenv(name, default).strip() or default


@dataclass(frozen=True)
class Settings:
    # Nebius
    nebius_api_key: str
    nebius_base_url: str
    nebius_embed_model: str
    nebius_llm_model: str

    # Pinecone
    pinecone_api_key: str
    pinecone_index: str
    pinecone_cloud: str
    pinecone_region: str
    embed_dim: int
    pinecone_metric: str

    # Corpus
    transcripts_dir: Path
    slides_dir: Path

    # Tunables
    chunk_size: int
    chunk_overlap: int
    top_k: int
    rerank_top_n: int
    similarity_cutoff: float
    hybrid_alpha: float


def load_settings() -> Settings:
    return Settings(
        nebius_api_key=_req("NEBIUS_API_KEY"),
        nebius_base_url=_get("NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1/"),
        nebius_embed_model=_get("NEBIUS_EMBED_MODEL", "Qwen/Qwen3-Embedding-8B"),
        nebius_llm_model=_get("NEBIUS_LLM_MODEL", "meta-llama/Llama-3.3-70B-Instruct"),
        pinecone_api_key=_req("PINECONE_API_KEY"),
        pinecone_index=_get("PINECONE_INDEX", "rag-simulator"),
        pinecone_cloud=_get("PINECONE_CLOUD", "aws"),
        pinecone_region=_get("PINECONE_REGION", "us-east-1"),
        embed_dim=int(_get("EMBED_DIM", "4096")),
        pinecone_metric=_get("PINECONE_METRIC", "dotproduct"),
        transcripts_dir=ROOT / _get("TRANSCRIPTS_DIR", "Input-Data/Transcripts"),
        slides_dir=ROOT / _get("SLIDES_DIR", "Input-Data/Slides"),
        chunk_size=int(_get("CHUNK_SIZE", "512")),
        chunk_overlap=int(_get("CHUNK_OVERLAP", "80")),
        top_k=int(_get("TOP_K", "8")),
        rerank_top_n=int(_get("RERANK_TOP_N", "4")),
        similarity_cutoff=float(_get("SIMILARITY_CUTOFF", "0.40")),
        hybrid_alpha=float(_get("HYBRID_ALPHA", "0.7")),
    )
