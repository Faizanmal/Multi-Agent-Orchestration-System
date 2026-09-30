"""
Caching Utilities for Performance Optimization
"""
import hashlib
import json
import logging
from functools import wraps

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


def cache_response(timeout=300, key_prefix=''):
    """
    Decorator to cache function responses
    
    Args:
        timeout: Cache timeout in seconds (default: 5 minutes)
        key_prefix: Prefix for cache key
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = generate_cache_key(func.__name__, args, kwargs, key_prefix)
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, timeout)
            logger.debug(f"Cache set: {cache_key}")
            
            return result
        return wrapper
    return decorator


def generate_cache_key(func_name, args, kwargs, prefix=''):
    """Generate unique cache key from function arguments"""
    # Create string representation of arguments
    args_str = json.dumps({
        'args': [str(arg) for arg in args],
        'kwargs': {k: str(v) for k, v in kwargs.items()}
    }, sort_keys=True)
    
    # Generate hash
    key_hash = hashlib.md5(args_str.encode()).hexdigest()
    
    # Combine prefix, function name, and hash
    cache_key = f"{prefix}:{func_name}:{key_hash}"
    return cache_key


def invalidate_cache(pattern):
    """
    Invalidate cache keys matching pattern
    
    Args:
        pattern: Pattern to match cache keys
    """
    try:
        # Note: This requires Redis backend for pattern matching
        if hasattr(cache, 'delete_pattern'):
            cache.delete_pattern(pattern)
            logger.info(f"Cache invalidated: {pattern}")
        else:
            logger.warning("Cache backend doesn't support pattern deletion")
    except Exception as e:  # noqa: BLE001
        logger.error(f"Cache invalidation error: {e!s}")


class CacheManager:
    """Manager for cache operations"""
    
    @staticmethod
    def get_agent_cache_key(agent_id):
        """Get cache key for agent"""
        return f"agent:{agent_id}"
    
    @staticmethod
    def get_session_cache_key(session_id):
        """Get cache key for session"""
        return f"session:{session_id}"
    
    @staticmethod
    def get_user_cache_key(user_id):
        """Get cache key for user"""
        return f"user:{user_id}"
    
    @staticmethod
    def cache_agent(agent_id, data, timeout=300):
        """Cache agent data"""
        key = CacheManager.get_agent_cache_key(agent_id)
        cache.set(key, data, timeout)
        logger.debug(f"Cached agent: {agent_id}")
    
    @staticmethod
    def get_cached_agent(agent_id):
        """Get cached agent data"""
        key = CacheManager.get_agent_cache_key(agent_id)
        return cache.get(key)
    
    @staticmethod
    def invalidate_agent(agent_id):
        """Invalidate agent cache"""
        key = CacheManager.get_agent_cache_key(agent_id)
        cache.delete(key)
        logger.debug(f"Invalidated agent cache: {agent_id}")
    
    @staticmethod
    def cache_session(session_id, data, timeout=600):
        """Cache session data"""
        key = CacheManager.get_session_cache_key(session_id)
        cache.set(key, data, timeout)
        logger.debug(f"Cached session: {session_id}")
    
    @staticmethod
    def get_cached_session(session_id):
        """Get cached session data"""
        key = CacheManager.get_session_cache_key(session_id)
        return cache.get(key)
    
    @staticmethod
    def invalidate_session(session_id):
        """Invalidate session cache"""
        key = CacheManager.get_session_cache_key(session_id)
        cache.delete(key)
        logger.debug(f"Invalidated session cache: {session_id}")
    
    @staticmethod
    def get_cache_stats():
        """Get cache statistics"""
        try:
            # This is backend-specific
            stats = {
                'backend': settings.CACHES['default']['BACKEND'],
                'status': 'connected'
            }
            
            # Test cache
            test_key = 'cache_stats_test'
            cache.set(test_key, 'test', 10)
            test_result = cache.get(test_key)
            stats['working'] = test_result == 'test'
            
            return stats
        except Exception as e:  # noqa: BLE001
            logger.error(f"Cache stats error: {e!s}")
            return {
                'status': 'error',
                'error': str(e)
            }


# Groq response caching
class GroqCacheManager:
    """Manager for Groq API response caching"""
    
    @staticmethod
    def get_groq_cache_key(messages, model):
        """Generate cache key for Groq request"""
        messages_str = json.dumps(messages, sort_keys=True)
        key_hash = hashlib.md5(messages_str.encode()).hexdigest()
        return f"groq:{model}:{key_hash}"
    
    @staticmethod
    def cache_groq_response(messages, model, response, timeout=300):
        """Cache Groq API response"""
        key = GroqCacheManager.get_groq_cache_key(messages, model)
        cache.set(key, response, timeout)
        logger.debug(f"Cached Groq response: {key}")
    
    @staticmethod
    def get_cached_groq_response(messages, model):
        """Get cached Groq response"""
        key = GroqCacheManager.get_groq_cache_key(messages, model)
        cached = cache.get(key)
        if cached:
            logger.debug(f"Groq cache hit: {key}")
        return cached
    
    @staticmethod
    def invalidate_groq_cache():
        """Invalidate all Groq cache"""
        invalidate_cache("groq:*")


# Query result caching
def cache_queryset(timeout=300):
    """
    Decorator to cache Django queryset results
    
    Args:
        timeout: Cache timeout in seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = generate_cache_key(func.__name__, args, kwargs, 'queryset')
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Queryset cache hit: {cache_key}")
                return cached_result
            
            # Execute query
            result = func(*args, **kwargs)
            
            # Convert queryset to list for caching
            if hasattr(result, '__iter__'):
                result_list = list(result)
                cache.set(cache_key, result_list, timeout)
                logger.debug(f"Queryset cached: {cache_key}")
                return result_list
            else:
                cache.set(cache_key, result, timeout)
                return result
        
        return wrapper
    return decorator
