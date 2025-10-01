import { useMemo, useState } from 'react';
import { api } from '../api/client';
import OptionalReactFlow from '../components/GraphPreview/OptionalReactFlow';
import CopyableCodeBox from '../components/CodeBox/CopyableCodeBox';

type Step = 'source' | 'preview' | 'recommend' | 'ddl' | 'pipeline' | 'done';

export default function AssistantPage() {
  const [step, setStep] = useState<Step>('source');
  const [filePath, setFilePath] = useState('');
  const [fileType, setFileType] = useState<'csv' | 'json' | 'xml'>('csv');
  const [profile, setProfile] = useState<any | null>(null);
  const [recommendation, setRecommendation] = useState<any | null>(null);
  const [ddl, setDdl] = useState<any | null>(null);
  const [draft, setDraft] = useState<any | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const profileSummary = useMemo(() => {
    if (!profile) return '';
    const cols = (profile.columns || []).map((c: any) => `${c.name}:${c.dtype}`).join(', ');
    return `rows=${profile.rows}; columns=[${cols}]; timeseries=${profile.is_time_series}`;
  }, [profile]);

  return (
    <div className="p-6 bg-white rounded-xl border border-neutral-200 shadow-sm" style={{ maxWidth: 1200, margin: '0 auto' }}>
      <h2 className="text-xl mb-3 font-semibold text-neutral-900">Мастер настройки загрузки</h2>
      <Steps value={step} onChange={setStep} />

      {step === 'source' && (
        <section className="mt-4">
          <div className="mb-2">Укажите путь к файлу на сервере и его тип</div>
          <div className="flex gap-2 flex-wrap items-center">
            <input placeholder="/path/to/data.csv" value={filePath} onChange={(e) => setFilePath(e.target.value)} className="px-3 py-2 min-w-72 bg-white border border-neutral-300 rounded-md shadow-sm" />
            <select value={fileType} onChange={(e) => setFileType(e.target.value as any)} className="px-3 py-2 bg-white border border-neutral-300 rounded-md shadow-sm">
              <option value="csv">csv</option>
              <option value="json">json</option>
              <option value="xml">xml</option>
            </select>
            <button
              onClick={async () => {
                setError(null);
                setBusy(true);
                try {
                  const res = await api.post<any>('/api/v1/analysis/file', {
                    file_path: filePath,
                    file_type: fileType,
                    connection: {},
                  });
                  setProfile(res);
                  setStep('preview');
                } catch (e: any) {
                  setError(e.message);
                } finally {
                  setBusy(false);
                }
              }}
              className="px-3 py-2 rounded-md bg-neutral-900 text-white hover:bg-neutral-800 transition-colors"
            >
              Профилировать
            </button>
          </div>
          {busy && <div className="mt-2 text-sm text-neutral-500">Запрос...</div>}
          {error && <div className="mt-2 text-sm text-red-600">{error}</div>}
        </section>
      )}

      {step === 'preview' && (
        <section className="mt-4">
          <div className="font-medium mb-2">Превью и метрики</div>
          <pre className="bg-neutral-50 text-neutral-800 p-3 rounded-lg border border-neutral-200 overflow-auto">
            {JSON.stringify(profile, null, 2)}
          </pre>
          <div className="mt-3 flex gap-2">
            <button onClick={() => setStep('source')} className="px-3 py-2 rounded-md bg-neutral-900 text-white hover:bg-neutral-800 transition-colors">Назад</button>
            <button
              onClick={async () => {
                setError(null);
                setBusy(true);
                try {
                  const res = await api.post<any>('/api/v1/recommend/storage', {
                    profile_summary: profileSummary,
                    workload: 'analytical',
                  });
                  setRecommendation(res);
                  setStep('recommend');
                } catch (e: any) {
                  setError(e.message);
                } finally {
                  setBusy(false);
                }
              }}
              className="px-3 py-2 rounded-md bg-neutral-900 text-white hover:bg-neutral-800 transition-colors"
            >
              Получить рекомендацию хранилища
            </button>
          </div>
          {busy && <div className="mt-2 text-sm text-neutral-500">Запрос...</div>}
          {error && <div className="mt-2 text-sm text-red-600">{error}</div>}
        </section>
      )}

      {step === 'recommend' && (
        <section className="mt-4">
          <div className="font-medium mb-2">Рекомендации ассистента</div>
          <pre className="bg-neutral-50 text-neutral-800 p-3 rounded-lg border border-neutral-200 overflow-auto">
            {JSON.stringify(recommendation, null, 2)}
          </pre>
          <div className="mt-3 flex gap-2">
            <button onClick={() => setStep('preview')} className="px-3 py-2 rounded-md bg-neutral-900 text-white hover:bg-neutral-800 transition-colors">Назад</button>
            <button
              onClick={async () => {
                setError(null);
                setBusy(true);
                try {
                  const res = await api.post<any>('/api/v1/ddl/generate', {
                    target_system: recommendation?.storage || 'postgres',
                    table_name: 'public.recommended_table',
                    sample: { profile_summary: profileSummary },
                  });
                  setDdl(res);
                  setStep('ddl');
                } catch (e: any) {
                  setError(e.message);
                } finally {
                  setBusy(false);
                }
              }}
              className="px-3 py-2 rounded-md bg-neutral-900 text-white hover:bg-neutral-800 transition-colors"
            >
              Сгенерировать DDL
            </button>
          </div>
          {busy && <div className="mt-2 text-sm text-neutral-500">Запрос...</div>}
          {error && <div className="mt-2 text-sm text-red-600">{error}</div>}
        </section>
      )}

      {step === 'ddl' && (
        <section className="mt-4">
          <div className="font-medium mb-2">DDL скрипт</div>
          <CopyableCodeBox value={ddl?.ddl_sql || ''} filename="schema.sql" />
          <div className="mt-3 flex gap-2">
            <button onClick={() => setStep('recommend')} className="px-3 py-2 rounded-md bg-neutral-900 text-white hover:bg-neutral-800 transition-colors">Назад</button>
            <button onClick={() => setStep('pipeline')} className="px-3 py-2 rounded-md bg-neutral-900 text-white hover:bg-neutral-800 transition-colors">Далее к пайплайну</button>
          </div>
        </section>
      )}

      {step === 'pipeline' && (
        <section className="mt-4">
          <div className="font-medium mb-2">Черновик и запуск пайплайна</div>
          <div className="flex gap-2 flex-wrap items-center">
            <button
              onClick={async () => {
                setError(null);
                setBusy(true);
                try {
                  const res = await api.post<any>('/api/v1/pipelines/draft', {
                    source: { file_path: filePath, file_type: fileType },
                    destination: { storage: recommendation?.storage || 'postgres' },
                    transform: {},
                    schedule_cron: recommendation?.refresh_cron || '0 12 * * *',
                  });
                  setDraft(res);
                } catch (e: any) {
                  setError(e.message);
                } finally {
                  setBusy(false);
                }
              }}
              className="px-3 py-2 rounded-md bg-neutral-900 text-white hover:bg-neutral-800 transition-colors"
            >
              Сформировать черновик DAG
            </button>
            <button
              disabled={!draft}
              onClick={async () => {
                if (!draft) return;
                setError(null);
                setBusy(true);
                try {
                  await api.post<any>('/api/v1/pipelines/publish', {
                    source: { file_path: filePath, file_type: fileType },
                    destination: { storage: recommendation?.storage || 'postgres' },
                    transform: {},
                    schedule_cron: recommendation?.refresh_cron || '0 12 * * *',
                  });
                  setStep('done');
                } catch (e: any) {
                  setError(e.message);
                } finally {
                  setBusy(false);
                }
              }}
              className="px-3 py-2 rounded-md bg-neutral-900 text-white hover:bg-neutral-800 transition-colors disabled:opacity-50"
            >
              Опубликовать DAG
            </button>
          </div>
          {draft && (
            <div className="mt-3">
              <div className="mb-2">Сгенерированный DAG</div>
              <CopyableCodeBox value={draft.dag_code} filename={`${draft?.dag_id || 'pipeline'}.py`} />
              <div className="mt-3">
                <div className="mb-2">Визуализация графа</div>
                <OptionalReactFlow graph={draft.preview_graph} />
              </div>
            </div>
          )}
          {busy && <div className="mt-2 text-sm text-neutral-500">Запрос...</div>}
          {error && <div className="mt-2 text-sm text-red-600">{error}</div>}
        </section>
      )}

      {step === 'done' && (
        <section className="mt-4">
          <div className="text-lg">Всё настроено! Загрузка начнётся по расписанию.</div>
        </section>
      )}
    </div>
  );
}

function Steps({ value, onChange }: { value: Step; onChange: (s: Step) => void }) {
  const list: Step[] = ['source', 'preview', 'recommend', 'ddl', 'pipeline', 'done'];
  return (
    <div className="flex flex-wrap gap-2">
      {list.map((s, idx) => (
        <div key={s} className="flex items-center gap-2">
          <button
            onClick={() => onChange(s)}
            className={`px-3 py-1 rounded-md border ${s === value ? 'bg-neutral-200 border-neutral-300' : 'bg-white border-neutral-200 hover:bg-neutral-100'}`}
          >
            {labelOf(s)}
          </button>
          {idx < list.length - 1 && <span className="text-neutral-400">→</span>}
        </div>
      ))}
    </div>
  );
}

function labelOf(s: Step): string {
  switch (s) {
    case 'source': return 'Источник';
    case 'preview': return 'Превью';
    case 'recommend': return 'Рекомендация';
    case 'ddl': return 'DDL';
    case 'pipeline': return 'Пайплайн';
    case 'done': return 'Готово';
  }
}

function CodeBox({ value }: { value: string }) {
  return (
    <pre style={{
      whiteSpace: 'pre-wrap',
      background: '#0b0b0b',
      color: '#e6e6e6',
      padding: 12,
      borderRadius: 8,
      maxHeight: 360,
      overflow: 'auto',
    }}>{value}</pre>
  );
}


