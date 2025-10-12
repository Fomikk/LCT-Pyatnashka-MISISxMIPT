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
    unique_count: Optional[int] = None
    null_count: Optional[int] = None
    null_percentage: Optional[float] = None
    numeric_stats: Optional[dict[str, Any]] = None


class DataQualityMetrics(BaseModel):
    completeness_score: float = Field(ge=0, le=100, description="Оценка полноты данных (0-100)")
    consistency_score: float = Field(ge=0, le=100, description="Оценка консистентности данных (0-100)")
    uniqueness_score: float = Field(ge=0, le=100, description="Оценка уникальности данных (0-100)")
    issues: list[str] = Field(default_factory=list, description="Список проблем с данными")


class DataProfile(BaseModel):
    rows: int
    columns: list[ColumnProfile]
    is_time_series: bool = False
    notes: Optional[str] = None
    sample_data: Optional[list[dict[str, Any]]] = None
    data_quality: Optional[DataQualityMetrics] = None
    file_metadata: Optional[dict[str, Any]] = None


class FileAnalysisRequest(BaseModel):
    file_path: str
    file_type: str  # csv|json|xml
    connection: dict[str, Any] = Field(default_factory=dict)


class DBAnalysisRequest(BaseModel):
    db_type: str  # postgres|clickhouse
    table: str
    connection: dict[str, Any] = Field(default_factory=dict)


