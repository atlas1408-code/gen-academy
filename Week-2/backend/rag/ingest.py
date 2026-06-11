"""Ingestion pipeline (PLAN.md §5, §7.1, §10 Phase 1).

load → light clean → transcript-aware chunk → embed (Nebius) → upsert (Pinecone)

Design choices that matter:
  * Transcript-aware chunking: segments are grouped greedily up to ~CHUNK_SIZE
    tokens with ~CHUNK_OVERLAP token overlap, carrying timestamp_start/end so
    every chunk is citable (§8.2).
  * Deterministic IDs (sha1 of lecture_id:content_type:chunk_index) so
    re-ingesting UPSERTS instead of duplicating (§7.1).
  * Doc-level dedup via manifest.json keyed on sha1(file bytes): unchanged files
    are skipped unless force=True (§7.1 / Phase 1 acceptance "no duplicates").
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path

import tiktoken

from .config import ROOT, load_settings
from .loader import lecture_id_for, parse_segments, title_for, Segment
from .nebius import get_embed_model
from .pinecone_store import ensure_index

_ENC = tiktoken.get_encoding("cl100k_base")
_MANIFEST = ROOT / "backend" / "manifest.json"
_NAMESPACE = "corpus"


def _ntoks(text: str) -> int:
    return len(_ENC.encode(text))


def _light_clean(text: str) -> str:
    """Phase 1 light cleaning: collapse whitespace. (Glossary/OOV is Phase 2.)"""
    return re.sub(r"\s+", " ", text).strip()


def _file_hash(path: Path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()


def _load_manifest() -> dict:
    if _MANIFEST.exists():
        return json.loads(_MANIFEST.read_text())
    return {}


def _save_manifest(m: dict) -> None:
    _MANIFEST.write_text(json.dumps(m, indent=2))


def chunk_segments(segments: list[Segment], chunk_size: int, overlap: int) -> list[dict]:
    """Greedily pack segments into ~chunk_size-token chunks with token overlap.

    Returns dicts with text + timestamp_start/end + speakers + chunk_index.
    """
    chunks: list[dict] = []
    cur: list[Segment] = []
    cur_tokens = 0

    def flush():
        nonlocal cur, cur_tokens
        if not cur:
            return
        text = _light_clean(" ".join(s.text for s in cur))
        speakers = sorted({s.speaker for s in cur if s.speaker})
        chunks.append({
            "text": text,
            "timestamp_start": cur[0].timestamp,
            "timestamp_end": cur[-1].timestamp,
            "speakers": speakers,
            "chunk_index": len(chunks),
        })
        # Build overlap tail: keep trailing segments worth ~`overlap` tokens.
        tail: list[Segment] = []
        tail_tokens = 0
        for seg in reversed(cur):
            t = _ntoks(seg.text)
            if tail_tokens + t > overlap:
                break
            tail.insert(0, seg)
            tail_tokens += t
        cur = tail
        cur_tokens = tail_tokens

    for seg in segments:
        t = _ntoks(seg.text)
        if cur and cur_tokens + t > chunk_size:
            flush()
        cur.append(seg)
        cur_tokens += t
    flush()
    return chunks


def _chunk_id(lecture_id: str, content_type: str, chunk_index: int) -> str:
    return hashlib.sha1(f"{lecture_id}:{content_type}:{chunk_index}".encode()).hexdigest()


def ingest_file(path: str | Path, *, force: bool = False) -> dict:
    """Ingest one transcript file. Returns a summary dict."""
    s = load_settings()
    path = Path(path)
    fhash = _file_hash(path)
    manifest = _load_manifest()

    if not force and manifest.get(path.name, {}).get("hash") == fhash:
        return {"file": path.name, "skipped": True, "reason": "unchanged (manifest hit)",
                "chunk_count": manifest[path.name].get("chunk_count", 0)}

    lecture_id = lecture_id_for(path)
    title = title_for(path)
    segments = parse_segments(path)
    chunks = chunk_segments(segments, s.chunk_size, s.chunk_overlap)

    # Embed all chunk texts via Nebius (batched by the embedding client).
    embed = get_embed_model()
    texts = [c["text"] for c in chunks]
    vectors = embed.get_text_embedding_batch(texts, show_progress=False)

    # Build Pinecone records with full §7.1 metadata + deterministic IDs.
    records = []
    for c, vec in zip(chunks, vectors):
        records.append({
            "id": _chunk_id(lecture_id, "transcript", c["chunk_index"]),
            "values": vec,
            "metadata": {
                "text": c["text"],
                "source": path.name,
                "lecture_id": lecture_id,
                "title": title,
                "timestamp_start": c["timestamp_start"],
                "timestamp_end": c["timestamp_end"],
                "chunk_index": c["chunk_index"],
                "content_type": "transcript",
                "speakers": c["speakers"],
            },
        })

    index = ensure_index()
    for i in range(0, len(records), 100):  # Pinecone upsert batch cap
        index.upsert(vectors=records[i:i + 100], namespace=_NAMESPACE)

    manifest[path.name] = {
        "hash": fhash,
        "lecture_id": lecture_id,
        "chunk_count": len(chunks),
        "ingested_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    _save_manifest(manifest)

    return {
        "file": path.name,
        "skipped": False,
        "lecture_id": lecture_id,
        "segment_count": len(segments),
        "chunk_count": len(chunks),
        "embedding_dim": len(vectors[0]) if vectors else 0,
        "sample_chunk": chunks[0]["text"][:240] if chunks else "",
    }


def ingest_dir(dir_path: str | Path, *, force: bool = False) -> list[dict]:
    dir_path = Path(dir_path)
    results = []
    for fp in sorted(dir_path.glob("*.txt")) + sorted(dir_path.glob("*.vtt")):
        results.append(ingest_file(fp, force=force))
    return results
