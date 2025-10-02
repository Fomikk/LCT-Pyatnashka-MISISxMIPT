from app.schemas.analysis import (
    SourceInput,
    DataProfile,
    ColumnProfile,
    DataQualityMetrics,
    FileAnalysisRequest,
    DBAnalysisRequest,
)
from app.connectors.file_connector import FileConnector
from app.connectors.database_connector import PostgresConnector, ClickHouseConnector
from app.services.cache_service import cache_analysis


async def analyze_source(payload: SourceInput) -> DataProfile:
    """Анализ источника данных с расширенной логикой"""
    columns: list[ColumnProfile] = []
    sample = payload.sample or {}
    
    if isinstance(sample, dict) and sample.get("columns"):
        for c in sample["columns"]:
            # Расширенная информация о колонке
            column_info = {
                "name": c.get("name", "col"),
                "dtype": c.get("dtype", "string"),
                "nullable": bool(c.get("nullable", True)),
                "example": c.get("example"),
            }
            
            # Добавляем дополнительную статистику если есть
            if "unique_count" in c:
                column_info["unique_count"] = c["unique_count"]
            if "null_count" in c:
                column_info["null_count"] = c["null_count"]
            if "null_percentage" in c:
                column_info["null_percentage"] = c["null_percentage"]
            if "numeric_stats" in c:
                column_info["numeric_stats"] = c["numeric_stats"]
            
            columns.append(ColumnProfile(**column_info))
    else:
        # Fallback с более умными значениями по умолчанию
        columns = [
            ColumnProfile(
                name="id", 
                dtype="int", 
                nullable=False, 
                example=1,
                unique_count=1000,
                null_count=0,
                null_percentage=0.0
            ),
            ColumnProfile(
                name="ts", 
                dtype="timestamp", 
                nullable=False, 
                example="2025-01-01T00:00:00Z",
                unique_count=1000,
                null_count=0,
                null_percentage=0.0
            ),
        ]

    # Улучшенное определение временных рядов
    is_ts = any(
        c.dtype in {"timestamp", "date", "datetime64[ns]", "datetime"} or 
        c.name.lower() in {"ts", "timestamp", "created_at", "updated_at", "date", "time"} or
        "time" in c.name.lower() or "date" in c.name.lower()
        for c in columns
    )

    # Дополнительный анализ данных
    data_quality = _analyze_data_quality_advanced(columns, sample.get("rows", 1000))
    
    return DataProfile(
        rows=sample.get("rows", 1000), 
        columns=columns, 
        is_time_series=is_ts,
        data_quality=data_quality
    )


def _analyze_data_quality_advanced(columns: list[ColumnProfile], total_rows: int) -> dict:
    """Расширенный анализ качества данных"""
    if total_rows == 0:
        return {
            "completeness_score": 0.0,
            "consistency_score": 0.0,
            "uniqueness_score": 0.0,
            "issues": ["Нет данных для анализа"]
        }
    
    issues = []
    completeness_scores = []
    uniqueness_scores = []
    
    for col in columns:
        # Анализ полноты
        null_pct = getattr(col, 'null_percentage', 0.0)
        completeness_scores.append(max(0, 100 - null_pct))
        
        if null_pct > 50:
            issues.append(f"Колонка '{col.name}' содержит {null_pct:.1f}% пустых значений")
        
        # Анализ уникальности
        unique_count = getattr(col, 'unique_count', 0)
        if total_rows > 0:
            unique_ratio = unique_count / total_rows
            uniqueness_scores.append(min(100, unique_ratio * 100))
            
            if unique_count == total_rows and total_rows > 1:
                issues.append(f"Колонка '{col.name}' содержит только уникальные значения")
            elif unique_count < 10 and total_rows > 100:
                issues.append(f"Колонка '{col.name}' имеет низкую уникальность ({unique_count} уникальных из {total_rows})")
        
        # Анализ типов данных
        if col.dtype == "object" and not col.nullable:
            issues.append(f"Колонка '{col.name}' имеет тип 'object' но не nullable")
    
    return {
        "completeness_score": sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0.0,
        "uniqueness_score": sum(uniqueness_scores) / len(uniqueness_scores) if uniqueness_scores else 0.0,
        "consistency_score": max(0, 100 - len(issues) * 10),
        "issues": issues
    }


@cache_analysis(ttl=1800)
async def analyze_file(req: FileAnalysisRequest) -> DataProfile:
    """Анализ файла с расширенной информацией"""
    meta = await FileConnector.analyze_file(req.file_path, req.file_type, req.connection)
    
    columns = []
    for c in meta.get("columns", []):
        column_info = {
            "name": c.get("name", "col"),
            "dtype": str(c.get("dtype", "string")),
            "nullable": bool(c.get("nullable", True)),
            "example": c.get("example"),
        }
        
        # Добавляем дополнительную статистику
        if "unique_count" in c:
            column_info["unique_count"] = c["unique_count"]
        if "null_count" in c:
            column_info["null_count"] = c["null_count"]
        if "null_percentage" in c:
            column_info["null_percentage"] = c["null_percentage"]
        if "numeric_stats" in c:
            column_info["numeric_stats"] = c["numeric_stats"]
        
        columns.append(ColumnProfile(**column_info))
    
    # Улучшенное определение временных рядов
    is_ts = any(
        c.name.lower() in {"ts", "timestamp", "created_at", "updated_at", "date", "time"} or
        c.dtype in {"datetime64[ns]", "timestamp", "date", "datetime"} or
        "time" in c.name.lower() or "date" in c.name.lower()
        for c in columns
    )
    
    # Анализ качества данных
    data_quality = None
    if "data_quality" in meta:
        quality_data = meta["data_quality"]
        data_quality = DataQualityMetrics(
            completeness_score=quality_data.get("completeness_score", 0.0),
            consistency_score=quality_data.get("consistency_score", 0.0),
            uniqueness_score=quality_data.get("uniqueness_score", 0.0),
            issues=quality_data.get("issues", [])
        )
    
    return DataProfile(
        rows=int(meta.get("rows", 0)),
        columns=columns,
        is_time_series=is_ts,
        sample_data=meta.get("sample_data"),
        data_quality=data_quality,
        file_metadata={
            "file_name": meta.get("file_name"),
            "file_size": meta.get("file_size"),
            "file_extension": meta.get("file_extension"),
            "created_at": meta.get("created_at"),
            "modified_at": meta.get("modified_at")
        }
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


