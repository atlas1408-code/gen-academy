-- Application tables (separate from the LangGraph checkpointer tables, which
-- PostgresSaver.setup() manages itself). run_id == the graph thread_id.

CREATE TABLE IF NOT EXISTS runs (
    run_id      TEXT PRIMARY KEY,
    pr_url      TEXT,
    status      TEXT NOT NULL DEFAULT 'running',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS findings (
    id            BIGSERIAL PRIMARY KEY,
    run_id        TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    agent         TEXT NOT NULL,
    path          TEXT NOT NULL,
    line          INTEGER NOT NULL,
    side          TEXT NOT NULL,
    severity      TEXT NOT NULL,
    rationale     TEXT,
    draft_comment TEXT,
    in_hunk       BOOLEAN NOT NULL DEFAULT FALSE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_findings_run ON findings(run_id);

-- Structured-finding columns (added after the original schema).
ALTER TABLE findings ADD COLUMN IF NOT EXISTS symbol     TEXT;
ALTER TABLE findings ADD COLUMN IF NOT EXISTS title      TEXT;
ALTER TABLE findings ADD COLUMN IF NOT EXISTS problem    TEXT;
ALTER TABLE findings ADD COLUMN IF NOT EXISTS suggestion TEXT;

CREATE TABLE IF NOT EXISTS approvals (
    id          BIGSERIAL PRIMARY KEY,
    run_id      TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    action      TEXT NOT NULL,
    edits       JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Idempotency ledger for posted comments. The UNIQUE key (head_sha, path, line,
-- side) makes re-approving the same run a no-op for already-posted findings.
CREATE TABLE IF NOT EXISTS posted_comments (
    id                BIGSERIAL PRIMARY KEY,
    run_id            TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    head_sha          TEXT NOT NULL,
    path              TEXT NOT NULL,
    line              INTEGER NOT NULL,
    side              TEXT NOT NULL,
    comment_type      TEXT NOT NULL,          -- 'inline' | 'general'
    github_comment_id BIGINT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (head_sha, path, line, side)
);

CREATE TABLE IF NOT EXISTS token_usage (
    id                BIGSERIAL PRIMARY KEY,
    run_id            TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    agent             TEXT NOT NULL,
    prompt_tokens     INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens      INTEGER NOT NULL DEFAULT 0,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_token_usage_run ON token_usage(run_id);
