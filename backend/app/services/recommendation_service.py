from app.schemas.recommend import RecommendationRequest, RecommendationResponse


async def recommend_storage_and_schedule(req: RecommendationRequest) -> RecommendationResponse:
    workload = req.workload
    storage = "postgres"
    cron = "0 * * * *"  # каждый час по умолчанию
    rationale = "Оперативные данные — PostgreSQL, часовой рефреш"

    if workload in {"analytical"}:
        storage = "clickhouse"
        cron = "*/30 * * * *"  # каждые 30 минут
        rationale = "Аналитические агрегаты — ClickHouse, партицирование по дате"
    elif workload in {"streaming"}:
        storage = "hdfs"
        cron = "*/5 * * * *"
        rationale = "Стриминговые сырые данные — HDFS, микробатчи через Kafka"
    elif workload in {"mixed"}:
        storage = "clickhouse+postgres"
        cron = "*/15 * * * *"
        rationale = "Смешанная нагрузка — агрегаты в ClickHouse, оперативка в PostgreSQL"

    if req.latency_sla_seconds is not None and req.latency_sla_seconds <= 300:
        cron = "*/5 * * * *"

    return RecommendationResponse(storage=storage, rationale=rationale, refresh_cron=cron)


