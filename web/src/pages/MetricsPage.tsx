// Metrics overview: latency p50/p95 and error rate over the last hour for a
// service/endpoint, with loading and error states and a 30s auto-refresh.
import { useEffect, useState } from 'react';
import { api, MetricWindow } from '../api/client';
import { ErrorBanner } from '../components/ErrorBanner';

const SERVICE = 'query-frontend';
const ENDPOINT = '/search';

export function MetricsPage() {
  const [windows, setWindows] = useState<MetricWindow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    let alive = true;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const end = new Date();
        const start = new Date(end.getTime() - 60 * 60 * 1000); // last 1h
        const res = await api.metrics(SERVICE, ENDPOINT, start.toISOString(), end.toISOString());
        if (alive) setWindows(res.windows);
      } catch (e) {
        if (alive) setError(e);
      } finally {
        if (alive) setLoading(false);
      }
    }
    load();
    const timer = setInterval(load, 30_000); // auto-refresh
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, []);

  if (loading && windows.length === 0) return <p>Loading metrics…</p>;

  return (
    <section>
      <h2>{SERVICE} {ENDPOINT}</h2>
      <ErrorBanner error={error} />
      <table>
        <thead>
          <tr><th>Window</th><th>Requests</th><th>Error rate</th><th>p50</th><th>p95</th></tr>
        </thead>
        <tbody>
          {windows.map((w) => (
            <tr key={w.window_start}>
              <td>{new Date(w.window_start).toLocaleTimeString()}</td>
              <td>{w.request_count}</td>
              <td>{(w.error_rate * 100).toFixed(1)}%</td>
              <td>{w.p50_latency_ms} ms</td>
              <td>{w.p95_latency_ms} ms</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
