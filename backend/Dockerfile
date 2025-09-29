FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Копирование и установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY app/ ./app/

# Создание директории для логов
RUN mkdir -p /app/logs

# Экспорт порта
EXPOSE 8080

# Команда запуска
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
