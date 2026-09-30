from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import collaboration_views, health_views, views, workflow_views

router = DefaultRouter()
# Existing endpoints
router.register(r'agents', views.AgentViewSet, basename='agent')
router.register(r'sessions', views.SessionViewSet, basename='session')
router.register(r'tasks', views.TaskViewSet, basename='task')
router.register(r'messages', views.MessageViewSet, basename='message')
router.register(r'performance', views.PerformanceViewSet, basename='performance')
router.register(r'memory', views.AgentMemoryViewSet, basename='memory')
router.register(r'groq', views.GroqIntegrationView, basename='groq')

# Enhanced feature endpoints
router.register(r'smart-agents', views.SmartAgentViewSet, basename='smart-agents')
router.register(r'workflows', workflow_views.WorkflowViewSet, basename='workflows')
router.register(r'multimodal', views.MultiModalProcessorViewSet, basename='multimodal')
router.register(r'analytics', views.AnalyticsDashboardViewSet, basename='analytics')
router.register(r'automation', views.AutomationViewSet, basename='automation')

# Collaboration endpoints
router.register(r'collaboration', collaboration_views.CollaborationViewSet, basename='collaboration')
router.register(r'notifications', collaboration_views.NotificationViewSet, basename='notifications')

app_name = 'agents'

urlpatterns = [
    path('api/', include(router.urls)),
    # Health check endpoints
    path('health/', health_views.health_check, name='health_check'),
    path('health/status/', health_views.system_status, name='system_status'),
    path('health/metrics/', health_views.performance_metrics, name='performance_metrics'),
    path('health/ready/', health_views.readiness_check, name='readiness_check'),
    path('health/live/', health_views.liveness_check, name='liveness_check'),
]