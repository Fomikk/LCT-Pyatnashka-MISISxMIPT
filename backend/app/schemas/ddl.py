from pydantic import BaseModel
from typing import Any


class DDLRequest(BaseModel):
    target_system: str  # postgres|clickhouse|hive
    table_name: str
    sample: dict[str, Any]


class DDLResponse(BaseModel):
    ddl_sql: str
    suggestions: list[str]


