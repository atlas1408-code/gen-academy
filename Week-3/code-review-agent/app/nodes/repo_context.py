"""repo_context node (improvement #2) — cross-file references for changed symbols.

Looks up where the changed functions/classes are used elsewhere in the repo so
the specialist agents can assess blast radius (broken callers, wide impact) and
avoid false "unused/dead code" claims. Fail-open: empty refs on any failure.
"""
from app.progress import emit
from app.state import ReviewState
from app.tools import repo_index


def repo_context(state: ReviewState) -> dict:
    pr = state.get("pr_meta", {})
    owner, repo, head_sha = pr.get("owner"), pr.get("repo"), pr.get("head_sha")
    context = state.get("context", {})

    symbols = sorted({
        e["name"]
        for blob in context.values()
        for e in blob.get("enclosing", [])
        if e.get("name")
    })
    if not symbols or not (owner and repo and head_sha):
        return {"repo_refs": {}}

    emit({"stage": "repo_index", "status": "running", "symbols": len(symbols)})
    refs = repo_index.find_references(
        owner, repo, head_sha, symbols, exclude_paths=set(context.keys())
    )
    total = sum(len(v) for v in refs.values())
    print(f"[repo_context] {len(symbols)} changed symbol(s) -> "
          f"{total} cross-file reference(s) in {len(refs)} symbol(s)")
    emit({"stage": "repo_index", "status": "done", "refs": total})
    return {"repo_refs": refs}
