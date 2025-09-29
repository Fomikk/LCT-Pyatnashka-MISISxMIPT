from app.schemas.analysis import (
    SourceInput,
    DataProfile,
    ColumnProfile,
    FileAnalysisRequest,
    DBAnalysisRequest,
)
from app.connectors.file_connector import FileConnector
from app.connectors.database_connector import PostgresConnector, ClickHouseConnector


async def analyze_source(payload: SourceInput) -> DataProfile:
    # Заглушка: простая эвристика на основе sample
    columns: list[ColumnProfile] = []
    sample = payload.sample or {}
    if isinstance(sample, dict) and sample.get("columns"):
        for c in sample["columns"]:
            columns.append(
                ColumnProfile(
                    name=c.get("name", "col"),
                    dtype=c.get("dtype", "string"),
                    nullable=bool(c.get("nullable", True)),
                    example=c.get("example"),
                )
            )
    else:
        # Fallback
        columns = [
            ColumnProfile(name="id", dtype="int", nullable=False, example=1),
            ColumnProfile(name="ts", dtype="timestamp", nullable=False, example="2025-01-01T00:00:00Z"),
        ]

    is_ts = any(c.dtype in {"timestamp", "date"} or c.name in {"ts", "created_at"} for c in columns)

    return DataProfile(rows=sample.get("rows", 1000), columns=columns, is_time_series=is_ts)


async def analyze_file(req: FileAnalysisRequest) -> DataProfile:
    meta = await FileConnector.analyze_file(req.file_path, req.file_type, req.connection)
    columns = [
        ColumnProfile(
            name=c.get("name", "col"),
            dtype=str(c.get("dtype", "string")),
            nullable=bool(c.get("nullable", True)),
            example=c.get("example"),
        )
        for c in meta.get("columns", [])
    ]
    is_ts = any(c.name in {"ts", "timestamp", "created_at"} or c.dtype in {"datetime64[ns]", "timestamp", "date"} for c in columns)
    return DataProfile(
        rows=int(meta.get("rows", 0)),
        columns=columns,
        is_time_series=is_ts,
        sample_data=meta.get("sample_data"),
    )


async def analyze_db(req: DBAnalysisRequest) -> DataProfile:
    if req.db_type == "postgres":
        pg = PostgresConnector(req.connection.get("dsn"))
        meta = await pg.sample_table_schema(req.table)
    elif req.db_type == "clickhouse":
        ch = ClickHouseConnector(
            host=req.connection.get("host"),
            port=req.connection.get("port"),
            user=req.connection.get("user"),
            password=req.connection.get("password"),
            database=req.connection.get("database"),
        )
        meta = await ch.sample_table_schema(req.table)
    else:
        raise ValueError("Unsupported db_type")

    columns = [
        ColumnProfile(
            name=c.get("name", "col"),
            dtype=str(c.get("dtype", "string")),
            nullable=bool(c.get("nullable", True)),
        )
        for c in meta.get("columns", [])
    ]
    is_ts = any(c.name in {"ts", "timestamp", "created_at"} or c.dtype.lower() in {"timestamp", "date", "datetime"} for c in columns)
    return DataProfile(rows=0, columns=columns, is_time_series=is_ts)


