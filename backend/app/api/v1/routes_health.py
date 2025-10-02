from fastapi import APIRouter
from app.integrations.airflow_client import airflow_client
from app.connectors.database_connector import PostgresConnector, ClickHouseConnector
from app.core.config import settings
from app.services.monitoring_service import monitoring_service, monitor_performance
import asyncio


router = APIRouter()


@router.get("/")
async def health_check():
    """Общий health check"""
    health_status = monitoring_service.get_health_status()
    return {
        "status": health_status["status"],
        "service": "etl-ai-assistant-backend",
        "version": "0.1.0",
        "uptime_seconds": health_status["uptime_seconds"],
        "timestamp": health_status["timestamp"]
    }


@router.get("/detailed")
async def detailed_health():
    """Детальная проверка здоровья всех сервисов"""
    health_status = monitoring_service.get_health_status()
    metrics_summary = monitoring_service.get_metrics_summary()
    
    return {
        "health": health_status,
        "metrics": metrics_summary,
        "recent_alerts": monitoring_service.get_recent_alerts(hours=1)
    }


@router.get("/metrics")
@monitor_performance("metrics")
async def get_metrics():
    """Получение метрик системы"""
    return monitoring_service.get_metrics_summary()


@router.get("/airflow")
@monitor_performance("airflow_health")
async def airflow_health():
    """Проверка доступности Airflow"""
    try:
        is_healthy = await airflow_client.health_check()
        return {
            "status": "ok" if is_healthy else "error",
            "airflow_url": settings.airflow_base_url,
            "connected": is_healthy
        }
    except Exception as e:
        return {
            "status": "error",
            "airflow_url": settings.airflow_base_url,
            "error": str(e)
        }


@router.get("/databases")
async def databases_health():
    """Проверка доступности баз данных"""
    results = {}
    
    # PostgreSQL
    try:
        pg = PostgresConnector()
        pg_ok = await pg.test_connection()
        results["postgres"] = {
            "status": "ok" if pg_ok else "error",
            "dsn": settings.postgres_dsn.split("@")[-1] if "@" in settings.postgres_dsn else "hidden"
        }
    except Exception as e:
        results["postgres"] = {"status": "error", "error": str(e)}
    
    # ClickHouse
    try:
        ch = ClickHouseConnector()
        ch_ok = await ch.test_connection()
        results["clickhouse"] = {
            "status": "ok" if ch_ok else "error",
            "host": f"{settings.clickhouse_host}:{settings.clickhouse_port}"
        }
    except Exception as e:
        results["clickhouse"] = {"status": "error", "error": str(e)}
    
    return results
