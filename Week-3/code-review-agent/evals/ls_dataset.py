"""Upsert the golden dataset (evals/prs.yaml) into LangSmith.

One example per PR:
  inputs   = {"pr_url", "name"}
  outputs  = {"expected": [known issues]}   (empty for precision-only PRs)
  metadata = {"scenario_type", "difficulty", "language", "note"}

Idempotent: clears existing examples and re-creates them so the LangSmith
dataset always matches prs.yaml exactly. Costs no Nebius tokens.

    python -m evals.ls_dataset
"""
from __future__ import annotations

from pathlib import Path

import yaml
from langsmith import Client

from app import config  # noqa: F401  (import loads .env -> LANGCHAIN_API_KEY)

DATASET_NAME = "code-review-eval"
_HERE = Path(__file__).parent


def main() -> None:
    spec = yaml.safe_load((_HERE / "prs.yaml").read_text())
    prs = spec["prs"]
    client = Client()

    if client.has_dataset(dataset_name=DATASET_NAME):
        ds = client.read_dataset(dataset_name=DATASET_NAME)
        stale = list(client.list_examples(dataset_id=ds.id))
        for ex in stale:
            client.delete_example(example_id=ex.id)
        print(f"Cleared {len(stale)} existing examples from {DATASET_NAME!r}")
    else:
        ds = client.create_dataset(
            dataset_name=DATASET_NAME,
            description=(
                "Code-review agent golden dataset: 30 PRs tagged happy / edge / "
                "known_failure / adversarial. Real seeded + merged OSS PRs."
            ),
        )
        print(f"Created dataset {DATASET_NAME!r} (id={ds.id})")

    examples = []
    for pr in prs:
        examples.append({
            "inputs": {"pr_url": pr["url"], "name": pr["name"]},
            "outputs": {"expected": pr.get("expected") or []},
            "metadata": {
                "scenario_type": pr["scenario_type"],
                "difficulty": pr["difficulty"],
                "language": pr.get("language", "python"),
                "note": pr.get("note", ""),
            },
        })

    client.create_examples(dataset_id=ds.id, examples=examples)
    print(f"Upserted {len(examples)} examples into LangSmith dataset {DATASET_NAME!r}")


if __name__ == "__main__":
    main()
