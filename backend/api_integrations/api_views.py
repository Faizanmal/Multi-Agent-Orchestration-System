from datetime import timezone

"""
API endpoints for frontend integration
"""
from datetime import datetime

from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def integrations_list(request):
    """List API integrations"""
    return Response(
        {
            "results": [
                {
                    "id": 1,
                    "name": "Groq API",
                    "status": "active",
                    "type": "llm",
                    "description": "Fast inference with Groq",
                },
                {
                    "id": 2,
                    "name": "OpenAI API",
                    "status": "active",
                    "type": "llm",
                    "description": "GPT models integration",
                },
            ]
        }
    )


@api_view(["GET"])
def integrations_calls(request):
    """List integration calls"""
    return Response(
        {
            "results": [
                {
                    "id": 1,
                    "integration": "Groq API",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "status": "success",
                    "response_time": 150,
                }
            ]
        }
    )


@api_view(["GET"])
def integrations_templates(request):
    """List integration templates"""
    return Response(
        {
            "results": [
                {
                    "id": 1,
                    "name": "Chat Completion",
                    "type": "llm",
                    "description": "Standard chat completion template",
                }
            ]
        }
    )


@api_view(["GET"])
def reports_charts(request):
    """Get chart data for reports"""
    return Response(
        {
            "charts": [
                {
                    "id": "agent_activity",
                    "title": "Agent Activity",
                    "type": "line",
                    "data": [
                        {
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "value": 85,
                        }
                    ],
                }
            ]
        }
    )


@api_view(["GET"])
def reports_metrics(request):
    """Get metrics data"""
    return Response(
        {
            "metrics": {
                "total_agents": 702,
                "active_agents": 45,
                "total_messages": 1247,
                "avg_response_time": 230,
            }
        }
    )


@api_view(["GET"])
def reports_templates(request):
    """Get report templates"""
    return Response(
        {
            "results": [
                {
                    "id": 1,
                    "name": "Agent Performance Report",
                    "description": "Comprehensive agent performance metrics",
                }
            ]
        }
    )


@api_view(["GET"])
def reports_custom(request):
    """Get custom reports"""
    return Response({"results": []})


@api_view(["GET"])
def notifications_list(request):
    """List notifications"""
    return Response(
        {
            "results": [
                {
                    "id": 1,
                    "title": "System Status",
                    "message": "All agents operational",
                    "type": "success",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ]
        }
    )


@api_view(["GET"])
def notifications_email_templates(request):
    """List email templates"""
    return Response({"results": []})


@api_view(["GET"])
def notifications_email_campaigns(request):
    """List email campaigns"""
    return Response({"results": []})


@api_view(["GET"])
def notifications_rules(request):
    """List notification rules"""
    return Response({"results": []})


@api_view(["GET"])
def notifications_settings(request):
    """Get notification settings"""
    return Response({"email_enabled": True, "push_enabled": False})


@api_view(["GET"])
def data_pipelines(request):
    """List data pipelines"""
    return Response(
        {
            "results": [
                {
                    "id": 1,
                    "name": "Agent Data Pipeline",
                    "status": "running",
                    "last_run": datetime.now(timezone.utc).isoformat(),
                }
            ]
        }
    )


@api_view(["GET"])
def data_connections(request):
    """List data connections"""
    return Response({"results": []})


@api_view(["GET"])
def data_pipeline_executions(request):
    """List pipeline executions"""
    return Response({"results": []})


@api_view(["GET"])
def data_quality_rules(request):
    """List data quality rules"""
    return Response({"results": []})


@api_view(["GET"])
def data_pipeline_templates(request):
    """List pipeline templates"""
    return Response({"results": []})
