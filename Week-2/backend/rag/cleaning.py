"""Transcript cleaning (PLAN.md §8.3) — Phase 2.

Zoom ASR mangles technical jargon ("Claude Code" -> "cloud code",
"LlamaIndex" -> "llama index"). We tackle it on two fronts here:

  1. FIX  — a curated glossary, applied as word-boundary find/replace before
     chunking, normalizing known manglings to their canonical spelling. This
     directly helps keyword/hybrid retrieval (the exact term is now present).
  2. SURFACE — an out-of-vocabulary (OOV) scan diffs corpus tokens against a
     system dictionary to surface *new* mangled-term candidates to add to the
     glossary. It's a diagnostic, run on demand, not part of ingest.

Glossary entries were seeded from an empirical scan of week1-session1
(e.g. "cloud code" x11). Right-hand sides are the canonical, correctly-cased
forms; left-hand sides are matched case-insensitively with flexible whitespace.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

# wrong (lowercased, whitespace-flexible) -> canonical replacement.
# Multi-word keys are matched with \s+ between words so "cloud  code" also hits.
GLOSSARY: dict[str, str] = {
    "cloud code": "Claude Code",
    "claude code": "Claude Code",      # normalize casing too
    "llama index": "LlamaIndex",
    "llm index": "LlamaIndex",
    "lang chain": "LangChain",
    "hugging phase": "Hugging Face",
    "hugging face": "Hugging Face",
    "open ai": "OpenAI",
    "pine cone": "Pinecone",
    "nebulous": "Nebius",
    "token factory": "Token Factory",
    "anthropic": "Anthropic",
}


def _compile(term: str) -> re.Pattern:
    # Build a whitespace-flexible, word-boundary, case-insensitive pattern.
    parts = [re.escape(w) for w in term.split()]
    return re.compile(r"\b" + r"\s+".join(parts) + r"\b", re.IGNORECASE)


# Apply longer keys first so multi-word terms win over any substring overlap.
_PATTERNS: list[tuple[re.Pattern, str]] = [
    (_compile(k), v) for k, v in sorted(GLOSSARY.items(), key=lambda kv: -len(kv[0]))
]


def apply_glossary(text: str) -> str:
    """Normalize known ASR-mangled jargon to canonical spelling."""
    for pat, repl in _PATTERNS:
        text = pat.sub(repl, text)
    return text


def clean_text(text: str) -> str:
    """Single cleaning entry point used by ingestion (Phase 2 = glossary only)."""
    return apply_glossary(text)


def glossary_hits(text: str) -> dict[str, int]:
    """Count how many replacements each glossary entry would make (diagnostics)."""
    return {k: len(_compile(k).findall(text)) for k in GLOSSARY
            if _compile(k).search(text)}


# ── OOV scan (diagnostic) ──────────────────────────────────────────────────
_DICT_PATH = Path("/usr/share/dict/words")
_TOKEN = re.compile(r"[a-zA-Z][a-zA-Z'\-]+")


@lru_cache(maxsize=1)
def _dictionary() -> frozenset[str]:
    if _DICT_PATH.exists():
        return frozenset(w.strip().lower() for w in _DICT_PATH.read_text().splitlines())
    return frozenset()


def oov_scan(text: str, *, min_count: int = 2, top: int = 40) -> list[tuple[str, int]]:
    """Return (token, count) for frequent tokens absent from the dictionary.

    Candidates for new glossary entries (mangled jargon, names). Filters tokens
    seen < min_count times. Returns the top-N most frequent.
    """
    words = _dictionary()
    if not words:
        return []
    counts: dict[str, int] = {}
    for m in _TOKEN.findall(text.lower()):
        if len(m) < 3 or m in words:
            continue
        counts[m] = counts.get(m, 0) + 1
    items = [(w, c) for w, c in counts.items() if c >= min_count]
    return sorted(items, key=lambda x: -x[1])[:top]
