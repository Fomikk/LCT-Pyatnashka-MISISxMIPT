from app.schemas.recommend import RecommendationRequest, RecommendationResponse
from app.services.llm_service import llm_service
from typing import Dict, Any
import asyncio


async def recommend_storage_and_schedule(req: RecommendationRequest) -> RecommendationResponse:
    """Улучшенные рекомендации с интеграцией LLM"""
    
    # Базовая логика (fallback)
    workload = req.workload
    storage = "postgres"
    cron = "0 * * * *"
    rationale = "Оперативные данные — PostgreSQL, часовой рефреш"

    if workload in {"analytical"}: 
        storage = "clickhouse"
        cron = "*/30 * * * *"
        rationale = "Аналитические агрегаты — ClickHouse, партицирование по дате"
    elif workload in {"streaming"}:
        storage = "hdfs"
        cron = "*/5 * * * *"
        rationale = "Стриминговые сырые данные — HDFS, микробатчи через Kafka"
    elif workload in {"mixed"}:
        storage = "clickhouse+postgres"
        cron = "*/15 * * * *"
        rationale = "Смешанная нагрузка — агрегаты в ClickHouse, оперативка в PostgreSQL"

    # Корректировка по SLA
    if req.latency_sla_seconds is not None and req.latency_sla_seconds <= 300:
        cron = "*/5 * * * *"
        if storage == "postgres":
            rationale += " (ускоренное обновление для низкой задержки)"
    
    # Попытка получить рекомендации от LLM
    try:
        llm_recommendation = await _get_llm_recommendation(req)
        if llm_recommendation:
            storage = llm_recommendation.get("storage_type", storage)
            rationale = llm_recommendation.get("rationale", rationale)
    except Exception as e:
        # Если LLM недоступен, используем базовую логику
        pass
    
    # Дополнительные рекомендации
    additional_recommendations = _generate_additional_recommendations(req, storage)
    
    return RecommendationResponse(
        storage=storage, 
        rationale=rationale, 
        refresh_cron=cron,
        additional_recommendations=additional_recommendations
    )


async def _get_llm_recommendation(req: RecommendationRequest) -> Dict[str, Any]:
    """Получение рекомендаций от LLM"""
    workload_info = {
        "workload": req.workload,
        "latency_sla_seconds": req.latency_sla_seconds,
        "data_volume": getattr(req, 'data_volume', None),
        "update_frequency": getattr(req, 'update_frequency', None)
    }
    
    try:
        result = await llm_service.recommend_storage_strategy(workload_info)
        return {
            "storage_type": result.get("storage_type", "postgres"),
            "rationale": result.get("rationale", "LLM рекомендация"),
            "confidence": result.get("confidence", 0.8)
        }
    except Exception:
        return None


def _generate_additional_recommendations(req: RecommendationRequest, storage: str) -> list[str]:
    """Генерация дополнительных рекомендаций"""
    recommendations = []
    
    # Рекомендации по производительности
    if req.latency_sla_seconds and req.latency_sla_seconds < 60:
        recommendations.append("Критически низкая задержка - рассмотрите кэширование")
    
    if req.latency_sla_seconds and req.latency_sla_seconds > 3600:
        recommendations.append("Высокая задержка допустима - можно использовать batch обработку")
    
    # Рекомендации по хранилищу
    if storage == "clickhouse":
        recommendations.extend([
            "Используйте партицирование по дате для временных данных",
            "Рассмотрите материализованные представления для агрегатов",
            "Настройте сжатие данных для экономии места"
        ])
    elif storage == "postgres":
        recommendations.extend([
            "Создайте индексы на часто фильтруемые поля",
            "Настройте connection pooling",
            "Рассмотрите read replicas для аналитических запросов"
        ])
    elif storage == "hdfs":
        recommendations.extend([
            "Используйте Parquet формат для эффективного сжатия",
            "Настройте партицирование по дате",
            "Рассмотрите Apache Spark для обработки"
        ])
    elif "clickhouse+postgres" in storage:
        recommendations.extend([
            "PostgreSQL для оперативных данных, ClickHouse для аналитики",
            "Настройте синхронизацию между системами",
            "Используйте CDC для real-time обновлений"
        ])
    
    # Рекомендации по мониторингу
    recommendations.extend([
        "Настройте мониторинг производительности",
        "Создайте алерты на превышение SLA",
        "Ведите логи для анализа проблем"
    ])
    
    return recommendations[:5]  # Максимум 5 рекомендаций


