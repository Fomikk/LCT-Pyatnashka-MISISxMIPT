import { useState } from 'react';
import { api } from '../api/client';
import OptionalReactFlow from '../components/GraphPreview/OptionalReactFlow';

export default function PipelinePage() {
  const [source, setSource] = useState('{"type":"file","path":"/data/sample.csv"}');
  const [destination, setDestination] = useState('{"type":"postgres","table":"public.out"}');
  const [cron, setCron] = useState('0 12 * * *');
  const [draft, setDraft] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  return (
    <div className="p-6 bg-white rounded-xl border border-neutral-200 shadow-sm">
      <h2 className="text-xl mb-3 font-semibold text-neutral-900">Проектирование пайплайна</h2>
      <div className="grid gap-2" style={{ gridTemplateColumns: '1fr 1fr' }}>
        <div>
          <div className="mb-1">Источник (JSON)</div>
          <textarea value={source} onChange={(e) => setSource(e.target.value)} rows={6} className="w-full p-2 bg-white border border-neutral-300 rounded-md shadow-sm" />
        </div>
        <div>
          <div className="mb-1">Приёмник (JSON)</div>
          <textarea value={destination} onChange={(e) => setDestination(e.target.value)} rows={6} className="w-full p-2 bg-white border border-neutral-300 rounded-md shadow-sm" />
        </div>
      </div>
      <div className="mt-3 flex gap-2 items-center flex-wrap">
        <input value={cron} onChange={(e) => setCron(e.target.value)} className="px-3 py-2 min-w-52 bg-white border border-neutral-300 rounded-md shadow-sm" />
        <button
          onClick={async () => {
            setError(null);
            setLoading(true);
            setDraft(null);
            try {
              const body = {
                source: JSON.parse(source),
                destination: JSON.parse(destination),
                transform: {},
                schedule_cron: cron,
              };
              const res = await api.post<any>('/api/v1/pipelines/draft', body);
              setDraft(res);
            } catch (e: any) {
              setError(e.message);
            } finally {
              setLoading(false);
            }
          }}
          className="px-3 py-2 rounded-md bg-neutral-900 text-white hover:bg-neutral-800 transition-colors"
        >
          Сформировать черновик DAG
        </button>
      </div>
      {loading && <div className="mt-2 text-sm text-neutral-500">Запрос...</div>}
      {error && <div className="mt-2 text-sm text-red-600">{error}</div>}
      {draft && (
        <>
          <pre className="mt-3 bg-neutral-50 text-neutral-800 p-3 rounded-lg border border-neutral-200 overflow-auto">
            {JSON.stringify(draft, null, 2)}
          </pre>
          <div className="mt-3">
            <div className="mb-2">Визуализация графа</div>
            <OptionalReactFlow graph={draft.preview_graph} />
          </div>
        </>
      )}
    </div>
  );
}
