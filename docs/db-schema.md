# Analytics schema

Two tables, two access patterns.

## `metrics_window` — read-optimized aggregates

One row per `(window_start, service, endpoint)`, written once per window by the
metrics job. It is **small** (a row per minute per service, not per request) and
read constantly by the dashboard. The unique constraint on
`(window_start, service, endpoint)` makes the metric write idempotent: a
re-emitted window upserts the same row.

Index choice mirrors the query: dashboards say "service X, this endpoint, last
N hours", so `(service, endpoint, window_start DESC)` lets Postgres seek
straight to the rows and read them already time-ordered.

## `request_trace` — debug records

One row per *captured* request (errors / slow ones only — see the trace
pipeline). `request_id` is the primary key so a redelivered event upserts
instead of duplicating — the idempotency the at-least-once pipeline needs.

The `error_type + event_time` index serves the most common triage query ("show
me the timeouts in the last hour"), and `trace_id` lets the UI jump from a
metric anomaly to the individual requests behind it.

## Why two tables

Metrics are **aggregate, write-once-per-window, read-heavy**. Traces are
**per-request, append-mostly, filtered-read**. Splitting them lets each carry
the indexes its own access pattern wants without one bloating the other.
