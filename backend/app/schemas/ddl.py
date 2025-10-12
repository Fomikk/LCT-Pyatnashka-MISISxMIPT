from pydantic import BaseModel, Field
from typing import Any, Optional, List


class DDLRequest(BaseModel):
    target_system: str = Field(description="postgres|clickhouse|mysql|hive|hdfs")
    table_name: str = Field(description="Имя таблицы")
    sample: dict[str, Any] = Field(description="Образец данных с колонками")
    schema_name: Optional[str] = Field(default=None, description="Имя схемы (для PostgreSQL)")
    database_name: Optional[str] = Field(default=None, description="Имя базы данных")


class DDLResponse(BaseModel):
    ddl_sql: str = Field(description="Основной DDL скрипт")
    suggestions: List[str] = Field(description="Рекомендации по оптимизации")
    indexes: Optional[List[str]] = Field(default=None, description="Дополнительные индексы")
    constraints: Optional[List[str]] = Field(default=None, description="Ограничения таблицы")
    performance_tips: Optional[List[str]] = Field(default=None, description="Советы по производительности")
    storage_requirements: Optional[dict[str, Any]] = Field(default=None, description="Оценка требований к хранению")


