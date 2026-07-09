"""Prometheus instrumentation for the trace-writer."""
from __future__ import annotations

from prometheus_client import Counter, start_http_server

CAPTURED = Counter("tracewriter_captured_total", "Events captured by the policy.")
SKIPPED = Counter("tracewriter_skipped_total", "Events the policy dropped.")
DB_WRITES = Counter("tracewriter_db_writes_total", "Trace rows written.", ["result"])  # ok | error


def serve(port: int = 9102) -> None:
    start_http_server(port)
