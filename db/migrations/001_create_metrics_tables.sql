-- Windowed search-quality metrics, one row per (window, service, endpoint).
-- Optimized for "metrics over a time range for a service" dashboard queries.

CREATE TABLE IF NOT EXISTS metrics_window (
    id              BIGSERIAL PRIMARY KEY,
    window_start    TIMESTAMPTZ NOT NULL,
    window_end      TIMESTAMPTZ NOT NULL,
    service         TEXT        NOT NULL,
    endpoint        TEXT        NOT NULL,
    request_count   BIGINT      NOT NULL,
    error_count     BIGINT      NOT NULL,
    error_rate      DOUBLE PRECISION NOT NULL,
    p50_latency_ms  DOUBLE PRECISION NOT NULL,
    p95_latency_ms  DOUBLE PRECISION NOT NULL,
    avg_relevance   DOUBLE PRECISION,            -- nullable: no relevance signal
    CONSTRAINT uq_metrics_window UNIQUE (window_start, service, endpoint)
);

-- Dashboards filter by time first, then service/endpoint. Lead the index with
-- the columns the WHERE clause constrains, in that order.
CREATE INDEX IF NOT EXISTS idx_metrics_window_lookup
    ON metrics_window (service, endpoint, window_start DESC);

-- A time-only index serves the cross-service overview ("all services, last 1h").
CREATE INDEX IF NOT EXISTS idx_metrics_window_time
    ON metrics_window (window_start DESC);
