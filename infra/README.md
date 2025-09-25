# Infra

Эта папка содержит инфраструктуру проекта: Docker, docker-compose, базы данных и оркестрацию ETL.

## Содержание
- `docker-compose.yml` — поднятие всех сервисов (PostgreSQL, ClickHouse, Airflow и др.)

## Требования
- Установленный [Docker](https://docs.docker.com/get-docker/)
- Установленный [Docker Compose](https://docs.docker.com/compose/install/)

## Запуск окружения
1. Перейдите в папку `infra`:
```bash
cd infra
```

2. Настройка окружения
	1. Создайте .env:

	2.	Откройте .env и замените значения при необходимости.

Пример :
```
# PostgreSQL
POSTGRES_USER=user
POSTGRES_PASSWORD=pass
POSTGRES_DB=testdb

# ClickHouse
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=

# Airflow
AIRFLOW__CORE__FERNET_KEY=<сгенерированный_ключ>
AIRFLOW__CORE__EXECUTOR=LocalExecutor
AIRFLOW__CORE__LOAD_EXAMPLES=False
```
не пушьте .env с настоящими паролями в репозиторий.


3.	Поднимите все сервисы:
```bash
docker-compose up -d
```
4.	Проверьте статус контейнеров:
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
  
5. Проверка работы Airflow
	1.	Откройте браузер на http://localhost:8080
	2.	Используйте логин/пароль, который вы создали при первом запуске.
	3.	Если нужно создать новых пользователей Airflow:
```bash
docker-compose exec airflow airflow users create \
    --username <username> \
    --firstname <FirstName> \
    --lastname <LastName> \
    --role Admin \
    --email <email@example.com> \
    --password <password>
```

Остановка окружения
```bash
docker-compose down
```
Очистка данных (по необходимости)
```bash
docker-compose down -v
```
