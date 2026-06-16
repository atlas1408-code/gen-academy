"""Phase 5 acceptance: dedupe, severity-order, and out-of-hunk flagging.

Calls the consolidate node directly with crafted findings (no LLM).
"""
from app.db import repo
from app.nodes.consolidate import consolidate
from app.tools.github import parse_diff

_DIFF = """\
diff --git a/app/search.py b/app/search.py
new file mode 100644
--- /dev/null
+++ b/app/search.py
@@ -0,0 +1,35 @@
""" + "".join(f"+line{i}\n" for i in range(1, 36))


def _f(agent, line, severity, rationale):
    return {
        "agent": agent, "path": "app/search.py", "line": line, "side": "RIGHT",
        "severity": severity, "rationale": rationale,
        "draft_comment": f"{agent} comment", "in_hunk": False,
    }


def main() -> None:
    hunks = parse_diff(_DIFF)
    state = {
        "pr_url": "https://example/pr",
        "hunks": hunks,
        "findings": [
            _f("security", 15, "critical", "SQL injection"),
            _f("quality", 15, "medium", "readability"),   # dup (line 15) -> merge
            _f("test_gap", 1, "low", "missing test"),
            _f("quality", 999, "medium", "out of hunk finding"),  # not in any hunk
        ],
        "degraded_agents": [],
    }
    repo.init_app_tables()
    cfg = {"configurable": {"thread_id": "phase5-check"}}

    out = consolidate(state, cfg)
    merged = out["consolidated"]

    print("\n--- consolidated (in severity order) ---")
    for f in merged:
        print(f"  [{f['severity']:<8}] {f['agent']:<17} line {f['line']:<4} "
              f"in_hunk={f['in_hunk']}  rationale={f['rationale']!r}")

    severities = [f["severity"] for f in merged]
    assert len(merged) == 3, f"expected 3 after dedupe, got {len(merged)}"
    assert severities == ["critical", "medium", "low"], severities  # ranked
    line15 = next(f for f in merged if f["line"] == 15)
    assert line15["agent"] == "quality+security"            # merged agents
    assert "SQL injection" in line15["rationale"] and "readability" in line15["rationale"]
    assert line15["in_hunk"] is True                         # within the hunk
    out_of_hunk = next(f for f in merged if f["line"] == 999)
    assert out_of_hunk["in_hunk"] is False                   # adjacent/outside
    print("\nPASS: deduped to 3, severity-ordered, line 15 merged & in_hunk, "
          "line 999 flagged in_hunk=False.")


if __name__ == "__main__":
    main()
