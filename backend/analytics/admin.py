from django.contrib import admin

from .models import (
    AnomalyDetection,
    CostAnalysis,
    PerformanceMetric,
    PredictiveAnalytics,
    WorkflowOptimization,
)


@admin.register(PerformanceMetric)
class PerformanceMetricAdmin(admin.ModelAdmin):
    list_display = ('metric_type', 'value', 'workflow_id', 'agent_id', 'timestamp')
    list_filter = ('metric_type', 'timestamp')
    search_fields = ('workflow_id', 'agent_id')


@admin.register(CostAnalysis)
class CostAnalysisAdmin(admin.ModelAdmin):
    list_display = ('provider', 'model_name', 'tokens_used', 'cost', 'user', 'timestamp')
    list_filter = ('provider', 'timestamp')
    search_fields = ('model_name', 'user__username')


@admin.register(WorkflowOptimization)
class WorkflowOptimizationAdmin(admin.ModelAdmin):
    list_display = ('workflow_id', 'optimization_type', 'confidence_score', 'implemented', 'created_at')
    list_filter = ('optimization_type', 'implemented', 'created_at')


@admin.register(AnomalyDetection)
class AnomalyDetectionAdmin(admin.ModelAdmin):
    list_display = ('anomaly_type', 'severity', 'affected_component', 'resolved', 'detected_at')
    list_filter = ('severity', 'resolved', 'detected_at')


@admin.register(PredictiveAnalytics)
class PredictiveAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('prediction_type', 'time_horizon', 'historical_data_used', 'created_at')
    list_filter = ('prediction_type', 'created_at')
