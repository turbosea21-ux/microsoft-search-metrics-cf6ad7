-- Persisted anomaly events for the dashboard to highlight.
CREATE TABLE IF NOT EXISTS anomaly_event (
    id            BIGSERIAL PRIMARY KEY,
    window_start  TIMESTAMPTZ NOT NULL,
    service       TEXT        NOT NULL,
    endpoint      TEXT        NOT NULL,
    kind          TEXT        NOT NULL,    -- error_rate | latency_p95
    observed      DOUBLE PRECISION NOT NULL,
    baseline      DOUBLE PRECISION NOT NULL,
    detected_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_anomaly UNIQUE (window_start, service, endpoint, kind)
);

CREATE INDEX IF NOT EXISTS idx_anomaly_recent
    ON anomaly_event (detected_at DESC);
