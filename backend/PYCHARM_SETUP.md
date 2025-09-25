# 🚀 Запуск из PyCharm

## Вариант 1: Готовые конфигурации (рекомендуется)

1. **Откройте проект в PyCharm**
2. **Запустите внешние сервисы:**
   - В меню `Run` → `Edit Configurations...`
   - Выберите `External Services` → `Run`
   - Это запустит PostgreSQL, ClickHouse, Airflow, LLM-заглушку

3. **Запустите бэкенд:**
   - Выберите `ETL Backend Dev` → `Run`
   - Или нажмите `Ctrl+Shift+F10` на файле `run_dev.py`

## Вариант 2: Ручная настройка

### 1. Создайте Python конфигурацию:
- `Run` → `Edit Configurations...` → `+` → `Python`
- **Name:** `ETL Backend Dev`
- **Script path:** `run_dev.py`
- **Working directory:** `C:\LCT`
- **Environment variables:**
  ```
  ENV=dev
  CORS_ALLOW_ORIGINS=*
  AIRFLOW_BASE_URL=http://localhost:8081
  LLM_BASE_URL=http://localhost:8000
  POSTGRES_DSN=postgresql+psycopg2://user:password@localhost:5432/etl_db
  CLICKHOUSE_HOST=localhost
  CLICKHOUSE_PORT=8123
  CLICKHOUSE_USER=default
  CLICKHOUSE_PASSWORD=
  CLICKHOUSE_DATABASE=default
  ```

### 2. Создайте Docker Compose конфигурацию:
- `Run` → `Edit Configurations...` → `+` → `Docker Compose`
- **Name:** `External Services`
- **Compose files:** `docker-compose.dev.yml`
- **Command:** `up -d`

## 🎯 Порядок запуска:

1. **Сначала внешние сервисы:**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

2. **Затем бэкенд в PyCharm:**
   - Запустите `ETL Backend Dev`
   - Или выполните `python run_dev.py`

## 🔍 Проверка:

- **API:** http://localhost:8080
- **Документация:** http://localhost:8080/api/docs
- **Простой UI:** http://localhost:8080/static/index.html
- **Airflow:** http://localhost:8081 (admin/admin)
- **PostgreSQL:** localhost:5432
- **ClickHouse:** localhost:8123

## 🛠️ Отладка:

- **Логи бэкенда:** В консоли PyCharm
- **Логи сервисов:** `docker-compose -f docker-compose.dev.yml logs`
- **Health check:** `GET http://localhost:8080/api/v1/health/`

## ⚠️ Важные моменты:

1. **Порты:** Убедитесь, что порты 8080, 8081, 5432, 8123 свободны
2. **Docker:** Должен быть запущен Docker Desktop
3. **Python:** Используйте Python 3.11+
4. **Зависимости:** Установите `pip install -r requirements.txt`

## 🐛 Устранение неполадок:

- **Ошибка подключения к БД:** Проверьте, что PostgreSQL запущен
- **Airflow не отвечает:** Подождите 1-2 минуты после запуска
- **Порт занят:** Измените порт в конфигурации или остановите конфликтующий процесс
