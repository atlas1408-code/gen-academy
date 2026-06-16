"""CRUD helpers for the app tables (runs, findings, approvals, token_usage).

These use short-lived psycopg connections; the LangGraph checkpointer owns its
own connection/pool separately.
"""
import json
from pathlib import Path
from typing import Any, Iterable

import psycopg

from app.config import DATABASE_URL
from app.state import Finding

_SCHEMA = Path(__file__).with_name("schema.sql")


def init_app_tables() -> None:
    """Create the application tables if they do not yet exist (idempotent)."""
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute(_SCHEMA.read_text())
        conn.commit()


def upsert_run(run_id: str, pr_url: str | None, status: str = "running") -> None:
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute(
            """
            INSERT INTO runs (run_id, pr_url, status)
            VALUES (%s, %s, %s)
            ON CONFLICT (run_id) DO UPDATE
                SET pr_url = EXCLUDED.pr_url,
                    status = EXCLUDED.status,
                    updated_at = now()
            """,
            (run_id, pr_url, status),
        )
        conn.commit()


def set_run_status(run_id: str, status: str) -> None:
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute(
            "UPDATE runs SET status = %s, updated_at = now() WHERE run_id = %s",
            (status, run_id),
        )
        conn.commit()


def replace_findings(run_id: str, findings: Iterable[Finding]) -> int:
    """Replace all findings for a run (so re-running is idempotent)."""
    rows = [
        (
            run_id,
            f["agent"],
            f["path"],
            f["line"],
            f["side"],
            f.get("symbol"),
            f["severity"],
            f.get("title"),
            f.get("problem"),
            f.get("suggestion"),
            f.get("draft_comment"),
            f.get("in_hunk", False),
        )
        for f in findings
    ]
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute("DELETE FROM findings WHERE run_id = %s", (run_id,))
        if rows:
            conn.cursor().executemany(
                """
                INSERT INTO findings
                    (run_id, agent, path, line, side, symbol, severity,
                     title, problem, suggestion, draft_comment, in_hunk)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                rows,
            )
        conn.commit()
    return len(rows)


def get_findings(run_id: str) -> list[dict[str, Any]]:
    with psycopg.connect(DATABASE_URL) as conn:
        cur = conn.execute(
            """
            SELECT agent, path, line, side, symbol, severity,
                   title, problem, suggestion, draft_comment, in_hunk
            FROM findings WHERE run_id = %s ORDER BY id
            """,
            (run_id,),
        )
        cols = [c.name for c in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def already_posted(head_sha: str, path: str, line: int, side: str) -> bool:
    with psycopg.connect(DATABASE_URL) as conn:
        cur = conn.execute(
            """
            SELECT 1 FROM posted_comments
            WHERE head_sha = %s AND path = %s AND line = %s AND side = %s
            """,
            (head_sha, path, line, side),
        )
        return cur.fetchone() is not None


def record_posted_comment(
    run_id: str, head_sha: str, path: str, line: int, side: str,
    comment_type: str, github_comment_id: int | None,
) -> None:
    """Record a posted comment; ON CONFLICT keeps the idempotency key unique."""
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute(
            """
            INSERT INTO posted_comments
                (run_id, head_sha, path, line, side, comment_type, github_comment_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (head_sha, path, line, side) DO NOTHING
            """,
            (run_id, head_sha, path, line, side, comment_type, github_comment_id),
        )
        conn.commit()


def record_approval(run_id: str, action: str, edits: dict | None = None) -> None:
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute(
            "INSERT INTO approvals (run_id, action, edits) VALUES (%s, %s, %s)",
            (run_id, action, json.dumps(edits) if edits is not None else None),
        )
        conn.commit()


def record_token_usage(
    run_id: str, agent: str, prompt_tokens: int, completion_tokens: int
) -> None:
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute(
            """
            INSERT INTO token_usage
                (run_id, agent, prompt_tokens, completion_tokens, total_tokens)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (run_id, agent, prompt_tokens, completion_tokens,
             prompt_tokens + completion_tokens),
        )
        conn.commit()
