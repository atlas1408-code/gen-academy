# Week 3 Project — Code Review Agent (Project 3E)

**Mastering Agentic AI Bootcamp · The Gen Academy**

- **Build track:** Track 2 — Code-heavy (LangChain + LangGraph), Python
- **Use case:** 3E — Code Review Agent (multi-agent)
- **Models:** Nebius Token Factory (`ChatNebius`) — every model call goes through Nebius
- **Code (agent):** https://github.com/atlas1408-code/gen-academy → `Week-3/code-review-agent`
- **Code (eval target repo, with 3 seeded PRs):** https://github.com/atlas1408-code/eval-target-repo

---

## 1. The Primer — one-liner

> My agent helps a **software engineer** review a **GitHub pull request** in a **browser (and via an API)**, replacing the manual, inconsistent ~30–60 minute first-pass review across correctness, security, and test coverage. It fetches the PR diff and code context and runs **three specialist reviewers in parallel** (quality, security, test-gap) on its own using a small set of tools, **hands off to the human to approve / reject / refine before any comment is posted**, and I’ll know it works when an engineer gets a ranked, postable review in **~1 minute** that catches the planted issues **8 out of 10** (we hit **7/7** on our seeded set).

**The three rules, applied:**
- **Task completion, not single-shot accuracy** — success = a usable, ranked review the engineer approves and posts, measured end-to-end against an eval set.
- **State is the hard part** — durable state in Postgres via a LangGraph checkpointer; a killed run resumes exactly where it paused.
- **Write actions deserve a human** — all reads (diff, file content, context) are autonomous; the only write (posting a comment) is gated behind explicit human approval.

---

## 2. The Agent Framework (filled)

| Field | Detail |
|---|---|
| **Agent goal** | Review a GitHub PR and post a ranked, human-approved set of inline review comments covering code quality, security, and test gaps. |
| **Where people use it** | A single-page web app (paste a PR URL) and a REST/SSE API; comments land on GitHub. |
| **Steps, in order** | 1) Fetch PR metadata + diff, parse into hunks. 2) Build diff-scoped code context with tree-sitter. 3) Run 3 specialist agents in parallel. 4) Consolidate: validate line-in-hunk, dedupe, severity-rank. 5) Pause for human approval. 6) On approve, post comments. |
| **What it can do (tools)** | `fetch PR diff` (read), `fetch file content` (read), `tree-sitter context` (read), `call specialist LLMs` (read/compute), `post inline review comment` (**write**), `post general PR comment` (**write**). |
| **What it remembers** | Per-run state (diff, context, findings, decisions, posted-comment ledger) persisted in Postgres, keyed by a `thread_id`; survives process restarts. Idempotency ledger remembers what was posted per commit. |
| **What it must never do** | Never post a comment without human approval; never post duplicates on re-approval; never crash the whole run because one agent or tool failed; never commit secrets. |
| **Human-in-the-loop** | The graph `interrupt()`s before any write. The human can **Approve** (post), **Reject** (drop a finding or the whole run), or **Refine** (regenerate a suggestion, which loops back through consolidation). |
| **When something breaks** | GitHub 5xx / rate-limit → retry with backoff (respects `Retry-After`); 404/bad URL → clean run-level error. A model returning bad JSON → repair-retry, then mark that agent **degraded** and continue with the others. Inline post rejected (422) → fall back to a general comment. |
| **How I know it worked** | Eval harness over 3 seeded PRs vs. expected findings → **7/7 caught (100%)**; 19 passing tests including failure-injection; ~$0.005 estimated cost/run. |

---

## 3. Architecture

**Pattern:** multi-agent (parallel specialists) + orchestrator/consolidator + human gate, expressed as a LangGraph state machine with a Postgres checkpointer.

```
                  ┌─ quality  ─┐
START → fetch_pr → build_context →┤  security  ├→ consolidate → human_gate ─approve→ post_comments → END
                  └─ test_gap ─┘                      │   ▲                 ─reject──────────────────→ END
                                                      └───┘ refine (regenerate suggestion, loop back)
```

**Specialist agents (each its own Nebius model, `temperature=0`):**

| Agent | Focus | Model (Nebius Token Factory) |
|---|---|---|
| quality | readability, duplication, dead code, error handling, mutable defaults | `moonshotai/Kimi-K2.6` |
| security | injection, hardcoded secrets, unsafe deserialization, SSRF, data exposure | `deepseek-ai/DeepSeek-V3.2` |
| test_gap | new/changed public code shipped without tests | `meta-llama/Llama-3.3-70B-Instruct` |
| consolidate / refine | comment regeneration on refine | `Qwen/Qwen3-235B-A22B-Instruct-2507` |

**Each finding is structured:** `severity · title · problem (reframed feedback) · suggestion (fix) · location (path:line + enclosing symbol)`.

**Tech stack:** Python 3.12 · LangGraph + LangChain · `langchain-nebius` · Postgres (`PostgresSaver` checkpointer + `runs`/`findings`/`approvals`/`token_usage`/`posted_comments` tables) · FastAPI + a single static HTML page (live SSE UI) · `tree-sitter` + `tree-sitter-python` · pytest. No vector DB, no Redis (out of scope for v1).

**Live UI:** the browser streams per-agent progress over Server-Sent Events — three columns go *queued → running → done/degraded* independently (e.g., security finishes at ~8s, the verbose quality model at ~42s), each showing what it’s reviewing, its model, and its result; then the ranked finding cards appear with Approve / Reject / Refine.

---

## 4. Datasets used

There is no training data; the “data” is **source code under review.**

1. **`eval-target-repo`** — a purpose-built, tiny Python “notes service” (clean `main` baseline + tests) with **three seeded pull requests**, each planting one class of bug mapped to one specialist:
   - **PR #1 (security):** f-string SQL injection + a hardcoded API token in `app/search.py`.
   - **PR #2 (quality):** mutable default argument, duplicated logic, dead code after `return`, bare `except` in `app/digest.py`.
   - **PR #3 (test-gap):** a new `app/stats.py` shipped with no matching test.
   - Ground truth lives in `SEEDED_BUGS.md`; expected findings encoded in `evals/prs.yaml`.
   - **Why a dedicated repo:** controlled ground truth makes the eval hit-rate meaningful, and GitHub PRs exist per-repo, so the agent needs real PR URLs to fetch and comment on.
2. **Any real public PR URL** — the agent also runs on arbitrary public GitHub PRs (reads are unauthenticated; posting needs a token).

---

## 5. Human-in-the-loop (the boundary)

- The graph **interrupts** at `human_gate` after consolidation and before any write. State is checkpointed, so the run can sit paused indefinitely (or across a restart).
- The UI surfaces every finding as a card. The human can:
  - **Reject** individual findings (per-card toggle) → those are not posted.
  - **Refine** a finding → the consolidate model regenerates the *suggestion* per the instruction, and the run loops back through consolidate → gate so the human re-reviews before approving.
  - **Approve & post** → comments are posted; **Reject all** → nothing is posted.
- **Idempotency:** posting is keyed on `(head_sha, path, line, side)`. Re-approving the same run (or a fresh run over the same commit) posts **zero** duplicates.

---

## 6. Error handling & resilience (the graded part)

| Failure | Behavior | Verified by |
|---|---|---|
| One agent returns garbage / errors | JSON-repair retries (≤2), then that agent is marked **degraded**; the others still produce a review; run completes | `tests/test_partial_failure.py` + `scripts/phase4_degrade_check.py` |
| GitHub 5xx / rate-limit | Retry with backoff, respect `Retry-After` then `X-RateLimit-Reset`; permanent 404/bad-URL → clean `GitHubError` | `tests/test_github_retry.py` |
| Malformed model JSON | `extract_json` handles fences/prose; repaired or degraded, never crashes | `tests/test_json_repair.py` |
| Inline comment rejected (line not in diff, 422) | Falls back to a general PR comment | `app/nodes/post_comments.py` |
| Process killed mid-run | Resumes from the Postgres checkpoint and completes (different process) | `scripts/durability_demo.py` |
| Re-approval | Idempotency ledger → no duplicate comments | `scripts/phase6_check.py` |

**Test suite:** 19 tests passing. **Eval:** `python -m evals.run_eval` → **7/7 (100%)** of seeded issues caught (target was 8/10). **Cost:** `python -m evals.cost_summary` → per-agent/per-run tokens + estimate (~$0.005/run; the verbose quality model dominates output tokens).

---

## 7. Prompts used during vibe coding

This project was built with Claude Code (Track 2 “vibe-coding”). The driving prompts, in order:

1. **Master build spec (the big one):** a phase-by-phase implementation plan handed in as the build spec — “build an agentic system that reviews a GitHub PR… three specialist agents in parallel… reads autonomous, the one write gated behind approval… durable state via a LangGraph checkpointer… no all-or-nothing failure… at least one model call through Nebius… Phase 1 skeleton → Phase 8 evals; do not start a phase until the previous phase’s acceptance checks pass.”
2. **Scoping the eval target:** “Does it make sense to write our own mini-repo or use an existing repo? … scaffold the eval-target-repo with three seeded PR branches.”
3. **Incremental phase prompts:** “proceed with Phase 1 … go ahead with Phase 3 … proceed [Phase 4 with the Nebius key] … go ahead with Phase 6 [GitHub PAT added] …”
4. **Refinement — structured output:** “Can we get the LLM to provide the output in a structured way as well? Severity, concise reframed feedback, location where the change needs to be done, and a suggested solution.”
5. **Refinement — live UI:** “Similar to how we see the running of the 3 agents in [a parallel-research screenshot], can we do that here?” and “should it also display what it’s looking at right now?”
6. **Internal agent/system prompts (in the code):** each specialist gets a strict role prompt (e.g., security: *“focus strictly on SECURITY vulnerabilities: injection, hardcoded secrets, unsafe deserialization, SSRF, path traversal, data exposure”*) plus a strict JSON schema instruction (`{findings:[{path,line,side,symbol,severity,title,problem,suggestion}]}`) and a repair instruction used on parse failure.

---

## 8. Iterations & things that broke (and how they were fixed)

Real debugging, not the happy path:

1. **Model catalog mismatch.** The plan named Kimi / DeepSeek-R1 / Qwen3 IDs that weren’t in our Token Factory account. Verified against the live `/v1/models` endpoint and mapped each agent to the closest available model (DeepSeek-R1 → DeepSeek-V3.2, etc.), all env-overridable.
2. **tree-sitter binding.** `tree-sitter-language-pack` 1.8.1 shipped a non-standard Rust-style API (`kind`, `start_position`, `root_node()` as a method) that fought the docs. Switched to the standard `tree-sitter` + `tree-sitter-python` bindings.
3. **Foreign-key ordering bug.** `token_usage` references `runs`, but agents (which record tokens) ran *before* the run row was created in `consolidate`. Fixed by registering the run in the first node (`fetch_pr`).
4. **Reducer vs. overwrite.** `findings` uses an additive (`operator.add`) reducer, so the consolidate node couldn’t overwrite it (it would re-append). Added a separate last-write-wins `consolidated` field for the deduped list.
5. **LangGraph config injection.** Renaming a node’s `config` parameter broke LangGraph’s *by-name* injection (`missing argument`). Kept the param named `config` and imported `MODELS` directly to avoid a name clash.
6. **SSE looked buffered.** Streaming appeared to arrive all-at-once under FastAPI’s `TestClient` — turned out `TestClient` buffers; against a real `uvicorn` server the events stream live and staggered. Used LangGraph’s custom stream writer (`get_stream_writer`) for per-agent progress.
7. **Dedupe attribution.** When two agents flag the same line, the merge keeps the top-severity title but unions the problem text — so an eval “caught by” label can name whichever agent matched first. Documented as a display nuance, not a miss.
8. **Structured output approach.** Chose prompt-schema + JSON-repair over provider-enforced structured output, because it works uniformly across all four open-weight models and we already had a robust repair/degrade layer.
9. **Secret hygiene.** Real keys live only in a gitignored `.env`; verified no secrets in tracked content before committing; kept `eval-target-repo` as its own GitHub repo (gitignored from the parent).

---

## 9. Learnings & observations

- **The agent loop is the easy 20%; control flow, state, and failure handling are the 80%.** The skeleton ran on day one; durability, partial-failure, idempotency, and the human gate were where the real work (and the value) was.
- **“Degrade, never crash” is a design stance, not a try/except.** Making every agent node return either findings *or* its name in `degraded_agents` (and never raise) is what lets one model hiccup without sinking the review.
- **Idempotency must be keyed on the artifact, not the run.** Keying on `head_sha + path + line + side` (not `run_id`) means even a brand-new run over the same commit won’t double-post.
- **Verify model availability against the provider, never assume IDs.** The single most repeated friction was model/tooling version drift.
- **Streaming makes a multi-agent system legible.** The parallel-column live view turns an opaque 1-minute wait into a visible, trustworthy process — and exposed the buffering bug we’d otherwise have shipped.
- **Human-in-the-loop is cheap with LangGraph `interrupt()` + a checkpointer**, and it’s exactly the right place to put the one irreversible action.

---

## 10. How to run (60 seconds)

```bash
cd code-review-agent
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env          # add NEBIUS_API_KEY, GITHUB_TOKEN
docker compose up -d          # Postgres on :5433
PYTHONPATH=. .venv/bin/uvicorn app.api.server:app --reload
# open http://127.0.0.1:8000 → paste a PR URL → Review → Approve & post
```

Tests / eval / cost:
```bash
PYTHONPATH=. .venv/bin/python -m pytest -q
PYTHONPATH=. .venv/bin/python -m evals.run_eval
PYTHONPATH=. .venv/bin/python -m evals.cost_summary
```

---

## 11. Submission checklist

- [x] **Project documentation** — this doc (overview, framework, datasets, prompts, iterations, learnings).
- [x] **Code base on GitHub** — `gen-academy/Week-3/code-review-agent` + standalone `eval-target-repo`.
- [ ] **Video demo (≤5 min)** — walk through the live UI on a seeded PR, show approve → posted, show a degraded-agent run, mention Nebius + LangGraph + how AI coding tools were used.
