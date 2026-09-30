"""
Health Check and System Status Endpoints
"""

import os
import time

import psutil
from django.conf import settings
from django.core.cache import cache
from django.db import connection
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """
    Comprehensive health check endpoint
    Returns system status and health of various components
    """
    health_status = {"status": "healthy", "timestamp": time.time(), "checks": {}}

    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status["checks"]["database"] = {
            "status": "up",
            "message": "Database connection successful",
        }
    except Exception as e:  # noqa: BLE001
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {"status": "down", "message": str(e)}

    # Check cache (Redis)
    try:
        cache.set("health_check", "ok", 10)
        cache_value = cache.get("health_check")
        if cache_value == "ok":
            health_status["checks"]["cache"] = {
                "status": "up",
                "message": "Cache connection successful",
            }
        else:
            raise Exception("Cache read/write failed")  # noqa: TRY002
    except Exception as e:  # noqa: BLE001
        health_status["status"] = "degraded"
        health_status["checks"]["cache"] = {"status": "down", "message": str(e)}

    # Check disk space
    disk = psutil.disk_usage("/")
    disk_percent = disk.percent
    health_status["checks"]["disk"] = {
        "status": "ok" if disk_percent < 80 else "warning",
        "usage_percent": disk_percent,
        "free_gb": round(disk.free / (1024**3), 2),
    }

    # Check memory
    memory = psutil.virtual_memory()
    memory_percent = memory.percent
    health_status["checks"]["memory"] = {
        "status": "ok" if memory_percent < 80 else "warning",
        "usage_percent": memory_percent,
        "available_gb": round(memory.available / (1024**3), 2),
    }

    # Check CPU
    cpu_percent = psutil.cpu_percent(interval=1)
    health_status["checks"]["cpu"] = {
        "status": "ok" if cpu_percent < 80 else "warning",
        "usage_percent": cpu_percent,
    }

    # Determine HTTP status code
    if health_status["status"] == "healthy" or health_status["status"] == "degraded":
        http_status = status.HTTP_200_OK
    else:
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE

    return Response(health_status, status=http_status)


@api_view(["GET"])
@permission_classes([AllowAny])
def readiness_check(request):
    """
    Readiness probe for Kubernetes
    Returns 200 if application is ready to accept traffic
    """
    try:
        # Check database
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        return Response(
            {"ready": True, "message": "Application is ready"},
            status=status.HTTP_200_OK,
        )

    except Exception as e:  # noqa: BLE001
        return Response(
            {"ready": False, "message": str(e)},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def liveness_check(request):
    """
    Liveness probe for Kubernetes
    Returns 200 if application is alive
    """
    return Response(
        {"alive": True, "message": "Application is alive"}, status=status.HTTP_200_OK
    )


@api_view(["GET"])
def system_info(request):
    """
    Get detailed system information
    Requires authentication
    """
    system_data = {
        "platform": os.uname().system,
        "python_version": os.sys.version,
        "django_version": (
            settings.VERSION if hasattr(settings, "VERSION") else "Unknown"
        ),
        "cpu": {
            "count": psutil.cpu_count(),
            "percent": psutil.cpu_percent(interval=1),
            "load_average": os.getloadavg() if hasattr(os, "getloadavg") else None,
        },
        "memory": {
            "total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
            "percent": psutil.virtual_memory().percent,
        },
        "disk": {
            "total_gb": round(psutil.disk_usage("/").total / (1024**3), 2),
            "free_gb": round(psutil.disk_usage("/").free / (1024**3), 2),
            "percent": psutil.disk_usage("/").percent,
        },
        "network": {"connections": len(psutil.net_connections())},
    }

    return Response(system_data)
