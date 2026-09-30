from rest_framework import serializers

from .models import (
    AnomalyDetection,
    CostAnalysis,
    PerformanceMetric,
    PredictiveAnalytics,
    WorkflowOptimization,
)


class PerformanceMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerformanceMetric
        fields = '__all__'
        read_only_fields = ('id', 'timestamp')


class CostAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = CostAnalysis
        fields = '__all__'
        read_only_fields = ('id', 'timestamp')


class WorkflowOptimizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowOptimization
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class AnomalyDetectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnomalyDetection
        fields = '__all__'
        read_only_fields = ('id', 'detected_at')


class PredictiveAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PredictiveAnalytics
        fields = '__all__'
        read_only_fields = ('id', 'created_at')
