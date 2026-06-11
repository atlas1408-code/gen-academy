"""Nebius Token Factory wiring (PLAN.md §3, §9).

Both model calls in this project run on Nebius (course constraint):
  - embedding model  : text → vector
  - generation LLM   : question + chunks → cited answer

We use the dedicated LlamaIndex Nebius integrations. They are thin wrappers over
the OpenAI-compatible endpoint at NEBIUS_BASE_URL.
"""
from __future__ import annotations

from functools import lru_cache

from llama_index.embeddings.nebius import NebiusEmbedding
from llama_index.llms.nebius import NebiusLLM

from .config import load_settings


@lru_cache(maxsize=1)
def get_embed_model() -> NebiusEmbedding:
    s = load_settings()
    return NebiusEmbedding(
        api_key=s.nebius_api_key,
        model_name=s.nebius_embed_model,
    )


@lru_cache(maxsize=1)
def get_llm() -> NebiusLLM:
    s = load_settings()
    return NebiusLLM(
        api_key=s.nebius_api_key,
        model=s.nebius_llm_model,
    )
