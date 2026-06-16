"""build_context node — tree-sitter diff-scoped context (Phase 3).

For each changed file: fetch its content at the PR head, then extract the
enclosing function/class for the changed lines, the imports, and the matching
test path. Returns {path: context_blob}.
"""
from app.progress import emit
from app.state import ReviewState
from app.tools import github, treesitter_ctx


def build_context(state: ReviewState) -> dict:
    emit({"stage": "context", "status": "running"})
    pr_meta = state.get("pr_meta", {})
    hunks = state.get("hunks", {})
    owner, repo = pr_meta.get("owner"), pr_meta.get("repo")
    head_sha = pr_meta.get("head_sha")

    context: dict[str, dict] = {}
    for path in hunks:
        source = (
            github.fetch_file_at(owner, repo, path, head_sha)
            if owner and repo and head_sha else None
        )
        changed = treesitter_ctx.changed_lines_for(path, hunks)
        blob = treesitter_ctx.build_file_context(path, source, changed)
        context[path] = blob
        names = [e["name"] for e in blob["enclosing"]]
        print(f"[build_context] {path}: enclosing={names} "
              f"imports={len(blob['imports'])} test={blob['matching_test']}")

    emit({"stage": "context", "status": "done", "files": len(context)})
    return {"context": context}
