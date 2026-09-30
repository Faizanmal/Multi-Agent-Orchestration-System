from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    VisualWorkflowViewSet,
    WorkflowExecutionViewSet,
    WorkflowTemplateViewSet,
)

router = DefaultRouter()
router.register(r'templates', WorkflowTemplateViewSet, basename='template')
router.register(r'workflows', VisualWorkflowViewSet, basename='workflow')
router.register(r'executions', WorkflowExecutionViewSet, basename='execution')

urlpatterns = [
    path('api/', include(router.urls)),
]
