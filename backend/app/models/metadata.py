"""
Модели для БД метаданных (информация о пайплайнах, источниках данных)
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Enum as SQLEnum, ForeignKey,
    Integer, JSON, String, Text, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, SoftDeleteMixin


class DataSourceType(str, Enum):
    """Типы источников данных"""
    FILE = "file"
    DATABASE = "database"
    API = "api"
    KAFKA = "kafka"
    S3 = "s3"
    HDFS = "hdfs"


class PipelineStatus(str, Enum):
    """Статусы пайплайнов"""
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"


class PipelineRunStatus(str, Enum):
    """Статусы выполнения пайплайнов"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DataSource(Base, TimestampMixin, SoftDeleteMixin):
    """Источники данных"""
    __tablename__ = "data_sources"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, comment="Название источника")
    description = Column(Text, comment="Описание источника")
    source_type = Column(
        String(50), 
        nullable=False,
        comment="Тип источника данных"
    )
    connection_config = Column(
        JSON, 
        nullable=False,
        comment="Конфигурация подключения к источнику"
    )
    is_active = Column(
        Boolean, 
        default=True, 
        nullable=False,
        comment="Активен ли источник"
    )
    
    # Связи
    pipelines = relationship(
        "Pipeline", 
        back_populates="data_source",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        UniqueConstraint('name', name='uq_data_source_name'),
        Index('idx_data_source_type', 'source_type'),
        Index('idx_data_source_active', 'is_active'),
    )


class Pipeline(Base, TimestampMixin, SoftDeleteMixin):
    """Пайплайны ETL"""
    __tablename__ = "pipelines"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, comment="Название пайплайна")
    description = Column(Text, comment="Описание пайплайна")
    data_source_id = Column(
        Integer, 
        ForeignKey("data_sources.id", ondelete="CASCADE"),
        nullable=False,
        comment="ID источника данных"
    )
    status = Column(
        String(50),
        default="draft",
        nullable=False,
        comment="Статус пайплайна"
    )
    configuration = Column(
        JSON,
        nullable=False,
        comment="Конфигурация пайплайна"
    )
    schedule_cron = Column(
        String(100),
        comment="Cron выражение для расписания"
    )
    max_retries = Column(
        Integer,
        default=3,
        nullable=False,
        comment="Максимальное количество повторов"
    )
    timeout_seconds = Column(
        Integer,
        comment="Таймаут выполнения в секундах"
    )
    tags = Column(
        JSON,
        comment="Теги для группировки пайплайнов"
    )
    
    # Связи
    data_source = relationship("DataSource", back_populates="pipelines")
    runs = relationship(
        "PipelineRun",
        back_populates="pipeline",
        cascade="all, delete-orphan",
        order_by="PipelineRun.created_at.desc()"
    )
    
    __table_args__ = (
        UniqueConstraint('name', name='uq_pipeline_name'),
        Index('idx_pipeline_status', 'status'),
        Index('idx_pipeline_data_source', 'data_source_id'),
        Index('idx_pipeline_schedule', 'schedule_cron'),
    )


class PipelineRun(Base, TimestampMixin):
    """Запуски пайплайнов"""
    __tablename__ = "pipeline_runs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pipeline_id = Column(
        Integer,
        ForeignKey("pipelines.id", ondelete="CASCADE"),
        nullable=False,
        comment="ID пайплайна"
    )
    status = Column(
        String(50),
        default="pending",
        nullable=False,
        comment="Статус выполнения"
    )
    started_at = Column(
        DateTime(timezone=True),
        comment="Время начала выполнения"
    )
    finished_at = Column(
        DateTime(timezone=True),
        comment="Время завершения выполнения"
    )
    duration_seconds = Column(
        Integer,
        comment="Длительность выполнения в секундах"
    )
    records_processed = Column(
        BigInteger,
        comment="Количество обработанных записей"
    )
    records_failed = Column(
        BigInteger,
        comment="Количество неудачно обработанных записей"
    )
    error_message = Column(
        Text,
        comment="Сообщение об ошибке"
    )
    execution_context = Column(
        JSON,
        comment="Контекст выполнения (параметры, переменные)"
    )
    retry_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Количество повторов"
    )
    triggered_by = Column(
        String(255),
        comment="Кто/что запустило пайплайн (user, scheduler, api)"
    )
    
    # Связи
    pipeline = relationship("Pipeline", back_populates="runs")
    analysis_results = relationship(
        "AnalysisResult",
        back_populates="pipeline_run",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index('idx_pipeline_run_pipeline', 'pipeline_id'),
        Index('idx_pipeline_run_status', 'status'),
        Index('idx_pipeline_run_started', 'started_at'),
        Index('idx_pipeline_run_finished', 'finished_at'),
    )


class AnalysisResult(Base, TimestampMixin):
    """Результаты анализа данных ML"""
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pipeline_run_id = Column(
        Integer,
        ForeignKey("pipeline_runs.id", ondelete="CASCADE"),
        nullable=False,
        comment="ID запуска пайплайна"
    )
    analysis_type = Column(
        String(100),
        nullable=False,
        comment="Тип анализа (data_quality, anomaly_detection, etc.)"
    )
    result_data = Column(
        JSON,
        nullable=False,
        comment="Результаты анализа в JSON формате"
    )
    metrics = Column(
        JSON,
        comment="Метрики качества данных"
    )
    recommendations = Column(
        JSON,
        comment="Рекомендации по улучшению данных"
    )
    is_alert = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Требует ли внимания (алерт)"
    )
    alert_level = Column(
        String(20),
        comment="Уровень алерта (low, medium, high, critical)"
    )
    
    # Связи
    pipeline_run = relationship("PipelineRun", back_populates="analysis_results")
    
    __table_args__ = (
        Index('idx_analysis_pipeline_run', 'pipeline_run_id'),
        Index('idx_analysis_type', 'analysis_type'),
        Index('idx_analysis_alert', 'is_alert'),
        Index('idx_analysis_created', 'created_at'),
    )
