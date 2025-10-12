import { useState } from 'react';

type Props = { onPreview: (lines: string[]) => void };

export default function FileUploader({ onPreview }: Props) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  return (
    <div className="border border-neutral-200 bg-white rounded-xl p-4 space-y-3">
      <input
        type="file"
        accept=".csv,.json,.xml"
        onChange={async (e) => {
          setError(null);
          const file = e.target.files?.[0];
          if (!file) return;
          try {
            setBusy(true);
            const text = await file.text();
            const lines = text.split(/\r?\n/).slice(0, 30);
            onPreview(lines);
          } catch (err: any) {
            setError(err?.message ?? 'Не удалось прочитать файл');
          } finally {
            setBusy(false);
          }
        }}
      />
      {busy && <div className="text-sm text-neutral-500">Загрузка...</div>}
      {error && <div className="text-sm text-red-600">{error}</div>}
    </div>
  );
}
