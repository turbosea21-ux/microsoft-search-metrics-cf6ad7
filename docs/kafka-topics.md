# Kafka topics

| Topic                  | Producers          | Consumers                         | Key         | Notes                                  |
|------------------------|--------------------|-----------------------------------|-------------|----------------------------------------|
| `search.events.raw`    | traffic-simulator  | ingest                            | `trace_id`  | Untrusted producer output.             |
| `search.events.clean`  | ingest             | metrics-stream, trace-writer      | `trace_id`  | Validated + enriched. Downstream feed. |
| `search.events.dlq`    | ingest             | (manual / ops tooling)            | `request_id`| Poison messages + a validation reason. |

## Why key by `trace_id`

Kafka guarantees ordering **within a partition**, and a record's key picks its
partition. Keying on `trace_id` keeps every event for one request on the same
partition, so a consumer rebuilding a trace sees those events in order. It also
spreads load: distinct traces hash to different partitions.

## Partitions & consumer groups

Start each topic at 6 partitions. A consumer **group** can run up to 6 instances
in parallel (one per partition); beyond that, instances sit idle. Pick the
partition count for the throughput you expect, not the throughput you have today
— raising it later re-shuffles keys across partitions and breaks per-key order.
