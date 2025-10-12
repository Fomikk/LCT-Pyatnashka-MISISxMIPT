# backend/app/core/config.py

from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import ConfigDict, Field, AliasChoices
from dotenv import load_dotenv

# Подтягиваем .env (pydantic-settings тоже умеет, но так удобнее локально)
load_dotenv()


class Settings(BaseSettings):
    # ===== Общие =====
    environment: str = "dev"
    cors_allow_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # ===== Внешние сервисы (заглушки / опционально) =====
    airflow_base_url: str = "http://airflow:8080"
    llm_base_url: str = "http://llm:8000"

    # ===== БД: метаданные (PostgreSQL) =====
    metadata_postgres_host: str = "localhost"
    metadata_postgres_port: int = 5432
    metadata_postgres_user: str = "metadata_user"
    metadata_postgres_password: str = "metadata_password"
    metadata_postgres_database: str = "etl_metadata"

    # ===== БД: staging (PostgreSQL) =====
    staging_postgres_host: str = "localhost"
    staging_postgres_port: int = 5433
    staging_postgres_user: str = "staging_user"
    staging_postgres_password: str = "staging_password"
    staging_postgres_database: str = "etl_staging"

    # ===== Целевая БД (ClickHouse) =====
    target_clickhouse_host: str = "localhost"
    target_clickhouse_port: int = 8123
    target_clickhouse_user: str = "default"
    target_clickhouse_password: str = "clickhouse_password"
    target_clickhouse_database: str = "etl_target"

    # ===== Legacy совместимость =====
    postgres_dsn: str = ""
    clickhouse_host: str = "localhost"
    clickhouse_port: int = 8123
    clickhouse_user: str = "default"
    clickhouse_password: str = ""
    clickhouse_database: str = "default"

    # ===== HDFS/Kafka (заглушки) =====
    hdfs_host: str = "hdfs"
    hdfs_port: int = 9870
    kafka_bootstrap: str = "kafka:9092"

    # ===== Yandex Cloud / YandexGPT =====
    # Принимаем и верхний, и нижний регистры из .env:
    # YC_FOLDER_ID / yc_folder_id, YC_API_KEY / yc_api_key, YC_MODEL / yc_model
    yc_folder_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("YC_FOLDER_ID", "yc_folder_id"),
    )
    yc_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("YC_API_KEY", "yc_api_key"),
    )
    yc_model: str = Field(
        default="yandexgpt",  # варианты: yandexgpt, yandexgpt-lite, yandexgpt-pro
        validation_alias=AliasChoices("YC_MODEL", "yc_model"),
    )

    # ===== Pydantic v2 settings =====
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,  # включает алиасы
        extra="ignore",         # игнорировать лишние ключи из .env
    )

    # ===== Удобные свойства =====
    @property
    def metadata_postgres_dsn(self) -> str:
        return (
            f"postgresql+psycopg2://{self.metadata_postgres_user}:"
            f"{self.metadata_postgres_password}@{self.metadata_postgres_host}:"
            f"{self.metadata_postgres_port}/{self.metadata_postgres_database}"
        )

    @property
    def staging_postgres_dsn(self) -> str:
        return (
            f"postgresql+psycopg2://{self.staging_postgres_user}:"
            f"{self.staging_postgres_password}@{self.staging_postgres_host}:"
            f"{self.staging_postgres_port}/{self.staging_postgres_database}"
        )

    @property
    def cors_origins(self) -> list[str]:
        return self.cors_allow_origins


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
