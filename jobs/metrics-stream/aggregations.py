"""Windowed aggregation of cleaned telemetry into metric rows.

A WindowAccumulator collects events for one (service, endpoint) key inside one
time window and emits a single MetricRow when the window closes.
"""
from __future__ import annotations

import bisect
from dataclasses import dataclass, field


@dataclass
class MetricRow:
    window_start: str
    window_end: str
    service: str
    endpoint: str
    request_count: int
    error_count: int
    error_rate: float
    p50_latency_ms: float
    p95_latency_ms: float
    avg_relevance: float | None


@dataclass
class WindowAccumulator:
    service: str
    endpoint: str
    latencies: list[float] = field(default_factory=list)
    relevances: list[float] = field(default_factory=list)
    count: int = 0
    errors: int = 0

    def add(self, event: dict) -> None:
        self.count += 1
        # keep latencies sorted so percentiles are a simple index lookup
        bisect.insort(self.latencies, float(event["latency_ms"]))
        if int(event["status_code"]) >= 500:
            self.errors += 1
        rel = event.get("relevance_score")
        if rel is not None:
            self.relevances.append(float(rel))

    def _percentile(self, p: float) -> float:
        if not self.latencies:
            return 0.0
        # nearest-rank percentile on the sorted list
        rank = max(0, min(len(self.latencies) - 1, round(p / 100 * len(self.latencies)) - 1))
        return round(self.latencies[rank], 2)

    def to_row(self, window_start: str, window_end: str) -> MetricRow:
        avg_rel = (
            round(sum(self.relevances) / len(self.relevances), 4)
            if self.relevances
            else None
        )
        return MetricRow(
            window_start=window_start,
            window_end=window_end,
            service=self.service,
            endpoint=self.endpoint,
            request_count=self.count,
            error_count=self.errors,
            error_rate=round(self.errors / self.count, 4) if self.count else 0.0,
            p50_latency_ms=self._percentile(50),
            p95_latency_ms=self._percentile(95),
            avg_relevance=avg_rel,
        )
