"""Decide which cleaned events are worth persisting as traces.

The rule: keep everything that failed, everything unusually slow, and a small
random sample of the rest (so 'normal' is represented for comparison).
"""
from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class CapturePolicy:
    latency_threshold_ms: float = 500.0   # slow-request cutoff (a p95 guess)
    sample_rate: float = 0.01             # 1% of healthy traffic, for context
    seed: int | None = None

    def __post_init__(self) -> None:
        # frozen dataclass: set the rng via object.__setattr__
        object.__setattr__(self, "_rng", random.Random(self.seed))

    def should_capture(self, event: dict) -> bool:
        if int(event["status_code"]) >= 500:
            return True
        if float(event["latency_ms"]) > self.latency_threshold_ms:
            return True
        return self._rng.random() < self.sample_rate  # type: ignore[attr-defined]
