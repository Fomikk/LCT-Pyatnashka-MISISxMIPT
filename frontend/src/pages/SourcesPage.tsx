import { useState } from 'react';
import FileUploader from '../components/FileUploader/FileUploader';
import { api } from '../api/client';

export default function SourcesPage() {
  const [preview, setPreview] = useState<string[] | null>(null);
  const [filePath, setFilePath] = useState('');
  const [fileType, setFileType] = useState<'csv' | 'json' | 'xml'>('csv');
  const [profile, setProfile] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  return (
    <div className="p-6 bg-white rounded-xl border border-neutral-200 shadow-sm">
      <h2 className="text-xl mb-3 font-semibold text-neutral-900">Загрузка источника данных</h2>
      <FileUploader onPreview={setPreview} />
      {preview && (
        <div className="mt-4">
          <div className="font-medium mb-2">Предпросмотр первых строк:</div>
          <pre style={{
            maxHeight: 280,
            overflow: 'auto',
            background: '#0b0b0b',
            color: '#e6e6e6',
            padding: 12,
            borderRadius: 8,
          }}>{preview.join('\n')}</pre>
        </div>
      )}

      <div className="mt-6">
        <h3 className="text-lg mb-2 font-medium text-neutral-900">Профилирование файла по пути (бэкенд /analysis/file)</h3>
        <div className="flex gap-2 items-center flex-wrap">
          <input
            placeholder="Путь до файла (на сервере)"
            value={filePath}
            onChange={(e) => setFilePath(e.target.value)}
            className="px-3 py-2 min-w-72 bg-white border border-neutral-300 rounded-md shadow-sm"
          />
          <select value={fileType} onChange={(e) => setFileType(e.target.value as any)} className="px-3 py-2 bg-white border border-neutral-300 rounded-md shadow-sm">
            <option value="csv">csv</option>
            <option value="json">json</option>
            <option value="xml">xml</option>
          </select>
          <button
            onClick={async () => {
              setError(null);
              setLoading(true);
              setProfile(null);
              try {
                const res = await api.post<any>('/api/v1/analysis/file', {
                  file_path: filePath,
                  file_type: fileType,
                  connection: {},
                });
                setProfile(res);
              } catch (e: any) {
                setError(e.message);
              } finally {
                setLoading(false);
              }
            }}
            className="px-3 py-2 rounded-md bg-neutral-900 text-white hover:bg-neutral-800 transition-colors"
          >
            Профилировать
          </button>
        </div>
        {loading && <div className="mt-2 text-sm text-neutral-500">Запрос...</div>}
        {error && <div className="mt-2 text-sm text-red-600">{error}</div>}
        {profile && (
          <pre className="mt-3 bg-neutral-50 text-neutral-800 p-3 rounded-lg border border-neutral-200 overflow-auto">
            {JSON.stringify(profile, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}
