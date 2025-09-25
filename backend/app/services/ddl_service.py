from app.schemas.ddl import DDLRequest, DDLResponse


def _infer_sql_type(py_type: str, target: str) -> str:
    mapping_pg = {
        "int": "INTEGER",
        "float": "DOUBLE PRECISION",
        "string": "TEXT",
        "bool": "BOOLEAN",
        "timestamp": "TIMESTAMP",
        "date": "DATE",
    }
    mapping_ch = {
        "int": "Int64",
        "float": "Float64",
        "string": "String",
        "bool": "UInt8",
        "timestamp": "DateTime",
        "date": "Date",
    }
    mapping_hive = {
        "int": "BIGINT",
        "float": "DOUBLE",
        "string": "STRING",
        "bool": "BOOLEAN",
        "timestamp": "TIMESTAMP",
        "date": "DATE",
    }
    if target == "postgres":
        return mapping_pg.get(py_type, "TEXT")
    if target == "clickhouse":
        return mapping_ch.get(py_type, "String")
    return mapping_hive.get(py_type, "STRING")


async def generate_ddl(req: DDLRequest) -> DDLResponse:
    sample_cols = req.sample.get("columns", [])
    cols_rendered: list[str] = []
    for c in sample_cols:
        name = c.get("name", "col")
        dtype = c.get("dtype", "string")
        sql_type = _infer_sql_type(dtype, req.target_system)
        cols_rendered.append(f"{name} {sql_type}")

    ddl = ""
    suggestions: list[str] = []
    if req.target_system == "postgres":
        ddl = f"CREATE TABLE IF NOT EXISTS {req.table_name} (\n  " + ",\n  ".join(cols_rendered) + "\n);"
        suggestions.append("Индексы на часто фильтруемые поля")
    elif req.target_system == "clickhouse":
        ddl = (
            f"CREATE TABLE IF NOT EXISTS {req.table_name} (\n  "
            + ",\n  ".join(cols_rendered)
            + "\n) ENGINE = MergeTree()\nPARTITION BY toDate(ts)\nORDER BY (ts);"
        )
        suggestions.append("Партицирование по дате для временных данных")
    else:
        ddl = f"CREATE TABLE {req.table_name} (" + ", ".join(cols_rendered) + ")"  # Hive/HDFS via Hive
        suggestions.append("Хранение сырых данных в колоннарном формате")

    return DDLResponse(ddl_sql=ddl, suggestions=suggestions)


