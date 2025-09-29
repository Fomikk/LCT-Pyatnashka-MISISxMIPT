"""
Базовые модели и миксины для SQLAlchemy
"""

from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import Column, DateTime, Boolean, func
from sqlalchemy.ext.declarative import declarative_base, declared_attr


Base = declarative_base()


class TimestampMixin:
    """Миксин для добавления временных меток"""
    
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Время создания записи"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
        comment="Время последнего обновления записи"
    )


class SoftDeleteMixin:
    """Миксин для мягкого удаления"""
    
    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Флаг мягкого удаления"
    )
    
    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Время мягкого удаления"
    )
