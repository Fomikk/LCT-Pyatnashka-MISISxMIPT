#!/usr/bin/env python3
"""
CLI утилита для управления базами данных ETL системы
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Добавляем путь к приложению
sys.path.append(str(Path(__file__).parent.parent))

from app.connectors.database_manager import db_manager


def test_connections():
    """Проверить подключения к БД"""
    print("🔍 Проверка подключений к базам данных...")
    results = db_manager.test_connections()
    
    for db_name, status in results.items():
        if status:
            print(f"✅ {db_name.upper()} БД: подключение успешно")
        else:
            print(f"❌ {db_name.upper()} БД: ошибка подключения")
    
    return all(results.values())


def show_stats():
    """Показать статистику по БД"""
    print("📊 Статистика баз данных:")
    print("=" * 50)
    
    stats = db_manager.get_database_stats()
    
    for db_name, db_stats in stats.items():
        print(f"\n🗄️  {db_name.upper()} БД:")
        if "error" in db_stats:
            print(f"   ❌ Ошибка: {db_stats['error']}")
        else:
            for key, value in db_stats.items():
                print(f"   • {key}: {value}")


def cleanup_old_data():
    """Очистка старых данных"""
    print("🧹 Очистка старых данных...")
    
    # По умолчанию удаляем данные старше 30 дней
    results = db_manager.cleanup_old_data(days=30)
    
    print("Результаты очистки:")
    for key, value in results.items():
        if "error" in key:
            print(f"   ❌ {key}: {value}")
        else:
            print(f"   ✅ {key}: {value}")


def create_backup():
    """Создание бэкапа"""
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)
    
    print(f"💾 Создание бэкапа в директории: {backup_dir.absolute()}")
    
    results = db_manager.backup_databases(str(backup_dir))
    
    print("Результаты бэкапа:")
    for key, value in results.items():
        if "error" in key:
            print(f"   ❌ {key}: {value}")
        else:
            print(f"   ✅ {key}: {value}")


def show_tables():
    """Показать список таблиц"""
    print("📋 Список таблиц в базах данных:")
    print("=" * 50)
    
    # Метаданные БД
    print("\n🗄️  МЕТАДАННЫЕ БД:")
    try:
        with db_manager.get_metadata_session() as session:
            tables = session.execute("""
                SELECT table_name, table_type 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            for table in tables:
                print(f"   • {table[0]} ({table[1]})")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # Рабочая БД
    print("\n🗄️  РАБОЧАЯ БД:")
    try:
        with db_manager.get_staging_session() as session:
            tables = session.execute("""
                SELECT table_name, table_type 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            for table in tables:
                print(f"   • {table[0]} ({table[1]})")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # ClickHouse
    print("\n🗄️  CLICKHOUSE:")
    try:
        import subprocess
        result = subprocess.run([
            "curl", "-s", "-u", "default:clickhouse_password",
            "http://localhost:8123/?query=SELECT%20name%2C%20engine%20FROM%20system.tables%20WHERE%20database%20%3D%20%27etl_target%27%20ORDER%20BY%20name"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if line.strip():
                    parts = line.strip().split('\t')
                    if len(parts) >= 2:
                        print(f"   • {parts[0]} ({parts[1]})")
        else:
            print(f"   ❌ Ошибка запроса: {result.stderr}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")


def show_recent_runs():
    """Показать последние запуски пайплайнов"""
    print("🔄 Последние запуски пайплайнов:")
    print("=" * 50)
    
    try:
        with db_manager.get_metadata_session() as session:
            runs = session.execute("""
                SELECT 
                    p.name as pipeline_name,
                    pr.status,
                    pr.started_at,
                    pr.finished_at,
                    pr.duration_seconds,
                    pr.records_processed,
                    pr.error_message
                FROM pipelines p
                JOIN pipeline_runs pr ON p.id = pr.pipeline_id
                ORDER BY pr.created_at DESC
                LIMIT 10
            """)
            
            for run in runs:
                print(f"\n📋 Пайплайн: {run[0]}")
                print(f"   Статус: {run[1]}")
                print(f"   Начало: {run[2]}")
                print(f"   Завершение: {run[3]}")
                print(f"   Длительность: {run[4]} сек")
                print(f"   Записей: {run[5]}")
                if run[6]:
                    print(f"   Ошибка: {run[6][:100]}...")
    except Exception as e:
        print(f"❌ Ошибка: {e}")


def show_data_quality():
    """Показать метрики качества данных"""
    print("📊 Метрики качества данных:")
    print("=" * 50)
    
    try:
        # Получаем последние метрики качества
        metrics = db_manager.clickhouse_client.query("""
            SELECT 
                table_name,
                metric_name,
                metric_value,
                is_passed,
                created_at
            FROM data_quality_metrics
            WHERE created_at >= now() - INTERVAL 7 DAY
            ORDER BY created_at DESC
            LIMIT 20
        """)
        
        for metric in metrics.result_rows:
            status = "✅" if metric[3] else "❌"
            print(f"{status} {metric[0]}.{metric[1]}: {metric[2]} ({metric[4]})")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")


def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description="CLI утилита для управления БД ETL системы")
    
    subparsers = parser.add_subparsers(dest="command", help="Доступные команды")
    
    # Команда проверки подключений
    subparsers.add_parser("test", help="Проверить подключения к БД")
    
    # Команда статистики
    subparsers.add_parser("stats", help="Показать статистику БД")
    
    # Команда очистки
    cleanup_parser = subparsers.add_parser("cleanup", help="Очистить старые данные")
    cleanup_parser.add_argument("--days", type=int, default=30, help="Удалить данные старше N дней")
    
    # Команда бэкапа
    subparsers.add_parser("backup", help="Создать бэкап БД")
    
    # Команда списка таблиц
    subparsers.add_parser("tables", help="Показать список таблиц")
    
    # Команда запусков пайплайнов
    subparsers.add_parser("runs", help="Показать последние запуски пайплайнов")
    
    # Команда качества данных
    subparsers.add_parser("quality", help="Показать метрики качества данных")
    
    # Команда инициализации
    subparsers.add_parser("init", help="Инициализировать все БД")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == "test":
            success = test_connections()
            sys.exit(0 if success else 1)
            
        elif args.command == "stats":
            show_stats()
            
        elif args.command == "cleanup":
            if args.days:
                results = db_manager.cleanup_old_data(days=args.days)
                print("Результаты очистки:")
                for key, value in results.items():
                    print(f"   {key}: {value}")
            else:
                cleanup_old_data()
                
        elif args.command == "backup":
            create_backup()
            
        elif args.command == "tables":
            show_tables()
            
        elif args.command == "runs":
            show_recent_runs()
            
        elif args.command == "quality":
            show_data_quality()
            
        elif args.command == "init":
            print("🚀 Инициализация БД...")
            
            # Проверяем подключения
            if not test_connections():
                print("❌ Не все БД доступны. Проверьте подключения.")
                sys.exit(1)
            
            # Показываем статистику
            show_stats()
            
            print("\n✅ Инициализация завершена!")
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Операция прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
