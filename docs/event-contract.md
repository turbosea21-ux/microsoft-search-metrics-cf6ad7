# The telemetry event contract

`schemas/telemetry/search_event_v1.json` is the agreement between everything
that produces telemetry and everything that consumes it. Treat it like an API.

## Versioning rules

- `schema_version` is **required** and pinned to the file version (`1`).
- **Additive, optional** fields can ship without a version bump — old consumers
  ignore unknown fields (their JSON parser drops them).
- **Renaming, removing, or retyping** a field, or making an optional field
  required, is breaking: publish `search_event_v2.json`, let producers emit `v2`
  while consumers learn to read both, then retire `v1`.

## JSON vs Protobuf

We use **JSON** for the MVP: human-readable, no codegen, trivial to inspect on a
topic while debugging. The cost is size and the lack of a compile-time guarantee
that a producer matches the schema — which is exactly why the ingest service
validates every event (next steps). At high volume you would switch the
`*.clean` topic to **Protobuf** (or Avro) behind a schema registry for compact
framing and enforced compatibility; the contract here is designed to port.

## Time fields

`event_time` is stamped by the producer when the request finished.
`ingest_time` is stamped later by the ingest service. Carrying both lets the
pipeline measure its own lag — `ingest_time - event_time` — independent of the
metric being measured.
