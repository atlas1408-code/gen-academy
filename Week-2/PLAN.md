# Course-Sessions RAG — Project Submission

Week-2 · Mastering Agentic AI Bootcamp

A Retrieval-Augmented Generation app that lets everyone in the Gen Academy cohort ask questions about the cohort's sessions and get grounded, citation-backed answers — or an honest "I don't know" when the answer isn't in the sessions.

## Contents

1. The RAG Framework — the primer and the framework table
2. How it works — approach and architecture
3. RAG concepts and decisions
4. Evaluation and results
5. What worked, what didn't, and how we recovered
6. Add-on — the Glass-Box RAG Simulator
7. Limitations and next steps
8. Appendix — config, how to run, links

---

# Part 1 — The RAG Framework

## The Primer

My RAG app helps **every learner in the Gen Academy cohort** answer **questions about any session in the cohort** from **the cohort's session transcripts** in a **web app**, with **greater than 90% faithfulness**.

How this primer follows the three rules:

- **The corpus is named specifically** — not "the course material," but the cohort's recorded sessions (so far 9: 4 weekly lectures plus 5 guest lectures on Codex, LlamaIndex, Nemotron, Pinecone, and Wispr; ~526 chunks, Zoom-transcribed with speaker labels and timestamps). The corpus shape drove every chunking and retrieval decision.
- **Faithfulness, not just relevance** — success means the answer is grounded in and cited to the retrieved session chunks, not merely plausible. Target: greater than 90% faithfulness. [INSERT: provided faithfulness / relevance figure.]
- **Latency is a first-class constraint** — we set a 6-second end-to-end ceiling up front so retrieval wouldn't be over-engineered. (Measured latency and the current gap are in Part 4.)

## The Framework

| Field | Our answer |
|---|---|
| Use case | Cohort learners ask conceptual questions ("how does X work", "what was said about Y") about the sessions; answers appear in a web app (also CLI/API), each grounded with a citation to the exact session and timestamp. |
| Corpus | The cohort's recorded sessions — **9 so far** (4 weekly lectures from weeks 1–2 + 5 guest lectures: Codex, LlamaIndex, Nemotron, Pinecone, Wispr), Zoom-transcribed as .txt with speaker labels and timestamps; English; **~526 chunks**. Source of truth = the recorded sessions. New sessions are added as the cohort continues. |
| Ingestion + cleaning | Transcripts are parsed into timestamped segments, then a glossary fixes speech-to-text jargon (e.g. "cloud code" to "Claude Code") and whitespace is normalized — all before chunking. The loader degrades gracefully: one session was a different, speaker-less export, and the chunker re-glues its fragments rather than failing. |
| Ingestion + freshness | Idempotent ingest — deterministic chunk IDs plus a content-hash record mean re-running only adds new or changed sessions (never duplicates). A new session is added on demand: upload its .txt and it is chunked, embedded, and stored immediately. No live feed; freshness is per-session and manual. |
| Chunking + embedding | Transcript-aware chunking — segments packed to ~512 tokens with ~15% overlap, with timestamps carried into metadata as citation anchors. Embedding model: Qwen3-Embedding-8B (4096-dim) via Nebius Token Factory. Chunk size was chosen together with the model so capacity matches. |
| Retrieve | Pinecone serverless (dotproduct metric); hybrid retrieval = dense semantic plus sparse BM25 (alpha = 0.7), top-k = 8; a **hosted cross-encoder reranker** (Pinecone `bge-reranker-v2-m3`) re-scores the candidates and keeps the top 4; refusal uses the rerank relevance score plus a grounded-generation gate. |

How this follows the framework tips:

- **Chunk size and embedding model picked together** — ~512-token chunks paired with the 4096-dim model, and the Pinecone index dimension set to match exactly.
- **Hybrid retrieval** — dense alone misses exact terms (product names, acronyms the transcription mangles); BM25 alone misses intent. We blend them, and the evaluation shows the blend pays off as the corpus grows (Part 4).
- **The "I don't know" path was designed first** — refusal is a first-class, tested behavior with two independent layers, not an afterthought.

---

# Part 2 — How it works

## Approach

We built in phases, with a test-and-approve gate at each step, on one principle: correctness before polish. Get a provably working retrieval-and-refusal slice first; only then add hybrid retrieval, evaluation, and the user interface.

| Phase | Goal | Status |
|---|---|---|
| 0 · Setup | Nebius and Pinecone working end-to-end | Done |
| 1 · Thin slice | Ingest and query (dense), grounded cited answers, refusal | Done |
| 2 · Quality | Cleaning, hybrid retrieval, evaluation harness | Done |
| 3 · Surface | A web app to use it (and watch the pipeline) | Done |
| 4 · Eval and deliverables | Evaluation report, this document, demo | Done / in progress |

## Architecture

Ingest (once per session): transcript .txt → parse into timestamped segments → clean (glossary) → chunk (~512 tokens, ~15% overlap) → embed (Nebius) → store in Pinecone (dense + sparse).

Query (every question): question → embed (Nebius) → hybrid search in Pinecone (dense + sparse, top-8) → rerank (Pinecone hosted cross-encoder, keep top-4) → if the top rerank relevance is below the cutoff, refuse ("not in the sessions"); otherwise generate a cited answer (Nebius LLM, grounded prompt).

| Layer | Tool |
|---|---|
| Orchestration | LlamaIndex |
| Models (embed + generate) | Nebius Token Factory (required) — Qwen3-Embedding-8B and Llama-3.3-70B-Instruct |
| Vector store | Pinecone (serverless, dense + sparse hybrid) |
| Interface | CLI / API, plus a web app (Part 6) |

---

# Part 3 — RAG concepts and decisions

- **Transcript-aware chunking.** Lecture transcripts have no headings, so we chunk on natural segment boundaries packed to ~512 tokens with overlap, and carry timestamps so every chunk is citable ("Week 1, Session 1 — 00:53:22").
- **One embedding space for sessions and questions.** The same Nebius model embeds chunks at ingest and the question at query time, so similarity is meaningful. Chunks are stored with their original text — we never reverse a vector back into text.
- **Speech-to-text cleaning via a glossary.** The auto-transcription mangles jargon ("cloud code" instead of "Claude Code", 11 times in one session). A word-boundary glossary normalizes known errors before chunking, which directly helps keyword and hybrid retrieval.
- **Hybrid retrieval (dense + sparse).** Dense captures meaning; BM25 recovers exact terms. Blended at alpha = 0.7 on a dotproduct index (dense vectors normalized so dotproduct behaves like cosine).
- **Cross-encoder reranking.** Hybrid returns the top-8 by similarity; a hosted cross-encoder (Pinecone `bge-reranker-v2-m3`) then reads each (question, chunk) pair *together* and re-scores them for true relevance, keeping the best 4 for generation. Uses the existing Pinecone key — no extra infrastructure. The rerank score is well-calibrated (≈0 for off-topic, high for genuine answers), so refusal moves onto it.
- **Refusal designed first, and layered.** A cheap similarity cutoff refuses before the LLM is even called; a strict grounded-generation prompt ("answer only from context; otherwise say you don't know") catches anything that slips past. This two-layer design is what makes the app trustworthy.
- **Grounded, cited generation.** The LLM answers only from retrieved chunks and cites the session and timestamp for each claim — making faithfulness checkable.
- **Idempotent ingest.** Deterministic chunk IDs plus a content-hash record mean re-ingesting never duplicates.

---

# Part 4 — Evaluation and results

Evaluation is the core of this project — we built a measurement harness early rather than eyeballing outputs. [INSERT: provided faithfulness / relevance figure or copy.]

## The evaluation set

23 questions across five behavior categories, each answerable one labeled with session-qualified ground-truth timestamps (so a timestamp can't match the wrong session):

| Category | Count | Tests |
|---|---|---|
| Single-chunk (obvious) | 10 | clearly in the corpus |
| Multi-session spanning | 4 | synthesizing across sessions |
| Ambiguous | 3 | underspecified — a reasonable answer |
| Borderline ("maybe") | 2 | lightly-covered robustness |
| Unanswerable (refusal) | 4 | must refuse |

Metrics: hit@k and hit@3 (did a correct chunk appear?), MRR (was it ranked near the top?), and end-to-end refusal rate.

## Retrieval quality (production setting: hybrid, alpha = 0.7)

| Category | hit@k | hit@3 | MRR |
|---|---|---|---|
| Single-chunk | 100% | 70% | 0.65 |
| Multi-session | 100% | 100% | 0.75 |
| Ambiguous | 100% | 100% | 0.61 |
| Borderline | 100% | 100% | 0.75 |
| All answerable | 100% | 84% | 0.68 |

Retrieval found a genuinely relevant chunk for every answerable question (hit@k = 100%) across all nine sessions.

## Key result — hybrid beats dense, and the gap holds at scale

| Configuration | hit@k | hit@3 | MRR |
|---|---|---|---|
| Dense only | 95% | 58% | 0.56 |
| Hybrid (alpha = 0.7) | 100% | 84% | 0.68 |

On a single clean session, hybrid merely tied dense. As the corpus grew to 4 and then 9 sessions, hybrid pulled clearly ahead and stayed ahead (a +26-point hit@3 gap). As the corpus gets larger and more lexically overlapping, the sparse keyword signal earns its keep. Lesson: evaluate retrieval strategy on a corpus that resembles production.

## Key result — retrieval finds the answer; ranking is the next lever

Tripling the corpus (3 → 9 sessions) kept **hit@k at 100%** — the right session is always retrieved — but **hit@3 / MRR softened** (92% → 84%, 0.70 → 0.68). For a few factual lookups (e.g. "what is an embedding?", "what is Codex?") the *definitional* chunk now ranks 5–8 amid many chunks that mention the term. The content is found; sharpening the *ranking* is the job of the reranker — which we then added.

## Key result — the cross-encoder reranker sharpens ranking and refusal

We added a hosted cross-encoder reranker (Pinecone `bge-reranker-v2-m3`, top-8 → top-4) and re-ran the same 23-question set:

| Metric | Hybrid only | Hybrid + rerank |
|---|---|---|
| MRR (all answerable) | 0.68 | **0.74** |
| Single-chunk hit@3 | 70% | **90%** |
| Single-chunk MRR | 0.65 | **0.80** |
| Off-topic refusal scores | ~0.2–0.3 | **~0.00** (crisp) |

The reranker pulls the genuinely-best chunk to **rank 1** for factual lookups (e.g. "What is Wispr Flow?" moved from rank 8 → 1, "What is an embedding?" 5 → 1), lifting MRR and single-chunk hit@3 sharply. It also makes refusal far cleaner: clearly off-topic questions now score ≈0 (vs ~0.2–0.3 on the similarity scale), so the refusal cutoff (rerank relevance < 0.10) catches them crisply, while the semantically-adjacent near-miss still falls through to the grounded-generation gate — **end-to-end refusal stays 100%.**

One honest caveat: overall hit@3 dipped slightly (84% → 79%) entirely within the **ambiguous** category. For broad questions like "how does chunking work?", the reranker surfaces a *different but equally valid* chunk than the single timestamp we labeled — the same narrow-ground-truth artifact we corrected for one multi-session question. The answers stay grounded; the metric, not the system, is the limitation there.

## Key result — layered refusal (100% end-to-end)

| Refusal layer | Catches | On our set |
|---|---|---|
| Similarity cutoff (cheap, before the LLM) | clearly off-topic questions | 3 of 4 |
| Grounded generation (strict prompt) | semantically-adjacent near-misses | the 4th |
| End to end | | 4 of 4 (100%) |

The 4th case ("how much does the Nebius API cost?") is instructive: "Nebius" is all over the corpus but pricing isn't, so retrieval scored it just above the cutoff — and the lowest genuine question scored just below it. No single threshold can separate them, which is exactly why the second (generation) gate matters. Full breakdown: eval/REPORT.md in the repo.

## Latency

End-to-end query latency is currently about 6–8 seconds (embedding + hybrid retrieval + generation), against our 6-second target. The 8-billion-parameter embedding model is the only embedder Nebius offers, so that floor is largely fixed; the levers are query-embedding caching, parallel calls, and a faster generation model.

---

# Part 5 — What worked, what didn't, and how we recovered

What worked well:

- Phased, test-gated build — every surprise below was cheap to absorb.
- Layered refusal — 100% end-to-end, including a near-miss no single threshold could catch.
- Measuring before tuning — the cutoff, the hybrid weight, and the dense-vs-hybrid decision were all settled by the evaluation harness, not by feel.
- Idempotent ingest — re-running never corrupted the index.

What didn't go to plan, and the recovery:

- The planned models weren't available on the Nebius account. We queried the models endpoint and switched to what is offered (Qwen3-Embedding-8B, Llama-3.3-70B), updating the index dimension. Lesson: confirm provider inventory in Phase 0.
- Hybrid didn't beat dense — at first. We reported the null result rather than forcing it; it then paid off once we re-ran the experiment at scale. The recovery was not code — it was using a realistic corpus.
- A full network outage mid-build — diagnosed (no route to the internet, even GitHub down), confirmed it wasn't our code, and resumed when connectivity returned.
- Real data is messy — one session had a different, speaker-less transcript format; the loader was made to re-glue its fragments instead of failing.

---

# Part 6 — Add-on: the Glass-Box RAG Simulator

This is a bonus, not the core deliverable. The highlight is the RAG itself (Parts 1–5); the simulator is an optional way to see it work.

To make the system understandable — and to satisfy the vibe-coded-UI bonus — we built a web app that visualizes the pipeline live. It guides a user through a short "what is RAG?" intro, an optional concept walkthrough, and an interactive screen where they ask a question (or ingest a transcript) and watch each stage happen with real data: the embedding, the retrieved chunks with scores and timestamps, the cited answer, or the refusal. It is an educational lens over the same pipeline; the RAG works identically via CLI/API without it.

[INSERT: screenshot(s) of the simulator.]

---

# Part 7 — Limitations and next steps

- Cross-encoder reranker — **done** (Part 4). Added via Pinecone's hosted rerank API (`bge-reranker-v2-m3`) using the existing key, so no GPU/Brev or self-hosting was needed. It sharpened rank-1 precision and refusal calibration. Possible next tweak: broaden the eval's ground truth on ambiguous questions so the metric credits the reranker's alternative-but-valid picks.
- Slide-deck ingestion. The metadata schema already supports slides; this is pending real decks. Slides add clean, correctly-spelled jargon and richer citations.
- Latency. Bring end-to-end under 6 seconds via query-embedding caching, parallelism, and a faster generation model.
- Deeper evaluation. Automated faithfulness scoring (e.g. RAGAS) and a larger, balanced question set as more sessions are added.

---

# Appendix

## As-built configuration

| Setting | Value |
|---|---|
| Embedding model | Qwen/Qwen3-Embedding-8B (4096-dim), Nebius |
| Generation model | meta-llama/Llama-3.3-70B-Instruct, Nebius |
| Vector store | Pinecone serverless, dotproduct |
| Sparse encoder | BM25 (pinecone-text) |
| Reranker | Pinecone hosted `bge-reranker-v2-m3`, keep top 4 |
| Chunk size / overlap | ~512 tokens / ~80 tokens |
| Top-k (pre-rerank) | 8 |
| Hybrid alpha | 0.7 |
| Rerank refusal cutoff | 0.10 (relevance) |

## How to run

```
uv venv --python 3.12 .venv && uv pip install -r backend/requirements.txt
# add NEBIUS_API_KEY and PINECONE_API_KEY to backend/.env
cd backend
../.venv/bin/python -m rag.cli ingest                          # ingest the corpus
../.venv/bin/python -m rag.cli ask "what is a context window?" # ask a question
../.venv/bin/python ../eval/run_eval.py --report               # evaluation report
```

## Links and deliverables

- GitHub repo: [INSERT link]
- Demo video (≤5 min): [INSERT link]
- Faithfulness / relevance figure: [INSERT provided image or copy]
- Evaluation report: eval/REPORT.md (in the repo)
