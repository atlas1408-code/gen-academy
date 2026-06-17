> Paste tip: this version is made for Google Docs. It has no backticks or code
> fences (those render literally in Docs). Command/code blocks are indented plain
> text — fully copyable; for best readability select each block and set the font
> to a monospace one (e.g. Consolas / Courier New).

# Week 3 Project — Code Review Agent (Project 3E)

**Mastering Agentic AI Bootcamp · The Gen Academy**

- **Build track:** Track 2 — Code-heavy (LangChain + LangGraph), Python
- **Use case:** 3E — Code Review Agent (multi-agent)
- **Models:** Nebius Token Factory (ChatNebius) — every model call goes through Nebius
- **Code (agent):** https://github.com/atlas1408-code/gen-academy → Week-3/code-review-agent
- **Code (eval target repo, with 4 PRs):** https://github.com/atlas1408-code/eval-target-repo

---

## 1. The Primer — one-liner

> My agent helps a **software engineer** review a **GitHub pull request** in a **browser (and via an API)**, replacing the manual, inconsistent ~30–60 minute first-pass review across correctness, security, and test coverage. It fetches the PR diff and code context and runs **three specialist reviewers in parallel** (quality, security, test-gap) on its own, grounds them in real linter/SAST output, filters likely false positives, and **hands off to the human to approve / reject / refine before any comment is posted**. I know it works because an independent eval measures it: **100% recall at 85% precision** (~1 false positive per PR).

**The three rules, applied:**
- **Task completion, not single-shot accuracy** — success = a usable, ranked review the engineer approves and posts, measured end-to-end with **precision and recall**, not one good answer.
- **State is the hard part** — durable state in Postgres via a LangGraph checkpointer; a killed run resumes exactly where it paused.
- **Write actions deserve a human** — all reads (diff, file content, context, lint) are autonomous; the only write (posting a comment) is gated behind explicit human approval.

---

## 2. The Agent Framework (filled)

| Field | Detail |
|---|---|
| **Agent goal** | Review a GitHub PR and post a ranked, human-approved set of inline review comments covering code quality, security, and test gaps. |
| **Where people use it** | A single-page web app (paste a PR URL) and a REST/SSE API; comments land on GitHub. |
| **Steps, in order** | 1) Fetch PR metadata + diff, parse into hunks. 2) Build context: tree-sitter scope + ruff lint/SAST signals + test-existence check. 3) Run 3 specialist agents in parallel (grounded in those signals). 4) Consolidate: validate line-in-hunk, dedupe, severity-rank. 5) Verify: an independent model filters likely false positives. 6) Pause for human approval. 7) On approve, post comments. |
| **What it can do (tools)** | fetch PR diff (read), fetch file content (read), tree-sitter context (read), ruff lint/SAST (read), call specialist LLMs (read/compute), post inline review comment (**write**), post general PR comment (**write**). |
| **What it remembers** | Per-run state (diff, context, findings, decisions, posted-comment ledger) persisted in Postgres, keyed by a thread_id; survives process restarts. The idempotency ledger remembers what was posted per commit. |
| **What it must never do** | Never post a comment without human approval; never post duplicates on re-approval; never crash the whole run because one agent or tool failed; never commit secrets. |
| **Human-in-the-loop** | The graph interrupts before any write. The human can **Approve** (post), **Reject** (drop a finding or the whole run), or **Refine** (regenerate a suggestion, which loops back through consolidation + verification). |
| **When something breaks** | GitHub 5xx / rate-limit → retry with backoff (respects Retry-After); 404/bad URL → clean run-level error. A model returning bad JSON → repair-retry, then mark that agent **degraded** and continue. The verifier or ruff failing → **fail open** (keep findings; never lose them). Inline post rejected (422) → fall back to a general comment. |
| **How I know it worked** | An independent-judge eval over 4 PRs: **recall 100%, precision 85%, F1 92%, ~1 false positive/PR**, all above threshold; 19 passing tests incl. failure-injection. |

---

## 3. Architecture

**Pattern:** multi-agent (parallel specialists) + grounding + consolidation + an independent verification filter + human gate, expressed as a LangGraph state machine with a Postgres checkpointer.

Flow (set this block to a monospace font in Docs):

    START
      → fetch_pr
      → build_context           (tree-sitter + ruff signals + test-existence check)
      → [ quality | security | test_gap ]   (run in parallel, grounded in the signals)
      → consolidate
      → verify                  (independent model filters likely false positives)
      → human_gate
            ├─ approve → post_comments → END
            ├─ reject  → END
            └─ refine  → back to consolidate (regenerate suggestion), then verify + gate

**Models (each its own Nebius model, temperature = 0):**

| Role | Focus | Model (Nebius Token Factory) |
|---|---|---|
| quality | readability, duplication, dead code, error handling, mutable defaults | moonshotai/Kimi-K2.6 |
| security | injection, hardcoded secrets, unsafe deserialization, SSRF, data exposure | deepseek-ai/DeepSeek-V3.2 |
| test_gap | new/changed public code shipped without tests | meta-llama/Llama-3.3-70B-Instruct |
| consolidate / refine | comment regeneration on refine | Qwen/Qwen3-235B-A22B-Instruct-2507 |
| verify (FP filter) | re-checks each finding to cut false positives | Qwen/Qwen3-235B-A22B-Instruct-2507 (distinct from producers) |
| judge (eval only) | scores finding validity for precision | openai/gpt-oss-120b (different family — no self-grading) |

**Each finding is structured:** severity · title · problem (reframed feedback) · suggestion (fix) · location (path:line + symbol) · confidence.

**Deterministic grounding:** ruff runs on the changed lines (lint + bugbear B + bandit-equivalent security S rules), and a deterministic check confirms whether a matching test file exists and references the changed symbols. These real signals are fed to the agents so findings are grounded in tool output, not guesses.

**Tech stack:** Python 3.12 · LangGraph + LangChain · langchain-nebius · Postgres (PostgresSaver checkpointer + runs/findings/approvals/token_usage/posted_comments tables) · FastAPI + a single static HTML page (live SSE UI) · tree-sitter + tree-sitter-python · ruff · pytest. No vector DB, no Redis.

**Live UI:** the browser streams per-agent progress over Server-Sent Events — three columns go queued → running → done/degraded independently, each showing what it's reviewing, its model, and its result; then the ranked finding cards appear (with confidence chips), plus a collapsible "filtered as likely false positives" section.

---

## 4. Datasets used

There is no training data; the “data” is **source code under review.**

1. **eval-target-repo** — a purpose-built, tiny Python “notes service” (clean main baseline + tests) with **four pull requests**:
   - **PR #1 (security):** f-string SQL injection + a hardcoded API token in app/search.py.
   - **PR #2 (quality):** mutable default argument, duplicated logic, dead code after return, bare except in app/digest.py.
   - **PR #3 (test-gap):** a new app/stats.py shipped with no matching test.
   - **PR #4 (clean control):** a benign, fully-tested helper — a noise / false-positive probe (any high-severity finding on it is almost certainly an FP).
   - Ground truth lives in SEEDED_BUGS.md; expected findings encoded in evals/prs.yaml.
2. **Any real public PR URL** — the agent also runs on arbitrary public GitHub PRs.

---

## 5. Human-in-the-loop (the boundary)

- The graph **interrupts** at human_gate after consolidation + verification, before any write. State is checkpointed, so the run can sit paused indefinitely (or across a restart).
- The UI surfaces every finding as a card (with a confidence chip), plus the suppressed findings collapsed. The human can:
  - **Reject** individual findings → not posted.
  - **Refine** a finding → the model regenerates the suggestion, and the run loops back through consolidate → verify → gate so the human re-reviews.
  - **Approve & post** → comments are posted; **Reject all** → nothing is posted.
- **Idempotency:** posting is keyed on (head_sha, path, line, side). Re-approving the same run (or a fresh run over the same commit) posts **zero** duplicates.

---

## 6. Error handling & resilience (the graded part)

| Failure | Behavior | Verified by |
|---|---|---|
| One agent returns garbage / errors | JSON-repair retries (≤2), then that agent is marked **degraded**; the others still review; run completes | tests/test_partial_failure.py |
| GitHub 5xx / rate-limit | Retry with backoff, respect Retry-After / X-RateLimit-Reset; 404/bad-URL → clean GitHubError | tests/test_github_retry.py |
| Malformed model JSON | extract_json handles fences/prose; repaired or degraded, never crashes | tests/test_json_repair.py |
| Verifier or ruff unavailable/errors | **Fail open** — keep all findings (never lose a finding to a tool hiccup) | app/nodes/verify.py, app/tools/static_analysis.py |
| Inline comment rejected (422) | Falls back to a general PR comment | app/nodes/post_comments.py |
| Process killed mid-run | Resumes from the Postgres checkpoint and completes | scripts/durability_demo.py |
| Re-approval | Idempotency ledger → no duplicate comments | scripts/phase6_check.py |

**Test suite:** 19 tests passing.

---

## 7. Beyond demo — measured, eval-driven improvements

After the first working build, the project was hardened using a real evaluation loop instead of vibes. Each improvement was **measured** by an independent judge model:

| Stage | recall | precision | FP/PR | F1 |
|---|---|---|---|---|
| Baseline (recall-only eval) | 100% | unmeasured | — | — |
| #4 Precision/recall eval harness | 100% | 67% (FAIL) | 2.5 | 80% |
| #2 Verification pass (FP filter) | 100% | 84% (PASS) | 1.0 | 91% |
| #3 Deterministic grounding (ruff) | 100% | 85% (PASS) | 1.2 | 92% |

- **#4 — Precision/recall eval (evals/run_eval.py, judge.py, label_cli.py).** The original eval measured only recall ("7/7, looks great"). The new harness has an independent judge (a different model family) label every produced finding valid/invalid, so we measure precision (noise), F1, false-positives-per-PR, per-agent precision, and an FP taxonomy — checked against thresholds, logged to a results ledger for regression tracking, and validated by a human-vs-judge agreement CLI (Cohen's kappa). First honest result: 67% precision — i.e. ~1 in 3 posted comments was noise, invisible to the old eval.
- **#2 — Verification pass (app/nodes/verify.py).** An independent verifier model re-checks each finding against the diff, assigns a confidence, and suppresses likely false positives (kept visible in the UI, never posted). Fails open. Lifted precision 67% → 84%, halved noise (2.5 → 1.0 FP/PR), and eliminated all hallucinated FPs — with recall unchanged.
- **#3 — Deterministic grounding (app/tools/static_analysis.py).** ruff (lint + bugbear + bandit-equivalent security rules) runs on the changed lines and a deterministic test-existence check grounds test_gap; both feed the agent prompts. ruff independently flags the seeded bugs (S105 hardcoded token, S608 SQL injection, B006 mutable default, E722 bare except). Findings are now backed by real tool evidence; the agents surfaced more valid findings (28 vs 21) at held precision (security and test_gap reached 100%).

**Honest caveat:** the eval set is small (3 buggy PRs + 1 clean control), so single-finding deltas are within run-to-run noise — #3's grounding benefit in particular shows up most on larger/real PRs. Expanding evals/prs.yaml with real PRs is the next eval step.

---

## 8. Prompts used during vibe coding

Built with Claude Code (Track 2). The driving prompts, in order:

1. **Master build spec:** a phase-by-phase plan — "build an agentic system that reviews a GitHub PR… three specialist agents in parallel… reads autonomous, the one write gated… durable state via a LangGraph checkpointer… no all-or-nothing failure… at least one model call through Nebius… Phase 1 skeleton → Phase 8 evals; don't start a phase until the previous one's acceptance checks pass."
2. **Eval target scoping:** "Write our own mini-repo or use an existing one? … scaffold the eval-target-repo with three seeded PR branches."
3. **Incremental phase prompts:** "proceed with Phase 1 … go ahead with Phase 3 … proceed [Phase 4 with the Nebius key] … go ahead with Phase 6 [GitHub PAT] …"
4. **Structured output:** "Can we get the LLM to provide the output in a structured way — severity, concise reframed feedback, location, suggested solution?"
5. **Live UI:** "Similar to how we see the 3 agents running [in a parallel-research screenshot], can we do that here?" + "should it also display what it's looking at right now?"
6. **Beyond demo:** "explore how AI code reviewers work … top 5 picks to make it beyond demo" → then implement #4 (eval), #2 (verification), #3 (grounding).
7. **In-code prompts:** strict role prompts per specialist + a strict JSON schema; a judge rubric; a verifier rubric; a repair instruction on parse failure.

The JSON schema each agent must emit (monospace block):

    {
      "findings": [
        {
          "path": "app/search.py", "line": 15, "side": "RIGHT",
          "symbol": "search_notes",
          "severity": "critical | high | medium | low",
          "title": "concise headline (<= ~8 words)",
          "problem": "1-2 sentences: what is wrong and why",
          "suggestion": "a concrete fix; a short code snippet is welcome"
        }
      ]
    }

---

## 9. Iterations & things that broke (and how they were fixed)

1. **Model catalog mismatch.** The plan named model IDs not in our Token Factory account; verified against /v1/models and mapped each agent to the closest live model.
2. **tree-sitter binding.** tree-sitter-language-pack 1.8.1 shipped a non-standard API; switched to tree-sitter + tree-sitter-python.
3. **Foreign-key ordering bug.** token_usage references runs, but agents ran before the run row was created; fixed by registering the run in fetch_pr.
4. **Reducer vs. overwrite.** findings uses an additive reducer, so consolidate couldn't overwrite it; added a separate last-write-wins consolidated field.
5. **LangGraph config injection.** Renaming a node's config parameter broke by-name injection; kept the name and imported MODELS directly.
6. **SSE looked buffered.** It was just TestClient buffering; against real uvicorn the events stream live. Used LangGraph's custom stream writer.
7. **Dedupe attribution.** Merged-line findings can show "caught by" whichever agent matched first — a display nuance, not a miss.
8. **Hermetic tests after adding the verifier.** The new verify node would make a real model call in offline tests; stubbed get_verifier (fail-open) so the suite stays network-free.
9. **Secret hygiene.** Real keys live only in a gitignored .env; verified no secrets in tracked content; eval-target-repo is its own GitHub repo (gitignored from the parent).

---

## 10. Learnings & observations

- **The agent loop is the easy 20%; control flow, state, and failure handling are the 80%.** Durability, partial-failure, idempotency, and the human gate were the real work.
- **Recall is a vanity metric without precision.** "7/7 caught" hid that a third of posted comments were noise. You cannot improve what you don't measure — the precision/recall eval changed everything downstream.
- **A separate verifier + deterministic grounding beat prompt-tuning for trust.** An independent FP filter (#2) plus real linter/SAST evidence (#3) moved precision 67% → 85% with recall held — and the verifier/judge being different models keeps the measurement honest.
- **“Degrade / fail open, never crash” is a design stance.** Every agent returns findings or marks itself degraded; the verifier and ruff fail open so a tool hiccup never loses a finding.
- **Idempotency must be keyed on the artifact** (head_sha + path + line + side), not the run.
- **Streaming makes a multi-agent system legible** — and exposed the buffering bug we'd otherwise have shipped.

---

## 11. How to run (60 seconds)

Setup (monospace block):

    cd code-review-agent
    python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt
    cp .env.example .env          # add NEBIUS_API_KEY, GITHUB_TOKEN
    docker compose up -d          # Postgres on :5433
    PYTHONPATH=. .venv/bin/uvicorn app.api.server:app --reload
    # open http://127.0.0.1:8000 -> paste a PR URL -> Review -> Approve & post

Tests / eval / cost (monospace block):

    PYTHONPATH=. .venv/bin/python -m pytest -q
    PYTHONPATH=. .venv/bin/python -m evals.run_eval        # precision + recall
    PYTHONPATH=. .venv/bin/python -m evals.label_cli 30    # validate the judge (Cohen's kappa)
    PYTHONPATH=. .venv/bin/python -m evals.cost_summary

---

## 12. Submission checklist

- [x] **Project documentation** — this doc (overview, framework, datasets, prompts, iterations, learnings, measured improvements).
- [x] **Code base on GitHub** — gen-academy/Week-3/code-review-agent + standalone eval-target-repo.
- [ ] **Video demo (≤5 min)** — walk through the live UI on a seeded PR, show approve → posted, a degraded-agent run, and the precision/recall eval; mention Nebius + LangGraph + how AI coding tools were used.
