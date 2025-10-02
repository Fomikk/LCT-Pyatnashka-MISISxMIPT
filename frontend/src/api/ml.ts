const API = import.meta.env.VITE_API_BASE;

export type Profile = {
  source: { type: 'file'|'postgres'|'clickhouse'|'hdfs'; format?: 'csv'|'json'|'xml'; name?: string };
  preview?: any[];
  schema: { column: string; dtype: string; nulls: number; uniques: number }[];
  checks: { has_time: boolean; rows: number; cols: number };
};

export type UserPrefs = { mode?: 'oltp'|'olap'; latency_sla?: 'hour'|'day'|'week'; primary_key?: string; table_name?: string };

export type Recommendation = {
  target_store: 'postgres'|'clickhouse'|'hdfs';
  ddl_hints: { primary_key: string; partition_by: string|null; order_by: string[]; table_name: string };
  pipeline: { dag: { op:'Extract'|'FilterByDate'|'Load'; params:any }[] };
  schedule: { cron: string; reason: string };
  risks: string[];
};

export async function apiRecommend(profile: Profile, user_prefs: UserPrefs) {
  const r = await fetch(`${API}/ml/recommend`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ profile, user_prefs })
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json() as Promise<Recommendation>;
}

export async function apiDDL(inp: { target_store: Recommendation['target_store']; ddl_hints: Recommendation['ddl_hints']; profile: Pick<Profile,'schema'>; }) {
  const r = await fetch(`${API}/ml/ddl`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(inp)
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json() as Promise<{ sql: string }>;
}

export async function apiReport(recommendation: Recommendation, profile: Pick<Profile,'source'|'checks'>) {
  const r = await fetch(`${API}/ml/report`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ recommendation, profile })
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json() as Promise<{ report: string }>;
}
