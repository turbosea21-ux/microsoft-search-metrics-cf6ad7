# Operational notes

## Failure modes & responses

| Symptom                         | Likely cause                          | Response                              |
|---------------------------------|---------------------------------------|---------------------------------------|
| Kafka consumer lag rising       | metrics/trace-writer too slow         | scale the consumer group (≤ partitions) |
| DLQ filling up                  | a producer broke the schema           | inspect `validation_error`, fix producer |
| API p95 spiking, DB CPU high    | uncached query storm / missing index  | check cache hit rate, confirm indexes  |
| Trace writes failing            | Postgres saturated / connection limit | bounded retry, then drop + metric       |
| Dashboards empty after deploy   | a consumer crashed on shutdown        | confirm graceful drain; replay if needed |

## Resilience rules

1. **Strict timeouts** on every external call (Kafka, Postgres, Redis). An
   unbounded call starves the worker pool — one slow dependency stalls all of it.
2. **Retry then give up.** Bounded exponential backoff, then DLQ or drop-with-a-
   metric. Never an infinite retry loop — that turns a blip into an outage.
3. **Backpressure.** Bound in-memory queues/batches. When full, slow intake (or
   drop with a counter) rather than growing memory without limit.
4. **Graceful shutdown.** On SIGTERM, stop accepting new work, drain in-flight
   items within a grace period, flush buffers, then exit. This is what keeps a
   rolling deploy from losing or duplicating data.

## At-least-once recap

Because every consumer is at-least-once, a crash mid-process causes a
**redelivery**, not a loss. All writes are idempotent (`request_id` /
`(window, service, endpoint)` keys), so a redelivered event is a no-op, not a
duplicate. Graceful shutdown minimizes how often redelivery happens at all.
