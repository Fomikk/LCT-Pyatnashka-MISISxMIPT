#!/bin/bash

# Скрипт для полной настройки ETL системы

set -e  # Остановка при ошибке

echo "🚀 Настройка ETL системы"
echo "========================"

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Установите Docker и повторите попытку."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен. Установите Docker Compose и повторите попытку."
    exit 1
fi

# Создание .env файла если его нет
if [ ! -f .env ]; then
    echo "📝 Создание .env файла..."
    cat > .env << EOF
# ETL System Configuration
ENV=dev
CORS_ALLOW_ORIGINS=*

# Метаданные БД
METADATA_POSTGRES_HOST=metadata-postgres
METADATA_POSTGRES_PORT=5432
METADATA_POSTGRES_USER=metadata_user
METADATA_POSTGRES_PASSWORD=metadata_password
METADATA_POSTGRES_DATABASE=etl_metadata

# Рабочая БД
STAGING_POSTGRES_HOST=staging-postgres
STAGING_POSTGRES_PORT=5432
STAGING_POSTGRES_USER=staging_user
STAGING_POSTGRES_PASSWORD=staging_password
STAGING_POSTGRES_DATABASE=etl_staging

# Целевая БД
TARGET_CLICKHOUSE_HOST=target-clickhouse
TARGET_CLICKHOUSE_PORT=8123
TARGET_CLICKHOUSE_USER=default
TARGET_CLICKHOUSE_PASSWORD=
TARGET_CLICKHOUSE_DATABASE=etl_target

# Legacy поддержка
POSTGRES_DSN=postgresql+psycopg2://metadata_user:metadata_password@metadata-postgres:5432/etl_metadata
CLICKHOUSE_HOST=target-clickhouse
CLICKHOUSE_PORT=8123
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=
CLICKHOUSE_DATABASE=etl_target

# Внешние сервисы
AIRFLOW_BASE_URL=http://airflow-webserver:8080
LLM_BASE_URL=http://llm:8000
EOF
    echo "✅ .env файл создан"
fi

# Запуск контейнеров
echo "🐳 Запуск Docker контейнеров..."
docker-compose up -d metadata-postgres staging-postgres target-clickhouse

# Ожидание готовности БД
echo "⏳ Ожидание готовности баз данных..."
sleep 10

# Проверка подключения к метаданным БД
echo "🔍 Проверка подключения к метаданным БД..."
until docker-compose exec -T metadata-postgres pg_isready -U metadata_user -d etl_metadata; do
    echo "⏳ Ожидание метаданных БД..."
    sleep 2
done
echo "✅ Метаданные БД готова"

# Проверка подключения к рабочей БД
echo "🔍 Проверка подключения к рабочей БД..."
until docker-compose exec -T staging-postgres pg_isready -U staging_user -d etl_staging; do
    echo "⏳ Ожидание рабочей БД..."
    sleep 2
done
echo "✅ Рабочая БД готова"

# Проверка подключения к ClickHouse
echo "🔍 Проверка подключения к ClickHouse..."
until curl -s http://localhost:8123/ping > /dev/null; do
    echo "⏳ Ожидание ClickHouse..."
    sleep 2
done
echo "✅ ClickHouse готова"

# Установка зависимостей Python
echo "📦 Установка зависимостей Python..."
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
    echo "✅ Зависимости установлены"
else
    echo "⚠️  requirements.txt не найден, пропускаем установку зависимостей"
fi

# Применение миграций
echo "🔄 Применение миграций..."

# Метаданные БД
echo "📊 Миграции метаданных БД..."
python scripts/migrate.py metadata upgrade head

# Рабочая БД
echo "📊 Миграции рабочей БД..."
python scripts/migrate.py staging upgrade head

# Инициализация ClickHouse
echo "📊 Инициализация ClickHouse..."
python scripts/init_clickhouse.py

# Запуск всех сервисов
echo "🚀 Запуск всех сервисов..."
docker-compose up -d

echo ""
echo "🎉 ETL система настроена и запущена!"
echo ""
echo "📋 Доступные сервисы:"
echo "  • Backend API: http://localhost:8080"
echo "  • Airflow: http://localhost:8081"
echo "  • LLM Stub: http://localhost:8000"
echo "  • Метаданные БД: localhost:5432"
echo "  • Рабочая БД: localhost:5433"
echo "  • ClickHouse: http://localhost:8123"
echo ""
echo "📚 Полезные команды:"
echo "  • Просмотр логов: docker-compose logs -f [service_name]"
echo "  • Остановка: docker-compose down"
echo "  • Перезапуск: docker-compose restart [service_name]"
echo "  • Миграции: python scripts/migrate.py [metadata|staging|target|all]"
echo ""
echo "✨ Готово к работе!"
