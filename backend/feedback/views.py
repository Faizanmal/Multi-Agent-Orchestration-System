"""
User Feedback Views
API endpoints for submitting and viewing feedback
"""

import logging

from django.db import models
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import AgentRating, FeedbackTrend, UserFeedback
from .serializers import (
    AgentRatingSerializer,
    FeedbackTrendSerializer,
    UserFeedbackSerializer,
)
from .services import get_feedback_service

logger = logging.getLogger(__name__)


class UserFeedbackViewSet(viewsets.ModelViewSet):
    """ViewSet for user feedback"""

    serializer_class = UserFeedbackSerializer
    permission_classes = [IsAuthenticated]  # noqa: RUF012

    def get_queryset(self):
        return UserFeedback.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Submit feedback"""
        feedback_service = get_feedback_service()
        data = serializer.validated_data

        create_kwargs = {
            key: value
            for key, value in {
                "rating": data.get("rating"),
                "thumbs_up": data.get("thumbs_up"),
                "comment": data.get("comment", "") or "",
                "message": data.get("message"),
                "session": data.get("session"),
                "agent": data.get("agent"),
            }.items()
            if value is not None
        }
        if "comment" not in create_kwargs:
            create_kwargs["comment"] = ""

        feedback = feedback_service.submit_feedback(
            user=self.request.user,
            feedback_type=data.get("feedback_type"),
            **create_kwargs,
        )

        if feedback:
            serializer.instance = feedback
        else:
            raise Exception("Failed to submit feedback")  # noqa: TRY002

    @action(detail=False, methods=["get"])
    def my_feedback(self, request):
        """Get user's feedback history"""
        feedbacks = self.get_queryset().order_by("-created_at")[:50]
        serializer = self.get_serializer(feedbacks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def quick_rating(self, request):
        """Quick rating endpoint"""
        message_id = request.data.get("message_id")
        rating = request.data.get("rating")

        if not message_id or not rating:
            return Response(
                {"error": "message_id and rating required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        feedback_service = get_feedback_service()
        feedback = feedback_service.submit_feedback(
            user=request.user,
            feedback_type="rating",
            rating=rating,
            message_id=message_id,
        )

        if feedback:
            return Response({"id": str(feedback.id), "message": "Rating submitted"})
        else:
            return Response(
                {"error": "Failed to submit rating"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"])
    def thumbs(self, request):
        """Thumbs up/down endpoint"""
        message_id = request.data.get("message_id")
        thumbs_up = request.data.get("thumbs_up")

        if not message_id or thumbs_up is None:
            return Response(
                {"error": "message_id and thumbs_up required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        feedback_service = get_feedback_service()
        feedback = feedback_service.submit_feedback(
            user=request.user,
            feedback_type="thumbs",
            thumbs_up=thumbs_up,
            message_id=message_id,
        )

        if feedback:
            return Response({"id": str(feedback.id), "message": "Feedback submitted"})
        else:
            return Response(
                {"error": "Failed to submit feedback"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AgentRatingViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for agent ratings"""

    serializer_class = AgentRatingSerializer
    permission_classes = [IsAuthenticated]  # noqa: RUF012

    def get_queryset(self):
        # Get ratings for user's agents
        from agents.models import Agent

        user_agent_ids = Agent.objects.filter(owner=self.request.user).values_list(
            "id", flat=True
        )
        return AgentRating.objects.filter(agent_id__in=user_agent_ids)

    @action(detail=False, methods=["get"])
    def agent_insights(self, request):
        """Get insights for a specific agent"""
        agent_id = request.query_params.get("agent_id")
        days = int(request.query_params.get("days", 30))

        if not agent_id:
            return Response(
                {"error": "agent_id required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Verify agent ownership
        from agents.models import Agent

        get_object_or_404(Agent, id=agent_id, owner=request.user)

        feedback_service = get_feedback_service()
        insights = feedback_service.get_agent_insights(agent_id, days)

        return Response(insights)


class FeedbackTrendViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for feedback trends"""

    serializer_class = FeedbackTrendSerializer
    permission_classes = [IsAuthenticated]  # noqa: RUF012

    def get_queryset(self):
        # Get trends for user's agents or system-wide
        from agents.models import Agent

        user_agent_ids = Agent.objects.filter(owner=self.request.user).values_list(
            "id", flat=True
        )
        return FeedbackTrend.objects.filter(
            models.Q(agent_id__in=user_agent_ids) | models.Q(agent__isnull=True)
        )

    @action(detail=False, methods=["post"])
    def generate(self, request):
        """Generate new trend report"""
        period = request.data.get("period", "weekly")
        agent_id = request.data.get("agent_id")

        if period not in ["daily", "weekly", "monthly"]:
            return Response(
                {"error": "Invalid period. Use daily, weekly, or monthly"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if agent_id:
            # Verify agent ownership
            from agents.models import Agent

            get_object_or_404(Agent, id=agent_id, owner=request.user)

        feedback_service = get_feedback_service()
        trend = feedback_service.generate_trend_report(period, agent_id)

        serializer = self.get_serializer(trend)
        return Response(serializer.data)
