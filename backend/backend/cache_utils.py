"""
Advanced caching decorators and utilities
"""

import hashlib
import logging
from collections.abc import Callable
from functools import wraps
from typing import Any

from django.core.cache import cache

logger = logging.getLogger(__name__)


def cache_response(
    timeout: int = 300, key_prefix: str = "", vary_on_user: bool = False
):
    """
    Cache decorator for API responses

    Args:
        timeout: Cache timeout in seconds (default: 5 minutes)
        key_prefix: Custom prefix for cache key
        vary_on_user: Whether to include user ID in cache key
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # Generate cache key
            cache_key = _generate_cache_key(
                func.__name__, request, key_prefix, vary_on_user, *args, **kwargs
            )

            # Try to get from cache
            cached_response = cache.get(cache_key)
            if cached_response is not None:
                logger.debug(f"Cache HIT: {cache_key}")
                return cached_response

            # Cache miss - execute function
            logger.debug(f"Cache MISS: {cache_key}")
            response = func(request, *args, **kwargs)

            # Cache the response
            cache.set(cache_key, response, timeout)

            return response

        return wrapper

    return decorator


def cache_method(timeout: int = 300, key_prefix: str = ""):
    """
    Cache decorator for class methods

    Args:
        timeout: Cache timeout in seconds
        key_prefix: Custom prefix for cache key
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Generate cache key
            cache_key = _generate_method_cache_key(
                self.__class__.__name__, func.__name__, key_prefix, *args, **kwargs
            )

            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Method cache HIT: {cache_key}")
                return cached_result

            # Cache miss - execute method
            logger.debug(f"Method cache MISS: {cache_key}")
            result = func(self, *args, **kwargs)

            # Cache the result
            cache.set(cache_key, result, timeout)

            return result

        return wrapper

    return decorator


def invalidate_cache(patterns: list):
    """
    Invalidate cache entries matching patterns

    Args:
        patterns: List of cache key patterns to invalidate
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Execute function first
            result = func(*args, **kwargs)

            # Invalidate matching cache entries
            for pattern in patterns:
                _invalidate_pattern(pattern)

            return result

        return wrapper

    return decorator


def cache_page_vary_on_params(timeout: int = 300, params: list | None = None):
    """
    Cache entire page response, varying on specific query parameters

    Args:
        timeout: Cache timeout in seconds
        params: List of query parameter names to include in cache key
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # Build cache key from query params
            param_values = []
            if params:
                for param in params:
                    value = request.GET.get(param, "")
                    param_values.append(f"{param}={value}")

            param_str = "&".join(sorted(param_values))
            cache_key = f"page:{func.__name__}:{param_str}"
            cache_key = hashlib.md5(cache_key.encode()).hexdigest()

            # Try cache
            cached_response = cache.get(cache_key)
            if cached_response is not None:
                return cached_response

            # Execute and cache
            response = func(request, *args, **kwargs)
            cache.set(cache_key, response, timeout)

            return response

        return wrapper

    return decorator


def _generate_cache_key(
    func_name: str, request, key_prefix: str, vary_on_user: bool, *args, **kwargs
) -> str:
    """Generate cache key for request"""
    parts = [key_prefix or "cache", func_name]

    # Add user ID if varying on user
    if vary_on_user and request.user.is_authenticated:
        parts.append(f"user_{request.user.id}")

    # Add query parameters
    query_params = sorted(request.GET.items())
    if query_params:
        query_str = "&".join([f"{k}={v}" for k, v in query_params])
        parts.append(query_str)

    # Add args and kwargs
    if args:
        parts.append(str(args))
    if kwargs:
        parts.append(str(sorted(kwargs.items())))

    # Create hash
    key_string = ":".join(str(p) for p in parts)
    return hashlib.md5(key_string.encode()).hexdigest()


def _generate_method_cache_key(
    class_name: str, method_name: str, key_prefix: str, *args, **kwargs
) -> str:
    """Generate cache key for class method"""
    parts = [key_prefix or "method", class_name, method_name]

    # Add args and kwargs
    if args:
        parts.append(str(args))
    if kwargs:
        parts.append(str(sorted(kwargs.items())))

    key_string = ":".join(str(p) for p in parts)
    return hashlib.md5(key_string.encode()).hexdigest()


def _invalidate_pattern(pattern: str):
    """Invalidate all cache keys matching pattern"""
    try:
        # Note: This is a simplified version
        # For production, use Redis KEYS command or maintain a key registry
        cache.delete_pattern(pattern)
        logger.info(f"Invalidated cache pattern: {pattern}")
    except AttributeError:
        # Fallback if cache backend doesn't support pattern deletion
        logger.warning(f"Cache backend doesn't support pattern deletion: {pattern}")


class CacheManager:
    """
    Centralized cache management with statistics
    """

    def __init__(self):
        self.stats_key = "cache:stats"

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache with statistics"""
        value = cache.get(key, default)

        # Update statistics
        stats = cache.get(self.stats_key, {"hits": 0, "misses": 0})
        if value is not None:
            stats["hits"] += 1
        else:
            stats["misses"] += 1
        cache.set(self.stats_key, stats, timeout=None)

        return value

    def set(self, key: str, value: Any, timeout: int | None = 300):
        """Set value in cache"""
        cache.set(key, value, timeout)

    def delete(self, key: str):
        """Delete key from cache"""
        cache.delete(key)

    def clear(self):
        """Clear entire cache"""
        cache.clear()
        logger.warning("Cache cleared")

    def get_stats(self) -> dict:
        """Get cache statistics"""
        stats = cache.get(self.stats_key, {"hits": 0, "misses": 0})
        total = stats["hits"] + stats["misses"]

        return {
            "hits": stats["hits"],
            "misses": stats["misses"],
            "total_requests": total,
            "hit_rate": round(stats["hits"] / total * 100, 2) if total > 0 else 0,
        }

    def warm_up(self, data_loaders: list):
        """
        Warm up cache with frequently accessed data

        Args:
            data_loaders: List of tuples (cache_key, loader_func, timeout)
        """
        logger.info("Starting cache warm-up...")

        for cache_key, loader_func, timeout in data_loaders:
            try:
                data = loader_func()
                self.set(cache_key, data, timeout)
                logger.info(f"Warmed up cache: {cache_key}")
            except Exception as e:  # noqa: BLE001
                logger.error(f"Failed to warm up cache {cache_key}: {e!s}")

        logger.info("Cache warm-up completed")


# Global cache manager instance
cache_manager = CacheManager()
