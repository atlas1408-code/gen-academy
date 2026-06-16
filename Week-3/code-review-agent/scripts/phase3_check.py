"""Phase 3 acceptance: fetch a real public PR, parse hunks, build context.

    python -m scripts.phase3_check [pr_url]

Defaults to eval-target-repo PR #1 (the seeded SQL-injection PR).
"""
import sys

from app.nodes.build_context import build_context
from app.nodes.fetch_pr import fetch_pr

DEFAULT_PR = "https://github.com/atlas1408-code/eval-target-repo/pull/1"


def main(pr_url: str) -> None:
    state = {"pr_url": pr_url}

    print("=== fetch_pr ===")
    state.update(fetch_pr(state))

    print("\n--- parsed hunks ---")
    for path, hunks in state["hunks"].items():
        for h in hunks:
            print(f"  {path}: {h['header'].strip()}  "
                  f"added={h['added_lines']} removed={h['removed_lines']}")

    print("\n=== build_context ===")
    state.update(build_context(state))

    print("\n--- context blobs ---")
    for path, blob in state["context"].items():
        print(f"  {path} [{blob['language']}]")
        for e in blob["enclosing"]:
            print(f"     enclosing {e['kind']} '{e['name']}' "
                  f"(lines {e['start_line']}-{e['end_line']})")
        print(f"     imports={blob['imports']}  matching_test={blob['matching_test']}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PR)
