"""Graph assembly for the code review agent.

Topology:
    START -> fetch_pr -> build_context -> repo_context -> {quality, security, test_gap}
          -> consolidate -> verify -> human_gate --(approve)--> post_comments -> END
                                                  --(else)----> END

The three specialists fan out from build_context and fan in at consolidate;
LangGraph waits for all three before running consolidate. Phase 1 uses
InMemorySaver and hardcoded node bodies.
"""
from contextlib import contextmanager

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command

from app.nodes.agents import make_agent_node
from app.nodes.build_context import build_context
from app.nodes.consolidate import consolidate
from app.nodes.deterministic import deterministic_findings
from app.nodes.fetch_pr import fetch_pr
from app.nodes.human_gate import human_gate, route_after_gate
from app.nodes.post_comments import post_comments
from app.nodes.repo_context import repo_context
from app.nodes.verify import verify
from app.state import ReviewState

AGENTS = ("quality", "security", "test_gap")


def build_graph(checkpointer=None):
    g = StateGraph(ReviewState)

    g.add_node("fetch_pr", fetch_pr)
    g.add_node("build_context", build_context)
    g.add_node("repo_context", repo_context)
    g.add_node("deterministic", deterministic_findings)
    for name in AGENTS:
        g.add_node(name, make_agent_node(name))
    g.add_node("consolidate", consolidate)
    g.add_node("verify", verify)
    g.add_node("human_gate", human_gate)
    g.add_node("post_comments", post_comments)

    g.add_edge(START, "fetch_pr")
    g.add_edge("fetch_pr", "build_context")
    g.add_edge("build_context", "repo_context")
    # Fan out to the three specialists + the deterministic branch in parallel...
    g.add_edge("repo_context", "deterministic")
    g.add_edge("deterministic", "consolidate")
    for name in AGENTS:
        g.add_edge("repo_context", name)
        # ...and fan in: consolidate waits for all of them.
        g.add_edge(name, "consolidate")
    g.add_edge("consolidate", "verify")
    g.add_edge("verify", "human_gate")
    g.add_conditional_edges(
        "human_gate",
        route_after_gate,
        {
            "post_comments": "post_comments",
            "consolidate": "consolidate",   # refine loop
            "__end__": END,
        },
    )
    g.add_edge("post_comments", END)

    return g.compile(checkpointer=checkpointer or InMemorySaver())


@contextmanager
def open_pg_checkpointer():
    """Yield a Postgres-backed checkpointer, running setup() once.

    Used by the durability demo and (later) the API server so that runs survive
    a process restart.
    """
    from langgraph.checkpoint.postgres import PostgresSaver

    from app.config import DATABASE_URL

    with PostgresSaver.from_conn_string(DATABASE_URL) as checkpointer:
        checkpointer.setup()
        yield checkpointer


def _demo() -> None:
    """Phase 1 acceptance: run to interrupt, then resume with approve."""
    graph = build_graph()
    config = {"configurable": {"thread_id": "demo-1"}}

    print("=== invoke (runs to human_gate interrupt) ===")
    result = graph.invoke(
        {"pr_url": "https://github.com/atlas1408-code/eval-target-repo/pull/1"}, config
    )

    interrupts = result.get("__interrupt__", [])
    print("\n--- INTERRUPT PAYLOAD ---")
    for itr in interrupts:
        print(itr.value)

    print("\n=== resume with approve ===")
    final = graph.invoke(Command(resume={"action": "approve"}), config)
    print(f"\nposted = {final.get('posted')}")


if __name__ == "__main__":
    _demo()
