"""
Сервис кэширования для оптимизации производительности
Поддерживает in-memory и Redis кэширование
"""
import json
import hashlib
import time
from typing import Any, Optional, Dict, Union, Tuple
from functools import wraps
import asyncio
from dataclasses import is_dataclass, asdict
from pathlib import Path
from pydantic import BaseModel
from loguru import logger


class CacheService:
    """Сервис кэширования"""

    def __init__(self, cache_type: str = "memory", redis_url: Optional[str] = None):
        self.cache_type = cache_type
        self.redis_url = redis_url
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._redis_client = None

        if cache_type == "redis" and redis_url:
            self._init_redis()

    def _init_redis(self):
        """Инициализация Redis клиента"""
        try:
            import redis.asyncio as redis
            self._redis_client = redis.from_url(self.redis_url)
            logger.info("Redis cache initialized")
        except ImportError:
            logger.warning("Redis not available, falling back to memory cache")
            self.cache_type = "memory"
        except Exception as e:
            logger.error(f"Redis initialization failed: {e}")
            self.cache_type = "memory"

    # --- СЕРИАЛИЗАЦИЯ / НОРМАЛИЗАЦИЯ ДЛЯ КЛЮЧЕЙ И REDIS ---

    @staticmethod
    def _to_jsonable(obj: Any) -> Any:
        """Преобразовать объект к JSON-совместимому виду (для значения в Redis)."""
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        if is_dataclass(obj):
            return asdict(obj)
        if isinstance(obj, Path):
            return str(obj)
        if isinstance(obj, (set, frozenset)):
            return list(obj)
        if isinstance(obj, bytes):
            # bytes в ключ/значение лучше не класть; но если вдруг — представим как hex
            return obj.hex()
        # Попытка сериализации стандартных типов
        try:
            json.dumps(obj)
            return obj
        except Exception:
            # Фолбэк — строковое представление
            return repr(obj)

    @classmethod
    def _normalize_for_key(cls, obj: Any) -> Any:
        """Рекурсивная нормализация аргументов для построения ключа кэша."""
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        if is_dataclass(obj):
            return asdict(obj)
        if isinstance(obj, dict):
            return {k: cls._normalize_for_key(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [cls._normalize_for_key(v) for v in obj]
        if isinstance(obj, (set, frozenset)):
            # чтобы порядок не влиял на ключ
            return sorted([cls._normalize_for_key(v) for v in obj])
        if isinstance(obj, Path):
            return str(obj)
        if isinstance(obj, bytes):
            return obj.hex()
        # примитивы / всё остальное
        return obj

    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Генерация ключа кэша из args/kwargs с нормализацией сложных типов."""
        key_data = {
            "args": self._normalize_for_key(args),
            "kwargs": self._normalize_for_key(kwargs),
        }
        key_string = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
        key_hash = hashlib.md5(key_string.encode("utf-8")).hexdigest()
        return f"{prefix}:{key_hash}"

    # --- ОПЕРАЦИИ С КЭШЕМ ---

    async def get(self, key: str) -> Optional[Any]:
        """Получение значения из кэша"""
        try:
            if self.cache_type == "redis" and self._redis_client:
                value = await self._redis_client.get(key)
                if value is not None:
                    try:
                        return json.loads(value)
                    except Exception:
                        # если вдруг лежит «сырое» значение
                        return value
            else:
                cache_entry = self._memory_cache.get(key)
                if cache_entry and cache_entry["expires_at"] > time.time():
                    return cache_entry["value"]
                elif cache_entry:
                    # Удаляем просроченный кэш
                    del self._memory_cache[key]

            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Сохранение значения в кэш"""
        try:
            if self.cache_type == "redis" and self._redis_client:
                # В Redis кладём JSON-представление
                payload = json.dumps(value, default=self._to_jsonable, ensure_ascii=False)
                await self._redis_client.setex(key, ttl, payload)
            else:
                # В памяти храним как есть (объект/модель) — быстрее
                self._memory_cache[key] = {
                    "value": value,
                    "expires_at": time.time() + ttl,
                }

            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Удаление значения из кэша"""
        try:
            if self.cache_type == "redis" and self._redis_client:
                await self._redis_client.delete(key)
            else:
                self._memory_cache.pop(key, None)

            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    async def clear(self, pattern: str = "*") -> bool:
        """Очистка кэша по паттерну"""
        try:
            if self.cache_type == "redis" and self._redis_client:
                keys = await self._redis_client.keys(pattern)
                if keys:
                    await self._redis_client.delete(*keys)
            else:
                if pattern == "*":
                    self._memory_cache.clear()
                else:
                    # Простая фильтрация для memory cache
                    needle = pattern.replace("*", "")
                    keys_to_delete = [k for k in list(self._memory_cache.keys()) if needle in k]
                    for key in keys_to_delete:
                        del self._memory_cache[key]

            return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """Получение статистики кэша"""
        try:
            if self.cache_type == "redis" and self._redis_client:
                info = await self._redis_client.info()
                return {
                    "type": "redis",
                    "used_memory": info.get("used_memory_human"),
                    "connected_clients": info.get("connected_clients"),
                    "keyspace_hits": info.get("keyspace_hits"),
                    "keyspace_misses": info.get("keyspace_misses"),
                }
            else:
                return {
                    "type": "memory",
                    "total_keys": len(self._memory_cache),
                    "memory_usage_approx": sum(len(str(v)) for v in self._memory_cache.values()),
                }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"error": str(e)}


def cached(prefix: str, ttl: int = 3600, cache_service: Optional[CacheService] = None):
    """Декоратор для кэширования результатов функций (поддержка async/sync)."""
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                if cache_service is None:
                    return await func(*args, **kwargs)

                cache_key = cache_service._generate_key(prefix, *args, **kwargs)
                cached_result = await cache_service.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for {cache_key}")
                    return cached_result

                value = await func(*args, **kwargs)
                await cache_service.set(cache_key, value, ttl)
                logger.debug(f"Cache set for {cache_key}")
                return value
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                if cache_service is None:
                    return func(*args, **kwargs)

                cache_key = cache_service._generate_key(prefix, *args, **kwargs)
                # sync-ветка использует memory cache; Redis — только из async-клиента
                entry = cache_service._memory_cache.get(cache_key)
                now = time.time()
                if entry and entry["expires_at"] > now:
                    logger.debug(f"Cache hit for {cache_key}")
                    return entry["value"]

                value = func(*args, **kwargs)
                cache_service._memory_cache[cache_key] = {
                    "value": value,
                    "expires_at": now + ttl,
                }
                logger.debug(f"Cache set for {cache_key}")
                return value
            return sync_wrapper
    return decorator


# Глобальный экземпляр сервиса кэширования
cache_service = CacheService(cache_type="memory")


# Специализированные кэш-декораторы для разных типов операций
def cache_analysis(ttl: int = 1800):
    """Кэширование результатов анализа данных"""
    return cached("analysis", ttl, cache_service)


def cache_ddl(ttl: int = 3600):
    """Кэширование DDL генерации"""
    return cached("ddl", ttl, cache_service)


def cache_recommendations(ttl: int = 1800):
    """Кэширование рекомендаций"""
    return cached("recommendations", ttl, cache_service)


def cache_llm(ttl: int = 3600):
    """Кэширование LLM ответов"""
    return cached("llm", ttl, cache_service)
