"""post_comments node — the gated, safe write (Phase 6).

Reached only via the approve branch. For each consolidated finding (minus the
ones the human rejected): post an inline review comment if it falls inside a
diff hunk, otherwise a general PR comment. Posting is idempotent via the
(head_sha, path, line, side) ledger, so re-approving the same run never
double-posts.
"""
from langchain_core.runnables import RunnableConfig

from app.db import repo
from app.state import ReviewState
from app.tools import github
from app.tools.github import GitHubError


def _format_inline(f: dict) -> str:
    return f"{f['draft_comment']}\n\n_— {f['agent']}_"


def _format_general(f: dict) -> str:
    loc = f"`{f['path']}:{f['line']}`" + (f" in `{f['symbol']}`" if f.get("symbol") else "")
    return f"{f['draft_comment']}\n\n{loc} (outside the diff hunk) _— {f['agent']}_"


def post_comments(state: ReviewState, config: RunnableConfig) -> dict:
    run_id = config["configurable"]["thread_id"]
    findings = state.get("consolidated", state.get("findings", []))
    pr = state.get("pr_meta", {})
    owner, repo_name, number = pr.get("owner"), pr.get("repo"), pr.get("number")
    head_sha = pr.get("head_sha")

    rejected = set((state.get("decision") or {}).get("rejected", []))

    posted = skipped_dupe = rejected_n = failed = 0
    for idx, f in enumerate(findings):
        if idx in rejected:
            rejected_n += 1
            continue
        if repo.already_posted(head_sha, f["path"], f["line"], f["side"]):
            skipped_dupe += 1
            continue

        try:
            if f["in_hunk"]:
                resp = github.post_inline_comment(
                    owner, repo_name, number,
                    body=_format_inline(f), commit_id=head_sha,
                    path=f["path"], line=f["line"], side=f["side"],
                )
                ctype = "inline"
            else:
                resp = github.post_general_comment(
                    owner, repo_name, number, _format_general(f)
                )
                ctype = "general"
        except GitHubError as exc:
            # Inline rejected because the line isn't really in the diff -> fall back.
            if exc.status == 422 and f["in_hunk"]:
                resp = github.post_general_comment(
                    owner, repo_name, number, _format_general(f)
                )
                ctype = "general"
            else:
                print(f"[post_comments] FAILED {f['path']}:{f['line']} -> {exc}")
                failed += 1
                continue

        repo.record_posted_comment(
            run_id, head_sha, f["path"], f["line"], f["side"],
            ctype, resp.get("id"),
        )
        posted += 1
        print(f"[post_comments] {ctype:<7} {f['path']}:{f['line']} "
              f"(#{resp.get('id')})")

    print(f"[post_comments] posted={posted} dup_skipped={skipped_dupe} "
          f"rejected={rejected_n} failed={failed}")
    repo.set_run_status(run_id, "posted")
    return {"posted": True}
