from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Report, ReportTemplate, Widget
from .serializers import ReportSerializer, ReportTemplateSerializer, WidgetSerializer


class ReportListCreateView(generics.ListCreateAPIView):
    """List and create reports"""

    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]  # noqa: RUF012

    def get_queryset(self):
        return Report.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ReportDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, delete report"""

    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]  # noqa: RUF012

    def get_queryset(self):
        return Report.objects.filter(user=self.request.user)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_report_view(request, pk):
    """Generate report snapshot from stored config."""
    report = get_object_or_404(Report, pk=pk, user=request.user)
    report.last_generated = timezone.now()
    report.save(update_fields=["last_generated"])
    return Response(
        {
            "report_id": str(report.id),
            "name": report.name,
            "report_data": {
                "charts": (
                    report.config.get("charts", [])
                    if isinstance(report.config, dict)
                    else []
                ),
                "metrics": {
                    "report_type": report.report_type,
                    "status": report.status,
                    "filters": report.filters,
                },
            },
            "generated_at": report.last_generated.isoformat(),
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def export_report_view(request, pk):
    """Export report metadata (file download requires object storage)."""
    report = get_object_or_404(Report, pk=pk, user=request.user)
    fmt = request.data.get("format", "json")
    return Response(
        {
            "report_id": str(report.id),
            "format": fmt,
            "download_url": None,
            "message": "Export queued. Configure object storage to enable file downloads.",
            "expires_at": (timezone.now() + timedelta(hours=24)).isoformat(),
            "payload": ReportSerializer(report).data,
        }
    )


class ReportTemplateListView(generics.ListAPIView):
    """List report templates"""

    serializer_class = ReportTemplateSerializer
    queryset = ReportTemplate.objects.filter(is_public=True)
    permission_classes = [IsAuthenticated]  # noqa: RUF012


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_view(request):
    """Get dashboard data with real-time analytics"""
    from datetime import timedelta

    from agents.models import Agent, Message, Session
    from django.utils import timezone
    from Multi_model_Intelligence.models import ModelExecution

    user = request.user
    today = timezone.now().date()
    week_ago = timezone.now() - timedelta(days=7)

    # Agent metrics
    total_agents = Agent.objects.filter(owner=user).count()
    active_agents = Agent.objects.filter(owner=user, is_active=True).count()

    # Session metrics
    total_sessions = Session.objects.filter(user=user).count()
    active_sessions = Session.objects.filter(user=user, is_active=True).count()

    # Message metrics
    messages_today = Message.objects.filter(
        session__user=user, created_at__date=today
    ).count()

    # Model execution metrics
    executions_week = ModelExecution.objects.filter(user=user, created_at__gte=week_ago)

    total_executions = executions_week.count()
    successful = executions_week.filter(success=True).count()
    success_rate = (successful / total_executions * 100) if total_executions > 0 else 0

    return Response(
        {
            "agents": {"total": total_agents, "active": active_agents},
            "sessions": {"total": total_sessions, "active": active_sessions},
            "messages": {"today": messages_today},
            "executions": {
                "week_total": total_executions,
                "success_rate": round(success_rate, 2),
            },
            "metadata": {"last_updated": timezone.now().isoformat()},
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def performance_metrics_view(request):
    """Get real-time performance metrics"""
    from real_time_performance.services import (
        get_cache_service,
        get_performance_service,
    )

    perf_service = get_performance_service()
    cache_service = get_cache_service()

    # System health
    system_health = perf_service.get_system_health()

    # Cache statistics
    cache_stats = cache_service.get_stats()

    # Recent endpoint metrics
    endpoints = ["agents", "sessions", "messages", "multimodel"]
    endpoint_metrics = {}

    for endpoint in endpoints:
        metrics = perf_service.get_endpoint_metrics(f"/api/{endpoint}/")
        endpoint_metrics[endpoint] = metrics

    return Response(
        {
            "system_health": system_health,
            "cache": cache_stats,
            "endpoints": endpoint_metrics,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def usage_trends_view(request):
    """Get usage trends over time"""
    from datetime import timedelta

    from django.db.models import Avg, Count, Sum
    from django.db.models.functions import TruncDate
    from django.utils import timezone
    from Multi_model_Intelligence.models import ModelExecution

    days = int(request.GET.get("days", 30))
    start_date = timezone.now() - timedelta(days=days)

    # Daily execution trends
    daily_executions = (
        ModelExecution.objects.filter(user=request.user, created_at__gte=start_date)
        .annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(
            count=Count("id"),
            avg_duration=Avg("duration_ms"),
            total_tokens=Sum("tokens_used"),
        )
        .order_by("date")
    )

    trends = [
        {
            "date": item["date"].isoformat(),
            "executions": item["count"],
            "avg_duration_ms": round(item["avg_duration"] or 0, 2),
            "total_tokens": item["total_tokens"] or 0,
        }
        for item in daily_executions
    ]

    return Response({"period_days": days, "trends": trends})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def model_usage_view(request):
    """Get model usage breakdown"""
    from datetime import timedelta

    from django.db.models import Avg, Count, Sum
    from django.utils import timezone
    from Multi_model_Intelligence.models import ModelExecution

    days = int(request.GET.get("days", 30))
    start_date = timezone.now() - timedelta(days=days)

    # Model usage by provider
    provider_stats = (
        ModelExecution.objects.filter(user=request.user, created_at__gte=start_date)
        .values("provider", "model_name")
        .annotate(
            count=Count("id"),
            avg_duration=Avg("duration_ms"),
            total_tokens=Sum("tokens_used"),
            success_rate=Avg("success") * 100,
        )
        .order_by("-count")
    )

    models = [
        {
            "provider": item["provider"],
            "model": item["model_name"],
            "executions": item["count"],
            "avg_duration_ms": round(item["avg_duration"] or 0, 2),
            "total_tokens": item["total_tokens"] or 0,
            "success_rate": round(item["success_rate"] or 0, 2),
        }
        for item in provider_stats
    ]

    return Response({"period_days": days, "models": models})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def system_health_view(request):
    """Get system health status"""
    from django.utils import timezone
    from integrations.azure_cosmosdb_service import get_cosmos_service
    from real_time_performance.services import get_cache_service

    health = {
        "status": "healthy",
        "timestamp": timezone.now().isoformat(),
        "services": {},
    }

    # Check Redis
    cache = get_cache_service()
    health["services"]["redis"] = {
        "status": "up" if cache.enabled else "down",
        "enabled": cache.enabled,
    }

    # Check CosmosDB
    cosmos = get_cosmos_service()
    health["services"]["cosmosdb"] = {
        "status": "up" if cosmos.client else "down",
        "enabled": cosmos.client is not None,
    }

    # Check database
    try:
        from django.db import connection

        connection.ensure_connection()
        health["services"]["database"] = {"status": "up", "enabled": True}
    except Exception as e:  # noqa: BLE001
        health["services"]["database"] = {
            "status": "down",
            "enabled": False,
            "error": str(e),
        }
        health["status"] = "degraded"

    return Response(health)


class WidgetListCreateView(generics.ListCreateAPIView):
    """List and create widgets"""

    serializer_class = WidgetSerializer
    permission_classes = [IsAuthenticated]  # noqa: RUF012

    def get_queryset(self):
        return Widget.objects.filter(dashboard__user=self.request.user)
