#!/usr/bin/env python3
"""
Скрипт для применения миграций к базам данных ETL системы
"""

import os
import sys
import subprocess
from pathlib import Path

# Добавляем путь к приложению
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import get_settings

def run_migration(db_type: str, command: str = "upgrade head"):
    """Запуск миграций для указанной БД"""
    settings = get_settings()
    
    if db_type == "metadata":
        db_url = settings.metadata_postgres_dsn
        env = os.environ.copy()
        env["ALEMBIC_DATABASE_URL"] = db_url
        
        print(f"🔄 Применение миграций для метаданных БД...")
        print(f"📡 URL: {db_url}")
        
        # Запускаем alembic
        result = subprocess.run(
            ["alembic", command],
            env=env,
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Миграции метаданных применены успешно")
            if result.stdout:
                print(result.stdout)
        else:
            print("❌ Ошибка при применении миграций метаданных:")
            print(result.stderr)
            return False
            
    elif db_type == "staging":
        db_url = settings.staging_postgres_dsn
        env = os.environ.copy()
        env["ALEMBIC_DATABASE_URL"] = db_url
        
        print(f"🔄 Применение миграций для рабочей БД...")
        print(f"📡 URL: {db_url}")
        
        # Для staging БД используем отдельную конфигурацию
        staging_env = env.copy()
        staging_env["ALEMBIC_CONFIG"] = str(Path(__file__).parent.parent / "alembic_staging.ini")
        
        result = subprocess.run(
            ["alembic", "-c", "alembic_staging.ini", command],
            env=staging_env,
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Миграции рабочей БД применены успешно")
            if result.stdout:
                print(result.stdout)
        else:
            print("❌ Ошибка при применении миграций рабочей БД:")
            print(result.stderr)
            return False
            
    elif db_type == "target":
        # Для ClickHouse миграции не нужны, так как это колоночная БД
        print("ℹ️  ClickHouse не требует миграций (колоночная БД)")
        return True
        
    else:
        print(f"❌ Неизвестный тип БД: {db_type}")
        return False
        
    return True

def main():
    """Основная функция"""
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python scripts/migrate.py <db_type> [command]")
        print("")
        print("Типы БД:")
        print("  metadata  - БД метаданных (пайплайны, источники)")
        print("  staging   - Рабочая БД (временное хранение)")
        print("  target    - Целевая БД (ClickHouse)")
        print("  all       - Все БД")
        print("")
        print("Команды:")
        print("  upgrade head  - Применить все миграции (по умолчанию)")
        print("  downgrade -1  - Откатить последнюю миграцию")
        print("  current       - Показать текущую версию")
        print("  history       - Показать историю миграций")
        sys.exit(1)
    
    db_type = sys.argv[1]
    command = sys.argv[2] if len(sys.argv) > 2 else "upgrade head"
    
    if db_type == "all":
        success = True
        for db in ["metadata", "staging", "target"]:
            print(f"\n{'='*50}")
            print(f"Работа с БД: {db}")
            print(f"{'='*50}")
            if not run_migration(db, command):
                success = False
                break
        
        if success:
            print(f"\n✅ Все миграции выполнены успешно!")
        else:
            print(f"\n❌ Ошибка при выполнении миграций!")
            sys.exit(1)
    else:
        if not run_migration(db_type, command):
            sys.exit(1)

if __name__ == "__main__":
    main()
