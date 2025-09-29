"""Initial migration for staging tables

Revision ID: 001_staging
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_staging'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create staging_tables table
    op.create_table('staging_tables',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='ID таблицы стадирования'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Время создания записи'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, comment='Время последнего обновления записи'),
        sa.Column('table_name', sa.String(length=255), nullable=False, comment='Название таблицы для стадирования'),
        sa.Column('schema_name', sa.String(length=100), nullable=True, comment='Название схемы'),
        sa.Column('source_type', sa.String(length=50), nullable=False, comment='Тип источника (csv, json, database, api)'),
        sa.Column('source_config', sa.JSON(), nullable=False, comment='Конфигурация источника'),
        sa.Column('row_count', sa.BigInteger(), nullable=True, comment='Количество строк в таблице'),
        sa.Column('column_count', sa.Integer(), nullable=True, comment='Количество столбцов'),
        sa.Column('file_size_bytes', sa.BigInteger(), nullable=True, comment='Размер файла в байтах'),
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Активна ли таблица'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True, comment='Время истечения (для автоочистки)'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('table_name', 'schema_name', name='uq_staging_table_name')
    )
    op.create_index('idx_staging_active', 'staging_tables', ['is_active'], unique=False)
    op.create_index('idx_staging_expires', 'staging_tables', ['expires_at'], unique=False)
    op.create_index('idx_staging_source_type', 'staging_tables', ['source_type'], unique=False)

    # Create file_metadata table
    op.create_table('file_metadata',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='ID метаданных файла'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Время создания записи'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, comment='Время последнего обновления записи'),
        sa.Column('filename', sa.String(length=500), nullable=False, comment='Имя файла'),
        sa.Column('original_filename', sa.String(length=500), nullable=False, comment='Оригинальное имя файла'),
        sa.Column('file_path', sa.String(length=1000), nullable=False, comment='Путь к файлу'),
        sa.Column('file_size', sa.BigInteger(), nullable=False, comment='Размер файла в байтах'),
        sa.Column('file_hash', sa.String(length=64), nullable=False, comment='SHA256 хеш файла'),
        sa.Column('mime_type', sa.String(length=100), nullable=True, comment='MIME тип файла'),
        sa.Column('encoding', sa.String(length=50), nullable=True, comment='Кодировка файла'),
        sa.Column('status', sa.Enum('uploaded', 'processing', 'processed', 'failed', 'deleted', name='filestatus'), nullable=False, comment='Статус файла'),
        sa.Column('uploaded_by', sa.String(length=255), nullable=True, comment='Кто загрузил файл'),
        sa.Column('processing_started_at', sa.DateTime(timezone=True), nullable=True, comment='Время начала обработки'),
        sa.Column('processing_finished_at', sa.DateTime(timezone=True), nullable=True, comment='Время завершения обработки'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='Сообщение об ошибке при обработке'),
        sa.Column('metadata', sa.JSON(), nullable=True, comment='Дополнительные метаданные файла'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('file_hash', name='uq_file_hash')
    )
    op.create_index('idx_file_created', 'file_metadata', ['created_at'], unique=False)
    op.create_index('idx_file_status', 'file_metadata', ['status'], unique=False)
    op.create_index('idx_file_uploaded_by', 'file_metadata', ['uploaded_by'], unique=False)

    # Create processing_logs table
    op.create_table('processing_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='ID лога обработки'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Время создания записи'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, comment='Время последнего обновления записи'),
        sa.Column('table_name', sa.String(length=255), nullable=False, comment='Название обрабатываемой таблицы'),
        sa.Column('operation_type', sa.String(length=50), nullable=False, comment='Тип операции (load, transform, validate, export)'),
        sa.Column('status', sa.Enum('pending', 'in_progress', 'completed', 'failed', 'cancelled', name='processingstatus'), nullable=False, comment='Статус обработки'),
        sa.Column('records_processed', sa.BigInteger(), nullable=True, comment='Количество обработанных записей'),
        sa.Column('records_success', sa.BigInteger(), nullable=True, comment='Количество успешно обработанных записей'),
        sa.Column('records_failed', sa.BigInteger(), nullable=True, comment='Количество неудачно обработанных записей'),
        sa.Column('processing_time_seconds', sa.Numeric(precision=10, scale=3), nullable=True, comment='Время обработки в секундах'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True, comment='Время начала обработки'),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True, comment='Время завершения обработки'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='Сообщение об ошибке'),
        sa.Column('execution_context', sa.JSON(), nullable=True, comment='Контекст выполнения'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_processing_operation', 'processing_logs', ['operation_type'], unique=False)
    op.create_index('idx_processing_started', 'processing_logs', ['started_at'], unique=False)
    op.create_index('idx_processing_status', 'processing_logs', ['status'], unique=False)
    op.create_index('idx_processing_table', 'processing_logs', ['table_name'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_processing_table', table_name='processing_logs')
    op.drop_index('idx_processing_status', table_name='processing_logs')
    op.drop_index('idx_processing_started', table_name='processing_logs')
    op.drop_index('idx_processing_operation', table_name='processing_logs')
    op.drop_table('processing_logs')
    op.drop_index('idx_file_uploaded_by', table_name='file_metadata')
    op.drop_index('idx_file_status', table_name='file_metadata')
    op.drop_index('idx_file_created', table_name='file_metadata')
    op.drop_table('file_metadata')
    op.drop_index('idx_staging_source_type', table_name='staging_tables')
    op.drop_index('idx_staging_expires', table_name='staging_tables')
    op.drop_index('idx_staging_active', table_name='staging_tables')
    op.drop_table('staging_tables')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS processingstatus CASCADE')
    op.execute('DROP TYPE IF EXISTS filestatus CASCADE')
