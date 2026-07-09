# Dashboard API

Base path `/api`. All errors share one envelope:
`{"error": {"code", "message", "request_id"}}`.

## Metrics

- `GET /api/metrics?service=&endpoint=&start=&end=` — windowed metrics for a
  service/endpoint over `[start, end)`. **Cached** ~60s.
- `GET /api/metrics/errors?start=&end=&limit=` — top error types by count.
  **Cached** ~60s.

## Traces

- `GET /api/traces/{trace_id}` — all captured events for a trace, time-ordered.
  **Not cached** — triage needs live data.

## Caching contract

Metric endpoints are cache-aside with a short TTL: the dashboard tolerates data
that is up to ~60s stale in exchange for fast, cheap reads. Trace lookups are
never cached because an engineer mid-incident must see the latest captures.
