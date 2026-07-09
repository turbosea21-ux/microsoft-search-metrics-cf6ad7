"""Traffic simulator entry point: generate events at a target QPS and publish
them to Kafka with bounded retry/backoff and graceful shutdown.
"""
from __future__ import annotations

import json
import signal
import time

from kafka import KafkaProducer
from kafka.errors import KafkaError

from simulator.config import SimConfig
from simulator.generator import EventGenerator

_running = True


def _stop(_signum, _frame) -> None:
    global _running
    _running = False


def build_producer(config: SimConfig) -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=config.bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8"),
        acks="all",
        retries=0,
        linger_ms=20,
        request_timeout_ms=5000,   # strict timeout: never block forever
    )


def publish_with_retry(producer: KafkaProducer, config: SimConfig, event: dict) -> bool:
    for attempt in range(config.max_publish_retries):
        try:
            future = producer.send(config.topic, key=event["trace_id"], value=event)
            future.get(timeout=5)
            return True
        except KafkaError:
            time.sleep(config.backoff_base_s * (2**attempt))
    return False


def main() -> None:
    config = SimConfig()
    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    gen = EventGenerator(config)
    producer = build_producer(config)

    interval = 1.0 / config.qps
    started = time.monotonic()
    sent = dropped = 0
    try:
        while _running:
            if config.duration_s and time.monotonic() - started >= config.duration_s:
                break
            event = gen.next_event()
            if publish_with_retry(producer, config, event):
                sent += 1
            else:
                dropped += 1
            time.sleep(interval)
    finally:
        # graceful shutdown: flush buffered events before exiting
        producer.flush(timeout=10)
        producer.close(timeout=10)
        print(f"simulator stopped gracefully: sent={sent} dropped={dropped}")


if __name__ == "__main__":
    main()
