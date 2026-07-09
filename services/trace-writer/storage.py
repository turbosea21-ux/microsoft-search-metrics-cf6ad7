"""Persist captured events into request_trace, idempotently, with bounded
retry-with-backoff on the batched write so a transient DB blip doesn't drop data.
"""
from __future__ import annotations

import time

import psycopg2
from psycopg2 import OperationalError
from psycopg2.extras import execute_values

UPSERT = """
INSERT INTO request_trace (
    request_id, trace_id, event_time, service, endpoint,
    status_code, error_type, latency_ms, query_hash, top_result_ids, error_message
) VALUES %s
ON CONFLICT (request_id) DO NOTHING
"""

MAX_RETRIES = 3
BACKOFF_BASE_S = 0.1


class TraceStore:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        self.conn = psycopg2.connect(dsn, connect_timeout=3)
        self.conn.autocommit = True

    def _reconnect(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass
        self.conn = psycopg2.connect(self.dsn, connect_timeout=3)
        self.conn.autocommit = True

    def _row(self, e: dict) -> tuple:
        return (
            e["request_id"], e["trace_id"], e["event_time"], e["service"], e["endpoint"],
            int(e["status_code"]), e.get("error_type"), float(e["latency_ms"]),
            e.get("query_hash"), e.get("result_ids") or [],
            (e.get("error_type") or "ok") + f" ({e['status_code']})",
        )

    def write_batch(self, events: list[dict]) -> int:
        if not events:
            return 0
        rows = [self._row(e) for e in events]
        for attempt in range(MAX_RETRIES):
            try:
                with self.conn.cursor() as cur:
                    execute_values(cur, UPSERT, rows)
                    return cur.rowcount
            except OperationalError:
                self._reconnect()
                time.sleep(BACKOFF_BASE_S * (2**attempt))
        # bounded retries exhausted: drop the batch but let the caller's
        # metric (DB_WRITES result=error) record the loss rather than hang.
        return 0

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass
