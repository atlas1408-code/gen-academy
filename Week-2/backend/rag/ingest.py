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

from .cleaning import clean_text, glossary_hits
from .config import ROOT, load_settings
from .events import Clock, event
from .loader import lecture_id_for, parse_segments, title_for, Segment
from .nebius import get_embed_model
from .pinecone_store import ensure_index, l2_normalize
from .sparse import encode_doc, fit_bm25

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


def ingest_file_stream(path: str | Path, *, force: bool = False, bm25=None):
    """Ingest one transcript file, yielding a StepEvent per stage (§7.2).

    The terminal event is stage="done" whose data is the summary dict (or a
    skip notice). bm25: pre-fitted encoder (ingest_dir fits corpus-wide); when
    None it is fit on this file's chunks.
    """
    clock = Clock()
    s = load_settings()
    path = Path(path)
    fhash = _file_hash(path)
    manifest = _load_manifest()

    yield event("load", "start", f"Loading {path.name}…", clock,
                doc=path.name, file_size_kb=round(path.stat().st_size / 1024, 1))

    if not force and manifest.get(path.name, {}).get("hash") == fhash:
        summary = {"file": path.name, "skipped": True, "reason": "unchanged (manifest hit)",
                   "chunk_count": manifest[path.name].get("chunk_count", 0)}
        yield event("done", "complete", f"{path.name} unchanged — skipped (idempotent)",
                    clock, **summary)
        return

    lecture_id = lecture_id_for(path)
    title = title_for(path)
    segments = parse_segments(path)
    yield event("load", "complete", f"Parsed {len(segments)} timestamped segments",
                clock, doc=path.name, segment_count=len(segments))

    # Cleaning: normalize ASR-mangled jargon before chunking (§8.3).
    raw_join = " ".join(seg.text for seg in segments)
    fixes = sum(glossary_hits(raw_join).values())
    segments = [Segment(speaker=seg.speaker, text=clean_text(seg.text),
                        timestamp=seg.timestamp) for seg in segments]
    yield event("clean", "complete", f"Applied glossary ({fixes} jargon fixes)",
                clock, glossary_fixes=fixes)

    chunks = chunk_segments(segments, s.chunk_size, s.chunk_overlap)
    texts = [c["text"] for c in chunks]
    yield event("chunk", "complete",
                f"Chunked into {len(chunks)} chunks (~{s.chunk_size} tok, {s.chunk_overlap} overlap)",
                clock, chunk_count=len(chunks), sample_chunk=texts[0][:240] if texts else "")

    # Dense embeddings via Nebius (batched), L2-normalized for the dotproduct index.
    yield event("embed", "start", f"Embedding {len(texts)} chunks via Nebius "
                f"({s.nebius_embed_model})…", clock, chunk_count=len(texts))
    embed = get_embed_model()
    vectors = [l2_normalize(v) for v in embed.get_text_embedding_batch(texts, show_progress=False)]
    preview = [round(x, 4) for x in vectors[0][:8]] if vectors else []
    yield event("embed", "complete", f"Embedded {len(vectors)} chunks ({s.embed_dim}-dim)",
                clock, embedding_dim=s.embed_dim, embedding_preview=preview)

    # Sparse BM25 vectors for hybrid retrieval (§8.3).
    if bm25 is None:
        bm25 = fit_bm25(texts)
    sparse_vecs = [encode_doc(bm25, t) for t in texts]

    records = []
    for c, vec, sv in zip(chunks, vectors, sparse_vecs):
        records.append({
            "id": _chunk_id(lecture_id, "transcript", c["chunk_index"]),
            "values": vec,
            "sparse_values": sv,
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

    total = len(records)
    yield event("upsert", "start", f"Upserting {total} vectors to Pinecone…",
                clock, vector_count=total, upserted=0)
    index = ensure_index()
    # Small batches so the long upsert reports real progress (§ glass-box).
    BATCH = 15
    upserted = 0
    for i in range(0, total, BATCH):
        index.upsert(vectors=records[i:i + BATCH], namespace=_NAMESPACE)
        upserted = min(upserted + BATCH, total)
        yield event("upsert", "progress", f"Upserted {upserted}/{total} vectors…",
                    clock, upserted=upserted, vector_count=total)
    yield event("upsert", "complete", f"Upserted {total} vectors (dense + sparse)",
                clock, vector_count=total, upserted=total)

    manifest[path.name] = {
        "hash": fhash,
        "lecture_id": lecture_id,
        "chunk_count": len(chunks),
        "ingested_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    _save_manifest(manifest)

    yield event("done", "complete", f"Ingested {path.name}", clock,
                file=path.name, skipped=False, lecture_id=lecture_id,
                segment_count=len(segments), chunk_count=len(chunks),
                embedding_dim=s.embed_dim,
                sample_chunk=chunks[0]["text"][:240] if chunks else "")


def ingest_file(path: str | Path, *, force: bool = False, bm25=None) -> dict:
    """Non-streaming wrapper for the CLI: drains the stream, returns the summary."""
    summary: dict = {}
    for ev in ingest_file_stream(path, force=force, bm25=bm25):
        if ev.stage == "done":
            summary = ev.data
    return summary


def _fit_corpus_bm25(files: list[Path]):
    """Fit BM25 once over all files' chunks (consistent IDF for hybrid)."""
    s = load_settings()
    all_texts: list[str] = []
    for fp in files:
        segs = [Segment(speaker=seg.speaker, text=clean_text(seg.text), timestamp=seg.timestamp)
                for seg in parse_segments(fp)]
        all_texts += [c["text"] for c in chunk_segments(segs, s.chunk_size, s.chunk_overlap)]
    return fit_bm25(all_texts)


def _corpus_files(dir_path: str | Path) -> list[Path]:
    dir_path = Path(dir_path)
    return sorted(dir_path.glob("*.txt")) + sorted(dir_path.glob("*.vtt"))


def ingest_dir(dir_path: str | Path, *, force: bool = False) -> list[dict]:
    """Ingest every transcript in a dir. BM25 is fit ONCE over the whole corpus
    so IDF statistics are consistent across files (hybrid correctness)."""
    files = _corpus_files(dir_path)
    if not files:
        return []
    bm25 = _fit_corpus_bm25(files)
    return [ingest_file(fp, force=force, bm25=bm25) for fp in files]


def ingest_corpus_stream(dir_path: str | Path, *, force: bool = False):
    """Streaming ingest of a whole dir, yielding StepEvents (§7.2). Fits BM25
    corpus-wide first, then streams each file."""
    files = _corpus_files(dir_path)
    if not files:
        yield event("error", "error", f"No transcripts found in {dir_path}", Clock())
        return
    bm25 = _fit_corpus_bm25(files)
    for fp in files:
        yield from ingest_file_stream(fp, force=force, bm25=bm25)
