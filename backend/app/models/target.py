"""
Модели для целевой БД (ClickHouse) - финальные результаты ETL
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, ForeignKey,
    Integer, JSON, String, Text, UniqueConstraint, Index, Numeric, Float
)
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class DataQualityMetrics(Base, TimestampMixin):
    """Метрики качества данных"""
    __tablename__ = "data_quality_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    table_name = Column(
        String(255),
        nullable=False,
        comment="Название таблицы"
    )
    column_name = Column(
        String(255),
        comment="Название столбца"
    )
    metric_name = Column(
        String(100),
        nullable=False,
        comment="Название метрики"
    )
    metric_value = Column(
        Float,
        nullable=False,
        comment="Значение метрики"
    )
    threshold_min = Column(
        Float,
        comment="Минимальный порог"
    )
    threshold_max = Column(
        Float,
        comment="Максимальный порог"
    )
    is_passed = Column(
        Boolean,
        nullable=False,
        comment="Прошла ли проверка"
    )
    pipeline_run_id = Column(
        Integer,
        comment="ID запуска пайплайна"
    )
    
    __table_args__ = (
        Index('idx_quality_table', 'table_name'),
        Index('idx_quality_column', 'column_name'),
        Index('idx_quality_metric', 'metric_name'),
        Index('idx_quality_passed', 'is_passed'),
        Index('idx_quality_pipeline_run', 'pipeline_run_id'),
    )


class BusinessMetrics(Base, TimestampMixin):
    """Бизнес метрики и KPI"""
    __tablename__ = "business_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_category = Column(
        String(100),
        nullable=False,
        comment="Категория метрики"
    )
    metric_name = Column(
        String(255),
        nullable=False,
        comment="Название метрики"
    )
    metric_value = Column(
        Float,
        nullable=False,
        comment="Значение метрики"
    )
    metric_unit = Column(
        String(50),
        comment="Единица измерения"
    )
    dimension_values = Column(
        JSON,
        comment="Значения измерений (фильтры, группировки)"
    )
    calculation_date = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="Дата расчета метрики"
    )
    pipeline_run_id = Column(
        Integer,
        comment="ID запуска пайплайна"
    )
    
    __table_args__ = (
        Index('idx_business_category', 'metric_category'),
        Index('idx_business_name', 'metric_name'),
        Index('idx_business_date', 'calculation_date'),
        Index('idx_business_pipeline_run', 'pipeline_run_id'),
    )


class DataLineage(Base, TimestampMixin):
    """Линия данных (откуда пришли данные)"""
    __tablename__ = "data_lineage"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_table = Column(
        String(255),
        nullable=False,
        comment="Исходная таблица"
    )
    source_column = Column(
        String(255),
        comment="Исходный столбец"
    )
    target_table = Column(
        String(255),
        nullable=False,
        comment="Целевая таблица"
    )
    target_column = Column(
        String(255),
        comment="Целевой столбец"
    )
    transformation_type = Column(
        String(100),
        nullable=False,
        comment="Тип трансформации"
    )
    transformation_logic = Column(
        Text,
        comment="Логика трансформации"
    )
    pipeline_run_id = Column(
        Integer,
        nullable=False,
        comment="ID запуска пайплайна"
    )
    record_count = Column(
        BigInteger,
        comment="Количество записей"
    )
    
    __table_args__ = (
        Index('idx_lineage_source', 'source_table'),
        Index('idx_lineage_target', 'target_table'),
        Index('idx_lineage_transformation', 'transformation_type'),
        Index('idx_lineage_pipeline_run', 'pipeline_run_id'),
    )


class DataCatalog(Base, TimestampMixin):
    """Каталог данных - описание всех таблиц и столбцов"""
    __tablename__ = "data_catalog"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    table_name = Column(
        String(255),
        nullable=False,
        comment="Название таблицы"
    )
    schema_name = Column(
        String(100),
        comment="Название схемы"
    )
    column_name = Column(
        String(255),
        comment="Название столбца"
    )
    data_type = Column(
        String(100),
        comment="Тип данных"
    )
    is_nullable = Column(
        Boolean,
        comment="Может ли быть NULL"
    )
    default_value = Column(
        String(500),
        comment="Значение по умолчанию"
    )
    description = Column(
        Text,
        comment="Описание таблицы/столбца"
    )
    business_meaning = Column(
        Text,
        comment="Бизнес-смысл данных"
    )
    owner = Column(
        String(255),
        comment="Владелец данных"
    )
    tags = Column(
        JSON,
        comment="Теги для категоризации"
    )
    sensitivity_level = Column(
        String(50),
        comment="Уровень чувствительности (public, internal, confidential)"
    )
    last_updated = Column(
        DateTime(timezone=True),
        comment="Время последнего обновления схемы"
    )
    
    __table_args__ = (
        UniqueConstraint('table_name', 'schema_name', 'column_name', name='uq_catalog_table_column'),
        Index('idx_catalog_table', 'table_name'),
        Index('idx_catalog_schema', 'schema_name'),
        Index('idx_catalog_owner', 'owner'),
        Index('idx_catalog_sensitivity', 'sensitivity_level'),
    )


class ETLAuditLog(Base, TimestampMixin):
    """Аудит лог ETL операций"""
    __tablename__ = "etl_audit_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    operation_type = Column(
        String(50),
        nullable=False,
        comment="Тип операции (create, update, delete, query)"
    )
    table_name = Column(
        String(255),
        nullable=False,
        comment="Название таблицы"
    )
    operation_details = Column(
        JSON,
        nullable=False,
        comment="Детали операции"
    )
    user_id = Column(
        String(255),
        comment="ID пользователя"
    )
    session_id = Column(
        String(255),
        comment="ID сессии"
    )
    ip_address = Column(
        String(45),
        comment="IP адрес"
    )
    user_agent = Column(
        Text,
        comment="User Agent"
    )
    pipeline_run_id = Column(
        Integer,
        comment="ID запуска пайплайна"
    )
    
    __table_args__ = (
        Index('idx_audit_operation', 'operation_type'),
        Index('idx_audit_table', 'table_name'),
        Index('idx_audit_user', 'user_id'),
        Index('idx_audit_pipeline_run', 'pipeline_run_id'),
        Index('idx_audit_created', 'created_at'),
    )
