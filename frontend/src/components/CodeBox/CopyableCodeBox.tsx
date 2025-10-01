import { useState } from 'react';

export default function CopyableCodeBox({ value, filename }: { value: string; filename?: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <div className="rounded-lg border border-neutral-200 overflow-hidden bg-white">
      <div className="flex items-center justify-between gap-2 px-3 py-2 border-b border-neutral-200 bg-neutral-50">
        <span className="text-xs text-neutral-600 select-none">{filename || 'output.txt'}</span>
        <button
          onClick={async () => {
            await navigator.clipboard.writeText(value || '');
            setCopied(true);
            setTimeout(() => setCopied(false), 1200);
          }}
          className="text-xs px-2 py-1 rounded-md bg-neutral-900 text-white hover:bg-neutral-800"
        >
          {copied ? 'Скопировано' : 'Копировать'}
        </button>
      </div>
      <pre className="bg-white text-neutral-800 p-3 overflow-auto">{value}</pre>
    </div>
  );
}


