"""build_context node — tree-sitter context + deterministic grounding (Phase 3 + #3).

For each changed file: fetch its content at the PR head, extract the enclosing
function/class and imports (tree-sitter), run ruff for deterministic lint/SAST
signals on the changed lines, and deterministically check whether a matching test
file exists and references the changed symbols. All of this grounds the agents.
"""
from app.progress import emit
from app.state import ReviewState
from app.tools import github, static_analysis, treesitter_ctx


def build_context(state: ReviewState) -> dict:
    emit({"stage": "context", "status": "running"})
    pr_meta = state.get("pr_meta", {})
    hunks = state.get("hunks", {})
    owner, repo = pr_meta.get("owner"), pr_meta.get("repo")
    head_sha = pr_meta.get("head_sha")

    context: dict[str, dict] = {}
    static_signals: list[dict] = []

    for path in hunks:
        source = (
            github.fetch_file_at(owner, repo, path, head_sha)
            if owner and repo and head_sha else None
        )
        changed = treesitter_ctx.changed_lines_for(path, hunks)
        blob = treesitter_ctx.build_file_context(path, source, changed)

        # deterministic lint/SAST signals on the changed lines
        signals = static_analysis.signals_on_lines(
            static_analysis.run_ruff(path, source or ""), set(changed)
        )
        for s in signals:
            static_signals.append({**s, "path": path})
        blob["signals"] = signals

        # deterministic test-existence check (grounds the test_gap agent)
        blob["test_exists"], blob["untested_symbols"] = _test_evidence(
            blob, owner, repo, head_sha
        )

        context[path] = blob
        names = [e["name"] for e in blob["enclosing"]]
        print(f"[build_context] {path}: enclosing={names} "
              f"imports={len(blob['imports'])} ruff={len(signals)} "
              f"test_exists={blob['test_exists']} untested={blob['untested_symbols']}")

    emit({"stage": "context", "status": "done",
          "files": len(context), "signals": len(static_signals)})
    return {"context": context, "static_signals": static_signals}


def _test_evidence(blob: dict, owner, repo, head_sha) -> tuple[bool, list[str]]:
    """Does the conventional test file exist, and which changed symbols are untested?"""
    test_path = blob.get("matching_test")
    symbols = [e["name"] for e in blob.get("enclosing", []) if e.get("name")]
    if not test_path or not (owner and repo and head_sha):
        return False, symbols
    test_src = github.fetch_file_at(owner, repo, test_path, head_sha)
    if not test_src:
        return False, symbols
    untested = [s for s in symbols if s not in test_src]
    return True, untested
