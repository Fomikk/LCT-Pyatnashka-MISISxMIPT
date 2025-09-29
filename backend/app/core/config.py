from functools import lru_cache
from pydantic import BaseSettings
from dotenv import load_dotenv
import os


load_dotenv()


class Settings(BaseSettings):
    environment: str = "dev"
    cors_allow_origins: str = "*"

    # External services (stubs)
    airflow_base_url: str = "http://airflow:8080"
    llm_base_url: str = "http://llm:8000"

    # Databases - Метаданные (PostgreSQL)
    metadata_postgres_host: str = "localhost"
    metadata_postgres_port: int = 5432
    metadata_postgres_user: str = "metadata_user"
    metadata_postgres_password: str = "metadata_password"
    metadata_postgres_database: str = "etl_metadata"
    
    # Рабочая БД (PostgreSQL)
    staging_postgres_host: str = "localhost"
    staging_postgres_port: int = 5433
    staging_postgres_user: str = "staging_user"
    staging_postgres_password: str = "staging_password"
    staging_postgres_database: str = "etl_staging"
    
    # Целевая БД (ClickHouse)
    target_clickhouse_host: str = "localhost"
    target_clickhouse_port: int = 8123
    target_clickhouse_user: str = "default"
    target_clickhouse_password: str = "clickhouse_password"
    target_clickhouse_database: str = "etl_target"
    
    # Legacy поддержка (для совместимости)
    postgres_dsn: str = ""
    clickhouse_host: str = "localhost"
    clickhouse_port: int = 8123
    clickhouse_user: str = "default"
    clickhouse_password: str = ""
    clickhouse_database: str = "default"

    # HDFS/Kafka (stubs)
    hdfs_host: str = "hdfs"
    hdfs_port: int = 9870
    kafka_bootstrap: str = "kafka:9092"

    class Config:
        env_file = ".env"
    
    # Методы для получения строк подключения
    @property
    def metadata_postgres_dsn(self) -> str:
        """Строка подключения к БД метаданных"""
        return f"postgresql+psycopg2://{self.metadata_postgres_user}:{self.metadata_postgres_password}@{self.metadata_postgres_host}:{self.metadata_postgres_port}/{self.metadata_postgres_database}"
    
    @property
    def staging_postgres_dsn(self) -> str:
        """Строка подключения к рабочей БД"""
        return f"postgresql+psycopg2://{self.staging_postgres_user}:{self.staging_postgres_password}@{self.staging_postgres_host}:{self.staging_postgres_port}/{self.staging_postgres_database}"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


