"""Retrieval evaluation harness (PLAN.md §10 Phase 2, §11).

Measures retrieval quality on the fixed question set so we can document the
required before/after comparisons (dense vs hybrid, no-rerank vs rerank).

Metrics:
  * hit@k / hit@3 — did a chunk whose time window contains a ground-truth
    timestamp appear in the top-k / top-3 results?
  * MRR          — mean reciprocal rank of the first relevant chunk.
  * refusal acc  — for unanswerable questions, would the system refuse
    (top score < SIMILARITY_CUTOFF)?
  * latency      — retrieval wall time per question.

The evaluator takes a `retrieve_fn(question, top_k) -> list[Source]`, so later
phases plug in hybrid / reranked retrievers without changing this file.

Run from repo root:  python eval/run_eval.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from rag.config import load_settings          # noqa: E402
from rag.query import _retrieve, _to_sources, Source  # noqa: E402
from rag.nebius import get_embed_model          # noqa: E402
from rag.pinecone_store import ensure_index, l2_normalize  # noqa: E402
from rag.sparse import encode_query, scale_sparse  # noqa: E402


def _sec(ts: str) -> int:
    h, m, s = (int(x) for x in ts.split(":"))
    return h * 3600 + m * 60 + s


def _load_questions() -> list[dict]:
    return yaml.safe_load((ROOT / "eval" / "questions.yaml").read_text())


def _first_hit_rank(sources: list[Source], gt: list[str]) -> int | None:
    """1-based rank of the first retrieved chunk that matches a ground-truth entry.

    Each gt entry is "lecture_id HH:MM:SS"; a match requires the chunk to be from
    that lecture AND its [start, end] window to contain the timestamp (so a bare
    timestamp can't match the wrong file in a multi-lecture corpus).
    """
    parsed = []
    for g in gt:
        lid, ts = g.rsplit(" ", 1)
        parsed.append((lid, _sec(ts)))
    for i, s in enumerate(sources, start=1):
        try:
            lo, hi = _sec(s.timestamp_start), _sec(s.timestamp_end)
        except Exception:
            continue
        if any(s.lecture_id == lid and lo <= sec <= hi for lid, sec in parsed):
            return i
    return None


def evaluate(retrieve_fn, label: str, *, top_k: int | None = None,
             cutoff: float | None = None) -> dict:
    s = load_settings()
    top_k = top_k or s.top_k
    cutoff = s.similarity_cutoff if cutoff is None else cutoff
    questions = _load_questions()

    rows = []
    for q in questions:
        t0 = time.perf_counter()
        sources = retrieve_fn(q["question"], top_k)
        dt = (time.perf_counter() - t0) * 1000
        top_score = sources[0].score if sources else 0.0

        row = {"id": q["id"], "category": q["category"],
               "answerable": q["answerable"], "top_score": top_score,
               "latency_ms": dt}
        if q["answerable"]:
            rank = _first_hit_rank(sources, q.get("ground_truth", []))
            row["rank"] = rank
            row["hit_k"] = rank is not None
            row["hit_3"] = rank is not None and rank <= 3
            row["rr"] = (1.0 / rank) if rank else 0.0
        else:
            # Correct behavior = would refuse (nothing clears the cutoff).
            row["refused"] = top_score < cutoff
        rows.append(row)

    return {"label": label, "top_k": top_k, "cutoff": cutoff, "rows": rows}


def summarize(result: dict) -> None:
    rows = result["rows"]
    ans = [r for r in rows if r["answerable"]]
    una = [r for r in rows if not r["answerable"]]

    print(f"\n===== {result['label']}  (top_k={result['top_k']}, "
          f"cutoff={result['cutoff']}) =====")
    print(f"{'id':<5}{'category':<14}{'score':>7}{'rank':>6}{'hit@k':>7}{'ms':>8}")
    for r in rows:
        rank = r.get("rank")
        rank_s = str(rank) if rank else ("—" if r["answerable"] else "n/a")
        hit = ("✓" if r.get("hit_k") else "✗") if r["answerable"] else \
              ("refuse✓" if r.get("refused") else "refuse✗")
        print(f"{r['id']:<5}{r['category']:<14}{r['top_score']:>7.3f}"
              f"{rank_s:>6}{hit:>7}{r['latency_ms']:>8.0f}")

    def rate(xs, key):
        return sum(1 for x in xs if x.get(key)) / len(xs) if xs else 0.0

    mrr = sum(r["rr"] for r in ans) / len(ans) if ans else 0.0
    print(f"\n  Answerable ({len(ans)}): hit@k={rate(ans,'hit_k'):.0%}  "
          f"hit@3={rate(ans,'hit_3'):.0%}  MRR={mrr:.3f}")
    print(f"  Unanswerable ({len(una)}): correct-refusal={rate(una,'refused'):.0%}")
    avg_ms = sum(r["latency_ms"] for r in rows) / len(rows)
    print(f"  Avg retrieval latency: {avg_ms:.0f} ms")


def _metrics(rows: list[dict]) -> dict:
    ans = [r for r in rows if r["answerable"]]
    una = [r for r in rows if not r["answerable"]]
    def rate(xs, k): return sum(1 for x in xs if x.get(k)) / len(xs) if xs else 0.0
    mrr = sum(r["rr"] for r in ans) / len(ans) if ans else 0.0
    return {"hit_k": rate(ans, "hit_k"), "hit_3": rate(ans, "hit_3"), "mrr": mrr,
            "refusal": rate(una, "refused")}


def compare_alphas(alphas=(1.0, 0.7, 0.5, 0.3), top_k=None, cutoff=None) -> None:
    """Embed each question ONCE, then re-query Pinecone at each alpha locally.

    alpha=1.0 is dense-only; lower alphas blend in BM25 sparse. This is the
    required dense-vs-hybrid before/after comparison (PLAN.md §10 Phase 2c).
    """
    s = load_settings()
    top_k = top_k or s.top_k
    cutoff = s.similarity_cutoff if cutoff is None else cutoff
    questions = _load_questions()
    index = ensure_index()
    embed = get_embed_model()

    # One embedding + one sparse encode per question (cached across alphas).
    cache = []
    for q in questions:
        dense_unit = l2_normalize(embed.get_text_embedding(q["question"]))
        sparse_raw = encode_query(q["question"])
        cache.append((q, dense_unit, sparse_raw))

    results = {a: [] for a in alphas}
    for a in alphas:
        for q, dense_unit, sparse_raw in cache:
            dense = [a * x for x in dense_unit]
            kwargs = dict(vector=dense, top_k=top_k, include_metadata=True, namespace="corpus")
            if a < 1.0:
                kwargs["sparse_vector"] = scale_sparse(sparse_raw, 1.0 - a)
            sources = _to_sources(index.query(**kwargs))
            top = sources[0].score if sources else 0.0
            row = {"answerable": q["answerable"]}
            if q["answerable"]:
                rank = _first_hit_rank(sources, q.get("ground_truth", []))
                row.update(hit_k=rank is not None, hit_3=rank is not None and rank <= 3,
                           rr=(1.0 / rank) if rank else 0.0)
            else:
                row["refused"] = top < cutoff
            results[a].append(row)

    print(f"\n===== DENSE vs HYBRID  (top_k={top_k}) =====")
    print(f"{'config':<18}{'hit@k':>8}{'hit@3':>8}{'MRR':>8}{'refusal*':>10}")
    for a in alphas:
        m = _metrics(results[a])
        label = "DENSE (α=1.0)" if a == 1.0 else f"HYBRID α={a}"
        print(f"{label:<18}{m['hit_k']:>7.0%}{m['hit_3']:>8.0%}{m['mrr']:>8.3f}{m['refusal']:>10.0%}")
    print("  *refusal at the dense-scale cutoff; refusal is retuned post-rerank in 2d.")


def report() -> None:
    """Full eval report: per-question + per-category at the production setting
    (hybrid α=0.7), plus the dense-vs-hybrid overall comparison. Embeds each
    question once and re-queries Pinecone at both alphas."""
    s = load_settings()
    top_k, cutoff = s.top_k, s.similarity_cutoff
    questions = _load_questions()
    index = ensure_index()
    embed = get_embed_model()

    cache = []
    for q in questions:
        t0 = time.perf_counter()
        dense_unit = l2_normalize(embed.get_text_embedding(q["question"]))
        embed_ms = (time.perf_counter() - t0) * 1000
        cache.append((q, dense_unit, encode_query(q["question"]), embed_ms))

    def run_alpha(a):
        rows = []
        for q, dense_unit, sparse_raw, embed_ms in cache:
            dense = [a * x for x in dense_unit]
            kw = dict(vector=dense, top_k=top_k, include_metadata=True, namespace="corpus")
            if a < 1.0:
                kw["sparse_vector"] = scale_sparse(sparse_raw, 1.0 - a)
            sources = _to_sources(index.query(**kw))
            top = sources[0].score if sources else 0.0
            row = {"id": q["id"], "category": q["category"], "answerable": q["answerable"],
                   "top_score": top, "embed_ms": embed_ms}
            if q["answerable"]:
                rank = _first_hit_rank(sources, q.get("ground_truth", []))
                row.update(rank=rank, hit_k=rank is not None,
                           hit_3=rank is not None and rank <= 3, rr=(1.0 / rank) if rank else 0.0)
            else:
                row["refused"] = top < cutoff
            rows.append(row)
        return rows

    prod = run_alpha(s.hybrid_alpha)
    dense = run_alpha(1.0)

    print(f"\n===== PER-QUESTION (hybrid α={s.hybrid_alpha}, cutoff={cutoff}) =====")
    print(f"{'id':<5}{'category':<14}{'score':>7}{'rank':>6}{'result':>10}")
    for r in prod:
        if r["answerable"]:
            res = "hit" if r["hit_k"] else "MISS"
            rank = str(r["rank"]) if r["rank"] else "—"
        else:
            res = "refuse✓" if r["refused"] else "ANSWER✗"
            rank = "n/a"
        print(f"{r['id']:<5}{r['category']:<14}{r['top_score']:>7.3f}{rank:>6}{res:>10}")

    print("\n===== BY CATEGORY (hybrid α=%.1f) =====" % s.hybrid_alpha)
    cats = ["single_chunk", "multi_topic", "ambiguous", "borderline", "unanswerable"]
    print(f"{'category':<14}{'n':>3}{'hit@k':>8}{'hit@3':>8}{'MRR':>8}{'refuse':>9}")
    for c in cats:
        rows = [r for r in prod if r["category"] == c]
        if not rows:
            continue
        ans = [r for r in rows if r["answerable"]]
        una = [r for r in rows if not r["answerable"]]
        hk = f"{sum(r['hit_k'] for r in ans)/len(ans):.0%}" if ans else "—"
        h3 = f"{sum(r['hit_3'] for r in ans)/len(ans):.0%}" if ans else "—"
        mrr = f"{sum(r['rr'] for r in ans)/len(ans):.3f}" if ans else "—"
        ref = f"{sum(r['refused'] for r in una)/len(una):.0%}" if una else "—"
        print(f"{c:<14}{len(rows):>3}{hk:>8}{h3:>8}{mrr:>8}{ref:>9}")

    print("\n===== OVERALL: DENSE vs HYBRID =====")
    print(f"{'config':<16}{'hit@k':>8}{'hit@3':>8}{'MRR':>8}{'refusal':>9}")
    for label, rows in [("DENSE α=1.0", dense), (f"HYBRID α={s.hybrid_alpha}", prod)]:
        m = _metrics(rows)
        print(f"{label:<16}{m['hit_k']:>7.0%}{m['hit_3']:>8.0%}{m['mrr']:>8.3f}{m['refusal']:>9.0%}")
    avg_embed = sum(e for *_, e in cache) / len(cache)
    print(f"\n  avg query-embed latency: {avg_embed:.0f} ms")


if __name__ == "__main__":
    import sys as _sys
    if "--report" in _sys.argv:
        report()
    elif "--compare" in _sys.argv:
        compare_alphas()
    else:
        summarize(evaluate(_retrieve, "DENSE (baseline)"))
