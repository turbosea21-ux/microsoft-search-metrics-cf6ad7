"""Postgres data-access for the API, hardened with strict timeouts and bounded
retry-with-backoff on transient connection errors.
"""
from __future__ import annotations

import os
import time
from contextlib import contextmanager

import psycopg2
from psycopg2 import OperationalError
from psycopg2.extras import RealDictCursor

MAX_RETRIES = 3
BACKOFF_BASE_S = 0.1
STATEMENT_TIMEOUT_MS = 2000


@contextmanager
def _cursor():
    conn = psycopg2.connect(
        os.environ.get("API_DB_DSN", "postgresql://localhost/searchmetrics"),
        cursor_factory=RealDictCursor,
        connect_timeout=3,                 # cap connect time
        options=f"-c statement_timeout={STATEMENT_TIMEOUT_MS}",  # cap query time
    )
    try:
        yield conn.cursor()
        conn.commit()
    finally:
        conn.close()


def _with_retry(fn):
    """Retry a read on transient OperationalError with exponential backoff."""
    last: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            return fn()
        except OperationalError as exc:
            last = exc
            time.sleep(BACKOFF_BASE_S * (2**attempt))
    raise last  # exhausted retries: surface to the error envelope as a 500


def metrics_in_range(service: str, endpoint: str, start: str, end: str) -> list[dict]:
    def run():
        with _cursor() as cur:
            cur.execute(
                """
                SELECT window_start, window_end, request_count, error_count,
                       error_rate, p50_latency_ms, p95_latency_ms, avg_relevance
                FROM metrics_window
                WHERE service = %s AND endpoint = %s
                  AND window_start >= %s AND window_start < %s
                ORDER BY window_start
                """,
                (service, endpoint, start, end),
            )
            return list(cur.fetchall())

    return _with_retry(run)


def top_error_types(start: str, end: str, limit: int) -> list[dict]:
    def run():
        with _cursor() as cur:
            cur.execute(
                """
                SELECT error_type, COUNT(*) AS n
                FROM request_trace
                WHERE event_time >= %s AND event_time < %s AND error_type IS NOT NULL
                GROUP BY error_type ORDER BY n DESC LIMIT %s
                """,
                (start, end, limit),
            )
            return list(cur.fetchall())

    return _with_retry(run)


def trace_by_id(trace_id: str) -> list[dict]:
    def run():
        with _cursor() as cur:
            cur.execute(
                "SELECT * FROM request_trace WHERE trace_id = %s ORDER BY event_time",
                (trace_id,),
            )
            return list(cur.fetchall())

    return _with_retry(run)
