# Infra

Эта папка содержит инфраструктуру проекта: Docker, docker-compose, базы данных и оркестрацию ETL.

## Содержание
- `docker-compose.yml` — поднятие всех сервисов (PostgreSQL, ClickHouse, Airflow и др.)
- `Dockerfile` (по необходимости) — кастомные образы сервисов

## Требования
- Установленный [Docker](https://docs.docker.com/get-docker/)
- Установленный [Docker Compose](https://docs.docker.com/compose/install/)

## Запуск окружения
1. Перейдите в папку `infra`:
```bash
cd infra
```

2.	Поднимите все сервисы:
```bash
docker-compose up -d
```
3.	Проверьте статус контейнеров:
```bash
docker ps
```

Доступ к сервисам:

**PostgreSQL:**
- хост: localhost
-	порт: 5432
-	пользователь: user
-	пароль: pass
-	база данных: testdb

**ClickHouse:**
- HTTP интерфейс: http://localhost:8123
- TCP порт: 9000

**Airflow:**
- веб-интерфейс: http://localhost:8080


Остановка окружения
```bash
docker-compose down
```
Очистка данных (по необходимости)
```bash
docker-compose down -v
```