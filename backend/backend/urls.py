"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from agents import health_views

urlpatterns = [
    path("admin/", admin.site.urls),
    # Health check endpoints (top-level for easy access)
    path("health/", health_views.health_check, name="health_check"),
    path("health/status/", health_views.system_status, name="system_status"),
    path("health/ready/", health_views.readiness_check, name="readiness"),
    path("health/live/", health_views.liveness_check, name="liveness"),
    path("agents/", include("agents.urls")),
    path("mcp/", include("Mcp_Integration.urls")),
    path("models/", include("models.urls")),
    path("coordination/", include("Multi_agents_cordination.urls")),
    path(
        "intelligence/",
        include("Multi_model_Intelligence.urls", namespace="intelligence"),
    ),
    path("performance/", include("real_time_performance.urls")),
    path("use-case/", include("use_case.urls")),
    # Enhanced feature URLs
    path(
        "authentication/api/",
        include("authentication.urls", namespace="authentication_api"),
    ),
    path(
        "api-integrations/api/",
        include("api_integrations.urls", namespace="api_integrations_api"),
    ),
    path("reporting/api/", include("reporting.urls", namespace="reporting_api")),
    path("notifications/api/", include("notifications.urls")),
    path("data-pipelines/api/", include("data_pipelines.urls")),
    # New feature modules
    path("agent-learning/", include("agent_learning.urls")),
    path("plugins/", include("plugin_system.urls")),
    path("webhooks/", include("webhooks.urls")),
    path("analytics/", include("analytics.urls")),
    path("workflow-builder/", include("workflow_builder.urls")),
    path("integrations/", include("integrations.urls", namespace="integrations_main")),
    path("feedback/", include("feedback.urls")),
    # API endpoints with /api/ prefix for frontend
    path(
        "api/multimodel/",
        include("Multi_model_Intelligence.urls", namespace="api_multimodel"),
    ),
    path("api/feedback/", include("feedback.urls")),
    path("api/reporting/", include("reporting.urls", namespace="api_reporting")),
    path(
        "api/integrations/", include("integrations.urls", namespace="integrations_api")
    ),
    path("api/auth/", include("authentication.urls", namespace="api_auth")),
    path("api/billing/", include("billing.urls", namespace="api_billing")),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
