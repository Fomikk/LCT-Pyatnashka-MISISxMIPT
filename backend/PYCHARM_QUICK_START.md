# 🚀 Быстрый запуск из PyCharm

## ❌ Если конфигурации не работают, используйте этот способ:

### 1. Создайте конфигурацию вручную:

1. **Откройте PyCharm**
2. **Run → Edit Configurations...**
3. **Нажмите "+" → Python**
4. **Заполните поля:**
   - **Name:** `ETL Backend Dev`
   - **Script path:** `C:\LCT\run_dev.py`
   - **Working directory:** `C:\LCT`
   - **Python interpreter:** Выберите Python 3.11+

5. **Environment variables (нажмите "..."):**
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

### 2. Запустите внешние сервисы:

**В терминале PyCharm выполните:**
```bash
docker-compose -f docker-compose.dev.yml up -d
```

**Или создайте Docker Compose конфигурацию:**
1. **Run → Edit Configurations...**
2. **"+" → Docker Compose**
3. **Name:** `External Services`
4. **Compose files:** `docker-compose.dev.yml`
5. **Command:** `up -d`

### 3. Запустите бэкенд:

- Выберите `ETL Backend Dev` в выпадающем списке
- Нажмите **Run** (зеленая стрелка)

## 🔍 Проверка:

- **API:** http://localhost:8080
- **Документация:** http://localhost:8080/api/docs
- **Простой UI:** http://localhost:8080/static/index.html
- **Airflow:** http://localhost:8081 (admin/admin)

## ⚠️ Если что-то не работает:

1. **Проверьте, что Docker запущен**
2. **Убедитесь, что порты свободны** (8080, 8081, 5432, 8123)
3. **Установите зависимости:** `pip install -r requirements.txt`
4. **Проверьте Python интерпретатор** (должен быть 3.11+)

## 🐛 Альтернативный способ (если ничего не работает):

**Запустите в терминале PyCharm:**
```bash
# 1. Запустите сервисы
docker-compose -f docker-compose.dev.yml up -d

# 2. Запустите бэкенд
python run_dev.py
```

Это должно точно работать! 🎉
