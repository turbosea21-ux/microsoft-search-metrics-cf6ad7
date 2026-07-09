"""Trace-writer: consume cleaned telemetry, apply the capture policy, and batch
matching events into the trace table. Batching bounds DB write amplification.
"""
from __future__ import annotations

import json
import os
import time

from kafka import KafkaConsumer

from policy import CapturePolicy
from storage import TraceStore

BATCH_SIZE = 100
FLUSH_INTERVAL_S = 2.0


def run(consumer: KafkaConsumer, store: TraceStore, policy: CapturePolicy) -> None:
    batch: list[dict] = []
    last_flush = time.monotonic()

    def flush() -> None:
        nonlocal last_flush
        if batch:
            store.write_batch(batch)
            batch.clear()
        last_flush = time.monotonic()

    for message in consumer:
        event = json.loads(message.value)
        if policy.should_capture(event):
            batch.append(event)
        if len(batch) >= BATCH_SIZE or time.monotonic() - last_flush >= FLUSH_INTERVAL_S:
            flush()


def main() -> None:
    dsn = os.environ.get("TRACE_DB_DSN", "postgresql://localhost/searchmetrics")
    consumer = KafkaConsumer(
        "search.events.clean",
        bootstrap_servers="localhost:9092",
        group_id="trace-writer",
        value_deserializer=lambda b: b.decode("utf-8"),
        auto_offset_reset="latest",
    )
    store = TraceStore(dsn)
    policy = CapturePolicy()
    try:
        run(consumer, store, policy)
    finally:
        store.close()


if __name__ == "__main__":
    main()
