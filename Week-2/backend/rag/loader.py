"""Transcript loader (PLAN.md §5, §8.2).

Parses the course transcript format into timestamped segments:

    Aishwarya Srinivasan        <- speaker line   (followed by a blank line)
                                <- blank
    Well, happy Saturday...     <- text line      (immediately followed by its timestamp)
    00:00:07                    <- timestamp line  (HH:MM:SS, trails the text)
                                <- blank
    effort the entire team...   <- text
    00:00:18

Structural rule used to classify lines:
  * a line matching the timestamp regex closes the current text buffer;
  * a non-timestamp line whose *next* line is blank, with no text pending, is a
    speaker label;
  * everything else is transcript text (accumulated until a timestamp flushes it).

This keeps the timestamps as metadata anchors — they become our "page numbers"
for citations ("Lecture 1, 12:30").
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_TS = re.compile(r"^\d{1,2}:\d{2}(?::\d{2})?$")


@dataclass(frozen=True)
class Segment:
    speaker: str | None
    text: str
    timestamp: str  # normalized HH:MM:SS


def _norm_ts(raw: str) -> str:
    """Normalize M:SS / MM:SS / HH:MM:SS to HH:MM:SS."""
    parts = raw.split(":")
    if len(parts) == 2:
        parts = ["00", *parts]
    h, m, s = (p.zfill(2) for p in parts)
    return f"{h}:{m}:{s}"


def parse_segments(path: str | Path) -> list[Segment]:
    lines = Path(path).read_text(encoding="utf-8").split("\n")
    segments: list[Segment] = []
    speaker: str | None = None
    buf: list[str] = []

    for i, line in enumerate(lines):
        s = line.strip()
        if _TS.match(s):
            text = " ".join(buf).strip()
            if text:
                segments.append(Segment(speaker=speaker, text=text, timestamp=_norm_ts(s)))
            buf = []
            continue
        if not s:
            continue
        nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
        if not buf and nxt == "":
            # Standalone line followed by a blank, nothing pending -> speaker label.
            speaker = s
        else:
            buf.append(s)

    # Any trailing text with no closing timestamp -> attach last known timestamp.
    if buf and segments:
        text = " ".join(buf).strip()
        segments.append(Segment(speaker=speaker, text=text, timestamp=segments[-1].timestamp))
    return segments


def lecture_id_for(path: str | Path) -> str:
    """Stable lecture id from filename, e.g. week1-session1.txt -> week1-session1."""
    return Path(path).stem


def title_for(path: str | Path) -> str:
    """Human-readable title from filename, e.g. week1-session1 -> Week1 Session1."""
    return lecture_id_for(path).replace("-", " ").replace("_", " ").title()
