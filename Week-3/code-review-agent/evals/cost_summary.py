"""Token / cost summary from the token_usage table.

Reports per-agent and per-run totals and an estimated USD cost. PRICES are
per-1M-token rates by model — edit them to match your Nebius Token Factory plan
(they are approximate defaults). LangSmith also captures per-call tokens if
tracing is enabled, but this table is the source of truth here.

    python -m evals.cost_summary [run_id_prefix]
"""
import sys

import psycopg

from app import config
from app.db.repo import DATABASE_URL

# Approximate USD per 1M tokens (input/output combined). EDIT to your plan.
PRICES = {
    "moonshotai/Kimi-K2.6": 0.60,
    "deepseek-ai/DeepSeek-V3.2": 0.50,
    "meta-llama/Llama-3.3-70B-Instruct": 0.30,
    "Qwen/Qwen3-235B-A22B-Instruct-2507": 0.40,
}


def _price_for_agent(agent: str) -> float:
    # agent labels may be merged like "quality+security"; price by first model.
    base = agent.split("+")[0]
    return PRICES.get(config.MODELS.get(base, ""), 0.0)


def _cost(agent: str, total_tokens: int) -> float:
    return total_tokens / 1_000_000 * _price_for_agent(agent)


def main(prefix: str = "") -> None:
    where = "WHERE run_id LIKE %s" if prefix else ""
    args = (f"{prefix}%",) if prefix else ()

    with psycopg.connect(DATABASE_URL) as conn:
        per_agent = conn.execute(
            f"""SELECT agent, SUM(prompt_tokens), SUM(completion_tokens),
                       SUM(total_tokens), COUNT(*)
                FROM token_usage {where} GROUP BY agent ORDER BY agent""", args
        ).fetchall()
        per_run = conn.execute(
            f"""SELECT run_id, SUM(total_tokens), COUNT(*)
                FROM token_usage {where} GROUP BY run_id ORDER BY run_id""", args
        ).fetchall()

    scope = f" (run_id LIKE {prefix!r})" if prefix else " (all runs)"
    print(f"=== Per-agent token/cost{scope} ===")
    print(f"{'agent':<20}{'in':>10}{'out':>10}{'total':>10}{'calls':>7}{'est $':>9}")
    grand_tokens = grand_cost = 0
    for agent, pin, pout, tot, calls in per_agent:
        c = _cost(agent, tot)
        grand_tokens += tot
        grand_cost += c
        print(f"{agent:<20}{pin:>10}{pout:>10}{tot:>10}{calls:>7}{c:>9.4f}")
    print(f"{'TOTAL':<20}{'':>10}{'':>10}{grand_tokens:>10}{'':>7}{grand_cost:>9.4f}")

    print(f"\n=== Per-run totals{scope} ===")
    print(f"{'run_id':<28}{'tokens':>10}{'calls':>7}{'est $':>9}")
    for run_id, tot, calls in per_run:
        # rough per-run cost: average agent price weighting is hard; reuse totals.
        print(f"{run_id:<28}{tot:>10}{calls:>7}{tot/1_000_000*0.45:>9.4f}")

    if per_run:
        avg = grand_cost / len(per_run)
        print(f"\nRuns: {len(per_run)}  ·  est. avg cost/run: ${avg:.4f}  "
              f"(prices are approximate — edit PRICES)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
