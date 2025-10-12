#!/bin/bash

# Скрипт для создания .env файла для локальной разработки

echo "Создание .env файла для локальной разработки..."

cat > .env << 'EOF'
# ETL System Configuration
ENV=dev
CORS_ALLOW_ORIGINS=*

# Метаданные БД (PostgreSQL)
METADATA_POSTGRES_HOST=localhost
METADATA_POSTGRES_PORT=5432
METADATA_POSTGRES_USER=metadata_user
METADATA_POSTGRES_PASSWORD=metadata_password
METADATA_POSTGRES_DATABASE=etl_metadata

# Рабочая БД (PostgreSQL)
STAGING_POSTGRES_HOST=localhost
STAGING_POSTGRES_PORT=5433
STAGING_POSTGRES_USER=staging_user
STAGING_POSTGRES_PASSWORD=staging_password
STAGING_POSTGRES_DATABASE=etl_staging

# Целевая БД (ClickHouse)
TARGET_CLICKHOUSE_HOST=localhost
TARGET_CLICKHOUSE_PORT=8123
TARGET_CLICKHOUSE_USER=default
TARGET_CLICKHOUSE_PASSWORD=
TARGET_CLICKHOUSE_DATABASE=etl_target

# Legacy поддержка (для совместимости)
POSTGRES_DSN=postgresql+psycopg2://metadata_user:metadata_password@localhost:5432/etl_metadata
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=
CLICKHOUSE_DATABASE=etl_target

# Внешние сервисы
AIRFLOW_BASE_URL=http://localhost:8081
LLM_BASE_URL=http://localhost:8000
HDFS_HOST=hdfs
HDFS_PORT=9870
KAFKA_BOOTSTRAP=kafka:9092
EOF

echo "✅ .env файл создан!"
echo "Теперь вы можете запустить:"
echo "  docker-compose up -d                    # Запуск всех сервисов"
echo "  docker-compose -f docker-compose.dev.yml up -d  # Только БД для разработки"
echo "  python run_local.py                     # Локальный запуск API"
