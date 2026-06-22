"""Run the LangSmith evaluation over the golden dataset.

    # baseline (verifier OFF) vs post (verifier ON) — same dataset, A/B in the
    # LangSmith Comparison view:
    VERIFY_ENABLED=false python -m evals.ls_run --label baseline
    python -m evals.ls_run --label post

    # smoke-test the plumbing on a single example (cheap):
    python -m evals.ls_run --label smoke --names security-sql-injection

`VERIFY_ENABLED` is read from the environment at import. Each example runs the
agent to the human-gate interrupt (no posting) and is scored by the judge
(precision/recall/FP) plus code-based latency/cost/degraded evaluators.
client.evaluate prints the experiment URL.
"""
from __future__ import annotations

import argparse
import subprocess

from langsmith import Client

from app import config
from app.config import JUDGE_MODEL, MODELS, VERIFIER_MODEL
from evals.ls_dataset import DATASET_NAME
from evals.ls_evaluators import ALL_EVALUATORS
from evals.ls_target import review_target


def _commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True
        ).strip()
    except Exception:
        return "unknown"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", default="post",
                    help="experiment label, e.g. baseline | post | smoke")
    ap.add_argument("--names", default="",
                    help="comma-separated PR names to limit to (smoke test)")
    args = ap.parse_args()

    client = Client()
    config.log_tracing_status()
    print(f"verify_enabled={config.VERIFY_ENABLED} · judge={JUDGE_MODEL}")

    if args.names:
        wanted = {n.strip() for n in args.names.split(",") if n.strip()}
        data = [ex for ex in client.list_examples(dataset_name=DATASET_NAME)
                if ex.inputs.get("name") in wanted]
        print(f"Subset: {len(data)} example(s) -> {sorted(wanted)}")
        if not data:
            raise SystemExit("No matching examples — run `python -m evals.ls_dataset` first.")
    else:
        data = DATASET_NAME

    metadata = {
        "label": args.label,
        "verify_enabled": config.VERIFY_ENABLED,
        "commit": _commit(),
        "judge": JUDGE_MODEL,
        "verifier": VERIFIER_MODEL,
        **{f"model_{k}": v for k, v in MODELS.items()},
    }

    results = client.evaluate(
        review_target,
        data=data,
        evaluators=ALL_EVALUATORS,
        experiment_prefix=f"cra-{args.label}",
        metadata=metadata,
        max_concurrency=1,  # serialize: Nebius budget + per-run PG checkpointer
    )
    print(f"\nDone. Experiment: {getattr(results, 'experiment_name', '?')}")


if __name__ == "__main__":
    main()
