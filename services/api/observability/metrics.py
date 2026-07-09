"""Prometheus instrumentation + structured logging for the dashboard API."""
from __future__ import annotations

import logging
import sys

from prometheus_client import Counter, Histogram, make_asgi_app

REQUESTS = Counter(
    "api_requests_total",
    "Dashboard API requests.",
    ["endpoint", "status"],          # low-cardinality: route + status class
)
REQUEST_SECONDS = Histogram(
    "api_request_seconds",
    "Request handling latency.",
    ["endpoint"],
)
CACHE = Counter(
    "api_cache_total",
    "Cache hits and misses.",
    ["result"],                       # hit | miss
)

# /metrics ASGI app to mount on the FastAPI server
metrics_app = make_asgi_app()


def configure_logging() -> logging.Logger:
    """JSON-ish structured logs with stable keys to stdout."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter('{"level":"%(levelname)s","msg":"%(message)s"}')
    )
    logger = logging.getLogger("api")
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)
    return logger
