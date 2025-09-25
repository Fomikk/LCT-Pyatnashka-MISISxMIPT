from pydantic import BaseModel, Field
from typing import Optional, Any


class SourceInput(BaseModel):
    source_type: str = Field(description="file|postgres|clickhouse|kafka|hdfs")
    connection: dict[str, Any] = Field(default_factory=dict)
    sample: Optional[dict[str, Any]] = None


class ColumnProfile(BaseModel):
    name: str
    dtype: str
    nullable: bool
    example: Optional[Any] = None


class DataProfile(BaseModel):
    rows: int
    columns: list[ColumnProfile]
    is_time_series: bool = False
    notes: Optional[str] = None
    sample_data: Optional[list[dict[str, Any]]] = None


class FileAnalysisRequest(BaseModel):
    file_path: str
    file_type: str  # csv|json|xml
    connection: dict[str, Any] = Field(default_factory=dict)


class DBAnalysisRequest(BaseModel):
    db_type: str  # postgres|clickhouse
    table: str
    connection: dict[str, Any] = Field(default_factory=dict)


