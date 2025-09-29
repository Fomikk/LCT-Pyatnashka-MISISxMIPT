# ETL Система - Базы Данных

Полная ETL система с тремя базами данных для обработки данных, метаданных и аналитики.

## 🏗️ Архитектура

### Три базы данных:

1. **Метаданные БД (PostgreSQL)** - `etl_metadata`
   - Информация о пайплайнах и источниках данных
   - Результаты анализа и аудит
   - Порт: `5432`

2. **Рабочая БД (PostgreSQL)** - `etl_staging`
   - Временное хранение данных из файлов/внешних источников
   - Промежуточные результаты обработки
   - Порт: `5433`

3. **Целевая БД (ClickHouse)** - `etl_target`
   - Финальные результаты ETL
   - Метрики качества данных
   - Бизнес-аналитика
   - Порт: `8123`

## 📊 Структура таблиц

### Метаданные БД (PostgreSQL)

#### `data_sources`
```sql
- id (PK)
- name - Название источника
- description - Описание
- source_type - Тип (file, database, api, kafka, s3, hdfs)
- connection_config - Конфигурация подключения (JSON)
- is_active - Активен ли источник
- created_at, updated_at, is_deleted, deleted_at
```

#### `pipelines`
```sql
- id (PK)
- name - Название пайплайна
- description - Описание
- data_source_id (FK) - Ссылка на источник данных
- status - Статус (draft, active, inactive, deprecated)
- configuration - Конфигурация пайплайна (JSON)
- schedule_cron - Расписание в cron формате
- max_retries - Максимум повторов
- timeout_seconds - Таймаут
- tags - Теги (JSON)
- created_at, updated_at, is_deleted, deleted_at
```

#### `pipeline_runs`
```sql
- id (PK)
- pipeline_id (FK) - Ссылка на пайплайн
- status - Статус выполнения (pending, running, success, failed, cancelled)
- started_at, finished_at - Время начала/завершения
- duration_seconds - Длительность выполнения
- records_processed, records_failed - Количество записей
- error_message - Сообщение об ошибке
- execution_context - Контекст выполнения (JSON)
- retry_count - Количество повторов
- triggered_by - Кто запустил
- created_at, updated_at
```

#### `analysis_results`
```sql
- id (PK)
- pipeline_run_id (FK) - Ссылка на запуск пайплайна
- analysis_type - Тип анализа (data_quality, anomaly_detection, etc.)
- result_data - Результаты анализа (JSON)
- metrics - Метрики качества (JSON)
- recommendations - Рекомендации (JSON)
- is_alert - Требует внимания
- alert_level - Уровень алерта (low, medium, high, critical)
- created_at, updated_at
```

### Рабочая БД (PostgreSQL)

#### `staging_tables`
```sql
- id (PK)
- table_name - Название таблицы для стадирования
- schema_name - Название схемы
- source_type - Тип источника (csv, json, database, api)
- source_config - Конфигурация источника (JSON)
- row_count, column_count - Количество строк/столбцов
- file_size_bytes - Размер файла
- is_active - Активна ли таблица
- expires_at - Время истечения (для автоочистки)
- created_at, updated_at
```

#### `file_metadata`
```sql
- id (PK)
- filename, original_filename - Имена файлов
- file_path - Путь к файлу
- file_size - Размер файла
- file_hash - SHA256 хеш
- mime_type - MIME тип
- encoding - Кодировка
- status - Статус файла (uploaded, processing, processed, failed, deleted)
- uploaded_by - Кто загрузил
- processing_started_at, processing_finished_at - Время обработки
- error_message - Сообщение об ошибке
- metadata - Дополнительные метаданные (JSON)
- created_at, updated_at
```

#### `processing_logs`
```sql
- id (PK)
- table_name - Название обрабатываемой таблицы
- operation_type - Тип операции (load, transform, validate, export)
- status - Статус обработки (pending, in_progress, completed, failed, cancelled)
- records_processed, records_success, records_failed - Количество записей
- processing_time_seconds - Время обработки
- started_at, finished_at - Время начала/завершения
- error_message - Сообщение об ошибке
- execution_context - Контекст выполнения (JSON)
- created_at, updated_at
```

### Целевая БД (ClickHouse)

#### `data_quality_metrics`
```sql
- id (PK)
- table_name - Название таблицы
- column_name - Название столбца
- metric_name - Название метрики
- metric_value - Значение метрики
- threshold_min, threshold_max - Пороги
- is_passed - Прошла ли проверка
- pipeline_run_id - ID запуска пайплайна
- created_at, updated_at
```

#### `business_metrics`
```sql
- id (PK)
- metric_category - Категория метрики
- metric_name - Название метрики
- metric_value - Значение метрики
- metric_unit - Единица измерения
- dimension_values - Значения измерений (JSON)
- calculation_date - Дата расчета
- pipeline_run_id - ID запуска пайплайна
- created_at, updated_at
```

#### `data_lineage`
```sql
- id (PK)
- source_table, source_column - Исходная таблица/столбец
- target_table, target_column - Целевая таблица/столбец
- transformation_type - Тип трансформации
- transformation_logic - Логика трансформации
- pipeline_run_id - ID запуска пайплайна
- record_count - Количество записей
- created_at, updated_at
```

#### `data_catalog`
```sql
- id (PK)
- table_name, schema_name, column_name - Названия
- data_type - Тип данных
- is_nullable - Может ли быть NULL
- default_value - Значение по умолчанию
- description - Описание
- business_meaning - Бизнес-смысл
- owner - Владелец данных
- tags - Теги (JSON)
- sensitivity_level - Уровень чувствительности
- last_updated - Время последнего обновления
- created_at, updated_at
```

#### `etl_audit_log`
```sql
- id (PK)
- operation_type - Тип операции (create, update, delete, query)
- table_name - Название таблицы
- operation_details - Детали операции (JSON)
- user_id, session_id - Пользователь и сессия
- ip_address - IP адрес
- user_agent - User Agent
- pipeline_run_id - ID запуска пайплайна
- created_at, updated_at
```

## 🚀 Быстрый старт

### 1. Автоматическая настройка
```bash
# Запуск полной настройки системы
./scripts/setup.sh
```

### 2. Ручная настройка

#### Поднятие БД через Docker Compose
```bash
# Запуск всех БД
docker-compose up -d metadata-postgres staging-postgres target-clickhouse

# Или запуск всех сервисов
docker-compose up -d
```

#### Применение миграций

**Метаданные БД:**
```bash
python scripts/migrate.py metadata upgrade head
```

**Рабочая БД:**
```bash
python scripts/migrate.py staging upgrade head
```

**ClickHouse (инициализация таблиц):**
```bash
python scripts/init_clickhouse.py
```

**Все БД сразу:**
```bash
python scripts/migrate.py all upgrade head
```

## 🔧 Управление миграциями

### Создание новых миграций

**Для метаданных БД:**
```bash
alembic revision --autogenerate -m "Описание изменений"
```

**Для рабочей БД:**
```bash
alembic -c alembic_staging.ini revision --autogenerate -m "Описание изменений"
```

### Применение миграций
```bash
# Применить все миграции
python scripts/migrate.py metadata upgrade head
python scripts/migrate.py staging upgrade head

# Откатить последнюю миграцию
python scripts/migrate.py metadata downgrade -1
python scripts/migrate.py staging downgrade -1

# Показать текущую версию
python scripts/migrate.py metadata current
python scripts/migrate.py staging current

# Показать историю миграций
python scripts/migrate.py metadata history
python scripts/migrate.py staging history
```

## 🔌 Подключение к БД

### Метаданные БД (PostgreSQL)
```python
from app.core.config import get_settings

settings = get_settings()
dsn = settings.metadata_postgres_dsn
# postgresql+psycopg2://metadata_user:metadata_password@localhost:5432/etl_metadata
```

### Рабочая БД (PostgreSQL)
```python
from app.core.config import get_settings

settings = get_settings()
dsn = settings.staging_postgres_dsn
# postgresql+psycopg2://staging_user:staging_password@localhost:5433/etl_staging
```

### Целевая БД (ClickHouse)
```python
import clickhouse_connect
from app.core.config import get_settings

settings = get_settings()
client = clickhouse_connect.get_client(
    host=settings.target_clickhouse_host,
    port=settings.target_clickhouse_port,
    username=settings.target_clickhouse_user,
    password=settings.target_clickhouse_password,
    database=settings.target_clickhouse_database
)
```

## 📋 Использование в пайплайнах

### Создание источника данных
```python
from app.models.metadata import DataSource, DataSourceType
from app.connectors.database_connector import DatabaseConnector

# Создание источника данных
data_source = DataSource(
    name="CSV файл продаж",
    description="Ежемесячные данные продаж в CSV формате",
    source_type=DataSourceType.FILE,
    connection_config={
        "file_path": "/data/sales_2024.csv",
        "delimiter": ",",
        "encoding": "utf-8"
    }
)
```

### Создание пайплайна
```python
from app.models.metadata import Pipeline, PipelineStatus

# Создание пайплайна
pipeline = Pipeline(
    name="Обработка продаж",
    description="Загрузка и обработка данных продаж",
    data_source_id=data_source.id,
    status=PipelineStatus.ACTIVE,
    configuration={
        "validation_rules": {
            "required_columns": ["date", "amount", "product_id"],
            "data_types": {
                "date": "date",
                "amount": "float",
                "product_id": "integer"
            }
        },
        "transformations": [
            "clean_duplicates",
            "validate_amounts",
            "enrich_product_data"
        ]
    },
    schedule_cron="0 2 * * *",  # Каждый день в 2:00
    max_retries=3,
    tags=["sales", "monthly", "critical"]
)
```

### Запуск пайплайна
```python
from app.models.metadata import PipelineRun, PipelineRunStatus
from datetime import datetime

# Создание запуска пайплайна
pipeline_run = PipelineRun(
    pipeline_id=pipeline.id,
    status=PipelineRunStatus.RUNNING,
    started_at=datetime.now(),
    triggered_by="scheduler"
)

# Обновление статуса при завершении
pipeline_run.status = PipelineRunStatus.SUCCESS
pipeline_run.finished_at = datetime.now()
pipeline_run.records_processed = 10000
```

## 🔍 Мониторинг и анализ

### Просмотр статуса пайплайнов
```sql
-- Последние запуски пайплайнов
SELECT 
    p.name as pipeline_name,
    pr.status,
    pr.started_at,
    pr.finished_at,
    pr.duration_seconds,
    pr.records_processed
FROM pipelines p
JOIN pipeline_runs pr ON p.id = pr.pipeline_id
ORDER BY pr.created_at DESC
LIMIT 10;
```

### Анализ качества данных
```sql
-- Метрики качества данных
SELECT 
    table_name,
    metric_name,
    metric_value,
    is_passed,
    created_at
FROM data_quality_metrics
WHERE is_passed = false
ORDER BY created_at DESC;
```

### Бизнес метрики
```sql
-- Топ метрики по категориям
SELECT 
    metric_category,
    metric_name,
    AVG(metric_value) as avg_value,
    MAX(calculation_date) as last_calculated
FROM business_metrics
GROUP BY metric_category, metric_name
ORDER BY metric_category, avg_value DESC;
```

## 🛠️ Разработка

### Структура проекта
```
backend/
├── app/
│   ├── models/           # SQLAlchemy модели
│   │   ├── __init__.py
│   │   ├── base.py       # Базовые классы
│   │   ├── metadata.py   # Модели метаданных
│   │   ├── staging.py    # Модели рабочей БД
│   │   └── target.py     # Модели целевой БД
│   ├── core/
│   │   └── config.py     # Конфигурация
│   └── connectors/       # Коннекторы к БД
├── migrations/           # Миграции Alembic
│   ├── versions/         # Миграции метаданных
│   ├── staging/          # Миграции рабочей БД
│   └── target/           # Миграции целевой БД
├── scripts/              # Скрипты управления
│   ├── setup.sh          # Автонастройка
│   ├── migrate.py        # Миграции
│   └── init_clickhouse.py # Инициализация ClickHouse
├── docker-compose.yml    # Docker конфигурация
├── alembic.ini           # Конфигурация Alembic
├── alembic_staging.ini   # Конфигурация для staging
└── requirements.txt      # Зависимости Python
```

### Добавление новых моделей

1. **Создайте модель в соответствующем файле** (`metadata.py`, `staging.py`, `target.py`)

2. **Добавьте импорт в `__init__.py`**

3. **Создайте миграцию:**
```bash
alembic revision --autogenerate -m "Add new model"
```

4. **Примените миграцию:**
```bash
python scripts/migrate.py metadata upgrade head
```

### Переменные окружения

Создайте файл `.env` с настройками:
```bash
# Метаданные БД
METADATA_POSTGRES_HOST=localhost
METADATA_POSTGRES_PORT=5432
METADATA_POSTGRES_USER=metadata_user
METADATA_POSTGRES_PASSWORD=metadata_password
METADATA_POSTGRES_DATABASE=etl_metadata

# Рабочая БД
STAGING_POSTGRES_HOST=localhost
STAGING_POSTGRES_PORT=5433
STAGING_POSTGRES_USER=staging_user
STAGING_POSTGRES_PASSWORD=staging_password
STAGING_POSTGRES_DATABASE=etl_staging

# Целевая БД
TARGET_CLICKHOUSE_HOST=localhost
TARGET_CLICKHOUSE_PORT=8123
TARGET_CLICKHOUSE_USER=default
TARGET_CLICKHOUSE_PASSWORD=
TARGET_CLICKHOUSE_DATABASE=etl_target
```

## 📚 Полезные команды

### Docker
```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f [service_name]

# Остановка сервисов
docker-compose down

# Перезапуск сервиса
docker-compose restart [service_name]

# Подключение к БД
docker-compose exec metadata-postgres psql -U metadata_user -d etl_metadata
docker-compose exec staging-postgres psql -U staging_user -d etl_staging
```

### Миграции
```bash
# Применить все миграции
python scripts/migrate.py all upgrade head

# Откатить миграции
python scripts/migrate.py metadata downgrade -1

# Показать историю
python scripts/migrate.py metadata history

# Создать новую миграцию
alembic revision --autogenerate -m "Описание"
```

### ClickHouse
```bash
# Подключение к ClickHouse
curl http://localhost:8123/

# Выполнение запроса
curl -X POST 'http://localhost:8123/' --data-binary "SELECT 1"

# Инициализация таблиц
python scripts/init_clickhouse.py
```

## 🔒 Безопасность

- Используйте сильные пароли в продакшене
- Настройте SSL для подключений к БД
- Ограничьте доступ к портам БД
- Регулярно обновляйте зависимости
- Используйте секреты для хранения паролей

## 📈 Мониторинг

### Метрики для отслеживания:
- Время выполнения пайплайнов
- Количество обработанных записей
- Процент успешных запусков
- Использование дискового пространства
- Производительность запросов

### Алерты:
- Неудачные запуски пайплайнов
- Превышение времени выполнения
- Низкое качество данных
- Отсутствие новых данных

---

## 🆘 Поддержка

При возникновении проблем:

1. Проверьте логи: `docker-compose logs -f [service_name]`
2. Убедитесь, что все контейнеры запущены: `docker-compose ps`
3. Проверьте подключение к БД
4. Перезапустите сервисы: `docker-compose restart`

**Готово к работе! 🎉**
