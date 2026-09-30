from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"models", views.AIModelConfigViewSet, basename="ai-model")
router.register(
    r"intelligence",
    views.MultiModalIntelligenceViewSet,
    basename="multimodal-intelligence",
)
router.register(
    r"orchestrate", views.MultiModelViewSet, basename="multimodel-orchestrate"
)
router.register(
    r"coordinate", views.ModelCoordinationViewSet, basename="model-coordinate"
)

app_name = "multi_model_intelligence"

urlpatterns = [
    path("api/", include(router.urls)),
]
