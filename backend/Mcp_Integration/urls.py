from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "mcp_integration"

# Create router for ViewSets
router = DefaultRouter()
router.register(r"tools", views.MCPToolViewSet, basename="mcp-tools")
router.register(r"sessions", views.MCPSessionViewSet, basename="mcp-sessions")
router.register(
    r"agent-integration",
    views.MCPAgentIntegrationViewSet,
    basename="mcp-agent-integration",
)

urlpatterns = [
    # Include router URLs
    path("api/", include(router.urls)),
    # Additional custom endpoints can be added here
]
