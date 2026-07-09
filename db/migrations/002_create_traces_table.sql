-- Trace-level records for failed or slow requests. Lean by design: only the
-- fields an engineer needs to debug one request live here, not full payloads.

CREATE TABLE IF NOT EXISTS request_trace (
    request_id     TEXT        PRIMARY KEY,       -- idempotency key: upsert on retry
    trace_id       TEXT        NOT NULL,
    event_time     TIMESTAMPTZ NOT NULL,
    service        TEXT        NOT NULL,
    endpoint       TEXT        NOT NULL,
    status_code    INT         NOT NULL,
    error_type     TEXT,                          -- null for slow-but-successful
    latency_ms     DOUBLE PRECISION NOT NULL,
    query_hash     TEXT,
    top_result_ids TEXT[],                        -- truncated result list
    error_message  TEXT                           -- short, human-readable
);

-- Incident triage filters by time and error_type ("all timeouts in the last hour").
CREATE INDEX IF NOT EXISTS idx_trace_time
    ON request_trace (event_time DESC);
CREATE INDEX IF NOT EXISTS idx_trace_error
    ON request_trace (error_type, event_time DESC);
-- Jumping from a metric spike to the underlying requests is a trace_id lookup.
CREATE INDEX IF NOT EXISTS idx_trace_trace_id
    ON request_trace (trace_id);
