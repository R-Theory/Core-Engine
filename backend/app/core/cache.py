"""
Redis-based caching system for Core Engine.
Provides multiple caching strategies and performance optimization.
"""

import redis.asyncio as redis
import json
import pickle
import hashlib
from typing import Any, Optional, Union, Dict, List
from functools import wraps
import asyncio
import logging
from datetime import datetime, timedelta
from app.core.config import settings

logger = logging.getLogger(__name__)

class CacheManager:
    """Advanced Redis cache manager with multiple strategies"""

    def __init__(self):
        self.redis_client = None
        self.default_ttl = 3600  # 1 hour
        self.serializers = {
            'json': (json.dumps, json.loads),
            'pickle': (pickle.dumps, pickle.loads)
        }

    async def connect(self):
        """Initialize Redis connection with connection pooling"""
        try:
            self.redis_client = redis.Redis(
                host=getattr(settings, 'REDIS_HOST', 'localhost'),
                port=getattr(settings, 'REDIS_PORT', 6379),
                db=getattr(settings, 'REDIS_DB', 0),
                password=getattr(settings, 'REDIS_PASSWORD', None),
                max_connections=20,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30,
            )

            # Test connection
            await self.redis_client.ping()
            logger.info("Redis cache manager connected successfully")

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None

    async def disconnect(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis cache manager disconnected")

    def _generate_key(self, key: str, namespace: str = "core") -> str:
        """Generate namespaced cache key"""
        return f"{namespace}:{key}"

    def _serialize(self, data: Any, method: str = 'json') -> bytes:
        """Serialize data for caching"""
        try:
            if method == 'json':
                return json.dumps(data, default=str).encode()
            elif method == 'pickle':
                return pickle.dumps(data)
            else:
                raise ValueError(f"Unknown serialization method: {method}")
        except Exception as e:
            logger.error(f"Serialization error: {e}")
            raise

    def _deserialize(self, data: bytes, method: str = 'json') -> Any:
        """Deserialize cached data"""
        try:
            if method == 'json':
                return json.loads(data.decode())
            elif method == 'pickle':
                return pickle.loads(data)
            else:
                raise ValueError(f"Unknown deserialization method: {method}")
        except Exception as e:
            logger.error(f"Deserialization error: {e}")
            raise

    async def get(self, key: str, namespace: str = "core", method: str = 'json') -> Optional[Any]:
        """Get value from cache"""
        if not self.redis_client:
            return None

        try:
            cache_key = self._generate_key(key, namespace)
            data = await self.redis_client.get(cache_key)

            if data is None:
                return None

            return self._deserialize(data, method)

        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None,
                  namespace: str = "core", method: str = 'json') -> bool:
        """Set value in cache"""
        if not self.redis_client:
            return False

        try:
            cache_key = self._generate_key(key, namespace)
            data = self._serialize(value, method)
            ttl = ttl or self.default_ttl

            result = await self.redis_client.setex(cache_key, ttl, data)
            return bool(result)

        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    async def delete(self, key: str, namespace: str = "core") -> bool:
        """Delete key from cache"""
        if not self.redis_client:
            return False

        try:
            cache_key = self._generate_key(key, namespace)
            result = await self.redis_client.delete(cache_key)
            return bool(result)

        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    async def clear_namespace(self, namespace: str) -> int:
        """Clear all keys in a namespace"""
        if not self.redis_client:
            return 0

        try:
            pattern = f"{namespace}:*"
            keys = await self.redis_client.keys(pattern)

            if keys:
                result = await self.redis_client.delete(*keys)
                logger.info(f"Cleared {result} keys from namespace {namespace}")
                return result

            return 0

        except Exception as e:
            logger.error(f"Cache clear namespace error for {namespace}: {e}")
            return 0

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.redis_client:
            return {"status": "disconnected"}

        try:
            info = await self.redis_client.info()
            return {
                "status": "connected",
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                )
            }

        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"status": "error", "error": str(e)}

    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate"""
        total = hits + misses
        return (hits / total * 100) if total > 0 else 0.0


# Global cache manager instance
cache_manager = CacheManager()


def cache_key_generator(*args, **kwargs) -> str:
    """Generate a unique cache key from function arguments"""
    key_parts = []

    # Add positional arguments
    for arg in args:
        if hasattr(arg, '__dict__'):
            # For objects, use their class name and relevant attributes
            key_parts.append(f"{arg.__class__.__name__}")
        else:
            key_parts.append(str(arg))

    # Add keyword arguments
    for k, v in sorted(kwargs.items()):
        key_parts.append(f"{k}:{v}")

    # Create hash of the combined key
    key_string = "|".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()


def cached(ttl: int = 3600, namespace: str = "core", method: str = 'json',
           key_func: Optional[callable] = None):
    """
    Decorator for caching function results

    Args:
        ttl: Time to live in seconds
        namespace: Cache namespace
        method: Serialization method ('json' or 'pickle')
        key_func: Custom key generation function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                func_name = f"{func.__module__}.{func.__name__}"
                args_key = cache_key_generator(*args, **kwargs)
                cache_key = f"{func_name}:{args_key}"

            # Try to get from cache
            cached_result = await cache_manager.get(cache_key, namespace, method)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result

            # Execute function and cache result
            logger.debug(f"Cache miss for {cache_key}")

            # Handle both sync and async functions
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Cache the result
            await cache_manager.set(cache_key, result, ttl, namespace, method)
            return result

        # Add cache management methods to the wrapped function
        wrapper.cache_clear = lambda: cache_manager.clear_namespace(namespace)
        wrapper.cache_key = lambda *args, **kwargs: (
            key_func(*args, **kwargs) if key_func
            else f"{func.__module__}.{func.__name__}:{cache_key_generator(*args, **kwargs)}"
        )

        return wrapper
    return decorator


class CacheStrategies:
    """Common caching strategies for different data types"""

    @staticmethod
    async def cache_user_data(user_id: int, data: Dict, ttl: int = 1800):
        """Cache user-specific data"""
        key = f"user:{user_id}:data"
        await cache_manager.set(key, data, ttl, namespace="users")

    @staticmethod
    async def get_user_data(user_id: int) -> Optional[Dict]:
        """Get cached user data"""
        key = f"user:{user_id}:data"
        return await cache_manager.get(key, namespace="users")

    @staticmethod
    async def cache_course_data(course_id: int, data: Dict, ttl: int = 3600):
        """Cache course data"""
        key = f"course:{course_id}"
        await cache_manager.set(key, data, ttl, namespace="courses")

    @staticmethod
    async def invalidate_user_cache(user_id: int):
        """Invalidate all user-related cache"""
        pattern_keys = [
            f"user:{user_id}:data",
            f"user:{user_id}:courses",
            f"user:{user_id}:assignments"
        ]

        for key in pattern_keys:
            await cache_manager.delete(key, namespace="users")

    @staticmethod
    async def cache_api_response(endpoint: str, params: Dict, response: Any, ttl: int = 900):
        """Cache API responses"""
        params_hash = hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()
        key = f"api:{endpoint}:{params_hash}"
        await cache_manager.set(key, response, ttl, namespace="api")

    @staticmethod
    async def get_cached_api_response(endpoint: str, params: Dict) -> Optional[Any]:
        """Get cached API response"""
        params_hash = hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()
        key = f"api:{endpoint}:{params_hash}"
        return await cache_manager.get(key, namespace="api")


# Session-based caching for temporary data
class SessionCache:
    """In-memory session cache for temporary data"""

    def __init__(self):
        self._cache = {}
        self._expiry = {}

    def set(self, key: str, value: Any, ttl: int = 300):
        """Set value with TTL"""
        self._cache[key] = value
        self._expiry[key] = datetime.now() + timedelta(seconds=ttl)

    def get(self, key: str) -> Optional[Any]:
        """Get value if not expired"""
        if key not in self._cache:
            return None

        if datetime.now() > self._expiry[key]:
            self.delete(key)
            return None

        return self._cache[key]

    def delete(self, key: str):
        """Delete key"""
        self._cache.pop(key, None)
        self._expiry.pop(key, None)

    def clear_expired(self):
        """Clear all expired keys"""
        now = datetime.now()
        expired_keys = [
            key for key, expiry in self._expiry.items()
            if now > expiry
        ]

        for key in expired_keys:
            self.delete(key)


# Global session cache instance
session_cache = SessionCache()