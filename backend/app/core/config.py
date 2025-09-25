from functools import lru_cache
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os


load_dotenv()


class Settings(BaseModel):
    environment: str = Field(default=os.getenv("ENV", "dev"))
    cors_allow_origins: list[str] = Field(
        default_factory=lambda: os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")
    )

    # External services (stubs)
    airflow_base_url: str = Field(default=os.getenv("AIRFLOW_BASE_URL", "http://airflow:8080"))
    llm_base_url: str = Field(default=os.getenv("LLM_BASE_URL", "http://llm:8000"))

    # Databases
    postgres_dsn: str = Field(default=os.getenv("POSTGRES_DSN", "postgresql+psycopg2://user:pass@localhost:5432/db"))
    clickhouse_host: str = Field(default=os.getenv("CLICKHOUSE_HOST", "localhost"))
    clickhouse_port: int = Field(default=int(os.getenv("CLICKHOUSE_PORT", "8123")))
    clickhouse_user: str = Field(default=os.getenv("CLICKHOUSE_USER", "default"))
    clickhouse_password: str = Field(default=os.getenv("CLICKHOUSE_PASSWORD", ""))
    clickhouse_database: str = Field(default=os.getenv("CLICKHOUSE_DATABASE", "default"))

    # HDFS/Kafka (stubs)
    hdfs_host: str = Field(default=os.getenv("HDFS_HOST", "hdfs"))
    hdfs_port: int = Field(default=int(os.getenv("HDFS_PORT", "9870")))
    kafka_bootstrap: str = Field(default=os.getenv("KAFKA_BOOTSTRAP", "kafka:9092"))


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


