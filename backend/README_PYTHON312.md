# 🚀 Обновление до Python 3.12

Проект был обновлен для работы с Python 3.12 и совместимости с различными версиями Python в команде.

## 📋 Что было обновлено

### 🐍 Python и зависимости
- **Python версия**: 3.7.9 → 3.12
- **FastAPI**: 0.103.2 → 0.104.1
- **Pydantic**: 1.10.13 → 2.5.1 (+ pydantic-settings)
- **SQLAlchemy**: 1.4.53 → 2.0.23
- **Pandas**: 1.5.3 → 2.1.4
- **Другие зависимости**: обновлены до совместимых версий

### 🐳 Docker
- **Базовый образ**: `python:3.11-slim` → `python:3.12-slim`
- **LLM сервис**: также обновлен до `python:3.12-slim`

### ⚙️ Конфигурация
- **Pydantic v2**: обновлена конфигурация с `BaseSettings` на `pydantic-settings`
- **SQLAlchemy 2.0**: обновлены модели с `declarative_base` на `DeclarativeBase`

## 🛠️ Быстрый запуск

### 1. Создание .env файла
```bash
cd backend
./setup_env.sh
```

### 2. Запуск через Docker (рекомендуется)
```bash
# Запуск всех сервисов (включая бэкенд)
docker-compose up -d

# Или только базы данных для локальной разработки
docker-compose -f docker-compose.dev.yml up -d
```

### 3. Локальная разработка
```bash
# Установка зависимостей (Python 3.12)
pip install -r requirements.txt

# Запуск API сервера
python run_dev.py

# Или альтернативно
python run_local.py
```

## 🔧 Совместимость с версиями Python

### Для Python 3.12 (рекомендуется)
```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Для Python 3.11
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Для Python 3.10+
Большинство зависимостей должны работать, но рекомендуется использовать 3.11+

## 📊 Доступные сервисы

После запуска `docker-compose up -d`:

| Сервис | URL | Описание |
|--------|-----|----------|
| **API Backend** | http://localhost:8080 | Основной API |
| **API Docs** | http://localhost:8080/api/docs | Swagger UI |
| **Web UI** | http://localhost:8080/static/index.html | Простой веб-интерфейс |
| **Airflow** | http://localhost:8081 | Airflow UI (admin/admin) |
| **PostgreSQL (metadata)** | localhost:5432 | БД метаданных |
| **PostgreSQL (staging)** | localhost:5433 | Рабочая БД |
| **ClickHouse** | localhost:8123 | Целевая БД |

## 🗃️ Структура баз данных

### PostgreSQL (Метаданные) - порт 5432
- **База**: `etl_metadata`
- **Пользователь**: `metadata_user` / `metadata_password`
- **Назначение**: хранение информации о пайплайнах, источниках данных

### PostgreSQL (Staging) - порт 5433
- **База**: `etl_staging`
- **Пользователь**: `staging_user` / `staging_password`
- **Назначение**: временное хранение и обработка данных

### ClickHouse - порт 8123
- **База**: `etl_target`
- **Пользователь**: `default` / пароль пустой
- **Назначение**: финальное хранилище результатов

## 🧪 Проверка работоспособности

### Проверка API
```bash
curl http://localhost:8080/api/v1/health
```

### Проверка баз данных
```bash
# PostgreSQL
psql -h localhost -p 5432 -U metadata_user -d etl_metadata -c "SELECT 1;"
psql -h localhost -p 5433 -U staging_user -d etl_staging -c "SELECT 1;"

# ClickHouse
curl "http://localhost:8123/?query=SELECT 1"
```

## 🔄 Миграции

Запуск миграций для создания таблиц:
```bash
# Метаданные БД
python scripts/migrate.py --database=metadata

# Рабочая БД
python scripts/migrate.py --database=staging

# ClickHouse
python scripts/init_clickhouse.py
```

## 🐛 Устранение проблем

### Ошибка "no module named app"
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python run_dev.py
```

### Проблемы с Pydantic v2
Убедитесь, что установлена версия `pydantic-settings>=2.0`:
```bash
pip install pydantic-settings==2.1.0
```

### Проблемы с SQLAlchemy 2.0
Все модели обновлены до SQLAlchemy 2.0. При ошибках проверьте импорты:
```python
from sqlalchemy.orm import DeclarativeBase  # вместо declarative_base
```

## 📝 Изменения в коде

### Pydantic v2
```python
# Старый способ (v1)
from pydantic import BaseSettings

class Settings(BaseSettings):
    class Config:
        env_file = ".env"

# Новый способ (v2)
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env")
```

### SQLAlchemy 2.0
```python
# Старый способ (1.4)
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

# Новый способ (2.0)
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
```

## 💡 Рекомендации

1. **Используйте Docker** для изоляции и единообразия среды
2. **Python 3.12** рекомендуется для лучшей производительности
3. **Виртуальные окружения** обязательны для локальной разработки
4. **Регулярно обновляйте зависимости** для безопасности

## 🤝 Совместная работа

Для работы в команде с разными версиями Python:

1. Используйте Docker для CI/CD и продакшена
2. Поддерживайте совместимость с Python 3.10+
3. Тестируйте на минимальной и максимальной поддерживаемых версиях
4. Используйте `.python-version` файл для pyenv

```bash
echo "3.12" > .python-version
```

---

🚀 **Проект готов к работе с Python 3.12!**
