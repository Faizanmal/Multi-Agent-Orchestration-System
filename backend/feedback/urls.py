"""
User Feedback URLs
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AgentRatingViewSet, FeedbackTrendViewSet, UserFeedbackViewSet

router = DefaultRouter()
router.register(r"feedback", UserFeedbackViewSet, basename="feedback")
router.register(r"ratings", AgentRatingViewSet, basename="ratings")
router.register(r"trends", FeedbackTrendViewSet, basename="trends")

urlpatterns = [
    path("", include(router.urls)),
]
