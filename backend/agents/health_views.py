from datetime import timezone

"""
Health Check and System Status Views
"""
from datetime import datetime, timedelta

import psutil
from authentication.models import CustomUser
from django.conf import settings
from django.core.cache import cache
from django.db import connection
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from agents.models import Agent, Message, Session, Task


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Basic health check endpoint
    Returns system health status
    """
    try:
        # Check database
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Check cache
        cache_key = 'health_check_test'
        cache.set(cache_key, 'ok', 10)
        cache_status = cache.get(cache_key) == 'ok'
        
        return Response({
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'database': 'connected',
            'cache': 'connected' if cache_status else 'disconnected',
            'version': '1.0.0'
        }, status=status.HTTP_200_OK)
    
    except Exception as e:  # noqa: BLE001
        return Response({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['GET'])
@permission_classes([AllowAny])
def system_status(request):
    """
    Detailed system status endpoint
    Returns comprehensive system metrics
    """
    try:
        # Database stats
        total_agents = Agent.objects.count()
        active_agents = Agent.objects.filter(is_active=True).count()
        total_sessions = Session.objects.count()
        active_sessions = Session.objects.filter(is_active=True).count()
        total_messages = Message.objects.count()
        total_tasks = Task.objects.count()
        total_users = CustomUser.objects.count()
        
        # Recent activity (last 24 hours)
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        recent_sessions = Session.objects.filter(created_at__gte=yesterday).count()
        recent_messages = Message.objects.filter(created_at__gte=yesterday).count()
        
        # System resources
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return Response({
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'database': {
                'agents': {
                    'total': total_agents,
                    'active': active_agents
                },
                'sessions': {
                    'total': total_sessions,
                    'active': active_sessions
                },
                'messages': total_messages,
                'tasks': total_tasks,
                'users': total_users
            },
            'activity_24h': {
                'sessions': recent_sessions,
                'messages': recent_messages
            },
            'system': {
                'cpu_percent': cpu_percent,
                'memory': {
                    'total_gb': round(memory.total / (1024**3), 2),
                    'used_gb': round(memory.used / (1024**3), 2),
                    'percent': memory.percent
                },
                'disk': {
                    'total_gb': round(disk.total / (1024**3), 2),
                    'used_gb': round(disk.used / (1024**3), 2),
                    'percent': disk.percent
                }
            },
            'configuration': {
                'debug': settings.DEBUG,
                'max_agents': settings.AGENT_CONFIG.get('MAX_AGENTS', 10),
                'groq_model': settings.GROQ_CONFIG.get('MODEL', 'unknown')
            }
        }, status=status.HTTP_200_OK)
    
    except Exception as e:  # noqa: BLE001
        return Response({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def performance_metrics(request):
    """
    Performance metrics endpoint
    Returns performance statistics
    """
    try:
        from agents.models import PerformanceMetric
        
        # Get recent metrics (last hour)
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        recent_metrics = PerformanceMetric.objects.filter(
            timestamp__gte=one_hour_ago
        )
        
        # Calculate averages
        metrics_by_agent = {}
        for metric in recent_metrics:
            agent_name = metric.agent.name
            if agent_name not in metrics_by_agent:
                metrics_by_agent[agent_name] = {
                    'count': 0,
                    'total_value': 0,
                    'metrics': []
                }
            metrics_by_agent[agent_name]['count'] += 1
            metrics_by_agent[agent_name]['total_value'] += metric.metric_value
            metrics_by_agent[agent_name]['metrics'].append({
                'name': metric.metric_name,
                'value': metric.metric_value,
                'timestamp': metric.timestamp.isoformat()
            })
        
        # Calculate averages
        for agent_name, agent_metrics in metrics_by_agent.items():
            count = agent_metrics['count']
            total = agent_metrics['total_value']
            agent_metrics['average'] = round(total / count, 2) if count > 0 else 0
        
        return Response({
            'status': 'success',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'period': 'last_hour',
            'metrics_by_agent': metrics_by_agent,
            'total_metrics': recent_metrics.count()
        }, status=status.HTTP_200_OK)
    
    except Exception as e:  # noqa: BLE001
        return Response({
            'status': 'error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def readiness_check(request):
    """
    Kubernetes readiness probe
    Checks if service is ready to accept traffic
    """
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Check if critical tables exist
        Agent.objects.exists()
        Session.objects.exists()
        
        return Response({
            'ready': True,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }, status=status.HTTP_200_OK)
    
    except Exception as e:  # noqa: BLE001
        return Response({
            'ready': False,
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['GET'])
@permission_classes([AllowAny])
def liveness_check(request):
    """
    Kubernetes liveness probe
    Checks if service is alive
    """
    return Response({
        'alive': True,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }, status=status.HTTP_200_OK)
