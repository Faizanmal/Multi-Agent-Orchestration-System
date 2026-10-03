from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AdaptiveStrategyViewSet,
    AgentLearningPolicyViewSet,
    AgentLearningViewSet,
    ReinforcementStateViewSet,
)

router = DefaultRouter()
router.register(r"profiles", AgentLearningViewSet, basename="learning-profile")
router.register(r"strategies", AdaptiveStrategyViewSet, basename="adaptive-strategy")
router.register(r"states", ReinforcementStateViewSet, basename="rl-state")
router.register(r"policies", AgentLearningPolicyViewSet, basename="learning-policy")

urlpatterns = [
    path("", include(router.urls)),
]
