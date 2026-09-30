from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import DataPipeline, DataQualityRule, DataSource
from .serializers import (
    DataPipelineSerializer,
    DataQualityRuleSerializer,
    DataSourceSerializer,
)


class DataPipelineListCreateView(generics.ListCreateAPIView):
    """List and create data pipelines"""

    serializer_class = DataPipelineSerializer
    permission_classes = [IsAuthenticated]  # noqa: RUF012

    def get_queryset(self):
        return DataPipeline.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DataPipelineDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, delete data pipeline"""

    serializer_class = DataPipelineSerializer
    permission_classes = [IsAuthenticated]  # noqa: RUF012

    def get_queryset(self):
        return DataPipeline.objects.filter(user=self.request.user)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def execute_pipeline_view(request, pk):
    """Execute data pipeline"""
    get_object_or_404(DataPipeline, pk=pk, user=request.user)

    # Implementation for pipeline execution would go here
    return Response(
        {
            "execution_id": "exec-123",
            "status": "running",
            "started_at": "2024-01-01T00:00:00Z",
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def pipeline_status_view(request, pk):
    """Get pipeline execution status"""
    get_object_or_404(DataPipeline, pk=pk, user=request.user)

    return Response(
        {"status": "completed", "progress": 100, "current_step": "Finished", "logs": []}
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def stop_pipeline_view(request, pk):
    """Stop pipeline execution"""
    get_object_or_404(DataPipeline, pk=pk, user=request.user)

    return Response({"status": "stopped", "stopped_at": "2024-01-01T00:00:00Z"})


class DataSourceListCreateView(generics.ListCreateAPIView):
    """List and create data sources"""

    serializer_class = DataSourceSerializer
    permission_classes = [IsAuthenticated]  # noqa: RUF012

    def get_queryset(self):
        return DataSource.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DataSourceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, delete data source"""

    serializer_class = DataSourceSerializer
    permission_classes = [IsAuthenticated]  # noqa: RUF012

    def get_queryset(self):
        return DataSource.objects.filter(user=self.request.user)


def _test_data_source_connection(data_source):
    """Attempt a real connection based on DataSource type/config."""
    import time

    from django.utils import timezone

    config = data_source.connection_config or {}
    source_type = data_source.source_type
    started = time.perf_counter()

    try:
        if source_type == "database":
            db_type = data_source.database_type or config.get("database_type", "")
            host = config.get("host", "localhost")
            port = config.get("port")
            database = config.get("database") or config.get("name") or config.get("db")
            user = config.get("user") or config.get("username")
            password = config.get("password", "")

            if db_type == "sqlite":
                import sqlite3

                path = config.get("path") or database
                if not path:
                    raise ValueError("SQLite path is required in connection_config")
                conn = sqlite3.connect(path, timeout=5)
                conn.execute("SELECT 1")
                conn.close()
            elif db_type == "postgresql":
                import psycopg2

                conn = psycopg2.connect(
                    host=host,
                    port=port or 5432,
                    dbname=database,
                    user=user,
                    password=password,
                    connect_timeout=5,
                )
                conn.close()
            elif db_type == "mysql":
                import MySQLdb

                conn = MySQLdb.connect(
                    host=host,
                    port=int(port or 3306),
                    db=database,
                    user=user,
                    passwd=password,
                    connect_timeout=5,
                )
                conn.close()
            elif db_type == "redis":
                import redis

                client = redis.Redis(
                    host=host,
                    port=int(port or 6379),
                    password=password or None,
                    db=int(config.get("db", 0)),
                    socket_connect_timeout=5,
                )
                client.ping()
            elif db_type == "mongodb":
                from pymongo import MongoClient

                uri = config.get("uri") or f"mongodb://{host}:{port or 27017}"
                client = MongoClient(uri, serverSelectionTimeoutMS=5000)
                client.admin.command("ping")
                client.close()
            else:
                raise ValueError(
                    f"Unsupported database_type '{db_type}'. "
                    "Configure postgresql, mysql, sqlite, redis, or mongodb."
                )

        elif source_type == "api":
            import urllib.request

            url = config.get("url") or config.get("endpoint") or config.get("base_url")
            if not url:
                raise ValueError("API url/endpoint is required in connection_config")
            method = (config.get("method") or "GET").upper()
            headers = config.get("headers") or {}
            req = urllib.request.Request(url, method=method, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status >= 400:
                    raise ValueError(f"HTTP {resp.status} from {url}")

        elif source_type == "file":
            import os

            path = (
                config.get("path") or config.get("file_path") or config.get("directory")
            )
            if not path:
                raise ValueError("File path is required in connection_config")
            if not os.path.exists(path):
                raise FileNotFoundError(f"Path does not exist: {path}")

        elif source_type in ("ftp",):
            import ftplib

            host = config.get("host")
            if not host:
                raise ValueError("FTP host is required in connection_config")
            ftp = ftplib.FTP()
            ftp.connect(host, int(config.get("port") or 21), timeout=10)
            ftp.login(config.get("user") or "anonymous", config.get("password") or "")
            ftp.quit()

        elif source_type in ("webhook", "stream", "cloud_storage", "email"):
            # Validate required config keys exist; full live probes need credentials
            required = {
                "webhook": ["url"],
                "stream": ["url"],
                "cloud_storage": ["bucket"],
                "email": ["host"],
            }.get(source_type, [])
            missing = [k for k in required if not config.get(k)]
            if missing:
                raise ValueError(f"Missing required config keys: {', '.join(missing)}")
            # Soft probe for webhook/stream URL when present
            if source_type in ("webhook", "stream") and config.get("url"):
                import urllib.request

                req = urllib.request.Request(config["url"], method="HEAD")
                try:
                    urllib.request.urlopen(req, timeout=10)
                except Exception as probe_err:  # noqa: BLE001
                    # HEAD may be rejected; try GET
                    try:
                        urllib.request.urlopen(config["url"], timeout=10)
                    except Exception:  # noqa: BLE001
                        raise probe_err from None
        else:
            raise ValueError(f"Unsupported source_type '{source_type}'")

        elapsed_ms = (time.perf_counter() - started) * 1000
        data_source.status = "active"
        data_source.last_test_at = timezone.now()
        data_source.last_test_success = True
        data_source.connection_time = elapsed_ms
        data_source.save(
            update_fields=[
                "status",
                "last_test_at",
                "last_test_success",
                "connection_time",
                "updated_at",
            ]
        )
        return {
            "success": True,
            "connection_time": round(elapsed_ms, 2),
            "message": "Connection successful",
        }
    except Exception as exc:  # noqa: BLE001
        elapsed_ms = (time.perf_counter() - started) * 1000
        data_source.status = "error"
        data_source.last_test_at = timezone.now()
        data_source.last_test_success = False
        data_source.connection_time = elapsed_ms
        data_source.save(
            update_fields=[
                "status",
                "last_test_at",
                "last_test_success",
                "connection_time",
                "updated_at",
            ]
        )
        return {
            "success": False,
            "connection_time": round(elapsed_ms, 2),
            "error": str(exc),
        }


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def test_data_source_view(request, pk):
    """Test data source connection with a real probe."""
    data_source = get_object_or_404(DataSource, pk=pk, user=request.user)
    result = _test_data_source_connection(data_source)
    status_code = 200 if result.get("success") else 400
    return Response(result, status=status_code)


class DataQualityRuleListCreateView(generics.ListCreateAPIView):
    """List and create data quality rules"""

    serializer_class = DataQualityRuleSerializer
    permission_classes = [IsAuthenticated]  # noqa: RUF012

    def get_queryset(self):
        return DataQualityRule.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
