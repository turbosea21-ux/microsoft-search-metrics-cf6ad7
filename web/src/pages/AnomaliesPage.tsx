// Anomalies list: recent flagged windows, each linking the operator toward the
// trace explorer for the affected service.
import { useEffect, useState } from 'react';
import { api, Anomaly } from '../api/client';
import { ErrorBanner } from '../components/ErrorBanner';

export function AnomaliesPage() {
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    api.anomalies().then((r) => setAnomalies(r.anomalies)).catch(setError);
  }, []);

  return (
    <section>
      <h2>Anomalies</h2>
      <ErrorBanner error={error} />
      <ul>
        {anomalies.map((a) => (
          <li key={`${a.window_start}-${a.service}-${a.kind}`}>
            <strong>{a.kind}</strong> on {a.service}{a.endpoint} —{' '}
            observed {a.observed.toFixed(2)} vs baseline {a.baseline.toFixed(2)}
          </li>
        ))}
      </ul>
    </section>
  );
}
