"""
Сервис кэширования для оптимизации производительности
Поддерживает in-memory и Redis кэширование
"""
import json
import hashlib
import time
from typing import Any, Optional, Dict, Union
from functools import wraps
import asyncio
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
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Генерация ключа кэша"""
        key_data = {
            "args": args,
            "kwargs": kwargs
        }
        key_string = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Получение значения из кэша"""
        try:
            if self.cache_type == "redis" and self._redis_client:
                value = await self._redis_client.get(key)
                if value:
                    return json.loads(value)
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
                await self._redis_client.setex(key, ttl, json.dumps(value))
            else:
                self._memory_cache[key] = {
                    "value": value,
                    "expires_at": time.time() + ttl
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
                    keys_to_delete = [k for k in self._memory_cache.keys() if pattern.replace("*", "") in k]
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
                    "keyspace_misses": info.get("keyspace_misses")
                }
            else:
                return {
                    "type": "memory",
                    "total_keys": len(self._memory_cache),
                    "memory_usage": sum(len(str(v)) for v in self._memory_cache.values())
                }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"error": str(e)}


def cached(prefix: str, ttl: int = 3600, cache_service: Optional[CacheService] = None):
    """Декоратор для кэширования результатов функций"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if cache_service is None:
                return await func(*args, **kwargs)
            
            # Генерация ключа кэша
            cache_key = cache_service._generate_key(prefix, *args, **kwargs)
            
            # Попытка получить из кэша
            cached_result = await cache_service.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
            
            # Выполнение функции и сохранение в кэш
            result = await func(*args, **kwargs)
            await cache_service.set(cache_key, result, ttl)
            logger.debug(f"Cache set for {cache_key}")
            
            return result
        
        return wrapper
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
