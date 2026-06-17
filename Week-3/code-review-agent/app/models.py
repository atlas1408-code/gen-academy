"""ChatNebius instances, one per agent, all at temperature=0.

All model calls in this project go through Nebius Token Factory. Models are
lazily built and cached so importing this module doesn't require a key until a
call is actually made.
"""
from functools import lru_cache

from langchain_nebius import ChatNebius

from app import config


def _build(model: str) -> ChatNebius:
    return ChatNebius(
        model=model,
        temperature=0,
        api_key=config.require_nebius_key(),
        base_url=config.NEBIUS_BASE_URL,
        timeout=120,
        max_retries=2,
    )


@lru_cache(maxsize=None)
def get_model(agent: str) -> ChatNebius:
    """Return the cached ChatNebius for an agent key (quality|security|test_gap|consolidate)."""
    if agent not in config.MODELS:
        raise ValueError(f"Unknown agent/model key: {agent!r}")
    return _build(config.MODELS[agent])


@lru_cache(maxsize=None)
def get_judge() -> ChatNebius:
    """Independent model used by the eval to score finding validity (precision)."""
    return _build(config.JUDGE_MODEL)
