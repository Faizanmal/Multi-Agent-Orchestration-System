from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(
    r"sessions", views.CoordinationSessionViewSet, basename="coordination-session"
)

app_name = "multi_agents_coordination"

urlpatterns = [
    path("api/", include(router.urls)),
]
