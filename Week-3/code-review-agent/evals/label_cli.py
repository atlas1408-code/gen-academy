"""Human spot-check of the judge — validates the automated precision number.

Loads the most recent eval run (evals/last_run.json), shows you a sample of
findings + the judge's verdict, and records your own valid/invalid label. Then
it reports judge-vs-human agreement and Cohen's kappa, so you know whether the
judge (and therefore the precision figure) can be trusted.

    python -m evals.label_cli [n]      # n = how many to label (default 30)
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

_HERE = Path(__file__).parent
_LASTRUN = _HERE / "last_run.json"
_LABELS = _HERE / "human_labels.jsonl"


def _cohen_kappa(pairs: list[tuple[str, str]]) -> float:
    """Two raters, binary labels (valid/invalid)."""
    n = len(pairs)
    if not n:
        return 0.0
    po = sum(1 for a, b in pairs if a == b) / n
    labels = {"valid", "invalid"}
    pe = 0.0
    for lab in labels:
        pa = sum(1 for a, _ in pairs if a == lab) / n
        pb = sum(1 for _, b in pairs if b == lab) / n
        pe += pa * pb
    return (po - pe) / (1 - pe) if pe != 1 else 1.0


def main(n: int = 30) -> None:
    if not _LASTRUN.exists():
        print("No last_run.json — run `python -m evals.run_eval` first.")
        return
    records = json.loads(_LASTRUN.read_text())
    # only judged-decisively findings are worth human comparison
    pool = [r for r in records if r["verdict"] in ("valid", "invalid")]
    random.shuffle(pool)
    sample = pool[:n]
    print(f"Labeling {len(sample)} findings. For each: [v]alid / [i]nvalid / [s]kip / [q]uit\n")

    pairs: list[tuple[str, str]] = []   # (judge, human)
    out = []
    for idx, r in enumerate(sample, 1):
        print(f"--- {idx}/{len(sample)}  [{r['severity']}] {r['agent']}  "
              f"{r['path']}:{r['line']}")
        print(f"    title: {r['title']}")
        print(f"    problem: {r['problem']}")
        print(f"    suggestion: {r['suggestion']}")
        print(f"    (judge said: {r['verdict']}"
              + (f" / {r['fp_type']}" if r['fp_type'] else "") + ")")
        ans = input("    your call [v/i/s/q]: ").strip().lower()
        if ans == "q":
            break
        if ans == "s" or ans not in ("v", "i"):
            continue
        human = "valid" if ans == "v" else "invalid"
        pairs.append((r["verdict"], human))
        out.append({**r, "human": human})

    if not pairs:
        print("\nNo labels recorded.")
        return

    with _LABELS.open("a") as fh:
        for row in out:
            fh.write(json.dumps(row) + "\n")

    agree = sum(1 for j, h in pairs if j == h) / len(pairs)
    kappa = _cohen_kappa(pairs)
    print(f"\nLabeled {len(pairs)} findings.")
    print(f"Judge–human agreement: {agree*100:.0f}%   Cohen's kappa: {kappa:.2f}")
    if kappa >= 0.6:
        print("→ Substantial agreement: the automated precision number is trustworthy.")
    elif kappa >= 0.4:
        print("→ Moderate agreement: treat precision as indicative; tune the judge rubric.")
    else:
        print("→ Low agreement: do NOT trust the automated precision yet — revise the judge.")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 30)
