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
os.environ.setdefault("POSTGRES_DSN", "postgresql+psycopg2://user:password@localhost:5432/etl_db")
os.environ.setdefault("CLICKHOUSE_HOST", "localhost")
os.environ.setdefault("CLICKHOUSE_PORT", "8123")
os.environ.setdefault("CLICKHOUSE_USER", "default")
os.environ.setdefault("CLICKHOUSE_PASSWORD", "")
os.environ.setdefault("CLICKHOUSE_DATABASE", "default")
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
