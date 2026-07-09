# Microsoft AI | Distributed Search Metrics & Debugging Platform

An intermediate capstone modeled on the kind of internal tooling search teams actually run. You version a telemetry event schema and lay out Kafka topics, write a deterministic traffic simulator, build a validating-enriching ingest boundary with a dead-letter queue, compute rolling p50/p95/error-rate/relevance aggregates with windowed stream processing, design analytics tables for metrics and traces, selectively persist failed/slow requests for debugging, serve it all through a Redis-cached API, layer on heuristic anomaly detection, build a React debugging dashboard, instrument every service with Prometheus + structured logs, and harden the whole thing with backpressure, retries, and graceful shutdown.

Built step-by-step with [KhwajaLabs Build](https://khwajalabs.com).

## Stack
- Python
- Go
- Kafka
- Stream Processing
- Postgres
- Redis
- React
- Prometheus
