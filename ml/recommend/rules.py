# ml/recommend/rules.py
def _count_types(schema):
    n_num = sum(1 for c in schema if any(str(c["dtype"]).startswith(t) for t in ("int","float","decimal")))
    n_dt  = sum(1 for c in schema if "datetime" in str(c["dtype"]).lower()
                or "date" in str(c["column"]).lower()
                or "time" in str(c["column"]).lower())
    return n_num, n_dt

def choose_store(profile: dict, prefs: dict) -> str:
    rows = int(profile["checks"]["rows"])
    has_time = bool(profile["checks"].get("has_time", False))
    n_num, n_dt = _count_types(profile["schema"])
    mode = (prefs or {}).get("mode")
    if mode == "oltp": return "postgres"
    if rows >= 5_000_000: return "hdfs"
    if rows >= 1_000_000 or has_time or n_dt > 0: return "clickhouse"
    return "postgres"

def ddl_hints(profile: dict, prefs: dict) -> dict:
    cols = [c["column"] for c in profile["schema"]]
    pk = (prefs or {}).get("primary_key") or ("id" if any(c.lower()=="id" for c in cols) else None)
    date_col = next((c for c in cols if "date" in c.lower() or "time" in c.lower()), None)
    return {
        "primary_key": pk,
        "partition_by": date_col,
        "order_by": [pk] if pk else ([date_col] if date_col else cols[:1]),
        "table_name": (prefs or {}).get("table_name","data"),
    }
