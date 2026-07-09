"""Streaming metrics job.

Reads cleaned telemetry from Kafka and computes rolling aggregates over
processing-time tumbling windows. One accumulator per (service, endpoint) per
window; when the window clock advances, all open accumulators are flushed.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone

from kafka import KafkaConsumer

from aggregations import WindowAccumulator
from sinks import MetricSink, StdoutSink

WINDOW_S = 60  # tumbling window length


def window_bounds(now: float) -> tuple[int, int]:
    start = int(now // WINDOW_S) * WINDOW_S
    return start, start + WINDOW_S


def _iso(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def run(consumer: KafkaConsumer, sink: MetricSink) -> None:
    accumulators: dict[tuple[str, str], WindowAccumulator] = {}
    current_start, _ = window_bounds(time.time())

    for message in consumer:
        now = time.time()
        start, end = window_bounds(now)

        # window rolled over: flush everything from the previous window
        if start != current_start:
            for acc in accumulators.values():
                sink.emit(acc.to_row(_iso(current_start), _iso(current_start + WINDOW_S)))
            accumulators = {}
            current_start = start

        event = json.loads(message.value)
        key = (event["service"], event["endpoint"])
        acc = accumulators.get(key)
        if acc is None:
            acc = WindowAccumulator(service=event["service"], endpoint=event["endpoint"])
            accumulators[key] = acc
        acc.add(event)


def main() -> None:
    consumer = KafkaConsumer(
        "search.events.clean",
        bootstrap_servers="localhost:9092",
        group_id="metrics-stream",
        value_deserializer=lambda b: b.decode("utf-8"),
        auto_offset_reset="latest",
    )
    run(consumer, StdoutSink())


if __name__ == "__main__":
    main()
