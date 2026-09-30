"""
Real-Time Performance Services with Redis Caching
"""

import json
import logging
import os
import time
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)


class RedisCacheService:
    """
    Redis caching service for model results and agent state
    """

    def __init__(self):
        """Initialize Redis connection (fail-fast so missing Redis cannot stall auth)."""
        self.enabled = False
        self.client = None

        # Local/dev without Redis: skip connect attempts entirely.
        # Rate limiting / metrics degrade gracefully when disabled.
        redis_required = os.getenv("REDIS_REQUIRED", "").lower() in ("1", "true", "yes")
        if getattr(settings, "DEBUG", False) and not redis_required:
            logger.info(
                "Redis skipped in DEBUG (set REDIS_REQUIRED=true to force connect)"
            )
            return

        try:
            import redis

            redis_url = getattr(
                settings,
                "REDIS_URL",
                os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            )

            self.client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=0.5,
                socket_timeout=0.5,
                retry_on_timeout=False,
            )

            # Test connection
            self.client.ping()
            self.enabled = True
            logger.info("Redis cache service initialized successfully")

        except Exception as e:  # noqa: BLE001
            logger.warning(f"Redis not available: {e}")
            self.enabled = False
            self.client = None

    def get(self, key: str) -> Any | None:
        """Get value from cache"""
        if not self.enabled:
            return None

        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:  # noqa: BLE001
            logger.error(f"Cache get error: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default 1 hour)

        Returns:
            Success status
        """
        if not self.enabled:
            return False

        try:
            serialized = json.dumps(value)
            self.client.setex(key, ttl, serialized)
            return True
        except Exception as e:  # noqa: BLE001
            logger.error(f"Cache set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.enabled:
            return False

        try:
            self.client.delete(key)
            return True
        except Exception as e:  # noqa: BLE001
            logger.error(f"Cache delete error: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.enabled:
            return False

        try:
            return self.client.exists(key) > 0
        except Exception as e:  # noqa: BLE001
            logger.error(f"Cache exists error: {e}")
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching pattern

        Args:
            pattern: Pattern to match (e.g., 'user:*', 'model:*')

        Returns:
            Number of keys deleted
        """
        if not self.enabled:
            return 0

        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:  # noqa: BLE001
            logger.error(f"Cache invalidate error: {e}")
            return 0

    def cache_model_result(
        self, model_id: str, input_hash: str, result: dict, ttl: int = 1800
    ):
        """Cache model inference result"""
        key = f"model:{model_id}:{input_hash}"
        return self.set(key, result, ttl)

    def get_cached_model_result(self, model_id: str, input_hash: str) -> dict | None:
        """Get cached model result"""
        key = f"model:{model_id}:{input_hash}"
        return self.get(key)

    def cache_agent_state(self, agent_id: str, state: dict, ttl: int = 600):
        """Cache agent state"""
        key = f"agent:state:{agent_id}"
        return self.set(key, state, ttl)

    def get_agent_state(self, agent_id: str) -> dict | None:
        """Get cached agent state"""
        key = f"agent:state:{agent_id}"
        return self.get(key)

    def cache_session_data(self, session_id: str, data: dict, ttl: int = 3600):
        """Cache session data"""
        key = f"session:{session_id}"
        return self.set(key, data, ttl)

    def get_session_data(self, session_id: str) -> dict | None:
        """Get cached session data"""
        key = f"session:{session_id}"
        return self.get(key)

    def increment_counter(self, key: str, amount: int = 1) -> int:
        """Increment counter"""
        if not self.enabled:
            return 0

        try:
            return self.client.incrby(key, amount)
        except Exception as e:  # noqa: BLE001
            logger.error(f"Counter increment error: {e}")
            return 0

    def get_counter(self, key: str) -> int:
        """Get counter value"""
        if not self.enabled:
            return 0

        try:
            value = self.client.get(key)
            return int(value) if value else 0
        except Exception as e:  # noqa: BLE001
            logger.error(f"Counter get error: {e}")
            return 0

    def add_to_list(self, key: str, value: Any, max_length: int | None = None):
        """Add value to list (LPUSH)"""
        if not self.enabled:
            return False

        try:
            serialized = json.dumps(value)
            self.client.lpush(key, serialized)

            if max_length:
                self.client.ltrim(key, 0, max_length - 1)

            return True
        except Exception as e:  # noqa: BLE001
            logger.error(f"List add error: {e}")
            return False

    def get_list(self, key: str, start: int = 0, end: int = -1) -> list[Any]:
        """Get list values"""
        if not self.enabled:
            return []

        try:
            values = self.client.lrange(key, start, end)
            return [json.loads(v) for v in values]
        except Exception as e:  # noqa: BLE001
            logger.error(f"List get error: {e}")
            return []

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        if not self.enabled:
            return {"enabled": False}

        try:
            info = self.client.info()
            return {
                "enabled": True,
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0), info.get("keyspace_misses", 0)
                ),
            }
        except Exception as e:  # noqa: BLE001
            logger.error(f"Stats retrieval error: {e}")
            return {"enabled": True, "error": str(e)}

    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate"""
        total = hits + misses
        if total == 0:
            return 0.0
        return (hits / total) * 100


class PerformanceMonitoringService:
    """
    Monitor and track system performance in real-time
    """

    def __init__(self):
        self.cache = get_cache_service()

    def track_request(
        self,
        endpoint: str,
        duration_ms: int,
        status_code: int,
        user_id: str | None = None,
    ):
        """Track API request performance"""
        timestamp = int(time.time())

        # Increment request counter
        self.cache.increment_counter(f"metrics:requests:{endpoint}:count")

        # Track response time
        metric_key = f"metrics:requests:{endpoint}:times"
        self.cache.add_to_list(
            metric_key,
            {
                "timestamp": timestamp,
                "duration_ms": duration_ms,
                "status_code": status_code,
                "user_id": user_id,
            },
            max_length=1000,
        )

        # Track errors
        if status_code >= 400:
            self.cache.increment_counter(f"metrics:requests:{endpoint}:errors")

    def track_model_execution(
        self, model_id: str, duration_ms: int, tokens: int, success: bool
    ):
        """Track model execution performance"""
        timestamp = int(time.time())

        # Track execution
        metric_key = f"metrics:models:{model_id}:executions"
        self.cache.add_to_list(
            metric_key,
            {
                "timestamp": timestamp,
                "duration_ms": duration_ms,
                "tokens": tokens,
                "success": success,
            },
            max_length=1000,
        )

        # Update counters
        self.cache.increment_counter(f"metrics:models:{model_id}:total")
        if success:
            self.cache.increment_counter(f"metrics:models:{model_id}:success")
        else:
            self.cache.increment_counter(f"metrics:models:{model_id}:failures")

    def get_endpoint_metrics(self, endpoint: str) -> dict[str, Any]:
        """Get performance metrics for endpoint"""
        total_requests = self.cache.get_counter(f"metrics:requests:{endpoint}:count")
        total_errors = self.cache.get_counter(f"metrics:requests:{endpoint}:errors")

        recent_times = self.cache.get_list(f"metrics:requests:{endpoint}:times", 0, 99)

        if recent_times:
            durations = [t["duration_ms"] for t in recent_times]
            avg_duration = sum(durations) / len(durations)
            p95_duration = (
                sorted(durations)[int(len(durations) * 0.95)]
                if len(durations) > 1
                else avg_duration
            )
        else:
            avg_duration = 0
            p95_duration = 0

        return {
            "endpoint": endpoint,
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": (total_errors / max(total_requests, 1)) * 100,
            "avg_duration_ms": avg_duration,
            "p95_duration_ms": p95_duration,
            "recent_samples": len(recent_times),
        }

    def get_model_metrics(self, model_id: str) -> dict[str, Any]:
        """Get performance metrics for model"""
        total = self.cache.get_counter(f"metrics:models:{model_id}:total")
        success = self.cache.get_counter(f"metrics:models:{model_id}:success")
        failures = self.cache.get_counter(f"metrics:models:{model_id}:failures")

        recent_executions = self.cache.get_list(
            f"metrics:models:{model_id}:executions", 0, 99
        )

        if recent_executions:
            durations = [e["duration_ms"] for e in recent_executions]
            tokens = [e["tokens"] for e in recent_executions]
            avg_duration = sum(durations) / len(durations)
            avg_tokens = sum(tokens) / len(tokens)
        else:
            avg_duration = 0
            avg_tokens = 0

        return {
            "model_id": model_id,
            "total_executions": total,
            "successful": success,
            "failures": failures,
            "success_rate": (success / max(total, 1)) * 100,
            "avg_duration_ms": avg_duration,
            "avg_tokens": avg_tokens,
            "recent_samples": len(recent_executions),
        }

    def get_system_health(self) -> dict[str, Any]:
        """Get overall system health metrics"""
        cache_stats = self.cache.get_stats()

        return {
            "status": "healthy",
            "cache": cache_stats,
            "timestamp": int(time.time()),
        }


# Singleton instances
_cache_service = None
_performance_service = None


def get_cache_service() -> RedisCacheService:
    """Get or create cache service singleton"""
    global _cache_service
    if _cache_service is None:
        _cache_service = RedisCacheService()
    return _cache_service


def get_performance_service() -> PerformanceMonitoringService:
    """Get or create performance monitoring service singleton"""
    global _performance_service
    if _performance_service is None:
        _performance_service = PerformanceMonitoringService()
    return _performance_service
