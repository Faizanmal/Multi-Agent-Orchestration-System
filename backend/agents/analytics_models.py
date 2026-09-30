"""
Advanced Analytics Models
Predictive insights, cost tracking, and anomaly detection
"""
import uuid
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class CostTracking(models.Model):
    """Track API usage costs"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Owner
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cost_tracking')
    
    # Resource details
    resource_type = models.CharField(max_length=50, choices=[
        ('agent', 'Agent'),
        ('session', 'Session'),
        ('workflow', 'Workflow'),
        ('api_call', 'API Call')
    ])
    resource_id = models.UUIDField(null=True, blank=True)
    
    # API provider
    provider = models.CharField(max_length=100, help_text="e.g., 'groq', 'openai', 'anthropic'")
    model_name = models.CharField(max_length=100)
    
    # Usage metrics
    input_tokens = models.IntegerField(default=0)
    output_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    
    # Cost calculation
    input_cost_per_token = models.DecimalField(max_digits=12, decimal_places=8)
    output_cost_per_token = models.DecimalField(max_digits=12, decimal_places=8)
    total_cost = models.DecimalField(max_digits=10, decimal_places=4)
    
    # Request details
    request_duration_ms = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('success', 'Success'),
        ('error', 'Error'),
        ('timeout', 'Timeout')
    ], default='success')
    
    # Metadata
    metadata = models.JSONField(default=dict)
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['provider', 'model_name', '-created_at']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]
    
    def __str__(self):
        return f"{self.provider}/{self.model_name} - ${self.total_cost}"


class PredictiveInsight(models.Model):
    """AI-generated predictive insights"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Owner
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='insights')
    
    # Insight details
    insight_type = models.CharField(max_length=50, choices=[
        ('cost_forecast', 'Cost Forecast'),
        ('performance_trend', 'Performance Trend'),
        ('optimization_opportunity', 'Optimization Opportunity'),
        ('anomaly_detection', 'Anomaly Detection'),
        ('usage_pattern', 'Usage Pattern'),
        ('recommendation', 'Recommendation')
    ])
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Prediction/Analysis
    prediction_data = models.JSONField(default=dict, help_text="Detailed prediction data")
    confidence_score = models.DecimalField(max_digits=5, decimal_places=4, help_text="0.0 to 1.0")
    
    # Impact assessment
    impact_level = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ])
    estimated_savings = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    estimated_improvement_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Recommendations
    recommended_actions = models.JSONField(default=list)
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('acknowledged', 'Acknowledged'),
        ('implemented', 'Implemented'),
        ('dismissed', 'Dismissed')
    ], default='active')
    
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    implemented_at = models.DateTimeField(null=True, blank=True)
    
    # Validity
    valid_until = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    source_data = models.JSONField(default=dict, help_text="Data used for analysis")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-confidence_score', '-impact_level', '-created_at']  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=['user', 'status', '-created_at']),
            models.Index(fields=['insight_type', '-created_at']),
            models.Index(fields=['-confidence_score', '-impact_level']),
        ]
    
    def __str__(self):
        return f"{self.insight_type}: {self.title}"


class AnomalyDetection(models.Model):
    """Detected anomalies in system behavior"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Context
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='anomalies', null=True, blank=True)
    
    # Anomaly details
    anomaly_type = models.CharField(max_length=50, choices=[
        ('cost_spike', 'Cost Spike'),
        ('performance_degradation', 'Performance Degradation'),
        ('error_rate_increase', 'Error Rate Increase'),
        ('usage_surge', 'Usage Surge'),
        ('unusual_pattern', 'Unusual Pattern')
    ])
    
    metric_name = models.CharField(max_length=100)
    expected_value = models.DecimalField(max_digits=12, decimal_places=4)
    actual_value = models.DecimalField(max_digits=12, decimal_places=4)
    deviation_percentage = models.DecimalField(max_digits=8, decimal_places=2)
    
    # Severity
    severity = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ])
    
    # Detection details
    detection_method = models.CharField(max_length=100, help_text="Algorithm used for detection")
    confidence_score = models.DecimalField(max_digits=5, decimal_places=4)
    
    # Context
    affected_resources = models.JSONField(default=list)
    time_window_start = models.DateTimeField()
    time_window_end = models.DateTimeField()
    
    # Root cause analysis
    potential_causes = models.JSONField(default=list)
    suggested_fixes = models.JSONField(default=list)
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('detected', 'Detected'),
        ('investigating', 'Investigating'),
        ('resolved', 'Resolved'),
        ('false_positive', 'False Positive')
    ], default='detected')
    
    resolution_note = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-severity', '-created_at']  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=['user', 'status', '-created_at']),
            models.Index(fields=['anomaly_type', '-created_at']),
            models.Index(fields=['-severity', 'status']),
        ]
    
    def __str__(self):
        return f"{self.anomaly_type} - {self.metric_name} ({self.severity})"


class WorkflowOptimization(models.Model):
    """Workflow optimization suggestions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Workflow
    workflow_id = models.UUIDField()
    workflow_name = models.CharField(max_length=200)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='workflow_optimizations')
    
    # Current metrics
    current_avg_duration_ms = models.IntegerField()
    current_avg_cost = models.DecimalField(max_digits=10, decimal_places=4)
    current_success_rate = models.DecimalField(max_digits=5, decimal_places=4)
    
    # Optimization suggestion
    optimization_type = models.CharField(max_length=50, choices=[
        ('parallel_execution', 'Parallel Execution'),
        ('agent_selection', 'Agent Selection'),
        ('model_optimization', 'Model Optimization'),
        ('caching', 'Caching Strategy'),
        ('dependency_reduction', 'Dependency Reduction'),
        ('retry_strategy', 'Retry Strategy')
    ])
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Expected improvements
    expected_duration_ms = models.IntegerField(null=True, blank=True)
    expected_cost = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    expected_success_rate = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    
    improvement_duration_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    improvement_cost_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    improvement_success_rate_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Implementation
    implementation_steps = models.JSONField(default=list)
    estimated_effort = models.CharField(max_length=20, choices=[
        ('low', 'Low - < 1 hour'),
        ('medium', 'Medium - 1-4 hours'),
        ('high', 'High - > 4 hours')
    ])
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('suggested', 'Suggested'),
        ('accepted', 'Accepted'),
        ('implemented', 'Implemented'),
        ('rejected', 'Rejected')
    ], default='suggested')
    
    # Results (after implementation)
    actual_duration_ms = models.IntegerField(null=True, blank=True)
    actual_cost = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    actual_success_rate = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    implemented_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-improvement_cost_percentage', '-improvement_duration_percentage', '-created_at']  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=['workflow_id', 'status']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.workflow_name} - {self.optimization_type}"


class UsageAnalytics(models.Model):
    """Aggregated usage analytics"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Time period
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='usage_analytics')
    date = models.DateField()
    hour = models.IntegerField(null=True, blank=True, help_text="Hour of day (0-23) for hourly analytics")
    
    # Usage metrics
    total_sessions = models.IntegerField(default=0)
    total_tasks = models.IntegerField(default=0)
    total_messages = models.IntegerField(default=0)
    
    # Agent usage
    agents_used = models.JSONField(default=dict, help_text="Agent ID to usage count mapping")
    most_used_agent = models.CharField(max_length=100, blank=True)
    
    # Performance
    avg_task_duration_ms = models.IntegerField(null=True, blank=True)
    avg_response_time_ms = models.IntegerField(null=True, blank=True)
    success_rate = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal('1.0000'))
    
    # Cost
    total_cost = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal('0.0000'))
    total_tokens = models.IntegerField(default=0)
    
    # Errors
    error_count = models.IntegerField(default=0)
    timeout_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'date', 'hour']  # noqa: RUF012
        ordering = ['-date', '-hour']  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=['user', '-date']),
            models.Index(fields=['-date', 'hour']),
        ]
    
    def __str__(self):
        period = f"{self.date} {self.hour}:00" if self.hour is not None else str(self.date)
        return f"{self.user.username} - {period}"


class PerformanceBenchmark(models.Model):
    """Performance benchmarks for comparison"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Benchmark details
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=[
        ('agent_performance', 'Agent Performance'),
        ('workflow_efficiency', 'Workflow Efficiency'),
        ('cost_efficiency', 'Cost Efficiency'),
        ('response_time', 'Response Time')
    ])
    
    # Metric
    metric_name = models.CharField(max_length=100)
    metric_unit = models.CharField(max_length=50)
    
    # Benchmark values
    percentile_25 = models.DecimalField(max_digits=12, decimal_places=4)
    percentile_50 = models.DecimalField(max_digits=12, decimal_places=4)  # Median
    percentile_75 = models.DecimalField(max_digits=12, decimal_places=4)
    percentile_90 = models.DecimalField(max_digits=12, decimal_places=4)
    percentile_95 = models.DecimalField(max_digits=12, decimal_places=4)
    
    # Sample size
    sample_count = models.IntegerField()
    
    # Metadata
    description = models.TextField()
    calculation_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'name']  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['-calculation_date']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.metric_name}"
    
    def get_percentile_rank(self, value: float) -> int:
        """Get percentile rank for a given value"""
        value = Decimal(str(value))
        
        if value <= self.percentile_25:
            return 25
        elif value <= self.percentile_50:
            return 50
        elif value <= self.percentile_75:
            return 75
        elif value <= self.percentile_90:
            return 90
        elif value <= self.percentile_95:
            return 95
        else:
            return 100


class MLModel(models.Model):
    """Machine learning models for predictions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Model details
    name = models.CharField(max_length=200)
    model_type = models.CharField(max_length=50, choices=[
        ('cost_prediction', 'Cost Prediction'),
        ('performance_prediction', 'Performance Prediction'),
        ('anomaly_detection', 'Anomaly Detection'),
        ('recommendation', 'Recommendation Engine')
    ])
    
    # Model metadata
    algorithm = models.CharField(max_length=100)
    version = models.CharField(max_length=50)
    description = models.TextField()
    
    # Training details
    training_data_size = models.IntegerField()
    training_date = models.DateTimeField()
    
    # Performance metrics
    accuracy = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    precision = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    recall = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    f1_score = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    
    # Model artifacts
    model_path = models.CharField(max_length=500, help_text="Path to saved model")
    model_config = models.JSONField(default=dict)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_production = models.BooleanField(default=False)
    
    # Usage
    prediction_count = models.IntegerField(default=0)
    last_used_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_production', '-training_date']  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=['model_type', 'is_active']),
            models.Index(fields=['-training_date']),
        ]
    
    def __str__(self):
        return f"{self.name} v{self.version}"
