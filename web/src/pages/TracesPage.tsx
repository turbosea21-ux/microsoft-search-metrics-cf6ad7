// Trace explorer: look up a trace_id and inspect each captured event in it.
import { useState } from 'react';
import { api, TraceEvent } from '../api/client';
import { ErrorBanner } from '../components/ErrorBanner';

export function TracesPage() {
  const [traceId, setTraceId] = useState('');
  const [events, setEvents] = useState<TraceEvent[]>([]);
  const [error, setError] = useState<unknown>(null);

  async function lookup() {
    setError(null);
    setEvents([]);
    try {
      const res = await api.trace(traceId.trim());
      setEvents(res.events);
    } catch (e) {
      setError(e);
    }
  }

  return (
    <section>
      <h2>Trace explorer</h2>
      <input
        value={traceId}
        placeholder="trace_id"
        onChange={(e) => setTraceId(e.target.value)}
      />
      <button onClick={lookup} disabled={!traceId.trim()}>Look up</button>
      <ErrorBanner error={error} />
      {events.map((ev) => (
        <div key={ev.request_id} className="trace-event">
          <code>{ev.service}{ev.endpoint}</code> — {ev.status_code}{' '}
          ({ev.error_type ?? 'ok'}), {ev.latency_ms} ms
          {ev.error_message && <div className="muted">{ev.error_message}</div>}
        </div>
      ))}
    </section>
  );
}
