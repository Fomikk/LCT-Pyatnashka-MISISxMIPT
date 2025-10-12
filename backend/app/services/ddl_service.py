from app.schemas.ddl import DDLRequest, DDLResponse
from typing import Dict, List, Optional
import re
from app.services.cache_service import cache_ddl


def _infer_sql_type(py_type: str, target: str, column_info: Optional[Dict] = None) -> str:
    """Улучшенное определение SQL типа с учетом дополнительной информации о колонке"""
    
    # Расширенные маппинги типов
    mapping_pg = {
        "int": "INTEGER",
        "int64": "BIGINT",
        "int32": "INTEGER",
        "int16": "SMALLINT",
        "int8": "SMALLINT",
        "float": "DOUBLE PRECISION",
        "float64": "DOUBLE PRECISION",
        "float32": "REAL",
        "string": "TEXT",
        "object": "TEXT",
        "bool": "BOOLEAN",
        "boolean": "BOOLEAN",
        "timestamp": "TIMESTAMP",
        "datetime64[ns]": "TIMESTAMP",
        "datetime": "TIMESTAMP",
        "date": "DATE",
        "category": "TEXT",
        "mixed": "TEXT"
    }
    
    mapping_ch = {
        "int": "Int64",
        "int64": "Int64",
        "int32": "Int32",
        "int16": "Int16",
        "int8": "Int8",
        "float": "Float64",
        "float64": "Float64",
        "float32": "Float32",
        "string": "String",
        "object": "String",
        "bool": "UInt8",
        "boolean": "UInt8",
        "timestamp": "DateTime",
        "datetime64[ns]": "DateTime",
        "datetime": "DateTime",
        "date": "Date",
        "category": "String",
        "mixed": "String"
    }
    
    mapping_mysql = {
        "int": "INT",
        "int64": "BIGINT",
        "int32": "INT",
        "int16": "SMALLINT",
        "int8": "TINYINT",
        "float": "DOUBLE",
        "float64": "DOUBLE",
        "float32": "FLOAT",
        "string": "TEXT",
        "object": "TEXT",
        "bool": "BOOLEAN",
        "boolean": "BOOLEAN",
        "timestamp": "TIMESTAMP",
        "datetime64[ns]": "DATETIME",
        "datetime": "DATETIME",
        "date": "DATE",
        "category": "TEXT",
        "mixed": "TEXT"
    }
    
    mapping_hive = {
        "int": "BIGINT",
        "int64": "BIGINT",
        "int32": "INT",
        "int16": "SMALLINT",
        "int8": "TINYINT",
        "float": "DOUBLE",
        "float64": "DOUBLE",
        "float32": "FLOAT",
        "string": "STRING",
        "object": "STRING",
        "bool": "BOOLEAN",
        "boolean": "BOOLEAN",
        "timestamp": "TIMESTAMP",
        "datetime64[ns]": "TIMESTAMP",
        "datetime": "TIMESTAMP",
        "date": "DATE",
        "category": "STRING",
        "mixed": "STRING"
    }
    
    # Нормализация типа
    py_type = py_type.lower().strip()
    
    # Выбор маппинга
    if target == "postgres":
        mapping = mapping_pg
    elif target == "clickhouse":
        mapping = mapping_ch
    elif target == "mysql":
        mapping = mapping_mysql
    else:  # hive, hdfs
        mapping = mapping_hive
    
    base_type = mapping.get(py_type, "TEXT" if target != "clickhouse" else "String")
    
    # Дополнительные модификаторы на основе информации о колонке
    if column_info:
        # Обработка NULL значений
        nullable = column_info.get("nullable", True)
        if not nullable and target == "postgres":
            base_type += " NOT NULL"
        elif not nullable and target == "mysql":
            base_type += " NOT NULL"
        
        # Обработка уникальности
        unique_count = column_info.get("unique_count", 0)
        total_rows = column_info.get("total_rows", 0)
        if unique_count == total_rows and total_rows > 1 and target in ["postgres", "mysql"]:
            base_type += " UNIQUE"
    
    return base_type


def _generate_constraints(columns: List[Dict], target: str) -> List[str]:
    """Генерация ограничений для таблицы"""
    constraints = []
    
    for col in columns:
        name = col.get("name", "")
        unique_count = col.get("unique_count", 0)
        total_rows = col.get("total_rows", 0)
        
        # Первичный ключ
        if name.lower() in ["id", "pk", "primary_key"] or (unique_count == total_rows and total_rows > 1):
            if target == "postgres":
                constraints.append(f"CONSTRAINT pk_{name} PRIMARY KEY ({name})")
            elif target == "mysql":
                constraints.append(f"PRIMARY KEY ({name})")
            elif target == "clickhouse":
                # ClickHouse не поддерживает PRIMARY KEY в обычном понимании
                pass
    
    return constraints


def _generate_indexes(columns: List[Dict], target: str) -> List[str]:
    """Генерация индексов для таблицы"""
    indexes = []
    
    for col in columns:
        name = col.get("name", "")
        dtype = col.get("dtype", "").lower()
        
        # Индексы для часто используемых полей
        if name.lower() in ["created_at", "updated_at", "timestamp", "date"] or "time" in name.lower():
            if target == "postgres":
                indexes.append(f"CREATE INDEX idx_{name} ON {name} ({name});")
            elif target == "mysql":
                indexes.append(f"CREATE INDEX idx_{name} ON {name} ({name});")
    
    return indexes


@cache_ddl(ttl=3600)
async def generate_ddl(req: DDLRequest) -> DDLResponse:
    """Генерация DDL с улучшенной логикой и поддержкой множества СУБД"""
    sample_cols = req.sample.get("columns", [])
    total_rows = req.sample.get("rows", 0)
    
    # Подготовка колонок с дополнительной информацией
    cols_rendered: list[str] = []
    for c in sample_cols:
        name = c.get("name", "col")
        dtype = c.get("dtype", "string")
        
        # Добавляем информацию о количестве строк для анализа уникальности
        column_info = c.copy()
        column_info["total_rows"] = total_rows
        
        sql_type = _infer_sql_type(dtype, req.target_system, column_info)
        cols_rendered.append(f"  {name} {sql_type}")

    # Генерация ограничений
    constraints = _generate_constraints(sample_cols, req.target_system)
    
    # Генерация индексов
    indexes = _generate_indexes(sample_cols, req.target_system)
    
    # Генерация DDL в зависимости от целевой СУБД
    ddl_parts = []
    suggestions: list[str] = []
    
    if req.target_system == "postgres":
        ddl_parts.append(f"CREATE TABLE IF NOT EXISTS {req.table_name} (")
        ddl_parts.extend(cols_rendered)
        if constraints:
            ddl_parts.append("  " + ",\n  ".join(constraints))
        ddl_parts.append(");")
        
        # Добавляем индексы
        if indexes:
            ddl_parts.extend(indexes)
        
        suggestions.extend([
            "Рекомендуется создать индексы на часто фильтруемые поля",
            "Рассмотрите партицирование для больших таблиц",
            "Используйте VACUUM для оптимизации производительности"
        ])
        
    elif req.target_system == "clickhouse":
        # Определяем колонку для партицирования
        partition_col = None
        for col in sample_cols:
            name = col.get("name", "").lower()
            if name in ["ts", "timestamp", "created_at", "date"] or "time" in name:
                partition_col = col.get("name")
                break
        
        # Определяем колонку для сортировки
        order_cols = []
        for col in sample_cols:
            name = col.get("name", "").lower()
            if name in ["id", "ts", "timestamp", "created_at"] or "time" in name:
                order_cols.append(col.get("name"))
        
        ddl_parts.append(f"CREATE TABLE IF NOT EXISTS {req.table_name} (")
        ddl_parts.extend(cols_rendered)
        ddl_parts.append(")")
        
        # Добавляем движок
        engine = "MergeTree()"
        if partition_col:
            engine += f"\nPARTITION BY toDate({partition_col})"
        if order_cols:
            engine += f"\nORDER BY ({', '.join(order_cols[:3])})"  # Максимум 3 колонки для сортировки
        
        ddl_parts.append(f"ENGINE = {engine};")
        
        suggestions.extend([
            "ClickHouse оптимизирован для аналитических запросов",
            "Используйте партицирование для улучшения производительности",
            "Рассмотрите использование материализованных представлений"
        ])
        
    elif req.target_system == "mysql":
        ddl_parts.append(f"CREATE TABLE IF NOT EXISTS {req.table_name} (")
        ddl_parts.extend(cols_rendered)
        if constraints:
            ddl_parts.append("  " + ",\n  ".join(constraints))
        ddl_parts.append(") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;")
        
        if indexes:
            ddl_parts.extend(indexes)
        
        suggestions.extend([
            "InnoDB движок обеспечивает ACID совместимость",
            "Создайте индексы для часто используемых полей",
            "Рассмотрите использование репликации для высокой доступности"
        ])
        
    else:  # Hive/HDFS
        ddl_parts.append(f"CREATE TABLE {req.table_name} (")
        ddl_parts.extend(cols_rendered)
        ddl_parts.append(")")
        ddl_parts.append("STORED AS PARQUET")
        ddl_parts.append("LOCATION '/user/hive/warehouse/your_database.db/your_table';")
        
        suggestions.extend([
            "Parquet формат обеспечивает эффективное сжатие",
            "Рассмотрите партицирование по дате",
            "Используйте колоннарное хранение для аналитики"
        ])
    
    # Объединяем все части DDL
    ddl = "\n".join(ddl_parts)
    
    # Дополнительные рекомендации на основе анализа данных
    if total_rows > 1000000:
        suggestions.append("Для больших таблиц рассмотрите партицирование")
    
    # Анализ временных рядов
    has_time_columns = any(
        col.get("name", "").lower() in ["ts", "timestamp", "created_at", "date"] or 
        "time" in col.get("name", "").lower()
        for col in sample_cols
    )
    if has_time_columns:
        suggestions.append("Обнаружены временные колонки - рассмотрите партицирование по времени")
    
    return DDLResponse(
        ddl_sql=ddl, 
        suggestions=suggestions,
        indexes=indexes if indexes else None,
        constraints=constraints if constraints else None
    )


