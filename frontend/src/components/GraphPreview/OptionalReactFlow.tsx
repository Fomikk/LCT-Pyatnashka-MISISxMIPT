import { useEffect, useMemo, useState } from 'react';

type Graph = {
  nodes?: Array<{ id: string; label?: string; position?: { x: number; y: number } } & Record<string, any>>;
  edges?: Array<{ id?: string; source: string; target: string } & Record<string, any>>;
};

type Props = {
  graph: Graph | null | undefined;
  height?: number;
};

export default function OptionalReactFlow({ graph, height = 420 }: Props) {
  const [rf, setRf] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const mod = await import('reactflow');
        await import('reactflow/dist/style.css');
        if (!cancelled) setRf(mod);
      } catch (e: any) {
        if (!cancelled) setError(e?.message || 'React Flow недоступен');
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const { nodes, edges } = useMemo(() => normalizeGraph(graph), [graph]);

  if (error) {
    return (
      <div className="p-3 rounded-lg border border-neutral-200 bg-neutral-50">
        <div className="mb-1 text-neutral-700">Для визуализации графа установите зависимость:</div>
        <pre className="bg-white text-neutral-800 p-2 rounded-md border border-neutral-200">npm i reactflow</pre>
      </div>
    );
  }

  if (!rf) {
    return <div style={{ padding: 12, color: '#aaa' }}>Загрузка визуализации...</div>;
  }

  const { default: ReactFlow, Background, Controls, MiniMap } = rf;
  return (
    <div style={{ height }} className="rounded-lg overflow-hidden border border-neutral-200 bg-white">
      <ReactFlow nodes={nodes} edges={edges} fitView>
        <Background />
        <MiniMap />
        <Controls />
      </ReactFlow>
    </div>
  );
}

function normalizeGraph(graph?: Graph | null) {
  const nodes = (graph?.nodes ?? []).map((n, idx, arr) => {
    const pos = n.position ?? autoPosition(idx, arr.length);
    return {
      id: n.id,
      position: pos,
      data: { label: n.label ?? n.id },
      ...n,
    };
  });
  const edges = (graph?.edges ?? []).map((e, i) => ({ id: e.id ?? `e${i}`, source: e.source, target: e.target, ...e }));
  return { nodes, edges };
}

function autoPosition(index: number, total: number) {
  const angle = (index / Math.max(total, 1)) * Math.PI * 2;
  const radius = 150 + (index % 5) * 10;
  return { x: Math.cos(angle) * radius + 200, y: Math.sin(angle) * radius + 160 };
}


