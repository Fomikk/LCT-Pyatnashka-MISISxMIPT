# 🤖 ETL AI Assistant Backend

MVP бэкенд для автоматизации ETL-задач с ИИ-ассистентом.

## 🚀 Запуск

```bash
# Клонируйте и запустите
git clone <repo-url>
cd etl-ai-assistant
docker-compose up -d
```

**Сервисы:**
- API: http://localhost:8080
- Docs: http://localhost:8080/api/docs
- UI: http://localhost:8080/static/index.html
- Airflow: http://localhost:8081 (admin/admin)

## 📋 API

- `GET /api/v1/health/` - статус
- `POST /api/v1/analysis/file` - анализ файлов
- `POST /api/v1/analysis/db` - анализ БД
- `POST /api/v1/recommend/storage` - рекомендации
- `POST /api/v1/ddl/generate` - генерация DDL
- `POST /api/v1/pipelines/draft` - создание пайплайна
- `POST /api/v1/pipelines/publish` - публикация в Airflow

## 🛠️ Разработка

```bash
# Только бэкенд
pip install -r requirements.txt
python run_dev.py
```

## 📦 Что включено

- FastAPI с API документацией
- Коннекторы: PostgreSQL, ClickHouse, файлы
- Интеграция с Airflow
- Health checks
- Простой веб-интерфейс


