"""Heuristic anomaly detection over the per-key metric stream.

No ML: a current window is anomalous when it deviates enough from a trailing
average, with a volume guard (ignore tiny samples) and anti-flap (require two
consecutive bad windows before firing).
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from .aggregations import MetricRow


@dataclass
class Baseline:
    window_count: int = 6                       # trailing windows to average
    error_rates: deque = field(default_factory=lambda: deque(maxlen=6))
    p95s: deque = field(default_factory=lambda: deque(maxlen=6))

    def mean_error_rate(self) -> float:
        return sum(self.error_rates) / len(self.error_rates) if self.error_rates else 0.0

    def mean_p95(self) -> float:
        return sum(self.p95s) / len(self.p95s) if self.p95s else 0.0

    def observe(self, row: MetricRow) -> None:
        self.error_rates.append(row.error_rate)
        self.p95s.append(row.p95_latency_ms)


@dataclass
class Anomaly:
    window_start: str
    service: str
    endpoint: str
    kind: str          # "error_rate" | "latency_p95"
    observed: float
    baseline: float


@dataclass
class AnomalyDetector:
    min_volume: int = 100        # don't alert on tiny samples
    error_floor: float = 0.05    # absolute error-rate floor
    error_factor: float = 3.0    # or 3x the trailing mean
    latency_factor: float = 2.0  # p95 jump factor
    _baselines: dict[tuple[str, str], Baseline] = field(default_factory=dict)
    _strikes: dict[tuple[str, str], int] = field(default_factory=dict)

    def check(self, row: MetricRow) -> Anomaly | None:
        key = (row.service, row.endpoint)
        base = self._baselines.setdefault(key, Baseline())

        bad: Anomaly | None = None
        if row.request_count >= self.min_volume:
            err_limit = max(self.error_floor, self.error_factor * base.mean_error_rate())
            if base.error_rates and row.error_rate > err_limit:
                bad = Anomaly(row.window_start, row.service, row.endpoint,
                              "error_rate", row.error_rate, base.mean_error_rate())
            elif base.p95s and base.mean_p95() > 0 and \
                    row.p95_latency_ms > self.latency_factor * base.mean_p95():
                bad = Anomaly(row.window_start, row.service, row.endpoint,
                              "latency_p95", row.p95_latency_ms, base.mean_p95())

        # anti-flap: require two consecutive bad windows before firing
        if bad is not None:
            self._strikes[key] = self._strikes.get(key, 0) + 1
            fired = bad if self._strikes[key] >= 2 else None
        else:
            self._strikes[key] = 0
            fired = None

        base.observe(row)   # update the baseline AFTER comparing
        return fired
