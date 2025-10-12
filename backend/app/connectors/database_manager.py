"""
Менеджер для работы с базами данных ETL системы
"""

from typing import Optional, Dict, Any, List
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
import clickhouse_connect
from loguru import logger

from app.core.config import get_settings


class DatabaseManager:
    """Менеджер для работы с базами данных"""
    
    def __init__(self):
        self.settings = get_settings()
        self._metadata_engine = None
        self._staging_engine = None
        self._clickhouse_client = None
        
    @property
    def metadata_engine(self):
        """Движок для метаданных БД"""
        if self._metadata_engine is None:
            self._metadata_engine = create_engine(
                self.settings.metadata_postgres_dsn,
                pool_pre_ping=True,
                pool_recycle=300
            )
        return self._metadata_engine
    
    @property
    def staging_engine(self):
        """Движок для рабочей БД"""
        if self._staging_engine is None:
            self._staging_engine = create_engine(
                self.settings.staging_postgres_dsn,
                pool_pre_ping=True,
                pool_recycle=300
            )
        return self._staging_engine
    
    @property
    def clickhouse_client(self):
        """Клиент ClickHouse"""
        if self._clickhouse_client is None:
            self._clickhouse_client = clickhouse_connect.get_client(
                host=self.settings.target_clickhouse_host,
                port=self.settings.target_clickhouse_port,
                username=self.settings.target_clickhouse_user,
                password=self.settings.target_clickhouse_password,
                database=self.settings.target_clickhouse_database
            )
        return self._clickhouse_client
    
    def get_metadata_session(self) -> Session:
        """Получить сессию для метаданных БД"""
        Session = sessionmaker(bind=self.metadata_engine)
        return Session()
    
    def get_staging_session(self) -> Session:
        """Получить сессию для рабочей БД"""
        Session = sessionmaker(bind=self.staging_engine)
        return Session()
    
    def test_connections(self) -> Dict[str, bool]:
        """Проверить подключения ко всем БД"""
        results = {}
        
        # Проверка метаданных БД
        try:
            with self.metadata_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            results["metadata"] = True
            logger.info("✅ Подключение к метаданным БД успешно")
        except Exception as e:
            results["metadata"] = False
            logger.error(f"❌ Ошибка подключения к метаданным БД: {e}")
        
        # Проверка рабочей БД
        try:
            with self.staging_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            results["staging"] = True
            logger.info("✅ Подключение к рабочей БД успешно")
        except Exception as e:
            results["staging"] = False
            logger.error(f"❌ Ошибка подключения к рабочей БД: {e}")
        
        # Проверка ClickHouse
        try:
            import subprocess
            result = subprocess.run([
                "curl", "-s", "-X", "POST", 
                f"http://{self.settings.target_clickhouse_host}:{self.settings.target_clickhouse_port}/",
                "--data-binary", "SELECT 1",
                "--user", f"{self.settings.target_clickhouse_user}:{self.settings.target_clickhouse_password}"
            ], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                results["target"] = True
                logger.info("✅ Подключение к ClickHouse успешно")
            else:
                results["target"] = False
                logger.error(f"❌ Ошибка подключения к ClickHouse: {result.stderr}")
        except Exception as e:
            results["target"] = False
            logger.error(f"❌ Ошибка подключения к ClickHouse: {e}")
        
        return results
    
    def get_database_stats(self) -> Dict[str, Dict[str, Any]]:
        """Получить статистику по базам данных"""
        stats = {}
        
        # Статистика метаданных БД
        try:
            with self.metadata_engine.connect() as conn:
                # Размер БД
                db_size = conn.execute(text("""
                    SELECT pg_size_pretty(pg_database_size(current_database())) as size
                """)).scalar()
                
                # Количество таблиц
                table_count = conn.execute(text("""
                    SELECT count(*) FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)).scalar()
                
                # Количество записей в основных таблицах
                pipeline_count = conn.execute(text("SELECT count(*) FROM pipelines")).scalar()
                run_count = conn.execute(text("SELECT count(*) FROM pipeline_runs")).scalar()
                
                stats["metadata"] = {
                    "size": db_size,
                    "tables": table_count,
                    "pipelines": pipeline_count,
                    "pipeline_runs": run_count
                }
        except Exception as e:
            logger.error(f"Ошибка получения статистики метаданных БД: {e}")
            stats["metadata"] = {"error": str(e)}
        
        # Статистика рабочей БД
        try:
            with self.staging_engine.connect() as conn:
                # Размер БД
                db_size = conn.execute(text("""
                    SELECT pg_size_pretty(pg_database_size(current_database())) as size
                """)).scalar()
                
                # Количество таблиц
                table_count = conn.execute(text("""
                    SELECT count(*) FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)).scalar()
                
                # Количество записей в основных таблицах
                file_count = conn.execute(text("SELECT count(*) FROM file_metadata")).scalar()
                log_count = conn.execute(text("SELECT count(*) FROM processing_logs")).scalar()
                
                stats["staging"] = {
                    "size": db_size,
                    "tables": table_count,
                    "files": file_count,
                    "processing_logs": log_count
                }
        except Exception as e:
            logger.error(f"Ошибка получения статистики рабочей БД: {e}")
            stats["staging"] = {"error": str(e)}
        
        # Статистика ClickHouse
        try:
            import subprocess
            
            # Получаем размер БД
            result = subprocess.run([
                "curl", "-s", "-u", "default:clickhouse_password",
                "http://localhost:8123/?query=SELECT%20formatReadableSize(sum(total_bytes))%20FROM%20system.tables%20WHERE%20database%20%3D%20%27etl_target%27"
            ], capture_output=True, text=True)
            db_size = result.stdout.strip() if result.returncode == 0 else "Unknown"
            
            # Получаем количество таблиц
            result = subprocess.run([
                "curl", "-s", "-u", "default:clickhouse_password",
                "http://localhost:8123/?query=SELECT%20count()%20FROM%20system.tables%20WHERE%20database%20%3D%20%27etl_target%27"
            ], capture_output=True, text=True)
            table_count = result.stdout.strip() if result.returncode == 0 else "Unknown"
            
            # Получаем количество метрик качества
            result = subprocess.run([
                "curl", "-s", "-u", "default:clickhouse_password",
                "http://localhost:8123/?query=SELECT%20count()%20FROM%20etl_target.data_quality_metrics"
            ], capture_output=True, text=True)
            metrics_count = result.stdout.strip() if result.returncode == 0 else "Unknown"
            
            # Получаем количество бизнес-метрик
            result = subprocess.run([
                "curl", "-s", "-u", "default:clickhouse_password",
                "http://localhost:8123/?query=SELECT%20count()%20FROM%20etl_target.business_metrics"
            ], capture_output=True, text=True)
            business_count = result.stdout.strip() if result.returncode == 0 else "Unknown"
            
            stats["target"] = {
                "size": db_size,
                "tables": table_count,
                "quality_metrics": metrics_count,
                "business_metrics": business_count
            }
        except Exception as e:
            logger.error(f"Ошибка получения статистики ClickHouse: {e}")
            stats["target"] = {"error": str(e)}
        
        return stats
    
    def cleanup_old_data(self, days: int = 30) -> Dict[str, int]:
        """Очистка старых данных"""
        results = {}
        
        # Очистка старых запусков пайплайнов
        try:
            with self.get_metadata_session() as session:
                # Удаляем старые запуски пайплайнов (кроме последних 100)
                result = session.execute(text("""
                    DELETE FROM pipeline_runs 
                    WHERE created_at < NOW() - INTERVAL '%s days'
                    AND id NOT IN (
                        SELECT id FROM pipeline_runs 
                        ORDER BY created_at DESC 
                        LIMIT 100
                    )
                """, (days,)))
                results["pipeline_runs_deleted"] = result.rowcount
                session.commit()
        except Exception as e:
            logger.error(f"Ошибка очистки запусков пайплайнов: {e}")
            results["pipeline_runs_error"] = str(e)
        
        # Очистка старых файлов
        try:
            with self.get_staging_session() as session:
                # Удаляем старые файлы
                result = session.execute(text("""
                    DELETE FROM file_metadata 
                    WHERE created_at < NOW() - INTERVAL '%s days'
                    AND status IN ('processed', 'failed')
                """, (days,)))
                results["files_deleted"] = result.rowcount
                session.commit()
        except Exception as e:
            logger.error(f"Ошибка очистки файлов: {e}")
            results["files_error"] = str(e)
        
        # Очистка старых логов обработки
        try:
            with self.get_staging_session() as session:
                result = session.execute(text("""
                    DELETE FROM processing_logs 
                    WHERE created_at < NOW() - INTERVAL '%s days'
                """, (days,)))
                results["logs_deleted"] = result.rowcount
                session.commit()
        except Exception as e:
            logger.error(f"Ошибка очистки логов: {e}")
            results["logs_error"] = str(e)
        
        return results
    
    def backup_databases(self, backup_dir: str) -> Dict[str, str]:
        """Создание бэкапов баз данных"""
        import subprocess
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results = {}
        
        # Бэкап метаданных БД
        try:
            backup_file = f"{backup_dir}/metadata_backup_{timestamp}.sql"
            cmd = [
                "pg_dump",
                "-h", self.settings.metadata_postgres_host,
                "-p", str(self.settings.metadata_postgres_port),
                "-U", self.settings.metadata_postgres_user,
                "-d", self.settings.metadata_postgres_database,
                "-f", backup_file
            ]
            subprocess.run(cmd, check=True, env={"PGPASSWORD": self.settings.metadata_postgres_password})
            results["metadata_backup"] = backup_file
            logger.info(f"✅ Бэкап метаданных БД создан: {backup_file}")
        except Exception as e:
            logger.error(f"❌ Ошибка создания бэкапа метаданных БД: {e}")
            results["metadata_backup_error"] = str(e)
        
        # Бэкап рабочей БД
        try:
            backup_file = f"{backup_dir}/staging_backup_{timestamp}.sql"
            cmd = [
                "pg_dump",
                "-h", self.settings.staging_postgres_host,
                "-p", str(self.settings.staging_postgres_port),
                "-U", self.settings.staging_postgres_user,
                "-d", self.settings.staging_postgres_database,
                "-f", backup_file
            ]
            subprocess.run(cmd, check=True, env={"PGPASSWORD": self.settings.staging_postgres_password})
            results["staging_backup"] = backup_file
            logger.info(f"✅ Бэкап рабочей БД создан: {backup_file}")
        except Exception as e:
            logger.error(f"❌ Ошибка создания бэкапа рабочей БД: {e}")
            results["staging_backup_error"] = str(e)
        
        # Бэкап ClickHouse (экспорт данных)
        try:
            backup_file = f"{backup_dir}/clickhouse_backup_{timestamp}.sql"
            # Экспорт основных таблиц
            tables = ["data_quality_metrics", "business_metrics", "data_lineage", "data_catalog", "etl_audit_log"]
            with open(backup_file, 'w') as f:
                for table in tables:
                    try:
                        data = self.clickhouse_client.query_df(f"SELECT * FROM {table}")
                        f.write(f"-- Table: {table}\n")
                        data.to_csv(f, mode='a', index=False)
                        f.write("\n")
                    except Exception as table_error:
                        f.write(f"-- Error exporting table {table}: {table_error}\n")
            results["clickhouse_backup"] = backup_file
            logger.info(f"✅ Бэкап ClickHouse создан: {backup_file}")
        except Exception as e:
            logger.error(f"❌ Ошибка создания бэкапа ClickHouse: {e}")
            results["clickhouse_backup_error"] = str(e)
        
        return results


# Глобальный экземпляр менеджера
db_manager = DatabaseManager()
