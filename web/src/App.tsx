// Dashboard shell: three tabs over the three core views.
import { useState } from 'react';
import { MetricsPage } from './pages/MetricsPage';
import { AnomaliesPage } from './pages/AnomaliesPage';
import { TracesPage } from './pages/TracesPage';

type Tab = 'metrics' | 'anomalies' | 'traces';

export default function App() {
  const [tab, setTab] = useState<Tab>('metrics');
  return (
    <div className="app">
      <nav>
        <button onClick={() => setTab('metrics')} aria-pressed={tab === 'metrics'}>Metrics</button>
        <button onClick={() => setTab('anomalies')} aria-pressed={tab === 'anomalies'}>Anomalies</button>
        <button onClick={() => setTab('traces')} aria-pressed={tab === 'traces'}>Traces</button>
      </nav>
      <main>
        {tab === 'metrics' && <MetricsPage />}
        {tab === 'anomalies' && <AnomaliesPage />}
        {tab === 'traces' && <TracesPage />}
      </main>
    </div>
  );
}
