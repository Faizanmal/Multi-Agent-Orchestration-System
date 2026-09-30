"""
Integrations URLs
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"integrations", views.IntegrationViewSet, basename="integration")
router.register(r"azure-cosmos", views.AzureCosmosDBViewSet, basename="azure-cosmos")
router.register(
    r"azure-functions", views.AzureFunctionsViewSet, basename="azure-functions"
)

app_name = "integrations"

urlpatterns = [
    path("", include(router.urls)),
    # Azure CosmosDB endpoints
    path(
        "azure-cosmos/containers/",
        views.list_cosmos_containers,
        name="list_cosmos_containers",
    ),
    path("azure-cosmos/query/", views.query_cosmos_db, name="query_cosmos_db"),
    # Azure Functions endpoints
    path(
        "azure-functions/trigger/",
        views.trigger_azure_function,
        name="trigger_azure_function",
    ),
    path("azure-functions/logs/", views.get_function_logs, name="get_function_logs"),
    # Zapier/Make endpoints
    path("zapier/webhook/", views.zapier_webhook, name="zapier_webhook"),
    path("make/webhook/", views.make_webhook, name="make_webhook"),
]
