#!/usr/bin/env python3
"""
Скрипт для инициализации ClickHouse (создание таблиц для целевой БД)
"""

import sys
import clickhouse_connect
from pathlib import Path

# Добавляем путь к приложению
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import get_settings

def create_clickhouse_tables():
    """Создание таблиц в ClickHouse"""
    settings = get_settings()
    
    # Подключение к ClickHouse
    client = clickhouse_connect.get_client(
        host=settings.target_clickhouse_host,
        port=settings.target_clickhouse_port,
        username=settings.target_clickhouse_user,
        password=settings.target_clickhouse_password,
        database=settings.target_clickhouse_database,
        secure=False,
        verify=False
    )
    
    print(f"🔄 Подключение к ClickHouse: {settings.target_clickhouse_host}:{settings.target_clickhouse_port}")
    
    # Создание таблицы для метрик качества данных
    create_data_quality_metrics = """
    CREATE TABLE IF NOT EXISTS data_quality_metrics (
        id UInt64,
        created_at DateTime64(3),
        updated_at Nullable(DateTime64(3)),
        table_name String,
        column_name Nullable(String),
        metric_name String,
        metric_value Float64,
        threshold_min Nullable(Float64),
        threshold_max Nullable(Float64),
        is_passed UInt8,
        pipeline_run_id Nullable(UInt64)
    ) ENGINE = MergeTree()
    ORDER BY (table_name, metric_name, created_at)
    PARTITION BY toYYYYMM(created_at)
    """
    
    # Создание таблицы для бизнес метрик
    create_business_metrics = """
    CREATE TABLE IF NOT EXISTS business_metrics (
        id UInt64,
        created_at DateTime64(3),
        updated_at Nullable(DateTime64(3)),
        metric_category String,
        metric_name String,
        metric_value Float64,
        metric_unit Nullable(String),
        dimension_values String,
        calculation_date DateTime64(3),
        pipeline_run_id Nullable(UInt64)
    ) ENGINE = MergeTree()
    ORDER BY (metric_category, metric_name, calculation_date)
    PARTITION BY toYYYYMM(calculation_date)
    """
    
    # Создание таблицы для линии данных
    create_data_lineage = """
    CREATE TABLE IF NOT EXISTS data_lineage (
        id UInt64,
        created_at DateTime64(3),
        updated_at Nullable(DateTime64(3)),
        source_table String,
        source_column Nullable(String),
        target_table String,
        target_column Nullable(String),
        transformation_type String,
        transformation_logic Nullable(String),
        pipeline_run_id UInt64,
        record_count Nullable(UInt64)
    ) ENGINE = MergeTree()
    ORDER BY (source_table, target_table, pipeline_run_id)
    PARTITION BY toYYYYMM(created_at)
    """
    
    # Создание таблицы для каталога данных
    create_data_catalog = """
    CREATE TABLE IF NOT EXISTS data_catalog (
        id UInt64,
        created_at DateTime64(3),
        updated_at Nullable(DateTime64(3)),
        table_name String,
        schema_name Nullable(String),
        column_name Nullable(String),
        data_type Nullable(String),
        is_nullable Nullable(UInt8),
        default_value Nullable(String),
        description Nullable(String),
        business_meaning Nullable(String),
        owner Nullable(String),
        tags String,
        sensitivity_level Nullable(String),
        last_updated Nullable(DateTime64(3))
    ) ENGINE = MergeTree()
    ORDER BY (table_name, schema_name, column_name)
    """
    
    # Создание таблицы для аудит лога
    create_etl_audit_log = """
    CREATE TABLE IF NOT EXISTS etl_audit_log (
        id UInt64,
        created_at DateTime64(3),
        updated_at Nullable(DateTime64(3)),
        operation_type String,
        table_name String,
        operation_details String,
        user_id Nullable(String),
        session_id Nullable(String),
        ip_address Nullable(String),
        user_agent Nullable(String),
        pipeline_run_id Nullable(UInt64)
    ) ENGINE = MergeTree()
    ORDER BY (table_name, operation_type, created_at)
    PARTITION BY toYYYYMM(created_at)
    """
    
    tables = [
        ("data_quality_metrics", create_data_quality_metrics),
        ("business_metrics", create_business_metrics),
        ("data_lineage", create_data_lineage),
        ("data_catalog", create_data_catalog),
        ("etl_audit_log", create_etl_audit_log)
    ]
    
    for table_name, create_sql in tables:
        try:
            print(f"🔄 Создание таблицы: {table_name}")
            client.command(create_sql)
            print(f"✅ Таблица {table_name} создана успешно")
        except Exception as e:
            print(f"❌ Ошибка при создании таблицы {table_name}: {e}")
            return False
    
    print("\n✅ Все таблицы ClickHouse созданы успешно!")
    return True

def main():
    """Основная функция"""
    try:
        if create_clickhouse_tables():
            print("\n🎉 Инициализация ClickHouse завершена!")
        else:
            print("\n❌ Ошибка при инициализации ClickHouse!")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
