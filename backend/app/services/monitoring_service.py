"""
Сервис мониторинга и метрик для ETL AI Assistant
"""
import time
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from loguru import logger
import json


@dataclass
class Metric:
    """Метрика для мониторинга"""
    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)
    unit: str = "count"


@dataclass
class PerformanceMetrics:
    """Метрики производительности"""
    request_count: int = 0
    success_count: int = 0
    error_count: int = 0
    avg_response_time: float = 0.0
    max_response_time: float = 0.0
    min_response_time: float = float('inf')
    total_response_time: float = 0.0


class MonitoringService:
    """Сервис мониторинга"""
    
    def __init__(self):
        self.metrics: List[Metric] = []
        self.performance_metrics: Dict[str, PerformanceMetrics] = {}
        self.health_checks: Dict[str, bool] = {}
        self.alerts: List[Dict[str, Any]] = []
        self.start_time = datetime.now()
    
    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None, unit: str = "count"):
        """Запись метрики"""
        metric = Metric(
            name=name,
            value=value,
            tags=tags or {},
            unit=unit
        )
        self.metrics.append(metric)
        
        # Ограничиваем количество метрик в памяти
        if len(self.metrics) > 10000:
            self.metrics = self.metrics[-5000:]
    
    def record_request(self, endpoint: str, response_time: float, success: bool = True):
        """Запись метрики запроса"""
        if endpoint not in self.performance_metrics:
            self.performance_metrics[endpoint] = PerformanceMetrics()
        
        metrics = self.performance_metrics[endpoint]
        metrics.request_count += 1
        metrics.total_response_time += response_time
        
        if success:
            metrics.success_count += 1
        else:
            metrics.error_count += 1
        
        # Обновляем статистику времени ответа
        metrics.avg_response_time = metrics.total_response_time / metrics.request_count
        metrics.max_response_time = max(metrics.max_response_time, response_time)
        metrics.min_response_time = min(metrics.min_response_time, response_time)
        
        # Записываем метрику
        self.record_metric(
            "api_request_duration",
            response_time,
            {"endpoint": endpoint, "status": "success" if success else "error"},
            "seconds"
        )
        
        self.record_metric(
            "api_request_total",
            1,
            {"endpoint": endpoint, "status": "success" if success else "error"}
        )
    
    def record_health_check(self, service: str, is_healthy: bool):
        """Запись проверки здоровья сервиса"""
        self.health_checks[service] = is_healthy
        self.record_metric(
            "health_check",
            1 if is_healthy else 0,
            {"service": service},
            "boolean"
        )
    
    def record_error(self, error_type: str, error_message: str, context: Optional[Dict[str, Any]] = None):
        """Запись ошибки"""
        self.record_metric(
            "error_total",
            1,
            {"error_type": error_type},
            "count"
        )
        
        # Добавляем алерт для критических ошибок
        if error_type in ["database_connection", "llm_service", "file_processing"]:
            self.add_alert(
                level="error",
                message=f"{error_type}: {error_message}",
                context=context
            )
    
    def add_alert(self, level: str, message: str, context: Optional[Dict[str, Any]] = None):
        """Добавление алерта"""
        alert = {
            "level": level,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "context": context or {}
        }
        self.alerts.append(alert)
        
        # Ограничиваем количество алертов
        if len(self.alerts) > 1000:
            self.alerts = self.alerts[-500:]
        
        logger.warning(f"ALERT [{level.upper()}]: {message}")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Получение сводки метрик"""
        now = datetime.now()
        last_hour = now - timedelta(hours=1)
        
        # Фильтруем метрики за последний час
        recent_metrics = [m for m in self.metrics if m.timestamp >= last_hour]
        
        # Группируем метрики по имени
        metrics_by_name = {}
        for metric in recent_metrics:
            if metric.name not in metrics_by_name:
                metrics_by_name[metric.name] = []
            metrics_by_name[metric.name].append(metric.value)
        
        # Вычисляем статистику
        summary = {
            "uptime_seconds": (now - self.start_time).total_seconds(),
            "total_metrics": len(recent_metrics),
            "health_checks": self.health_checks.copy(),
            "performance_metrics": {},
            "alerts_count": len([a for a in self.alerts if datetime.fromisoformat(a["timestamp"]) >= last_hour]),
            "metrics_summary": {}
        }
        
        # Статистика по метрикам
        for name, values in metrics_by_name.items():
            summary["metrics_summary"][name] = {
                "count": len(values),
                "sum": sum(values),
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values)
            }
        
        # Статистика по производительности
        for endpoint, perf in self.performance_metrics.items():
            summary["performance_metrics"][endpoint] = {
                "request_count": perf.request_count,
                "success_rate": perf.success_count / perf.request_count if perf.request_count > 0 else 0,
                "avg_response_time": perf.avg_response_time,
                "max_response_time": perf.max_response_time,
                "min_response_time": perf.min_response_time if perf.min_response_time != float('inf') else 0
            }
        
        return summary
    
    def get_health_status(self) -> Dict[str, Any]:
        """Получение статуса здоровья системы"""
        all_healthy = all(self.health_checks.values())
        
        return {
            "status": "healthy" if all_healthy else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "services": self.health_checks.copy(),
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "total_requests": sum(pm.request_count for pm in self.performance_metrics.values()),
            "error_rate": sum(pm.error_count for pm in self.performance_metrics.values()) / 
                         sum(pm.request_count for pm in self.performance_metrics.values()) 
                         if sum(pm.request_count for pm in self.performance_metrics.values()) > 0 else 0
        }
    
    def get_recent_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Получение недавних алертов"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [
            alert for alert in self.alerts 
            if datetime.fromisoformat(alert["timestamp"]) >= cutoff
        ]
    
    def cleanup_old_data(self, hours: int = 24):
        """Очистка старых данных"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        # Очищаем старые метрики
        self.metrics = [m for m in self.metrics if m.timestamp >= cutoff]
        
        # Очищаем старые алерты
        self.alerts = [a for a in self.alerts if datetime.fromisoformat(a["timestamp"]) >= cutoff]
        
        logger.info(f"Cleaned up data older than {hours} hours")


# Глобальный экземпляр сервиса мониторинга
monitoring_service = MonitoringService()


def monitor_performance(endpoint: str):
    """Декоратор для мониторинга производительности"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                monitoring_service.record_error(
                    error_type="function_error",
                    error_message=str(e),
                    context={"function": func.__name__, "endpoint": endpoint}
                )
                raise
            finally:
                response_time = time.time() - start_time
                monitoring_service.record_request(endpoint, response_time, success)
        
        return wrapper
    return decorator


async def periodic_health_checks():
    """Периодические проверки здоровья сервисов"""
    while True:
        try:
            # Проверяем доступность основных сервисов
            from app.connectors.database_connector import PostgresConnector, ClickHouseConnector
            from app.core.config import settings
            
            # Проверка PostgreSQL
            try:
                pg = PostgresConnector()
                pg_healthy = await pg.test_connection()
                monitoring_service.record_health_check("postgres", pg_healthy)
            except Exception as e:
                monitoring_service.record_health_check("postgres", False)
                monitoring_service.record_error("database_connection", f"PostgreSQL: {e}")
            
            # Проверка ClickHouse
            try:
                ch = ClickHouseConnector()
                ch_healthy = await ch.test_connection()
                monitoring_service.record_health_check("clickhouse", ch_healthy)
            except Exception as e:
                monitoring_service.record_health_check("clickhouse", False)
                monitoring_service.record_error("database_connection", f"ClickHouse: {e}")
            
            # Проверка LLM сервиса
            try:
                from app.services.llm_service import llm_service
                # Простая проверка доступности
                llm_healthy = True  # В реальности нужно сделать ping запрос
                monitoring_service.record_health_check("llm", llm_healthy)
            except Exception as e:
                monitoring_service.record_health_check("llm", False)
                monitoring_service.record_error("llm_service", f"LLM: {e}")
            
            # Очистка старых данных
            monitoring_service.cleanup_old_data(hours=24)
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
        
        # Ждем 5 минут до следующей проверки
        await asyncio.sleep(300)
