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
from .nebius import get_embed_model, get_llm
from .pinecone_store import ensure_index

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


@dataclass
class Answer:
    refused: bool
    answer: str
    top_score: float
    sources: list[Source] = field(default_factory=list)


def _retrieve(question: str, top_k: int) -> list[Source]:
    vec = get_embed_model().get_text_embedding(question)
    res = ensure_index().query(
        vector=vec, top_k=top_k, include_metadata=True, namespace=_NAMESPACE
    )
    sources = []
    for m in res.get("matches", []):
        md = m.get("metadata", {})
        sources.append(Source(
            score=m["score"],
            title=md.get("title", ""),
            lecture_id=md.get("lecture_id", ""),
            timestamp_start=md.get("timestamp_start", ""),
            timestamp_end=md.get("timestamp_end", ""),
            text=md.get("text", ""),
        ))
    return sources


def _build_context(sources: list[Source]) -> str:
    blocks = []
    for s in sources:
        blocks.append(
            f"[{s.title} {s.timestamp_start}-{s.timestamp_end}] (score={s.score:.3f})\n{s.text}"
        )
    return "\n\n".join(blocks)


def answer_question(question: str) -> Answer:
    s = load_settings()
    sources = _retrieve(question, s.top_k)
    top_score = sources[0].score if sources else 0.0

    # Refusal path: nothing cleared the similarity cutoff.
    if not sources or top_score < s.similarity_cutoff:
        return Answer(
            refused=True,
            answer="I couldn't find this in the lectures.",
            top_score=top_score,
            sources=sources,
        )

    context = _build_context(sources)
    prompt = (
        f"{_SYSTEM}\n\n=== CONTEXT ===\n{context}\n\n"
        f"=== QUESTION ===\n{question}\n\n=== ANSWER ==="
    )
    resp = get_llm().complete(prompt)
    return Answer(
        refused=False,
        answer=str(resp).strip(),
        top_score=top_score,
        sources=sources,
    )
