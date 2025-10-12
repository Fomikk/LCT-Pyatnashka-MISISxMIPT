"""
Модели SQLAlchemy для ETL системы
"""

from .base import Base, TimestampMixin, SoftDeleteMixin
from .metadata import (
    DataSource,
    Pipeline,
    PipelineRun,
    AnalysisResult,
    DataSourceType,
    PipelineStatus,
    PipelineRunStatus
)
from .staging import (
    StagingTable,
    FileMetadata,
    ProcessingLog,
    FileStatus,
    ProcessingStatus
)
from .target import (
    DataQualityMetrics,
    BusinessMetrics,
    DataLineage,
    DataCatalog,
    ETLAuditLog
)

__all__ = [
    # Базовые классы
    "Base",
    "TimestampMixin", 
    "SoftDeleteMixin",
    
    # Метаданные
    "DataSource",
    "Pipeline", 
    "PipelineRun",
    "AnalysisResult",
    "DataSourceType",
    "PipelineStatus",
    "PipelineRunStatus",
    
    # Рабочая БД
    "StagingTable",
    "FileMetadata",
    "ProcessingLog",
    "FileStatus",
    "ProcessingStatus",
    
    # Целевая БД
    "DataQualityMetrics",
    "BusinessMetrics",
    "DataLineage",
    "DataCatalog",
    "ETLAuditLog"
]