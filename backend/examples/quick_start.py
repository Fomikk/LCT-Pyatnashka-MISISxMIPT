#!/usr/bin/env python3
"""
Быстрый старт - пример использования ETL системы
"""

import sys
from pathlib import Path
from datetime import datetime

# Добавляем путь к приложению
sys.path.append(str(Path(__file__).parent.parent))

from app.models.metadata import DataSource, Pipeline, PipelineRun, DataSourceType, PipelineStatus, PipelineRunStatus
from app.models.staging import FileMetadata, FileStatus
from app.connectors.database_manager import db_manager


def create_sample_data():
    """Создание примерных данных для демонстрации"""
    
    # Получаем сессию для метаданных БД
    session = db_manager.get_metadata_session()
    
    try:
        # Создаем источник данных
        data_source = DataSource(
            name="CSV файл продаж",
            description="Ежемесячные данные продаж в CSV формате",
            source_type="file",
            connection_config={
                "file_path": "/data/sales_2024.csv",
                "delimiter": ",",
                "encoding": "utf-8",
                "has_header": True
            },
            is_active=True
        )
        session.add(data_source)
        session.flush()  # Получаем ID
        
        # Создаем пайплайн
        pipeline = Pipeline(
            name="Обработка продаж",
            description="Загрузка и обработка данных продаж",
            data_source_id=data_source.id,
            status="active",
            configuration={
                "validation_rules": {
                    "required_columns": ["date", "amount", "product_id", "customer_id"],
                    "data_types": {
                        "date": "date",
                        "amount": "float",
                        "product_id": "integer",
                        "customer_id": "integer"
                    },
                    "constraints": {
                        "amount": {"min": 0},
                        "date": {"format": "%Y-%m-%d"}
                    }
                },
                "transformations": [
                    "clean_duplicates",
                    "validate_amounts", 
                    "enrich_product_data",
                    "calculate_totals"
                ],
                "output_config": {
                    "target_table": "sales_final",
                    "partition_by": "date"
                }
            },
            schedule_cron="0 2 * * *",  # Каждый день в 2:00
            max_retries=3,
            timeout_seconds=3600,
            tags=["sales", "monthly", "critical"]
        )
        session.add(pipeline)
        session.flush()
        
        # Создаем запуск пайплайна
        pipeline_run = PipelineRun(
            pipeline_id=pipeline.id,
            status="success",
            started_at=datetime.now(),
            finished_at=datetime.now(),
            duration_seconds=120,
            records_processed=10000,
            records_failed=0,
            triggered_by="manual_test",
            retry_count=0
        )
        session.add(pipeline_run)
        session.flush()
        
        # Создаем результат анализа
        from app.models.metadata import AnalysisResult
        
        analysis_result = AnalysisResult(
            pipeline_run_id=pipeline_run.id,
            analysis_type="data_quality",
            result_data={
                "completeness": 99.8,
                "accuracy": 98.5,
                "consistency": 97.2,
                "validity": 99.1
            },
            metrics={
                "null_percentage": 0.2,
                "duplicate_percentage": 0.1,
                "outlier_percentage": 1.5
            },
            recommendations=[
                "Проверить данные за последний месяц на предмет аномалий",
                "Добавить валидацию для полей customer_id",
                "Настроить алерты при превышении порога outliers > 2%"
            ],
            is_alert=False,
            alert_level=None
        )
        session.add(analysis_result)
        
        session.commit()
        
        print("✅ Примерные данные созданы:")
        print(f"   • Источник данных: {data_source.name} (ID: {data_source.id})")
        print(f"   • Пайплайн: {pipeline.name} (ID: {pipeline.id})")
        print(f"   • Запуск пайплайна: ID {pipeline_run.id}")
        print(f"   • Результат анализа: ID {analysis_result.id}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Ошибка создания данных: {e}")
        raise
    finally:
        session.close()


def create_sample_file():
    """Создание примера файла в рабочей БД"""
    
    session = db_manager.get_staging_session()
    
    try:
        # Создаем метаданные файла
        file_metadata = FileMetadata(
            filename="sales_2024_01.csv",
            original_filename="sales_2024_01.csv",
            file_path="/data/upload/sales_2024_01.csv",
            file_size=1024000,  # 1MB
            file_hash="a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
            mime_type="text/csv",
            encoding="utf-8",
            status="processed",
            uploaded_by="admin",
            processing_started_at=datetime.now(),
            processing_finished_at=datetime.now(),
            metadata={
                "columns": ["date", "amount", "product_id", "customer_id"],
                "row_count": 10000,
                "delimiter": ",",
                "has_header": True
            }
        )
        session.add(file_metadata)
        session.commit()
        
        print(f"✅ Файл создан: {file_metadata.filename} (ID: {file_metadata.id})")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Ошибка создания файла: {e}")
        raise
    finally:
        session.close()


def show_sample_queries():
    """Показать примеры запросов"""
    
    print("\n📊 Примеры запросов:")
    print("=" * 50)
    
    # Запрос к метаданным БД
    try:
        with db_manager.get_metadata_session() as session:
            # Получаем все пайплайны
            pipelines = session.execute("""
                SELECT p.name, p.status, ds.name as source_name, p.created_at
                FROM pipelines p
                JOIN data_sources ds ON p.data_source_id = ds.id
                ORDER BY p.created_at DESC
            """)
            
            print("\n🗄️  Пайплайны:")
            for pipeline in pipelines:
                print(f"   • {pipeline[0]} ({pipeline[1]}) - источник: {pipeline[2]}")
            
            # Получаем последние запуски
            runs = session.execute("""
                SELECT p.name, pr.status, pr.records_processed, pr.duration_seconds
                FROM pipeline_runs pr
                JOIN pipelines p ON pr.pipeline_id = p.id
                ORDER BY pr.created_at DESC
                LIMIT 5
            """)
            
            print("\n🔄 Последние запуски:")
            for run in runs:
                print(f"   • {run[0]}: {run[1]}, записей: {run[2]}, время: {run[3]}с")
                
    except Exception as e:
        print(f"❌ Ошибка запроса к метаданным: {e}")
    
    # Запрос к рабочей БД
    try:
        with db_manager.get_staging_session() as session:
            files = session.execute("""
                SELECT filename, status, file_size, created_at
                FROM file_metadata
                ORDER BY created_at DESC
                LIMIT 5
            """)
            
            print("\n📁 Последние файлы:")
            for file in files:
                print(f"   • {file[0]} ({file[1]}), размер: {file[2]} байт")
                
    except Exception as e:
        print(f"❌ Ошибка запроса к рабочей БД: {e}")


def main():
    """Основная функция"""
    print("🚀 Быстрый старт ETL системы")
    print("=" * 50)
    
    # Проверяем подключения
    print("\n🔍 Проверка подключений...")
    results = db_manager.test_connections()
    
    if not all(results.values()):
        print("❌ Не все БД доступны. Запустите Docker контейнеры:")
        print("   docker-compose up -d metadata-postgres staging-postgres target-clickhouse")
        return
    
    print("✅ Все БД доступны")
    
    # Создаем примерные данные
    print("\n📝 Создание примерных данных...")
    try:
        create_sample_data()
        create_sample_file()
        
        # Показываем примеры запросов
        show_sample_queries()
        
        print("\n🎉 Быстрый старт завершен!")
        print("\n📚 Следующие шаги:")
        print("   1. Изучите README_ETL_DATABASE.md для подробной документации")
        print("   2. Используйте python scripts/db_cli.py для управления БД")
        print("   3. Создайте свои пайплайны через API или напрямую в БД")
        print("   4. Настройте мониторинг и алерты")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print("\n💡 Убедитесь, что:")
        print("   1. Все Docker контейнеры запущены")
        print("   2. Миграции применены: python scripts/migrate.py all upgrade head")
        print("   3. ClickHouse инициализирован: python scripts/init_clickhouse.py")


if __name__ == "__main__":
    main()
