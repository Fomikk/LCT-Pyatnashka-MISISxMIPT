# 🚀 Руководство по развертыванию

## 📋 Требования

- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM минимум
- 10GB свободного места

## 🐳 Docker развертывание

### 1. Клонирование и настройка
```bash
git clone <repo-url>
cd etl-ai-assistant

# Создайте .env файл
cp .env.example .env
# Отредактируйте .env под ваши настройки
```

### 2. Запуск всех сервисов
```bash
# Запуск в фоне
docker-compose up -d

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f
```

### 3. Проверка работы
- **API:** http://localhost:8080
- **Документация:** http://localhost:8080/api/docs
- **Airflow:** http://localhost:8081 (admin/admin)
- **PostgreSQL:** localhost:5432
- **ClickHouse:** localhost:8123

## ⚙️ Конфигурация

### Переменные окружения (.env)
```bash
# Основные настройки
ENV=production
CORS_ALLOW_ORIGINS=https://yourdomain.com

# Airflow
AIRFLOW_BASE_URL=http://airflow-webserver:8080

# LLM Service
LLM_BASE_URL=http://llm:8000

# PostgreSQL
POSTGRES_DSN=postgresql+psycopg2://user:password@postgres:5432/etl_db

# ClickHouse
CLICKHOUSE_HOST=clickhouse
CLICKHOUSE_PORT=8123
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=your_password
CLICKHOUSE_DATABASE=default

# HDFS/Kafka
HDFS_HOST=hdfs
HDFS_PORT=9870
KAFKA_BOOTSTRAP=kafka:9092
```

## 🔧 Продакшн настройки

### 1. Безопасность
```bash
# Измените пароли по умолчанию
POSTGRES_PASSWORD=strong_password
CLICKHOUSE_PASSWORD=strong_password

# Ограничьте CORS
CORS_ALLOW_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

### 2. Мониторинг
```yaml
# Добавьте в docker-compose.yml
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

### 3. Логирование
```bash
# Настройте централизованное логирование
docker-compose logs -f > /var/log/etl-assistant.log
```

## ☸️ Kubernetes развертывание

### 1. Создайте namespace
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: etl-assistant
```

### 2. Создайте ConfigMap
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: etl-config
  namespace: etl-assistant
data:
  ENV: "production"
  CORS_ALLOW_ORIGINS: "https://yourdomain.com"
  # ... другие переменные
```

### 3. Создайте Secret
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: etl-secrets
  namespace: etl-assistant
type: Opaque
data:
  POSTGRES_PASSWORD: <base64-encoded-password>
  CLICKHOUSE_PASSWORD: <base64-encoded-password>
```

### 4. Deploy приложения
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: etl-backend
  namespace: etl-assistant
spec:
  replicas: 3
  selector:
    matchLabels:
      app: etl-backend
  template:
    metadata:
      labels:
        app: etl-backend
    spec:
      containers:
      - name: backend
        image: etl-ai-backend:latest
        ports:
        - containerPort: 8080
        envFrom:
        - configMapRef:
            name: etl-config
        - secretRef:
            name: etl-secrets
```

## 🔍 Мониторинг и логирование

### Health Checks
```bash
# Проверка API
curl http://localhost:8080/api/v1/health/

# Проверка Airflow
curl http://localhost:8080/api/v1/health/airflow

# Проверка БД
curl http://localhost:8080/api/v1/health/databases
```

### Логи
```bash
# Все сервисы
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f backend
docker-compose logs -f postgres
docker-compose logs -f clickhouse
```

### Метрики
- **Prometheus:** http://localhost:9090
- **Grafana:** http://localhost:3000 (admin/admin)

## 🛠️ Обслуживание

### Обновление
```bash
# Остановка
docker-compose down

# Обновление кода
git pull

# Пересборка и запуск
docker-compose up -d --build
```

### Бэкапы
```bash
# PostgreSQL
docker-compose exec postgres pg_dump -U user etl_db > backup.sql

# ClickHouse
docker-compose exec clickhouse clickhouse-client --query "BACKUP DATABASE default TO Disk('backups', 'backup_$(date +%Y%m%d_%H%M%S)')"
```

### Масштабирование
```bash
# Увеличить количество реплик backend
docker-compose up -d --scale backend=3
```

## 🚨 Устранение неполадок

### Частые проблемы
1. **Out of memory:** увеличьте лимиты Docker
2. **Port conflicts:** измените порты в docker-compose.yml
3. **Database connection failed:** проверьте переменные окружения

### Логи для отладки
```bash
# Детальные логи
docker-compose logs --tail=100 -f backend

# Проверка ресурсов
docker stats

# Проверка сети
docker network ls
docker network inspect etl-ai-assistant_default
```

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи: `docker-compose logs -f`
2. Проверьте статус: `docker-compose ps`
3. Проверьте health checks: `curl http://localhost:8080/api/v1/health/`
4. Создайте issue в репозитории
