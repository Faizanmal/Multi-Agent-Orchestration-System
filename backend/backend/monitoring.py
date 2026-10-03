"""
Advanced monitoring and metrics system using Prometheus
"""

import logging
import time
from functools import wraps

from django.http import HttpResponse
from django.views import View
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    REGISTRY,
    Counter,
    Gauge,
    Histogram,
    Info,
    generate_latest,
)

logger = logging.getLogger(__name__)

# Define Prometheus metrics

# Request metrics
http_requests_total = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds", "HTTP request latency", ["method", "endpoint"]
)

# Agent metrics
agent_tasks_total = Counter(
    "agent_tasks_total", "Total agent tasks", ["agent_type", "status"]
)

agent_task_duration_seconds = Histogram(
    "agent_task_duration_seconds", "Agent task execution time", ["agent_type"]
)

active_agents = Gauge("active_agents", "Number of active agents", ["agent_type"])

# Groq API metrics
groq_api_calls_total = Counter(
    "groq_api_calls_total", "Total Groq API calls", ["model", "status"]
)

groq_api_latency_seconds = Histogram(
    "groq_api_latency_seconds", "Groq API response time", ["model"]
)

groq_tokens_used = Counter(
    "groq_tokens_used_total",
    "Total tokens used in Groq API",
    ["model", "type"],  # type: prompt or completion
)

# Cache metrics
cache_hits_total = Counter("cache_hits_total", "Total cache hits", ["cache_type"])

cache_misses_total = Counter("cache_misses_total", "Total cache misses", ["cache_type"])

# Database metrics
db_queries_total = Counter("db_queries_total", "Total database queries", ["operation"])

db_query_duration_seconds = Histogram(
    "db_query_duration_seconds", "Database query execution time", ["operation"]
)

# WebSocket metrics
websocket_connections = Gauge(
    "websocket_connections", "Number of active WebSocket connections"
)

websocket_messages_sent = Counter(
    "websocket_messages_sent_total", "Total WebSocket messages sent", ["message_type"]
)

websocket_messages_received = Counter(
    "websocket_messages_received_total",
    "Total WebSocket messages received",
    ["message_type"],
)

# System metrics
app_info = Info("app", "Application information")
app_info.info(
    {
        "name": "Multi-Agent Orchestration System",
        "version": "2.0.0",
        "environment": "production",
    }
)

# Error metrics
errors_total = Counter(
    "errors_total", "Total application errors", ["error_type", "severity"]
)


class PrometheusMetricsView(View):
    """
    Endpoint to expose Prometheus metrics
    """

    def get(self, request):
        metrics = generate_latest(REGISTRY)
        return HttpResponse(metrics, content_type=CONTENT_TYPE_LATEST)


def track_request_metrics(func):
    """
    Decorator to track HTTP request metrics
    """

    @wraps(func)
    def wrapper(request, *args, **kwargs):
        start_time = time.time()

        # Get endpoint name
        endpoint = request.path
        method = request.method

        try:
            response = func(request, *args, **kwargs)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            errors_total.labels(error_type=type(e).__name__, severity="error").inc()
            raise
        finally:
            # Record metrics
            duration = time.time() - start_time

            http_requests_total.labels(
                method=method, endpoint=endpoint, status=status_code
            ).inc()

            http_request_duration_seconds.labels(
                method=method, endpoint=endpoint
            ).observe(duration)

        return response

    return wrapper


def track_agent_task(agent_type: str):
    """
    Decorator to track agent task execution
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                errors_total.labels(error_type=type(e).__name__, severity="error").inc()
                raise
            finally:
                duration = time.time() - start_time

                agent_tasks_total.labels(agent_type=agent_type, status=status).inc()

                agent_task_duration_seconds.labels(agent_type=agent_type).observe(
                    duration
                )

        return wrapper

    return decorator


def track_groq_call(model: str):
    """
    Decorator to track Groq API calls
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"

            try:
                result = func(*args, **kwargs)

                # Track token usage if available
                if isinstance(result, dict) and "usage" in result:
                    usage = result["usage"]
                    if "prompt_tokens" in usage:
                        groq_tokens_used.labels(model=model, type="prompt").inc(
                            usage["prompt_tokens"]
                        )
                    if "completion_tokens" in usage:
                        groq_tokens_used.labels(model=model, type="completion").inc(
                            usage["completion_tokens"]
                        )

                return result
            except Exception as e:
                status = "error"
                errors_total.labels(
                    error_type=type(e).__name__, severity="warning"
                ).inc()
                raise
            finally:
                duration = time.time() - start_time

                groq_api_calls_total.labels(model=model, status=status).inc()

                groq_api_latency_seconds.labels(model=model).observe(duration)

        return wrapper

    return decorator


def track_cache_access(cache_type: str = "default"):
    """
    Track cache hits and misses
    """

    def track_hit():
        cache_hits_total.labels(cache_type=cache_type).inc()

    def track_miss():
        cache_misses_total.labels(cache_type=cache_type).inc()

    return track_hit, track_miss


def track_db_query(operation: str):
    """
    Decorator to track database queries
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time

                db_queries_total.labels(operation=operation).inc()

                db_query_duration_seconds.labels(operation=operation).observe(duration)

        return wrapper

    return decorator


class MetricsCollector:
    """
    Centralized metrics collection and reporting
    """

    @staticmethod
    def increment_active_agents(agent_type: str):
        """Increment active agents count"""
        active_agents.labels(agent_type=agent_type).inc()

    @staticmethod
    def decrement_active_agents(agent_type: str):
        """Decrement active agents count"""
        active_agents.labels(agent_type=agent_type).dec()

    @staticmethod
    def set_websocket_connections(count: int):
        """Set WebSocket connections count"""
        websocket_connections.set(count)

    @staticmethod
    def track_websocket_message_sent(message_type: str):
        """Track WebSocket message sent"""
        websocket_messages_sent.labels(message_type=message_type).inc()

    @staticmethod
    def track_websocket_message_received(message_type: str):
        """Track WebSocket message received"""
        websocket_messages_received.labels(message_type=message_type).inc()

    @staticmethod
    def record_error(error_type: str, severity: str = "error"):
        """Record an application error"""
        errors_total.labels(error_type=error_type, severity=severity).inc()

    @staticmethod
    def get_metrics_summary() -> dict:
        """Get summary of key metrics"""
        return {
            "http_requests": http_requests_total._value.get(),
            "agent_tasks": agent_tasks_total._value.get(),
            "groq_api_calls": groq_api_calls_total._value.get(),
            "cache_hits": cache_hits_total._value.get(),
            "cache_misses": cache_misses_total._value.get(),
            "errors": errors_total._value.get(),
        }


# Global metrics collector
metrics_collector = MetricsCollector()
