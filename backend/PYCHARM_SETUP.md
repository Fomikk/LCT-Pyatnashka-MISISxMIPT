# Запуск из PyCharm

## Шаг 1: Настройка интерпретатора Python

1. Откройте PyCharm
2. Откройте проект (папка C:\LCT)
3. Перейдите в File → Settings → Project → Python Interpreter
4. Выберите существующий интерпретатор или создайте новый виртуальный

## Шаг 2: Установка зависимостей

Выполните в терминале PyCharm:
```bash
pip install -r requirements_local.txt
```

## Шаг 3: Запуск приложения

### Вариант 1: Через скрипт (Рекомендуется)
1. Откройте файл `run_local.py`
2. Нажмите правой кнопкой мыши
3. Выберите "Run 'run_local'"

### Вариант 2: Через конфигурацию запуска
1. Перейдите в Run → Edit Configurations
2. Нажмите "+" → Python
3. Установите:
   - Name: ETL Backend
   - Script path: C:\LCT\run_local.py
   - Working directory: C:\LCT
4. Нажмите OK и запустите

### Вариант 3: Прямой запуск uvicorn
В терминале PyCharm:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

## Доступные URL после запуска:

- **API документация**: http://localhost:8080/api/docs
- **Главная страница**: http://localhost:8080/
- **Веб-интерфейс**: http://localhost:8080/static/index.html

## Примечания:

- Приложение запустится на порту 8080
- Режим разработки включен (автоперезагрузка при изменении кода)
- Все внешние сервисы (PostgreSQL, ClickHouse) будут недоступны, но приложение запустится
