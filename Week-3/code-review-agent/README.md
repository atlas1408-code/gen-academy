# Code Review Agent

An agentic system that reviews a GitHub pull request. It fetches the PR diff,
builds diff-scoped code context with tree-sitter, runs **three specialist agents
in parallel** (code quality, security, test gaps) on Nebius Token Factory,
consolidates and severity-ranks their findings, **pauses for human approval**,
and only then posts inline review comments to GitHub.

The browser shows the three agents working **live** (one column each), then the
ranked findings as structured cards you can approve, reject per-finding, or
refine before anything is posted.

## Design rules

1. **Reads are autonomous; the one write (posting a comment) is gated behind human approval.**
2. **State is durable** — a paused or crashed run resumes via a LangGraph Postgres checkpointer.
3. **No all-or-nothing failure** — if one agent fails it's marked *degraded* and the others still produce a review.
4. **Every model call goes through Nebius Token Factory** (`ChatNebius`, `temperature=0`).

## Stack

Python 3.11+ · LangGraph + LangChain · `langchain-nebius` · Postgres
(`PostgresSaver` checkpointer + app tables) · FastAPI + a single static HTML page
· tree-sitter (`tree-sitter` + `tree-sitter-python`) · `ruff` for deterministic
lint/SAST grounding. A separate verifier model cuts false positives, and an
independent judge model scores eval precision. No vector DB, no Redis.

**Current eval:** 100% recall · 85% precision · F1 92% · ~1 false positive/PR
(measured by an independent judge — see _Evals_ below).

## How it works

```
                 ┌─ quality ─┐
START → fetch_pr → build_context →┤  security  ├→ consolidate → verify → human_gate ─approve→ post_comments → END
                 └─ test_gap ─┘                          │  ▲                        ─reject──────────────────→ END
                                                         └──┘ refine (regenerate suggestion, loop back)
```

- **fetch_pr** — parse the PR URL, fetch metadata + raw diff (REST), parse the diff into per-file hunks; retries 5xx/rate-limits, raises a clean error on 404/bad URL.
- **build_context** — for each changed file, tree-sitter extracts the enclosing function/class and imports; **ruff** (lint + bugbear `B` + bandit-equivalent security `S` rules) runs on the changed lines for deterministic grounding; and a deterministic check confirms whether the matching test file exists and references the changed symbols. These signals are fed to the agents so findings are grounded in real tool output, not guesses.
- **quality / security / test_gap** — run in parallel; each calls its model through a JSON-repair helper and either appends findings or marks itself *degraded* (never crashes).
- **consolidate** — validates each finding's `in_hunk` against the hunks, dedupes by `(path, line, side)`, applies any refinements, severity-ranks, and persists.
- **verify** — an independent verifier model (distinct from the agents) re-checks each finding against the diff, assigns a confidence, and **suppresses likely false positives** (kept visible, never posted). Fails open. Lifted eval precision 67% → 84% with recall unchanged.
- **human_gate** — `interrupt()`s for approval; resumes with approve / reject / refine.
- **post_comments** — only on approve: inline comment if in a hunk, else a general PR comment; idempotent via a `(head_sha, path, line, side)` ledger.

Each finding is structured: `severity · title · problem · suggestion · location (path:line + symbol)`.

## Setup

```bash
cd code-review-agent
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env        # then fill in the values below
docker compose up -d        # Postgres on host port 5433
```

### Environment variables (`.env`)

| Var | Needed for | Notes |
|---|---|---|
| `DATABASE_URL` | always | defaults to the docker-compose Postgres (`localhost:5433`) |
| `NEBIUS_API_KEY` | the agents | Nebius Token Factory key |
| `NEBIUS_BASE_URL` | the agents | `https://api.tokenfactory.nebius.com/v1/` |
| `MODEL_QUALITY / MODEL_SECURITY / MODEL_TEST_GAP / MODEL_CONSOLIDATE` | the agents | verify against `/v1/models` for your account |
| `VERIFIER_MODEL` | false-positive filter | defaults to Qwen3-235B; distinct from the agents |
| `JUDGE_MODEL` | the eval only | defaults to `openai/gpt-oss-120b`; a different family than the reviewers/verifier |
| `GITHUB_TOKEN` | posting comments | PAT (classic `repo`, or fine-grained with PR read/write) for the repo you review. Reads work unauthenticated. |
| `LANGCHAIN_TRACING_V2` / `LANGCHAIN_API_KEY` / `LANGCHAIN_PROJECT` | optional | turns on LangSmith tracing |

## 60-second run-through

```bash
# 1. start Postgres + the server
docker compose up -d
PYTHONPATH=. .venv/bin/uvicorn app.api.server:app --reload

# 2. open the UI
open http://127.0.0.1:8000
```

In the browser: paste a PR URL → **Review**. Watch the three agent columns go
**running → done** live, then read the ranked finding cards. Reject any you don't
want, **Refine** a suggestion if needed, then **Approve & post** — comments are
posted to the PR (inline where the line is in the diff, general otherwise).
Re-approving the same run posts **zero** duplicates.

> Heads-up: **Approve posts real comments** to the live PR. Use a throwaway/test PR.

### API (driven by the UI, usable directly)

| Endpoint | Purpose |
|---|---|
| `GET /` | the single-page UI |
| `GET /review/stream?pr_url=…` | SSE: live per-agent progress, then final findings |
| `POST /review {pr_url}` | blocking variant: run to the interrupt, return findings |
| `GET /run/{run_id}` | current findings + status |
| `POST /run/{run_id}/decision {action, rejected, refine}` | resume: `approve` \| `reject` \| `refine` |

## Tests

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q
```
Covers hunk mapping, JSON repair/degrade, GitHub retry/backoff, and partial
failure (one agent down → run still completes). Hermetic — no network or DB.

## Evals & cost

```bash
PYTHONPATH=. .venv/bin/python -m evals.run_eval        # precision + recall -> evals/last_report.md
PYTHONPATH=. .venv/bin/python -m evals.label_cli 30    # human spot-check: judge vs you (Cohen's kappa)
PYTHONPATH=. .venv/bin/python -m evals.cost_summary    # per-agent / per-run tokens + est. $
```
`run_eval` runs the agent over `evals/prs.yaml` (read-only — never posts), then an
**independent judge** (`evals/judge.py`, a different model family than the
reviewers) labels every finding valid/invalid so we can report **precision** (noise),
not just **recall** (coverage), plus F1, false-positives-per-PR, per-agent precision,
and an FP taxonomy. Results are checked against thresholds in `prs.yaml`, written to
`evals/last_report.md`, and appended to `evals/results_ledger.jsonl` (regression
tracking over time). `prs.yaml` includes a **clean control PR** to probe noise.

`label_cli` validates that the judge agrees with a human before you trust the
precision number. Edit the `PRICES` map in `cost_summary.py` to match your Nebius plan.

## Layout

```
app/
  config.py            env + model ids
  state.py             ReviewState + Finding + Hunk
  models.py            ChatNebius per agent (temperature=0)
  graph.py             build_graph() + Postgres checkpointer
  format.py            compose_comment() — structured fields -> markdown
  progress.py          emit() -> LangGraph custom stream (live UI events)
  nodes/               fetch_pr, build_context, agents, consolidate, verify, human_gate, post_comments
  tools/               github (diff/hunks/posting), treesitter_ctx, static_analysis (ruff), json_repair
  db/                  schema.sql, repo.py (runs/findings/approvals/token_usage/posted_comments)
  api/                 server.py (FastAPI) + static/index.html
evals/   prs.yaml, run_eval.py (precision/recall), judge.py, label_cli.py, cost_summary.py
scripts/ durability_demo.py + per-phase acceptance checks
tests/   pytest suite
```

## Durability demo

```bash
PYTHONPATH=. .venv/bin/python -m scripts.durability_demo start  pr-1-run
# process exits at the interrupt; resume from a fresh process:
PYTHONPATH=. .venv/bin/python -m scripts.durability_demo resume pr-1-run
```
The second process restores the paused run from Postgres and finishes it.
