#!/usr/bin/env python3
"""
Скрипт для запуска приложения локально из PyCharm
"""
import os
import sys
import uvicorn
from pathlib import Path

# Добавляем корневую директорию проекта в Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Устанавливаем переменные окружения для локального запуска
os.environ.setdefault("ENV", "dev")
os.environ.setdefault("CORS_ALLOW_ORIGINS", "*")

# Метаданные БД (PostgreSQL)
os.environ.setdefault("METADATA_POSTGRES_HOST", "localhost")
os.environ.setdefault("METADATA_POSTGRES_PORT", "5432")
os.environ.setdefault("METADATA_POSTGRES_USER", "metadata_user")
os.environ.setdefault("METADATA_POSTGRES_PASSWORD", "metadata_password")
os.environ.setdefault("METADATA_POSTGRES_DATABASE", "etl_metadata")

# Рабочая БД (PostgreSQL)
os.environ.setdefault("STAGING_POSTGRES_HOST", "localhost")
os.environ.setdefault("STAGING_POSTGRES_PORT", "5433")
os.environ.setdefault("STAGING_POSTGRES_USER", "staging_user")
os.environ.setdefault("STAGING_POSTGRES_PASSWORD", "staging_password")
os.environ.setdefault("STAGING_POSTGRES_DATABASE", "etl_staging")

# Целевая БД (ClickHouse)
os.environ.setdefault("TARGET_CLICKHOUSE_HOST", "localhost")
os.environ.setdefault("TARGET_CLICKHOUSE_PORT", "8123")
os.environ.setdefault("TARGET_CLICKHOUSE_USER", "default")
os.environ.setdefault("TARGET_CLICKHOUSE_PASSWORD", "")
os.environ.setdefault("TARGET_CLICKHOUSE_DATABASE", "etl_target")

# Legacy поддержка
os.environ.setdefault("POSTGRES_DSN", "postgresql+psycopg2://metadata_user:metadata_password@localhost:5432/etl_metadata")
os.environ.setdefault("CLICKHOUSE_HOST", "localhost")
os.environ.setdefault("CLICKHOUSE_PORT", "8123")
os.environ.setdefault("CLICKHOUSE_USER", "default")
os.environ.setdefault("CLICKHOUSE_PASSWORD", "")
os.environ.setdefault("CLICKHOUSE_DATABASE", "etl_target")

# Внешние сервисы
os.environ.setdefault("AIRFLOW_BASE_URL", "http://localhost:8081")
os.environ.setdefault("LLM_BASE_URL", "http://localhost:8000")

if __name__ == "__main__":
    print("🚀 Запуск ETL AI Assistant Backend...")
    print("📖 Документация API: http://localhost:8080/api/docs")
    print("🌐 Веб-интерфейс: http://localhost:8080/static/index.html")
    print("🛑 Для остановки нажмите Ctrl+C")
    print("-" * 50)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )
