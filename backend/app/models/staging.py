"""
Модели для рабочей БД (временное хранение данных)
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Enum as SQLEnum, ForeignKey,
    Integer, JSON, String, Text, UniqueConstraint, Index, Numeric
)
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class FileStatus(str, Enum):
    """Статусы файлов"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    DELETED = "deleted"


class ProcessingStatus(str, Enum):
    """Статусы обработки"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StagingTable(Base, TimestampMixin):
    """Универсальная таблица для временного хранения данных"""
    __tablename__ = "staging_tables"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    table_name = Column(
        String(255),
        nullable=False,
        comment="Название таблицы для стадирования"
    )
    schema_name = Column(
        String(100),
        comment="Название схемы"
    )
    source_type = Column(
        String(50),
        nullable=False,
        comment="Тип источника (csv, json, database, api)"
    )
    source_config = Column(
        JSON,
        nullable=False,
        comment="Конфигурация источника"
    )
    row_count = Column(
        BigInteger,
        comment="Количество строк в таблице"
    )
    column_count = Column(
        Integer,
        comment="Количество столбцов"
    )
    file_size_bytes = Column(
        BigInteger,
        comment="Размер файла в байтах"
    )
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Активна ли таблица"
    )
    expires_at = Column(
        DateTime(timezone=True),
        comment="Время истечения (для автоочистки)"
    )
    
    __table_args__ = (
        UniqueConstraint('table_name', 'schema_name', name='uq_staging_table_name'),
        Index('idx_staging_source_type', 'source_type'),
        Index('idx_staging_active', 'is_active'),
        Index('idx_staging_expires', 'expires_at'),
    )


class FileMetadata(Base, TimestampMixin):
    """Метаданные загруженных файлов"""
    __tablename__ = "file_metadata"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(
        String(500),
        nullable=False,
        comment="Имя файла"
    )
    original_filename = Column(
        String(500),
        nullable=False,
        comment="Оригинальное имя файла"
    )
    file_path = Column(
        String(1000),
        nullable=False,
        comment="Путь к файлу"
    )
    file_size = Column(
        BigInteger,
        nullable=False,
        comment="Размер файла в байтах"
    )
    file_hash = Column(
        String(64),
        nullable=False,
        comment="SHA256 хеш файла"
    )
    mime_type = Column(
        String(100),
        comment="MIME тип файла"
    )
    encoding = Column(
        String(50),
        comment="Кодировка файла"
    )
    status = Column(
        String(50),
        default="uploaded",
        nullable=False,
        comment="Статус файла"
    )
    uploaded_by = Column(
        String(255),
        comment="Кто загрузил файл"
    )
    processing_started_at = Column(
        DateTime(timezone=True),
        comment="Время начала обработки"
    )
    processing_finished_at = Column(
        DateTime(timezone=True),
        comment="Время завершения обработки"
    )
    error_message = Column(
        Text,
        comment="Сообщение об ошибке при обработке"
    )
    file_metadata = Column(
        JSON,
        comment="Дополнительные метаданные файла"
    )
    
    __table_args__ = (
        UniqueConstraint('file_hash', name='uq_file_hash'),
        Index('idx_file_status', 'status'),
        Index('idx_file_uploaded_by', 'uploaded_by'),
        Index('idx_file_created', 'created_at'),
    )


class ProcessingLog(Base, TimestampMixin):
    """Логи обработки данных"""
    __tablename__ = "processing_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    table_name = Column(
        String(255),
        nullable=False,
        comment="Название обрабатываемой таблицы"
    )
    operation_type = Column(
        String(50),
        nullable=False,
        comment="Тип операции (load, transform, validate, export)"
    )
    status = Column(
        String(50),
        default="pending",
        nullable=False,
        comment="Статус обработки"
    )
    records_processed = Column(
        BigInteger,
        comment="Количество обработанных записей"
    )
    records_success = Column(
        BigInteger,
        comment="Количество успешно обработанных записей"
    )
    records_failed = Column(
        BigInteger,
        comment="Количество неудачно обработанных записей"
    )
    processing_time_seconds = Column(
        Numeric(10, 3),
        comment="Время обработки в секундах"
    )
    started_at = Column(
        DateTime(timezone=True),
        comment="Время начала обработки"
    )
    finished_at = Column(
        DateTime(timezone=True),
        comment="Время завершения обработки"
    )
    error_message = Column(
        Text,
        comment="Сообщение об ошибке"
    )
    execution_context = Column(
        JSON,
        comment="Контекст выполнения"
    )
    
    __table_args__ = (
        Index('idx_processing_table', 'table_name'),
        Index('idx_processing_operation', 'operation_type'),
        Index('idx_processing_status', 'status'),
        Index('idx_processing_started', 'started_at'),
    )
