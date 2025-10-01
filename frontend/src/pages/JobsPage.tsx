import { useState } from 'react';
import { api } from '../api/client';

export default function JobsPage() {
  const [dagId, setDagId] = useState('example_dag');
  const [status, setStatus] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  return (
    <div className="p-6 bg-white rounded-xl border border-neutral-200 shadow-sm">
      <h2 className="text-xl mb-3 font-semibold text-neutral-900">Запуски (Airflow)</h2>
      <div className="flex gap-2 items-center flex-wrap">
        <input value={dagId} onChange={(e) => setDagId(e.target.value)} className="px-3 py-2 bg-white border border-neutral-300 rounded-md shadow-sm" />
        <button
          onClick={async () => {
            setError(null);
            setLoading(true);
            setStatus(null);
            try {
              const res = await api.get<any>(`/api/v1/pipelines/status/${encodeURIComponent(dagId)}`);
              setStatus(res);
            } catch (e: any) {
              setError(e.message);
            } finally {
              setLoading(false);
            }
          }}
          className="px-3 py-2 rounded-md bg-neutral-900 text-white hover:bg-neutral-800 transition-colors"
        >
          Получить статус DAG
        </button>
      </div>
      {loading && <div className="mt-2 text-sm text-neutral-500">Запрос...</div>}
      {error && <div className="mt-2 text-sm text-red-600">{error}</div>}
      {status && (
        <pre className="mt-3 bg-neutral-50 text-neutral-800 p-3 rounded-lg border border-neutral-200 overflow-auto">
          {JSON.stringify(status, null, 2)}
        </pre>
      )}
    </div>
  );
}
