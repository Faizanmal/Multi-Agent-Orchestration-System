from datetime import timedelta

from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    AnomalyDetection,
    CostAnalysis,
    PerformanceMetric,
    PredictiveAnalytics,
    WorkflowOptimization,
)
from .serializers import (
    AnomalyDetectionSerializer,
    CostAnalysisSerializer,
    PerformanceMetricSerializer,
    PredictiveAnalyticsSerializer,
    WorkflowOptimizationSerializer,
)
from .services import AnalyticsService


class PerformanceMetricViewSet(viewsets.ModelViewSet):
    """ViewSet for performance metrics"""

    queryset = PerformanceMetric.objects.all()
    serializer_class = PerformanceMetricSerializer
    permission_classes = (IsAuthenticated,)

    @action(detail=False, methods=["get"])
    def trends(self, request):
        """Get performance trends"""
        metric_type = request.query_params.get("metric_type", "response_time")
        time_range = request.query_params.get("time_range", "7d")
        workflow_id = request.query_params.get("workflow_id")

        trends = AnalyticsService.calculate_performance_trends(
            metric_type=metric_type, time_range=time_range, workflow_id=workflow_id
        )

        return Response(trends)

    @action(detail=False, methods=["post"])
    def bulk_create(self, request):
        """Bulk create performance metrics"""
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CostAnalysisViewSet(viewsets.ModelViewSet):
    """ViewSet for cost analysis"""

    queryset = CostAnalysis.objects.all()
    serializer_class = CostAnalysisSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """Filter by user"""
        if self.request.user.is_staff:
            return CostAnalysis.objects.all()
        return CostAnalysis.objects.filter(user=self.request.user)

    @action(detail=False, methods=["get"])
    def optimization(self, request):
        """Get cost optimization suggestions"""
        time_range = request.query_params.get("time_range", "30d")

        analysis = AnalyticsService.analyze_cost_optimization(
            user_id=request.user.id, time_range=time_range
        )

        return Response(analysis)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Get cost summary by provider"""
        time_range = request.query_params.get("time_range", "30d")
        time_delta = self._parse_time_range(time_range)
        start_date = timezone.now() - time_delta

        costs = self.get_queryset().filter(timestamp__gte=start_date)

        summary = {
            "total_cost": sum(float(c.cost) for c in costs),
            "total_tokens": sum(c.tokens_used for c in costs),
            "total_requests": sum(c.request_count for c in costs),
            "by_provider": {},
        }

        for cost in costs:
            if cost.provider not in summary["by_provider"]:
                summary["by_provider"][cost.provider] = {
                    "cost": 0,
                    "tokens": 0,
                    "requests": 0,
                }

            summary["by_provider"][cost.provider]["cost"] += float(cost.cost)
            summary["by_provider"][cost.provider]["tokens"] += cost.tokens_used
            summary["by_provider"][cost.provider]["requests"] += cost.request_count

        return Response(summary)

    def _parse_time_range(self, time_range: str) -> timedelta:
        """Parse time range string"""
        unit = time_range[-1]
        value = int(time_range[:-1])

        if unit == "h":
            return timedelta(hours=value)
        elif unit == "d":
            return timedelta(days=value)
        elif unit == "w":
            return timedelta(weeks=value)
        else:
            return timedelta(days=7)


class WorkflowOptimizationViewSet(viewsets.ModelViewSet):
    """ViewSet for workflow optimization suggestions"""

    queryset = WorkflowOptimization.objects.all()
    serializer_class = WorkflowOptimizationSerializer
    permission_classes = (IsAuthenticated,)

    @action(detail=False, methods=["post"])
    def generate(self, request):
        """Generate optimization suggestions for a workflow"""
        workflow_id = request.data.get("workflow_id")

        if not workflow_id:
            return Response(
                {"error": "workflow_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        optimizations = AnalyticsService.generate_workflow_optimizations(workflow_id)

        # Save optimizations to database
        saved_optimizations = []
        for opt in optimizations:
            optimization = WorkflowOptimization.objects.create(
                workflow_id=workflow_id,
                optimization_type=opt["type"],
                current_performance=opt["current_performance"],
                suggested_changes=opt["suggested_changes"],
                estimated_improvement=opt["estimated_improvement"],
                confidence_score=opt["confidence_score"],
            )
            saved_optimizations.append(optimization)

        serializer = self.get_serializer(saved_optimizations, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def implement(self, request, pk=None):
        """Mark optimization as implemented"""
        optimization = self.get_object()
        optimization.implemented = True
        optimization.save()

        return Response({"status": "implemented"})


class AnomalyDetectionViewSet(viewsets.ModelViewSet):
    """ViewSet for anomaly detection"""

    queryset = AnomalyDetection.objects.all()
    serializer_class = AnomalyDetectionSerializer
    permission_classes = (IsAuthenticated,)

    @action(detail=False, methods=["post"])
    def detect(self, request):
        """Detect anomalies in metrics"""
        metric_type = request.data.get("metric_type", "response_time")
        workflow_id = request.data.get("workflow_id")
        sensitivity = float(request.data.get("sensitivity", 2.5))

        anomalies = AnalyticsService.detect_anomalies(
            metric_type=metric_type, workflow_id=workflow_id, sensitivity=sensitivity
        )

        # Save detected anomalies
        saved_anomalies = []
        for anomaly in anomalies:
            anomaly_obj = AnomalyDetection.objects.create(
                anomaly_type=metric_type,
                severity=anomaly["severity"],
                affected_component=(
                    f"workflow_{workflow_id}" if workflow_id else "system"
                ),
                description=f"Anomalous {metric_type} detected: {anomaly['value']} (expected: {anomaly['expected_range']})",
                metrics={
                    "value": anomaly["value"],
                    "z_score": anomaly["z_score"],
                    "expected_range": anomaly["expected_range"],
                },
            )
            saved_anomalies.append(anomaly_obj)

        serializer = self.get_serializer(saved_anomalies, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        """Mark anomaly as resolved"""
        anomaly = self.get_object()
        anomaly.resolved = True
        anomaly.resolved_at = timezone.now()
        anomaly.save()

        return Response({"status": "resolved"})


class PredictiveAnalyticsViewSet(viewsets.ModelViewSet):
    """ViewSet for predictive analytics"""

    queryset = PredictiveAnalytics.objects.all()
    serializer_class = PredictiveAnalyticsSerializer
    permission_classes = (IsAuthenticated,)

    @action(detail=False, methods=["post"])
    def forecast(self, request):
        """Generate forecast for metrics"""
        metric_type = request.data.get("metric_type", "response_time")
        prediction_horizon = request.data.get("prediction_horizon", "24h")
        workflow_id = request.data.get("workflow_id")

        predictions = AnalyticsService.predict_future_metrics(
            metric_type=metric_type,
            prediction_horizon=prediction_horizon,
            workflow_id=workflow_id,
        )

        if predictions.get("prediction") == "insufficient_data":
            return Response(
                {"error": "Insufficient historical data for prediction"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Save prediction
        prediction_obj = PredictiveAnalytics.objects.create(
            prediction_type="load_forecast",
            time_horizon=prediction_horizon,
            predictions=predictions["predictions"],
            confidence_intervals={
                "level": predictions.get("confidence", 0.95),
                "trend": predictions.get("trend", "stable"),
            },
            historical_data_used=len(predictions.get("predictions", [])),
        )

        serializer = self.get_serializer(prediction_obj)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
