import uuid

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class PerformanceMetric(models.Model):
    """Track detailed performance metrics for workflows and agents"""

    METRIC_TYPE_CHOICES = (
        ("response_time", "Response Time"),
        ("token_usage", "Token Usage"),
        ("cost", "Cost"),
        ("success_rate", "Success Rate"),
        ("error_rate", "Error Rate"),
        ("throughput", "Throughput"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    metric_type = models.CharField(max_length=50, choices=METRIC_TYPE_CHOICES)
    value = models.FloatField()
    workflow_id = models.UUIDField(null=True, blank=True)
    agent_id = models.UUIDField(null=True, blank=True)
    session_id = models.UUIDField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "analytics_performance_metrics"
        indexes = (
            models.Index(fields=["metric_type", "timestamp"]),
            models.Index(fields=["workflow_id", "timestamp"]),
            models.Index(fields=["agent_id", "timestamp"]),
        )


class CostAnalysis(models.Model):
    """Track and analyze API usage costs"""

    PROVIDER_CHOICES = (
        ("groq", "Groq"),
        ("openai", "OpenAI"),
        ("anthropic", "Anthropic"),
        ("custom", "Custom Provider"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES)
    model_name = models.CharField(max_length=100)
    tokens_used = models.IntegerField()
    cost = models.DecimalField(max_digits=10, decimal_places=6)
    request_count = models.IntegerField(default=1)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="cost_analyses"
    )
    workflow_id = models.UUIDField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "analytics_cost_analysis"
        indexes = (
            models.Index(fields=["user", "timestamp"]),
            models.Index(fields=["provider", "timestamp"]),
        )


class WorkflowOptimization(models.Model):
    """AI-powered workflow optimization suggestions"""

    OPTIMIZATION_TYPE_CHOICES = (
        ("reduce_cost", "Reduce Cost"),
        ("improve_speed", "Improve Speed"),
        ("increase_accuracy", "Increase Accuracy"),
        ("reduce_tokens", "Reduce Token Usage"),
        ("parallel_execution", "Parallel Execution"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow_id = models.UUIDField()
    optimization_type = models.CharField(
        max_length=50, choices=OPTIMIZATION_TYPE_CHOICES
    )
    current_performance = models.JSONField()
    suggested_changes = models.JSONField()
    estimated_improvement = models.JSONField()
    confidence_score = models.FloatField()
    implemented = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "analytics_workflow_optimization"
        ordering = ("-created_at",)


class AnomalyDetection(models.Model):
    """Detect anomalies in system performance"""

    SEVERITY_CHOICES = (
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    anomaly_type = models.CharField(max_length=100)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    affected_component = models.CharField(max_length=100)
    description = models.TextField()
    metrics = models.JSONField()
    detected_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "analytics_anomaly_detection"
        ordering = ("-detected_at",)


class PredictiveAnalytics(models.Model):
    """Predictive analytics for capacity planning and forecasting"""

    PREDICTION_TYPE_CHOICES = (
        ("load_forecast", "Load Forecast"),
        ("cost_forecast", "Cost Forecast"),
        ("capacity_planning", "Capacity Planning"),
        ("failure_prediction", "Failure Prediction"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prediction_type = models.CharField(max_length=50, choices=PREDICTION_TYPE_CHOICES)
    time_horizon = models.CharField(max_length=50)  # e.g., "24h", "7d", "30d"
    predictions = models.JSONField()
    confidence_intervals = models.JSONField()
    historical_data_used = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "analytics_predictive_analytics"
        ordering = ("-created_at",)
