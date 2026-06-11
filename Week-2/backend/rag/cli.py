"""Phase 1 CLI (PLAN.md §10).

  python -m rag.cli ingest [PATH] [--force]   # PATH = file or dir; default: TRANSCRIPTS_DIR
  python -m rag.cli ask "your question"
  python -m rag.cli manifest                   # show ingested-doc registry
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import load_settings
from .ingest import _MANIFEST, ingest_dir, ingest_file


def _cmd_ingest(args) -> int:
    s = load_settings()
    target = Path(args.path) if args.path else s.transcripts_dir
    if target.is_dir():
        results = ingest_dir(target, force=args.force)
    else:
        results = [ingest_file(target, force=args.force)]
    for r in results:
        if r.get("skipped"):
            print(f"⏭  {r['file']}: skipped ({r['reason']}), {r['chunk_count']} chunks on file")
        else:
            print(f"✅ {r['file']}: {r['segment_count']} segments → {r['chunk_count']} chunks "
                  f"({r['embedding_dim']}-dim) upserted")
            print(f"   sample chunk: {r['sample_chunk'][:160]}…")
    return 0


def _cmd_ask(args) -> int:
    from .query import answer_question
    ans = answer_question(args.question)
    print(f"\nQ: {args.question}")
    print(f"top_score={ans.top_score:.3f}  refused={ans.refused}\n")
    print(ans.answer)
    if ans.sources:
        print("\n— retrieved —")
        for src in ans.sources[:5]:
            print(f"  [{src.score:.3f}] {src.title} {src.timestamp_start}-{src.timestamp_end}: "
                  f"{src.text[:90]}…")
    return 0


def _cmd_clean_report(args) -> int:
    from .cleaning import glossary_hits, oov_scan
    from .loader import parse_segments
    s = load_settings()
    target = Path(args.path) if args.path else (s.transcripts_dir / "week1-session1.txt")
    raw = "\n".join(seg.text for seg in parse_segments(target))
    print(f"=== {target.name} ===")
    print("\n-- glossary fixes that would apply --")
    hits = glossary_hits(raw)
    if hits:
        for term, n in sorted(hits.items(), key=lambda x: -x[1]):
            print(f"  {n:4d}  {term!r} → canonical")
    else:
        print("  (none)")
    print("\n-- OOV candidates (frequent non-dictionary tokens) --")
    for tok, n in oov_scan(raw):
        print(f"  {n:4d}  {tok}")
    return 0


def _cmd_manifest(_args) -> int:
    if _MANIFEST.exists():
        print(_MANIFEST.read_text())
    else:
        print("(no manifest yet — nothing ingested)")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="rag.cli")
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("ingest", help="ingest a file or directory")
    pi.add_argument("path", nargs="?", default=None)
    pi.add_argument("--force", action="store_true", help="re-ingest even if unchanged")
    pi.set_defaults(func=_cmd_ingest)

    pa = sub.add_parser("ask", help="ask a question")
    pa.add_argument("question")
    pa.set_defaults(func=_cmd_ask)

    pc = sub.add_parser("clean-report", help="show glossary fixes + OOV candidates for a file")
    pc.add_argument("path", nargs="?", default=None)
    pc.set_defaults(func=_cmd_clean_report)

    pm = sub.add_parser("manifest", help="show ingested-doc registry")
    pm.set_defaults(func=_cmd_manifest)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
