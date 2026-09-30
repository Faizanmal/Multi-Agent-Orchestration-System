from datetime import timedelta
from typing import Any

import numpy as np
from django.db.models import Avg, Sum
from django.utils import timezone

from .models import CostAnalysis, PerformanceMetric


class AnalyticsService:
    """Service for advanced analytics calculations"""

    @staticmethod
    def calculate_performance_trends(
        metric_type: str, time_range: str = "7d", workflow_id: str | None = None
    ) -> dict[str, Any]:
        """Calculate performance trends over time"""

        # Parse time range
        time_delta = AnalyticsService._parse_time_range(time_range)
        start_date = timezone.now() - time_delta

        # Query metrics
        query = PerformanceMetric.objects.filter(
            metric_type=metric_type, timestamp__gte=start_date
        )

        if workflow_id:
            query = query.filter(workflow_id=workflow_id)

        metrics = query.order_by("timestamp")

        if not metrics.exists():
            return {"trend": "no_data", "data_points": []}

        # Calculate trend
        values = list(metrics.values_list("value", flat=True))
        timestamps = list(metrics.values_list("timestamp", flat=True))

        trend = AnalyticsService._calculate_trend(values)

        return {
            "trend": trend,
            "current_value": values[-1] if values else 0,
            "average": np.mean(values),
            "min": np.min(values),
            "max": np.max(values),
            "std_dev": np.std(values),
            "data_points": [
                {"timestamp": ts.isoformat(), "value": val}
                for ts, val in zip(timestamps, values)
            ],
        }

    @staticmethod
    def analyze_cost_optimization(
        user_id: int, time_range: str = "30d"
    ) -> dict[str, Any]:
        """Analyze cost patterns and suggest optimizations"""

        time_delta = AnalyticsService._parse_time_range(time_range)
        start_date = timezone.now() - time_delta

        costs = CostAnalysis.objects.filter(user_id=user_id, timestamp__gte=start_date)

        # Group by provider
        provider_costs = costs.values("provider").annotate(
            total_cost=Sum("cost"),
            total_tokens=Sum("tokens_used"),
            request_count=Sum("request_count"),
        )

        # Calculate cost per token for each provider
        optimizations = []
        for provider_data in provider_costs:
            cost_per_token = (
                float(provider_data["total_cost"]) / provider_data["total_tokens"]
                if provider_data["total_tokens"] > 0
                else 0
            )

            optimizations.append(
                {
                    "provider": provider_data["provider"],
                    "total_cost": float(provider_data["total_cost"]),
                    "total_tokens": provider_data["total_tokens"],
                    "cost_per_token": cost_per_token,
                    "request_count": provider_data["request_count"],
                }
            )

        # Find cheapest provider
        if optimizations:
            cheapest = min(optimizations, key=lambda x: x["cost_per_token"])

            suggestions = []
            for opt in optimizations:
                if opt["provider"] != cheapest["provider"]:
                    potential_savings = (
                        opt["cost_per_token"] - cheapest["cost_per_token"]
                    ) * opt["total_tokens"]
                    if potential_savings > 0:
                        suggestions.append(
                            {
                                "type": "switch_provider",
                                "from": opt["provider"],
                                "to": cheapest["provider"],
                                "estimated_savings": round(potential_savings, 2),
                                "percentage": round(
                                    (potential_savings / opt["total_cost"]) * 100, 1
                                ),
                            }
                        )

            return {
                "total_cost": sum(opt["total_cost"] for opt in optimizations),
                "provider_breakdown": optimizations,
                "suggestions": suggestions,
                "cheapest_provider": cheapest["provider"],
            }

        return {"total_cost": 0, "provider_breakdown": [], "suggestions": []}

    @staticmethod
    def detect_anomalies(
        metric_type: str, workflow_id: str | None = None, sensitivity: float = 2.5
    ) -> list[dict[str, Any]]:
        """Detect anomalies using statistical methods"""

        # Get recent metrics
        time_delta = timedelta(days=7)
        start_date = timezone.now() - time_delta

        query = PerformanceMetric.objects.filter(
            metric_type=metric_type, timestamp__gte=start_date
        )

        if workflow_id:
            query = query.filter(workflow_id=workflow_id)

        metrics = query.order_by("timestamp")

        if metrics.count() < 10:
            return []

        values = np.array(list(metrics.values_list("value", flat=True)))
        mean = np.mean(values)
        std = np.std(values)

        anomalies = []
        for metric in metrics:
            z_score = abs((metric.value - mean) / std) if std > 0 else 0

            if z_score > sensitivity:
                severity = (
                    "critical" if z_score > 4 else "high" if z_score > 3 else "medium"
                )

                anomalies.append(
                    {
                        "timestamp": metric.timestamp.isoformat(),
                        "value": metric.value,
                        "expected_range": f"{mean - 2*std:.2f} - {mean + 2*std:.2f}",
                        "z_score": round(z_score, 2),
                        "severity": severity,
                    }
                )

        return anomalies

    @staticmethod
    def generate_workflow_optimizations(workflow_id: str) -> list[dict[str, Any]]:
        """Generate AI-powered workflow optimization suggestions"""

        # Get workflow performance data
        time_delta = timedelta(days=30)
        start_date = timezone.now() - time_delta

        metrics = PerformanceMetric.objects.filter(
            workflow_id=workflow_id, timestamp__gte=start_date
        )

        optimizations = []

        # Analyze response time
        response_times = metrics.filter(metric_type="response_time")
        if response_times.exists():
            avg_time = response_times.aggregate(Avg("value"))["value__avg"]

            if avg_time > 5000:  # More than 5 seconds
                optimizations.append(
                    {
                        "type": "improve_speed",
                        "current_performance": {"avg_response_time": avg_time},
                        "suggested_changes": {
                            "enable_caching": True,
                            "parallel_execution": True,
                            "reduce_model_complexity": True,
                        },
                        "estimated_improvement": {
                            "response_time_reduction": "40-60%",
                            "estimated_new_time": avg_time * 0.5,
                        },
                        "confidence_score": 0.85,
                    }
                )

        # Analyze token usage
        token_metrics = metrics.filter(metric_type="token_usage")
        if token_metrics.exists():
            avg_tokens = token_metrics.aggregate(Avg("value"))["value__avg"]

            if avg_tokens > 2000:
                optimizations.append(
                    {
                        "type": "reduce_tokens",
                        "current_performance": {"avg_token_usage": avg_tokens},
                        "suggested_changes": {
                            "compress_prompts": True,
                            "use_smaller_context": True,
                            "implement_summarization": True,
                        },
                        "estimated_improvement": {
                            "token_reduction": "30-50%",
                            "cost_savings": "30-50%",
                        },
                        "confidence_score": 0.78,
                    }
                )

        # Analyze error rate
        error_metrics = metrics.filter(metric_type="error_rate")
        if error_metrics.exists():
            avg_error_rate = error_metrics.aggregate(Avg("value"))["value__avg"]

            if avg_error_rate > 0.05:  # More than 5% error rate
                optimizations.append(
                    {
                        "type": "increase_accuracy",
                        "current_performance": {"error_rate": avg_error_rate},
                        "suggested_changes": {
                            "add_retry_logic": True,
                            "improve_error_handling": True,
                            "add_validation": True,
                        },
                        "estimated_improvement": {
                            "error_rate_reduction": "50-70%",
                            "reliability_increase": "40-60%",
                        },
                        "confidence_score": 0.82,
                    }
                )

        return optimizations

    @staticmethod
    def predict_future_metrics(
        metric_type: str,
        prediction_horizon: str = "24h",
        workflow_id: str | None = None,
    ) -> dict[str, Any]:
        """Predict future metric values using simple time series analysis"""

        # Get historical data
        time_delta = timedelta(days=14)
        start_date = timezone.now() - time_delta

        query = PerformanceMetric.objects.filter(
            metric_type=metric_type, timestamp__gte=start_date
        )

        if workflow_id:
            query = query.filter(workflow_id=workflow_id)

        metrics = query.order_by("timestamp")

        if metrics.count() < 10:
            return {"prediction": "insufficient_data"}

        values = np.array(list(metrics.values_list("value", flat=True)))

        # Simple linear regression for trend
        x = np.arange(len(values))
        coeffs = np.polyfit(x, values, 1)
        trend_line = np.poly1d(coeffs)

        # Predict future values
        horizon_hours = AnalyticsService._parse_prediction_horizon(prediction_horizon)
        future_x = np.arange(len(values), len(values) + horizon_hours)
        predictions = trend_line(future_x)

        # Calculate confidence intervals
        residuals = values - trend_line(x)
        std_error = np.std(residuals)

        return {
            "predictions": [
                {
                    "time_offset": f"+{i}h",
                    "predicted_value": float(pred),
                    "confidence_interval": {
                        "lower": float(pred - 1.96 * std_error),
                        "upper": float(pred + 1.96 * std_error),
                    },
                }
                for i, pred in enumerate(predictions, 1)
            ],
            "trend": "increasing" if coeffs[0] > 0 else "decreasing",
            "confidence": 0.95,
        }

    @staticmethod
    def _parse_time_range(time_range: str) -> timedelta:
        """Parse time range string to timedelta"""
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

    @staticmethod
    def _parse_prediction_horizon(horizon: str) -> int:
        """Parse prediction horizon to hours"""
        unit = horizon[-1]
        value = int(horizon[:-1])

        if unit == "h":
            return value
        elif unit == "d":
            return value * 24
        else:
            return 24

    @staticmethod
    def _calculate_trend(values: list[float]) -> str:
        """Calculate trend direction"""
        if len(values) < 2:
            return "stable"

        # Simple linear regression
        x = np.arange(len(values))
        coeffs = np.polyfit(x, values, 1)
        slope = coeffs[0]

        # Calculate percentage change
        avg_value = np.mean(values)
        change_rate = abs(slope) / avg_value if avg_value != 0 else 0

        if change_rate < 0.05:
            return "stable"
        elif slope > 0:
            return "increasing"
        else:
            return "decreasing"
