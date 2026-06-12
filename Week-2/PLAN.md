# Glass-Box RAG — Project Write-up

> **Week-2 · Mastering Agentic AI Bootcamp**
> A working Retrieval-Augmented Generation system over ~17 hours of bootcamp
> lecture transcripts, wrapped in an interactive web app that **animates every
> stage of the pipeline** — so you can *watch* a document get chunked, embedded,
> stored, retrieved, and answered, and ask your own questions with cited,
> grounded answers (or an honest "I don't know").

This document is the project narrative: **how we approached the challenge, what
we tried, what worked and what didn't, the RAG concepts we explored and
evaluated, and where we'd take it next.** It is intentionally not a line-by-line
build log — the code and git history carry that.

---

## 1. The challenge and how we framed it

The brief was to build a real RAG application using **Nebius Token Factory** for
the model calls. Rather than a plain question box, we framed it as a **"glass
box"**: the same pipeline a normal bot hides, this one *instruments and
animates*. Every stage emits a structured event that the UI renders live. That
single decision shaped everything — it forced clean stage boundaries in the
backend and turned the app into a teaching tool as much as a product.

**The one-liner we built to:** *answer "how does X work / what was said about Y"
questions from bootcamp lecture transcripts, with grounded citations, an
explicit refusal when the answer isn't in the corpus, and a live visualization
of the retrieval pipeline.*

Two guiding principles:
- **Correctness before polish.** Get a provably-working CLI slice (and the
  refusal path) before any hybrid/rerank cleverness, and finish the retrieval
  substance before building the animated UI.
- **Be honest about results.** The graded substance of RAG is the *retrieval
  decisions and the evaluation beneath them*, so we measured rather than assumed
  — even when the measurement said our fancy idea didn't help (see §6).

---

## 2. How we approached it (methodology)

We worked in **phases, with a test-and-approve gate at each component**:

| Phase | Goal | Outcome |
|---|---|---|
| 0 · Setup | Prove Nebius + Pinecone work end-to-end | Smoke test: embed → upsert → query ✓ |
| 1 · Thin slice | CLI ingest + query, dense only, one transcript | Grounded cited answers + working refusal + idempotent ingest ✓ |
| 2 · Quality | Cleaning, hybrid retrieval, evaluation | Measured retrieval, tuned the refusal cutoff on data ✓ |
| 3 · Glass box | FastAPI + SSE backend, React visualizer | Live 3-screen guided app (landing → concept tour → interactive) ✓ |
| 4 · Eval & deliverables | Eval report, deck, video | In progress |

Each phase was built, tested against explicit acceptance criteria, and reviewed
before moving on. This kept the system provable at every step and made the
inevitable surprises (§7) cheap to recover from.

---

## 3. Architecture at a glance

```
INGEST (once per document)
  transcript .txt → load (timestamped segments) → clean (glossary)
    → chunk (~512 tok, ~15% overlap) → embed (Nebius) → upsert (Pinecone: dense + sparse)

QUERY (every question)
  question → embed (Nebius) → hybrid search (Pinecone: dense + sparse)
    → cutoff check ──low──▶ refuse ("not in the lectures")
                   └─pass─▶ generate cited answer (Nebius LLM)
```

| Layer | Tool | Role |
|---|---|---|
| Orchestration | **LlamaIndex** | Loaders, chunking, model calls |
| Models (embed + generate) | **Nebius Token Factory** | Required; OpenAI-compatible |
| Vector store | **Pinecone** | Dense + sparse hybrid search |
| Backend API | **FastAPI + SSE** | Streams a `StepEvent` per pipeline stage |
| Frontend | **React + Vite** | Animated, educational pipeline visualizer |

A deliberate choice: we call Pinecone through its **official client directly**
(not LlamaIndex's black-box query engine) so every stage is explicit and
instrumentable — the glass box needs to see each step to animate it.

---

## 4. The data

Transcripts were provided as **`.txt` files** in a recurring shape: a speaker
name, then paragraphs of speech, each followed by a trailing `HH:MM:SS`
timestamp. We wrote a structural parser around that pattern (a text line is
immediately followed by its timestamp; a speaker line is followed by a blank).

**A real-world wrinkle we hit:** the four course transcripts were *not* uniform.
Three followed the speaker/sentence format; one (`week2-session2`) was a
different export with **no speaker labels** and text fragmented into thousands of
tiny phrase-level segments. Rather than special-casing it, the chunker simply
**re-glues** fragments into normal ~512-token chunks, so that file ingests
cleanly — just without speaker metadata. The lesson: real corpora are messy;
build the loader to degrade gracefully, and treat metadata like speaker as
*optional per document*.

Timestamps are the key design asset here — transcripts have no page numbers, so
**timestamps become the citation anchors** ("Week1 Session1, 00:53:22").

> **Note on what's shared:** the actual course transcripts are kept local and are
> **not committed**. The repo ships only synthetic sample transcripts
> (`random*.txt`) so the ingest/query flows can be demonstrated without
> redistributing course content.

---

## 5. RAG concepts we explored (and the decisions we made)

- **Transcript-aware chunking.** Fixed-size chunking on raw text loses meaning.
  We chunk on natural boundaries (segments) packed to ~512 tokens with ~15%
  overlap, carrying `timestamp_start/end` into metadata so every chunk is
  citable.
- **One embedding space for documents and questions.** The same Nebius model
  embeds chunks at ingest and the question at query time, so similarity is
  meaningful. Vectors are stored *with their original text* — we never try to
  reverse a vector back into text.
- **ASR cleaning via a glossary.** Zoom's speech-to-text mangles jargon
  ("cloud code" → should be "Claude Code", 11× in one lecture). A
  word-boundary glossary fixes known manglings *before* chunking; an
  out-of-vocabulary scan (diff against a system dictionary) surfaces new
  candidates. This matters most for keyword/hybrid retrieval, which can only
  match a term that's actually spelled correctly.
- **Hybrid retrieval (dense + sparse).** Dense embeddings capture *meaning*;
  BM25 sparse vectors recover *exact terms* (product names, acronyms) that
  embeddings blur. We blend them: `score = α·dense + (1−α)·sparse`. This
  required a Pinecone `dotproduct` index with L2-normalized dense vectors (so
  dotproduct behaves like cosine).
- **Refusal as a first-class path.** A bot that hallucinates on retrieval
  failure is worse than one that says "not in the lectures." If the best
  retrieved score is below a cutoff, we **refuse before calling the LLM**. We
  designed and tested this early, not as an afterthought.
- **Strictly grounded, cited generation.** The LLM is instructed to answer
  *only* from the provided chunks and cite the lecture + timestamp for each
  claim — making faithfulness checkable.
- **Idempotent ingest.** Chunk IDs are deterministic (a hash of
  `lecture_id:type:index`) and a document-level manifest skips unchanged files,
  so re-ingesting never duplicates.

---

## 6. Experiments and evaluation (the RAG point of view)

Evaluation is the heart of the project, so we built a measurement harness early
rather than eyeballing outputs.

**The eval set.** A fixed set of 13 questions across four categories —
single-chunk factual, multi-topic spanning, ambiguous, and **unanswerable (must
refuse)** — each labeled with the ground-truth timestamps that actually answer
it. A retrieval "hit" means a returned chunk whose time window contains a
ground-truth timestamp, which keeps scoring independent of score scale.

**Metrics.** hit@k and hit@3 (did the right chunk appear?), **MRR** (was it
ranked near the top?), **refusal accuracy** (did unanswerable questions get
refused?), and end-to-end latency.

### Experiment 1 — dense baseline
Dense retrieval was already strong on this corpus: **hit@k 100%, hit@3 100%,
MRR 0.85**. On a clean, modest corpus the embeddings find the right chunk for
every answerable question.

### Experiment 2 — dense vs. hybrid (an honest null result)
We expected hybrid to win. It didn't — at least not here:

| Config | hit@k | hit@3 | MRR |
|---|---|---|---|
| Dense (α=1.0) | 100% | 100% | 0.850 |
| **Hybrid α=0.7** | 100% | 100% | 0.850 |
| Hybrid α=0.5 | 100% | 90% | 0.808 |
| Hybrid α=0.3 | 100% | 90% | 0.803 |

Hybrid at α=0.7 **ties** dense; pushing *more* weight to BM25 actually **hurts**
(keyword noise creeps into semantic questions). The honest conclusion: on a
small, clean, single-domain corpus, dense is already saturated and hybrid gives
no measurable lift — its payoff shows up at scale and on exact-jargon queries.
We kept α=0.7 as cheap lexical insurance and documented the result rather than
overselling it.

### Experiment 3 — tuning the refusal cutoff on data
The plan's default cutoff (0.30) was **too low**: tech-adjacent but off-topic
questions leaked through (a Tesla-revenue question scored 0.34, a Kubernetes
question 0.43 — both above 0.30, so both would have been answered from junk
context). Measuring the score distribution showed a clean gap: answerable
questions never dropped below ~0.49, unanswerable never rose above ~0.30. We set
the cutoff to **0.40**, giving **100% correct refusal and 100% answerable
retention**. This is the project in microcosm: *measure the distribution, then
pick the threshold — don't guess a number.*

### A standing concern — latency
End-to-end query latency is **~6–8s** (embed ~1–4s, hybrid retrieve ~3s,
generation ~4–5s), which sits over our 6s target. The 8B embedding model is the
only embedder Nebius offers, so that floor is somewhat fixed; the realistic
levers are query-embedding caching, parallelism, and a faster generation model.

---

## 7. What worked, what didn't, and how we recovered

**Worked well**
- The **phased, test-gated approach** — every surprise below was cheap because
  the system was provable at each step.
- **Refusal-first design** and **data-driven cutoff tuning** — the most
  trustworthy parts of the system.
- **Idempotent ingest** — re-running never corrupted the index.
- The **glass-box framing** — it improved the architecture (clean stage events)
  and became the product's differentiator.

**Didn't go to plan — and how we recovered**
- **Planned models weren't available on the account.** The intended embedding
  model (`bge-en-icl`) returned 404 and the intended LLM (`Llama-3.1-70B`)
  wasn't listed. We queried the models endpoint, switched to what's actually
  offered — **Qwen3-Embedding-8B (4096-dim)** and **Llama-3.3-70B-Instruct** —
  and updated the index dimension accordingly. Lesson: confirm provider
  inventory in Phase 0, don't trust a spec sheet.
- **Hybrid retrieval didn't beat dense** (Experiment 2). We resisted the urge to
  force it; kept it on at a conservative weight and reported the null result.
- **A full network outage mid-build.** Every API call started timing out; we
  diagnosed it (DNS resolved but no route to the public internet — even GitHub
  was unreachable), confirmed it wasn't our code, and resumed once connectivity
  returned. The work already done (a re-ingested index) survived.
- **An IPv6 dev-server gotcha** cost real time: Vite served on `localhost`
  (IPv6 `::1`) while health checks hit `127.0.0.1` (IPv4) and failed, making the
  server look dead. Recorded so it won't recur.
- **Frontend layout iterations.** The first results view buried the answer under
  a tall stack of evidence; later, columns overflowed on laptops and looked
  empty on large monitors. We iterated to a **docking workspace** (pipeline
  docks left, answer + sources fill the right) for query and a **horizontal
  pipeline** for ingest, both fitting the viewport across screen sizes.

---

## 8. The glass box (our approach to the visualizer)

The UI is a **guided, educational flow**, not a bare chat box:

1. **Landing** — a short "what is RAG?" primer and a choice: Ingest or Query.
2. **Concept tour** — a step-through of *that phase's* RAG concepts (embed →
   hybrid search → threshold/refusal → cited generation for query; load → clean
   → chunk → embed → store for ingest), skippable and remembered.
3. **Interactive** — the real pipeline against the live backend, animated stage
   by stage from the SSE stream, with **real data at each stage**: the actual
   embedding preview, retrieved chunks with scores and timestamps, the cited
   answer (or refusal), and live ingest progress.

Design decisions worth calling out:
- Each stage card shows the **real tool, model, and parameters** (pulled live
  from the backend) with a link to that vendor's docs — turning the animation
  into a teaching surface.
- A **minimum on-screen duration per stage** so fast stages (parsing, cleaning)
  don't flash by, while genuinely slow stages (embedding, upserting) show an
  honest indeterminate or progress loader. We never fake progress — faithfulness
  applies to the UI too.
- Query results lead with the **answer** (with clickable citations that
  highlight the matching source), evidence beside it — the opposite of the first
  draft.

---

## 9. Where it stands today

- ✅ Working RAG end-to-end (ingest + query), dense **and** hybrid retrieval.
- ✅ Designed, tested refusal path with a data-tuned cutoff.
- ✅ Evaluation harness with documented dense-vs-hybrid comparison.
- ✅ Live glass-box web app: landing → concept tour → interactive, for both
  ingest and query, responsive across screen sizes.
- ⏳ Phase 4 deliverables (polished eval report, Gamma deck, demo video).

---

## 10. Limitations and what we'd do next

- **Cross-encoder reranker** — designed as a drop-in (it only re-orders the
  retrieved chunks before generation), deferred to run on GPU (NVIDIA Brev).
  Worth adding only if a larger corpus shows retrieval needs the precision; on
  today's corpus dense is already saturated.
- **Slide-deck ingestion** — the metadata schema already supports slides
  (`content_type`, `slide_number`); the loader plumbing is pending real decks.
  Slides would add clean, correctly-spelled jargon and richer citations.
- **Latency** — bring end-to-end under the 6s target via query-embedding
  caching, parallel calls, and/or a faster generation model.
- **Scale the corpus and re-run the experiments** — hybrid's value, and the
  reranker's, should re-emerge as the corpus grows and gets noisier.
- **Deeper eval** — automated faithfulness scoring (e.g. RAGAS) and a larger,
  category-balanced question set.

---

## Appendix A — As-built configuration

| Setting | Value | Why |
|---|---|---|
| Embedding model | `Qwen/Qwen3-Embedding-8B` (4096-dim) | Only embedder offered on the account |
| Generation model | `meta-llama/Llama-3.3-70B-Instruct` | 3.1-70B not available; 3.3 is the swap |
| Vector store | Pinecone serverless, `dotproduct` | Required for dense + sparse hybrid |
| Sparse encoder | BM25 (`pinecone-text`) | CPU-friendly; recovers exact jargon |
| Chunk size / overlap | ~512 tok / ~80 tok | Transcript-aware, citation-anchored |
| `TOP_K` | 8 | Retrieval breadth |
| `HYBRID_ALPHA` | 0.7 | Ties dense, adds lexical recall |
| `SIMILARITY_CUTOFF` | 0.40 | Tuned on the eval set (see §6) |

## Appendix B — How to run

```bash
# one-time
uv venv --python 3.12 .venv && uv pip install -r backend/requirements.txt
# fill backend/.env with NEBIUS_API_KEY and PINECONE_API_KEY

# CLI
cd backend
../.venv/bin/python -m rag.cli ingest                       # ingest the corpus (idempotent)
../.venv/bin/python -m rag.cli ask "what is a context window?"
../.venv/bin/python ../eval/run_eval.py --compare           # dense vs hybrid table

# web app (glass box)
../.venv/bin/python -m uvicorn app:app --port 8000          # backend
cd ../frontend && npm install && npm run dev                # frontend → http://localhost:5173
```
