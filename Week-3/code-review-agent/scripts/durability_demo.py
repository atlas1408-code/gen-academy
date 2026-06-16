"""Phase 2 durability proof — two separate process invocations.

    # process 1: run up to the human_gate interrupt, then EXIT (simulated crash)
    python -m scripts.durability_demo start  <thread_id>

    # process 2: brand-new process resumes the SAME thread_id from Postgres
    python -m scripts.durability_demo resume <thread_id>

If state is durable, process 2 picks up exactly where process 1 stopped and
runs through to "posted" — without re-running fetch/agents/consolidate.
"""
import sys

from langgraph.types import Command

from app.db import repo
from app.graph import build_graph, open_pg_checkpointer


def start(thread_id: str) -> None:
    repo.init_app_tables()
    config = {"configurable": {"thread_id": thread_id}}
    with open_pg_checkpointer() as cp:
        graph = build_graph(cp)
        result = graph.invoke(
            {"pr_url": "https://github.com/atlas1408-code/eval-target-repo/pull/1"},
            config,
        )
        interrupts = result.get("__interrupt__", [])
        print("\n--- PAUSED AT INTERRUPT (state now in Postgres) ---")
        for itr in interrupts:
            print(itr.value["summary"])
    print(f"\nProcess exiting WITHOUT resuming. Re-run: "
          f"python -m scripts.durability_demo resume {thread_id}")


def resume(thread_id: str) -> None:
    config = {"configurable": {"thread_id": thread_id}}
    with open_pg_checkpointer() as cp:
        graph = build_graph(cp)

        snapshot = graph.get_state(config)
        if not snapshot.next:
            print(f"No pending run for thread_id={thread_id!r}. Run `start` first.")
            return
        print(f"Loaded checkpoint from Postgres; graph is paused before: {snapshot.next}")

        final = graph.invoke(Command(resume={"action": "approve"}), config)
        print(f"\nRESUMED IN A FRESH PROCESS -> posted = {final.get('posted')}")

    print("\n--- findings persisted in Postgres ---")
    for f in repo.get_findings(thread_id):
        print(f"  [{f['severity']:<8}] {f['agent']:<9} {f['path']}:{f['line']}")


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in {"start", "resume"}:
        print(__doc__)
        sys.exit(1)
    {"start": start, "resume": resume}[sys.argv[1]](sys.argv[2])
