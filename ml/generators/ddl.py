# ml/generators/ddl.py
from __future__ import annotations
from typing import Dict, Any

def ddl_postgres(table: str, columns: Dict[str, str], pk: str | None) -> str:
    cols = []
    for name, dtype in columns.items():
        pg = "TEXT"
        if dtype.startswith(("int", "Int")): pg = "BIGINT"
        elif dtype.startswith(("float", "Float", "double")): pg = "DOUBLE PRECISION"
        elif "datetime" in dtype or "date" in dtype: pg = "TIMESTAMP"
        cols.append(f'"{name}" {pg}')
    if pk: cols.append(f'PRIMARY KEY ("{pk}")')
    return f'CREATE TABLE IF NOT EXISTS "{table}" (\n  ' + ",\n  ".join(cols) + "\n);"

def ddl_clickhouse(table: str, columns: Dict[str, str], order_by: list[str], partition_by: str | None) -> str:
    cols = []
    for name, dtype in columns.items():
        ch = "String"
        if dtype.startswith(("int", "Int")): ch = "Int64"
        elif dtype.startswith(("float", "Float", "double")): ch = "Float64"
        elif "datetime" in dtype or "date" in dtype: ch = "DateTime"
        cols.append(f'`{name}` {ch}')
    order = ", ".join(f'`{c}`' for c in (order_by or ["tuple()"]))
    part  = f"PARTITION BY toYYYYMM(`{partition_by}`)" if partition_by else ""
    return (
        f"CREATE TABLE IF NOT EXISTS `{table}` (\n  " + ",\n  ".join(cols) + "\n)\n"
        f"ENGINE = MergeTree\n"
        f"{part}\n"
        f"ORDER BY ({order});"
    )

def generate_ddl(target_store: str, profile: Dict[str, Any], hints: Dict[str, Any]) -> str:
    table = hints.get("table_name", "data")
    # соберём колонki и dtype из профайла
    columns = {c["column"]: c["dtype"] for c in profile.get("schema", [])}
    if target_store == "postgres":
        return ddl_postgres(table, columns, hints.get("primary_key"))
    else:
        return ddl_clickhouse(table, columns, hints.get("order_by", []), hints.get("partition_by"))
