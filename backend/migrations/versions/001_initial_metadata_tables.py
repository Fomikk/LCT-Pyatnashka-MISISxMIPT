"""Initial migration for metadata tables

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create data_sources table
    op.create_table('data_sources',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='ID источника данных'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Время создания записи'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, comment='Время последнего обновления записи'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, comment='Флаг мягкого удаления'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Время мягкого удаления'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='Название источника'),
        sa.Column('description', sa.Text(), nullable=True, comment='Описание источника'),
        sa.Column('source_type', sa.Enum('file', 'database', 'api', 'kafka', 's3', 'hdfs', name='datasourcetype'), nullable=False, comment='Тип источника данных'),
        sa.Column('connection_config', sa.JSON(), nullable=False, comment='Конфигурация подключения к источнику'),
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Активен ли источник'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_data_source_name')
    )
    op.create_index('idx_data_source_active', 'data_sources', ['is_active'], unique=False)
    op.create_index('idx_data_source_type', 'data_sources', ['source_type'], unique=False)

    # Create pipelines table
    op.create_table('pipelines',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='ID пайплайна'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Время создания записи'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, comment='Время последнего обновления записи'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, comment='Флаг мягкого удаления'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='Время мягкого удаления'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='Название пайплайна'),
        sa.Column('description', sa.Text(), nullable=True, comment='Описание пайплайна'),
        sa.Column('data_source_id', sa.Integer(), nullable=False, comment='ID источника данных'),
        sa.Column('status', sa.Enum('draft', 'active', 'inactive', 'deprecated', name='pipelinestatus'), nullable=False, comment='Статус пайплайна'),
        sa.Column('configuration', sa.JSON(), nullable=False, comment='Конфигурация пайплайна'),
        sa.Column('schedule_cron', sa.String(length=100), nullable=True, comment='Cron выражение для расписания'),
        sa.Column('max_retries', sa.Integer(), nullable=False, comment='Максимальное количество повторов'),
        sa.Column('timeout_seconds', sa.Integer(), nullable=True, comment='Таймаут выполнения в секундах'),
        sa.Column('tags', sa.JSON(), nullable=True, comment='Теги для группировки пайплайнов'),
        sa.ForeignKeyConstraint(['data_source_id'], ['data_sources.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_pipeline_name')
    )
    op.create_index('idx_pipeline_data_source', 'pipelines', ['data_source_id'], unique=False)
    op.create_index('idx_pipeline_schedule', 'pipelines', ['schedule_cron'], unique=False)
    op.create_index('idx_pipeline_status', 'pipelines', ['status'], unique=False)

    # Create pipeline_runs table
    op.create_table('pipeline_runs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='ID запуска пайплайна'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Время создания записи'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, comment='Время последнего обновления записи'),
        sa.Column('pipeline_id', sa.Integer(), nullable=False, comment='ID пайплайна'),
        sa.Column('status', sa.Enum('pending', 'running', 'success', 'failed', 'cancelled', name='pipelinerunstatus'), nullable=False, comment='Статус выполнения'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True, comment='Время начала выполнения'),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True, comment='Время завершения выполнения'),
        sa.Column('duration_seconds', sa.Integer(), nullable=True, comment='Длительность выполнения в секундах'),
        sa.Column('records_processed', sa.BigInteger(), nullable=True, comment='Количество обработанных записей'),
        sa.Column('records_failed', sa.BigInteger(), nullable=True, comment='Количество неудачно обработанных записей'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='Сообщение об ошибке'),
        sa.Column('execution_context', sa.JSON(), nullable=True, comment='Контекст выполнения (параметры, переменные)'),
        sa.Column('retry_count', sa.Integer(), nullable=False, comment='Количество повторов'),
        sa.Column('triggered_by', sa.String(length=255), nullable=True, comment='Кто/что запустило пайплайн (user, scheduler, api)'),
        sa.ForeignKeyConstraint(['pipeline_id'], ['pipelines.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_pipeline_run_finished', 'pipeline_runs', ['finished_at'], unique=False)
    op.create_index('idx_pipeline_run_pipeline', 'pipeline_runs', ['pipeline_id'], unique=False)
    op.create_index('idx_pipeline_run_started', 'pipeline_runs', ['started_at'], unique=False)
    op.create_index('idx_pipeline_run_status', 'pipeline_runs', ['status'], unique=False)

    # Create analysis_results table
    op.create_table('analysis_results',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='ID результата анализа'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Время создания записи'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, comment='Время последнего обновления записи'),
        sa.Column('pipeline_run_id', sa.Integer(), nullable=False, comment='ID запуска пайплайна'),
        sa.Column('analysis_type', sa.String(length=100), nullable=False, comment='Тип анализа (data_quality, anomaly_detection, etc.)'),
        sa.Column('result_data', sa.JSON(), nullable=False, comment='Результаты анализа в JSON формате'),
        sa.Column('metrics', sa.JSON(), nullable=True, comment='Метрики качества данных'),
        sa.Column('recommendations', sa.JSON(), nullable=True, comment='Рекомендации по улучшению данных'),
        sa.Column('is_alert', sa.Boolean(), nullable=False, comment='Требует ли внимания (алерт)'),
        sa.Column('alert_level', sa.String(length=20), nullable=True, comment='Уровень алерта (low, medium, high, critical)'),
        sa.ForeignKeyConstraint(['pipeline_run_id'], ['pipeline_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_analysis_alert', 'analysis_results', ['is_alert'], unique=False)
    op.create_index('idx_analysis_created', 'analysis_results', ['created_at'], unique=False)
    op.create_index('idx_analysis_pipeline_run', 'analysis_results', ['pipeline_run_id'], unique=False)
    op.create_index('idx_analysis_type', 'analysis_results', ['analysis_type'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_analysis_type', table_name='analysis_results')
    op.drop_index('idx_analysis_pipeline_run', table_name='analysis_results')
    op.drop_index('idx_analysis_created', table_name='analysis_results')
    op.drop_index('idx_analysis_alert', table_name='analysis_results')
    op.drop_table('analysis_results')
    op.drop_index('idx_pipeline_run_status', table_name='pipeline_runs')
    op.drop_index('idx_pipeline_run_started', table_name='pipeline_runs')
    op.drop_index('idx_pipeline_run_pipeline', table_name='pipeline_runs')
    op.drop_index('idx_pipeline_run_finished', table_name='pipeline_runs')
    op.drop_table('pipeline_runs')
    op.drop_index('idx_pipeline_status', table_name='pipelines')
    op.drop_index('idx_pipeline_schedule', table_name='pipelines')
    op.drop_index('idx_pipeline_data_source', table_name='pipelines')
    op.drop_table('pipelines')
    op.drop_index('idx_data_source_type', table_name='data_sources')
    op.drop_index('idx_data_source_active', table_name='data_sources')
    op.drop_table('data_sources')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS pipelinerunstatus CASCADE')
    op.execute('DROP TYPE IF EXISTS pipelinestatus CASCADE')
    op.execute('DROP TYPE IF EXISTS datasourcetype CASCADE')
