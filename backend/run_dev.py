#!/usr/bin/env python3
"""
Скрипт для запуска в режиме разработки из PyCharm
"""
import os
import sys
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Устанавливаем переменные окружения для разработки
os.environ.setdefault("ENV", "dev")
os.environ.setdefault("CORS_ALLOW_ORIGINS", "*")
os.environ.setdefault("AIRFLOW_BASE_URL", "http://localhost:8081")
os.environ.setdefault("LLM_BASE_URL", "http://localhost:8000")
os.environ.setdefault("POSTGRES_DSN", "postgresql+psycopg2://user:password@localhost:5432/etl_db")
os.environ.setdefault("CLICKHOUSE_HOST", "localhost")
os.environ.setdefault("CLICKHOUSE_PORT", "8123")
os.environ.setdefault("CLICKHOUSE_USER", "default")
os.environ.setdefault("CLICKHOUSE_PASSWORD", "")
os.environ.setdefault("CLICKHOUSE_DATABASE", "default")

if __name__ == "__main__":
    import uvicorn
    from app.main import app
    
    print("🚀 Запуск ETL AI Assistant Backend в режиме разработки")
    print("📊 API: http://localhost:8080")
    print("📖 Документация: http://localhost:8080/api/docs")
    print("🖥️  Простой UI: http://localhost:8080/static/index.html")
    print("🔄 Airflow UI: http://localhost:8081 (admin/admin)")
    print("\n⚠️  Убедитесь, что внешние сервисы запущены:")
    print("   docker-compose -f docker-compose.dev.yml up -d")
    print("\n" + "="*60)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        reload_dirs=["app"],
        log_level="info"
    )
