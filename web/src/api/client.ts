// Typed client for the dashboard API. One place that knows the wire shapes and
// the shared error envelope, so pages never touch fetch directly.

const BASE = import.meta.env.VITE_API_BASE ?? '/api';

export interface MetricWindow {
  window_start: string;
  window_end: string;
  request_count: number;
  error_count: number;
  error_rate: number;
  p50_latency_ms: number;
  p95_latency_ms: number;
  avg_relevance: number | null;
}

export interface Anomaly {
  window_start: string;
  service: string;
  endpoint: string;
  kind: 'error_rate' | 'latency_p95';
  observed: number;
  baseline: number;
}

export interface TraceEvent {
  request_id: string;
  trace_id: string;
  event_time: string;
  service: string;
  endpoint: string;
  status_code: number;
  error_type: string | null;
  latency_ms: number;
  error_message: string | null;
}

class ApiError extends Error {
  constructor(public code: number, message: string) {
    super(message);
  }
}

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  const body = await res.json();
  if (!res.ok) {
    // unwrap the shared { error: { code, message } } envelope
    throw new ApiError(body?.error?.code ?? res.status, body?.error?.message ?? 'request failed');
  }
  return body as T;
}

export const api = {
  metrics: (service: string, endpoint: string, start: string, end: string) =>
    getJson<{ windows: MetricWindow[] }>(
      `/metrics?service=${service}&endpoint=${endpoint}&start=${start}&end=${end}`,
    ),
  anomalies: () => getJson<{ anomalies: Anomaly[] }>(`/anomalies`),
  trace: (traceId: string) => getJson<{ events: TraceEvent[] }>(`/traces/${traceId}`),
};

export { ApiError };
