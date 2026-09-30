import logging

from django.db.models import Count
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import EventLog, NotificationChannel, WebhookEndpoint, WebhookNotification
from .serializers import (
    EventLogSerializer,
    NotificationChannelSerializer,
    WebhookDeliverySerializer,
    WebhookEndpointSerializer,
    WebhookNotificationSerializer,
)
from .services import NotificationService, WebhookService

logger = logging.getLogger(__name__)


class WebhookEndpointViewSet(viewsets.ModelViewSet):
    """Manage webhook endpoints"""
    serializer_class = WebhookEndpointSerializer
    
    def get_queryset(self):
        return WebhookEndpoint.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Test webhook endpoint"""
        webhook = self.get_object()
        
        try:
            service = WebhookService()
            test_payload = {
                'event_type': 'test.webhook',
                'message': 'This is a test webhook delivery',
                'timestamp': timezone.now().isoformat()
            }
            
            result = service.deliver_webhook(webhook, 'test.webhook', test_payload)
            
            return Response({
                'message': 'Test webhook sent',
                'success': result['success'],
                'status_code': result.get('status_code'),
                'delivery_id': str(result.get('delivery_id'))
            })
            
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error testing webhook: {e!s}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def deliveries(self, request, pk=None):
        """Get delivery history for webhook"""
        webhook = self.get_object()
        deliveries = webhook.deliveries.all()[:100]
        serializer = WebhookDeliverySerializer(deliveries, many=True)
        return Response(serializer.data)


class NotificationChannelViewSet(viewsets.ModelViewSet):
    """Manage notification channels"""
    serializer_class = NotificationChannelSerializer
    
    def get_queryset(self):
        return NotificationChannel.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Test notification channel"""
        channel = self.get_object()
        
        try:
            service = NotificationService()
            result = service.send_notification(
                channel=channel,
                title='Test Notification',
                message='This is a test notification from your Multi-Agent System',
                event_type='test.notification'
            )
            
            return Response({
                'message': 'Test notification sent',
                'success': result['success']
            })
            
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error testing notification: {e!s}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """View and manage notifications"""
    serializer_class = WebhookNotificationSerializer
    
    def get_queryset(self):
        return WebhookNotification.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        
        return Response({'message': 'Notification marked as read'})
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        updated = self.get_queryset().filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return Response({'message': f'{updated} notifications marked as read'})
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count})


class EventLogViewSet(viewsets.ReadOnlyModelViewSet):
    """View system events"""
    queryset = EventLog.objects.all()
    serializer_class = EventLogSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by event type
        event_type = self.request.query_params.get('event_type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        # Filter by session
        session_id = self.request.query_params.get('session_id')
        if session_id:
            queryset = queryset.filter(session_id=session_id)
        
        return queryset[:1000]  # Limit to recent 1000 events
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get event statistics"""
        queryset = self.get_queryset()
        
        stats = {
            'total_events': queryset.count(),
            'by_type': {},
            'recent_errors': []
        }
        
        # Events by type
        event_types = queryset.values('event_type').annotate(count=Count('id'))
        for et in event_types:
            stats['by_type'][et['event_type']] = et['count']
        
        # Recent errors
        errors = queryset.filter(event_type='error.occurred').order_by('-created_at')[:10]
        stats['recent_errors'] = EventLogSerializer(errors, many=True).data
        
        return Response(stats)
