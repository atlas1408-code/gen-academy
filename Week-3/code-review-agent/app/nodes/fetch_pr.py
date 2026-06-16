"""fetch_pr node — real GitHub read (Phase 3).

Fetches PR metadata + raw diff and parses the diff into per-file hunks. Also
registers the run row up front so downstream nodes (token_usage at agent time)
satisfy their foreign key. A failure here (bad URL, PR not found, GitHub down
after retries) is an unrecoverable run-level error and is allowed to raise.
"""
from langchain_core.runnables import RunnableConfig

from app.db import repo
from app.progress import emit
from app.state import ReviewState
from app.tools import github


def fetch_pr(state: ReviewState, config: RunnableConfig) -> dict:
    pr_url = state["pr_url"]
    run_id = config["configurable"]["thread_id"]
    print(f"[fetch_pr] fetching {pr_url}")
    emit({"stage": "fetch", "status": "running"})
    repo.upsert_run(run_id, pr_url, status="running")

    pr_meta, diff_text = github.fetch_pr(pr_url)
    hunks = github.parse_diff(diff_text)
    n_files = len(hunks)
    n_hunks = sum(len(v) for v in hunks.values())
    print(f"[fetch_pr] {pr_meta['title']!r} @ {pr_meta['head_sha'][:7]} — "
          f"{n_files} file(s), {n_hunks} hunk(s)")
    emit({"stage": "fetch", "status": "done",
          "title": pr_meta["title"], "files": n_files, "hunks": n_hunks})
    return {"diff": diff_text, "pr_meta": pr_meta, "hunks": hunks}
