"""deterministic_findings node — fact-grounded findings that don't depend on an LLM.

Right now this emits a high-confidence "missing test coverage" finding whenever
the deterministic test-existence check (in build_context) shows a changed file's
new/changed symbols have no matching test. Because it's grounded in fact, it runs
as its own branch and is exempt from verifier suppression — so the planted bug
can't be drowned out by a chatty LLM agent.
"""
from app.format import compose_comment
from app.progress import emit
from app.state import Finding, ReviewState


def deterministic_findings(state: ReviewState) -> dict:
    findings: list[Finding] = []
    for path, blob in (state.get("context") or {}).items():
        untested = blob.get("untested_symbols") or []
        test_path = blob.get("matching_test")
        if not test_path or not untested:
            continue

        # Anchor the comment on the first untested symbol's def line (in-hunk).
        line = 1
        for e in blob.get("enclosing", []):
            if e.get("name") in untested and e.get("start_line"):
                line = e["start_line"]
                break

        why = ("has no matching test file" if not blob.get("test_exists")
               else "is not referenced by the matching test file")
        syms = ", ".join(untested)
        f = Finding(
            agent="test_gap", path=path, line=line, side="RIGHT",
            symbol=untested[0], severity="medium",
            title="Missing test coverage for new code",
            problem=f"{path} adds/changes {syms} but {why} ({test_path}).",
            suggestion=f"Add tests in {test_path} covering {syms}.",
            source="deterministic", confidence="high",
            draft_comment="", in_hunk=False,
        )
        f["draft_comment"] = compose_comment(f)
        findings.append(f)

    if findings:
        print(f"[deterministic] {len(findings)} grounded missing-test finding(s)")
        emit({"stage": "deterministic", "status": "done", "findings": len(findings)})
    return {"findings": findings}
