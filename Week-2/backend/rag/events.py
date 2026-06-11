"""StepEvent schema + helpers for the glass-box stream (PLAN.md §7.2).

Both /ingest and /query yield a sequence of these; the backend serializes each
as a Server-Sent Event and the React UI animates the matching pipeline node.
Payloads are kept SMALL (1-2 sample chunks, an 8-dim embedding preview) so the
stream stays light.
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field

# Allowed stages (drives which pipeline node lights up):
#   load | clean | chunk | embed | upsert | retrieve | rerank | generate
#   | done | refuse | error
# Allowed statuses: start | progress | complete | error


@dataclass
class StepEvent:
    stage: str
    status: str
    message: str
    elapsed_ms: int
    data: dict = field(default_factory=dict)

    def to_sse(self) -> str:
        """Serialize as a Server-Sent Event frame."""
        return f"data: {json.dumps(asdict(self))}\n\n"


class Clock:
    """Tracks elapsed ms from construction, for the elapsed_ms field."""

    def __init__(self) -> None:
        self._t0 = time.perf_counter()

    def ms(self) -> int:
        return int((time.perf_counter() - self._t0) * 1000)


def event(stage: str, status: str, message: str, clock: Clock, **data) -> StepEvent:
    return StepEvent(stage=stage, status=status, message=message,
                     elapsed_ms=clock.ms(), data=data)
