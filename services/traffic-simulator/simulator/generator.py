"""Deterministic search-event generator.

Given a seed, the sequence of events is fully reproducible — the same seed
replays the same traffic, which is what makes a pipeline bug repeatable.
"""
from __future__ import annotations

import hashlib
import random
import uuid
from datetime import datetime, timezone

from .config import SimConfig

SCHEMA_VERSION = 1
SAMPLE_QUERIES = (
    "best running shoes",
    "python kafka tutorial",
    "weather tomorrow",
    "distributed tracing",
    "search relevance metrics",
)


class EventGenerator:
    def __init__(self, config: SimConfig) -> None:
        self.config = config
        self.rng = random.Random(config.seed)

    def _query_hash(self) -> str:
        q = self.rng.choice(SAMPLE_QUERIES)
        return hashlib.sha256(q.encode()).hexdigest()[:16]

    def _latency_ms(self, is_slow: bool) -> float:
        base = self.rng.lognormvariate(
            mu=self._mu(), sigma=self._sigma()
        )
        return round(base * (self.config.slow_multiplier if is_slow else 1.0), 2)

    def _mu(self) -> float:
        # convert mean/sigma in ms to log-normal mu
        m, s = self.config.latency_mean_ms, self.config.latency_sigma_ms
        return float(__import__("math").log(m**2 / (m**2 + s**2) ** 0.5))

    def _sigma(self) -> float:
        m, s = self.config.latency_mean_ms, self.config.latency_sigma_ms
        return float(__import__("math").sqrt(__import__("math").log(1 + (s**2) / m**2)))

    def next_event(self) -> dict:
        cfg = self.config
        is_error = self.rng.random() < cfg.error_rate
        is_slow = (not is_error) and self.rng.random() < cfg.slow_rate
        top_k = cfg.top_k

        event = {
            "schema_version": SCHEMA_VERSION,
            "event_time": datetime.now(timezone.utc).isoformat(),
            "ingest_time": None,
            "service": self.rng.choice(cfg.services),
            "endpoint": cfg.endpoint,
            "request_id": str(uuid.uuid4()),
            "trace_id": str(uuid.uuid4()),
            "query_hash": self._query_hash(),
            "top_k": top_k,
            "result_ids": [
                str(self.rng.randrange(cfg.catalog_size)) for _ in range(top_k)
            ],
            "status_code": 200,
            "error_type": None,
            "latency_ms": self._latency_ms(is_slow),
            "relevance_score": round(self.rng.uniform(0.4, 0.98), 3),
        }

        if is_error:
            event["error_type"] = self.rng.choice(cfg.error_types)
            event["status_code"] = 504 if event["error_type"] == "timeout" else 500
            event["relevance_score"] = None
            event["result_ids"] = []

        return event
