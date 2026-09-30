from django.urls import path

from . import views

app_name = "api_integrations"

urlpatterns = [
    path(
        "integrations/",
        views.APIIntegrationListCreateView.as_view(),
        name="integrations",
    ),
    path(
        "integrations/<uuid:pk>/",
        views.APIIntegrationDetailView.as_view(),
        name="integration_detail",
    ),
    path(
        "integrations/<uuid:pk>/test/",
        views.test_integration_view,
        name="test_integration",
    ),
    path(
        "integrations/<uuid:pk>/execute/",
        views.execute_integration_view,
        name="execute_integration",
    ),
    path("activity/", views.integration_activity_view, name="integration_activity"),
    path("tools/", views.integration_tools_view, name="integration_tools"),
    path(
        "automations/",
        views.ScheduledAutomationListCreateView.as_view(),
        name="automations",
    ),
    path(
        "automations/<uuid:pk>/",
        views.ScheduledAutomationDetailView.as_view(),
        name="automation_detail",
    ),
    path(
        "automations/<uuid:pk>/run/",
        views.run_automation_now_view,
        name="automation_run",
    ),
    path("templates/", views.IntegrationTemplateListView.as_view(), name="templates"),
]
