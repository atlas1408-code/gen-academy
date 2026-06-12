# Evaluation Report — Glass-Box RAG

> Retrieval + refusal evaluation over the 4-lecture corpus. Reproduce with
> `python eval/run_eval.py --report` (question set: `eval/questions.yaml`).

## Headline results

- **Retrieval is strong:** every answerable question retrieves a correct chunk
  (**hit@k = 100%**), and 92% put it in the top 3 (**hit@3 = 92%**, **MRR = 0.70**)
  at the production setting (hybrid, α=0.7).
- **Hybrid clearly beats dense on this corpus** — the *opposite* of what we saw
  on a single lecture, confirming hybrid's value emerges at scale.
- **Refusal is layered and effective:** 3 of 4 unanswerable questions are
  refused at the cheap retrieval gate; the 4th — a semantically-adjacent
  near-miss — is caught by the grounded-generation gate. **End-to-end refusal:
  100%.**

---

## Methodology

**Corpus.** 4 real bootcamp lectures (`week1-session1/2`, `week2-session1/2`,
~360 chunks) plus 3 short synthetic primers (`random*.txt`) used for ingest-flow
testing, all in one Pinecone index.

**Question set.** 17 questions across five behavior categories
(`eval/questions.yaml`):

| Category | n | What it tests |
|---|---|---|
| single_chunk | 5 | Obvious, factual, clearly in the corpus |
| multi_topic | 3 | Spans / appears across multiple lectures |
| ambiguous | 3 | Underspecified; a reasonable answer expected |
| borderline | 2 | Only lightly covered ("maybe"); thin-coverage robustness |
| unanswerable | 4 | Not in the corpus; **must refuse** |

**Ground truth.** Each answerable question is labeled with **lecture-qualified**
timestamps (`"week2-session1 00:31:34"`) — the points in a specific lecture that
actually answer it. A retrieval **hit** = a returned chunk *from that lecture*
whose `[timestamp_start, timestamp_end]` window contains the timestamp. Labeling
by lecture (not bare timestamp) matters in a multi-file corpus, where any
timestamp exists in every lecture.

**Metrics.** hit@k and hit@3 (did the right chunk appear in the top-k / top-3?),
**MRR** (mean reciprocal rank of the first correct chunk), and **refusal rate**
for unanswerable questions. `top_k = 8`, `similarity_cutoff = 0.40`,
`hybrid α = 0.7`.

---

## Results — retrieval quality (hybrid, α=0.7)

| Category | n | hit@k | hit@3 | MRR |
|---|---|---|---|---|
| single_chunk | 5 | 100% | 80% | 0.640 |
| multi_topic | 3 | 100% | 100% | 0.667 |
| ambiguous | 3 | 100% | 100% | 0.778 |
| borderline | 2 | 100% | 100% | 0.750 |
| **Overall (answerable, 13)** | | **100%** | **92%** | **0.695** |

Every answerable question — including the ambiguous and lightly-covered
"borderline" ones — retrieved a genuinely relevant chunk. The only sub-top-3
case was a *single-chunk* question (q03, "what is an embedding?"): embeddings are
discussed in **four** lectures, so the specific labeled chunk landed at rank 5
among many valid embedding chunks. That's a labeling artifact, not a real miss —
the answer was well-covered.

### Dense vs. hybrid — the scale effect

| Config | hit@k | hit@3 | MRR | refusal* |
|---|---|---|---|---|
| Dense (α=1.0) | 92% | 54% | 0.499 | 50% |
| **Hybrid (α=0.7)** | **100%** | **92%** | **0.695** | **75%** |

\*retrieval-gate refusal at cutoff 0.40 (tuned for the hybrid scale).

This is the most important experimental result. On a **single clean lecture**,
hybrid merely *tied* dense (documented earlier). On the **4-lecture corpus**,
hybrid **substantially outperforms** dense — hit@3 jumps 54% → 92%, MRR 0.50 →
0.70. As the corpus grows and gets noisier (more lexically-overlapping content,
more ASR jargon), the sparse BM25 signal earns its keep by anchoring on exact
terms that dense similarity blurs. **Lesson: evaluate retrieval strategy on a
corpus that resembles production, not a toy slice.**

---

## Results — refusal (defense in depth)

| # | Question | top score | retrieval gate | end-to-end |
|---|---|---|---|---|
| q14 | best pizza dough recipe | 0.223 | refuse ✓ | refuse ✓ |
| q15 | Tesla 2024 revenue | 0.296 | refuse ✓ | refuse ✓ |
| q16 | Kubernetes ingress TLS | 0.316 | refuse ✓ | refuse ✓ |
| q17 | Nebius API price per token | **0.500** | **answer ✗** | **refuse ✓** |

Three clearly off-topic questions are refused cheaply at the **retrieval gate**
(top score below the 0.40 cutoff — no LLM call needed). q17 is the interesting
one: it's a **semantically-adjacent near-miss** — "Nebius" is heavily present in
the corpus, so retrieval returns a high-scoring Nebius chunk (0.500), but that
chunk says nothing about *pricing*. It slips past the cutoff, but the **strict
grounded-generation prompt** ("answer only from context; say you don't know
otherwise") catches it and the system replies *"I couldn't find this in the
lectures."* So the two gates are complementary, and **end-to-end refusal is 4/4
(100%)**.

---

## Failure analysis

- **The similarity cutoff has a ceiling.** q17's top score (0.500) sits *above*
  the lowest answerable score (q02 "temperature", 0.507). The gap is ~0.007 —
  there is **no cutoff value that refuses q17 without also over-refusing a
  genuine question**. A pure similarity threshold cannot distinguish "close to
  the topic" from "actually contains the answer." This is the structural limit
  of cutoff-based refusal, and the argument for the two-layer design (and for a
  reranker, below).
- **Generation-level refusal is doing real work** and isn't captured by
  retrieval-only metrics — worth measuring end-to-end, not just at the gate.
- **Multi-location topics depress MRR slightly** (q03). When a concept appears in
  many lectures, "the" correct chunk is fuzzy; hit@k stays 100% but rank scatters.

---

## Key findings

1. **Hybrid retrieval pays off at scale** — the headline reversal from the
   single-lecture experiment.
2. **Layered refusal works:** cheap retrieval cutoff for off-topic, strict
   grounded generation for adjacent near-misses → 100% end-to-end on our set.
3. **Cutoff-only refusal is provably insufficient** for near-misses (q17).
4. Retrieval quality is high across *all* question types, including ambiguous
   and lightly-covered ones.

---

## Recommendations / next steps

- **Add the cross-encoder reranker** (designed as a drop-in). A cross-encoder
  scores the (question, chunk) pair jointly and would rate the Nebius-overview
  chunk as low-relevance to a *pricing* question — closing the q17 gap at the
  retrieval gate instead of relying on generation.
- **Report end-to-end refusal**, not just the retrieval gate, as the headline
  refusal metric.
- **Faithfulness scoring** (e.g. RAGAS or an LLM judge) to quantify how well
  cited answers are grounded — the next metric beyond retrieval hit-rate.
- **Grow + balance the question set** as the corpus grows; re-run dense-vs-hybrid
  to track how the gap widens.

---

## Reproduce

```bash
python eval/run_eval.py --report      # per-question + per-category + dense-vs-hybrid
python eval/run_eval.py --compare     # alpha sweep (dense → hybrid)
```
*(Numbers above from a run on 2026-06-12; latency and exact scores vary slightly
run to run with embedding-endpoint warmth.)*
