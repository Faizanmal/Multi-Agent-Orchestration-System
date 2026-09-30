from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    EventLogViewSet,
    NotificationChannelViewSet,
    NotificationViewSet,
    WebhookEndpointViewSet,
)

router = DefaultRouter()
router.register(r'endpoints', WebhookEndpointViewSet, basename='webhook-endpoint')
router.register(r'channels', NotificationChannelViewSet, basename='notification-channel')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'events', EventLogViewSet, basename='event-log')

urlpatterns = [
    path('', include(router.urls)),
]
