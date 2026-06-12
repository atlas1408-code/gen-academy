"""Query pipeline (PLAN.md §5, §8.4, §10 Phase 1).

embed question (Nebius) → retrieve top-k (Pinecone) → refuse OR generate.

Refusal is a first-class path (§8.4): if the best retrieved similarity is below
SIMILARITY_CUTOFF, we refuse instead of feeding weak context to the LLM. The
generation prompt is strict: answer ONLY from context, cite the timestamp, and
say "not covered" if the answer isn't present.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .config import load_settings
from .events import Clock, event
from .nebius import get_embed_model, get_llm
from .pinecone_store import ensure_index, l2_normalize
from .rerank import rerank
from .sparse import encode_query, scale_sparse

_NAMESPACE = "corpus"

_SYSTEM = (
    "You answer questions about course lectures using ONLY the provided context "
    "excerpts. Rules:\n"
    "1. Use only facts present in the context. Do not use outside knowledge.\n"
    "2. Cite the source after each claim as [<title> <timestamp_start>], e.g. "
    "[Week1 Session1 00:12:30].\n"
    "3. If the context does not contain the answer, reply exactly: "
    "\"I couldn't find this in the lectures.\" Do not guess.\n"
    "4. Be concise and faithful."
)


@dataclass
class Source:
    score: float
    title: str
    lecture_id: str
    timestamp_start: str
    timestamp_end: str
    text: str
    speaker: str = ""
    rerank_score: float = 0.0


@dataclass
class Answer:
    refused: bool
    answer: str
    top_score: float
    sources: list[Source] = field(default_factory=list)


def _to_sources(res) -> list[Source]:
    sources = []
    for m in res.get("matches", []):
        md = m.get("metadata", {})
        speakers = md.get("speakers", []) or []
        sources.append(Source(
            score=m["score"],
            title=md.get("title", ""),
            lecture_id=md.get("lecture_id", ""),
            timestamp_start=md.get("timestamp_start", ""),
            timestamp_end=md.get("timestamp_end", ""),
            text=md.get("text", ""),
            speaker=", ".join(speakers) if isinstance(speakers, list) else str(speakers),
        ))
    return sources


def _retrieve(question: str, top_k: int) -> list[Source]:
    """Dense-only retrieval (normalized vector on the dotproduct index ⇒ cosine)."""
    vec = l2_normalize(get_embed_model().get_text_embedding(question))
    res = ensure_index().query(
        vector=vec, top_k=top_k, include_metadata=True, namespace=_NAMESPACE
    )
    return _to_sources(res)


def _retrieve_hybrid(question: str, top_k: int, alpha: float | None = None) -> list[Source]:
    """Hybrid dense+sparse retrieval. Weighting applied to the query vectors:
    score = alpha * cosine + (1 - alpha) * bm25.  alpha=1 ⇒ dense, 0 ⇒ sparse."""
    if alpha is None:
        alpha = load_settings().hybrid_alpha
    dense = [alpha * x for x in l2_normalize(get_embed_model().get_text_embedding(question))]
    sparse = scale_sparse(encode_query(question), 1.0 - alpha)
    res = ensure_index().query(
        vector=dense, sparse_vector=sparse, top_k=top_k,
        include_metadata=True, namespace=_NAMESPACE,
    )
    return _to_sources(res)


def _build_context(sources: list[Source]) -> str:
    blocks = []
    for s in sources:
        blocks.append(
            f"[{s.title} {s.timestamp_start}-{s.timestamp_end}] (score={s.score:.3f})\n{s.text}"
        )
    return "\n\n".join(blocks)


def _sources_payload(sources: list[Source], n: int = 5) -> list[dict]:
    # Small payload for the hover card: a couple lines of text + useful metadata.
    # `score` is the cross-encoder rerank score when present, else hybrid score.
    return [{"score": round(s.rerank_score if s.rerank_score else s.score, 3),
             "title": s.title, "timestamp": s.timestamp_start,
             "timestamp_end": s.timestamp_end, "speaker": s.speaker,
             "text": s.text[:240]}
            for s in sources[:n]]


def query_stream(question: str):
    """Run the query pipeline yielding a StepEvent per stage (§7.2).

    Terminal event is stage="done" (with the cited answer + sources) or
    stage="refuse" when nothing clears the similarity cutoff.
    """
    clock = Clock()
    s = load_settings()

    yield event("embed", "start", f"Embedding question via Nebius ({s.nebius_embed_model})…",
                clock)
    dense_unit = l2_normalize(get_embed_model().get_text_embedding(question))
    yield event("embed", "complete", f"Question embedded ({s.embed_dim}-dim)", clock,
                embedding_dim=s.embed_dim,
                embedding_preview=[round(x, 4) for x in dense_unit[:8]])

    yield event("retrieve", "start",
                f"Hybrid search top-{s.top_k} (α={s.hybrid_alpha}) in Pinecone…", clock)
    dense = [s.hybrid_alpha * x for x in dense_unit]
    sparse = scale_sparse(encode_query(question), 1.0 - s.hybrid_alpha)
    res = ensure_index().query(vector=dense, sparse_vector=sparse, top_k=s.top_k,
                               include_metadata=True, namespace=_NAMESPACE)
    sources = _to_sources(res)
    top_score = sources[0].score if sources else 0.0
    yield event("retrieve", "complete",
                f"Retrieved {len(sources)} chunks (top similarity {top_score:.3f})", clock,
                retrieved=_sources_payload(sources), top_score=round(top_score, 3))

    # Rerank: cross-encoder re-scores the candidates; refusal moves onto this
    # well-calibrated score (§10).
    yield event("rerank", "start",
                f"Reranking {len(sources)} chunks via Pinecone ({s.rerank_model})…", clock)
    ranked = rerank(question, sources, s.rerank_top_n)
    top_rr = ranked[0].rerank_score if ranked else 0.0
    yield event("rerank", "complete",
                f"Kept top {len(ranked)} (relevance {top_rr:.3f})", clock,
                retrieved=_sources_payload(ranked), top_rerank=round(top_rr, 3),
                rerank_cutoff=s.rerank_cutoff)

    # Refusal path: nothing cleared the rerank-relevance cutoff.
    if not ranked or top_rr < s.rerank_cutoff:
        msg = "I couldn't find this in the lectures."
        yield event("refuse", "complete",
                    f"Top relevance {top_rr:.3f} < cutoff {s.rerank_cutoff} — refusing",
                    clock, refused=True, answer=msg, top_score=round(top_rr, 3),
                    sources=_sources_payload(ranked))
        return

    yield event("generate", "start", f"Generating cited answer via Nebius "
                f"({s.nebius_llm_model})…", clock)
    prompt = (f"{_SYSTEM}\n\n=== CONTEXT ===\n{_build_context(ranked)}\n\n"
              f"=== QUESTION ===\n{question}\n\n=== ANSWER ===")
    answer = str(get_llm().complete(prompt)).strip()
    yield event("generate", "complete", "Answer generated", clock)

    yield event("done", "complete", "Done", clock, refused=False, answer=answer,
                top_score=round(top_rr, 3), sources=_sources_payload(ranked))


def answer_question(question: str) -> Answer:
    """Non-streaming path for the CLI: hybrid retrieve → rerank → refuse/generate."""
    s = load_settings()
    ranked = rerank(question, _retrieve_hybrid(question, s.top_k), s.rerank_top_n)
    top_rr = ranked[0].rerank_score if ranked else 0.0

    if not ranked or top_rr < s.rerank_cutoff:
        return Answer(refused=True, answer="I couldn't find this in the lectures.",
                      top_score=top_rr, sources=ranked)

    prompt = (f"{_SYSTEM}\n\n=== CONTEXT ===\n{_build_context(ranked)}\n\n"
              f"=== QUESTION ===\n{question}\n\n=== ANSWER ===")
    answer = str(get_llm().complete(prompt)).strip()
    return Answer(refused=False, answer=answer, top_score=top_rr, sources=ranked)
