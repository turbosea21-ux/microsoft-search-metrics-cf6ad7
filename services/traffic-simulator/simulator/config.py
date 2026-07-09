"""Configuration for the traffic simulator.

All knobs live here so a run is fully described by a config object, which makes
load shapes reproducible and easy to diff.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SimConfig:
    # Kafka
    bootstrap_servers: str = "localhost:9092"
    topic: str = "search.events.raw"

    # Load shape
    qps: float = 50.0                 # target events per second
    duration_s: float = 60.0          # 0 means run until interrupted
    services: tuple[str, ...] = ("query-frontend", "ranker", "doc-fetcher")
    endpoint: str = "/search"

    # Latency distribution (log-normal-ish via mean/sigma on ms)
    latency_mean_ms: float = 80.0
    latency_sigma_ms: float = 40.0

    # Error injection
    error_rate: float = 0.03          # fraction of requests that fail
    slow_rate: float = 0.05           # fraction that are deliberately slow
    slow_multiplier: float = 6.0

    # Reproducibility
    seed: int = 1337

    # Producer reliability
    max_publish_retries: int = 3
    backoff_base_s: float = 0.05

    # Result shape
    top_k: int = 10
    catalog_size: int = 10_000

    error_types: tuple[str, ...] = field(
        default=("timeout", "downstream", "validation", "internal")
    )
