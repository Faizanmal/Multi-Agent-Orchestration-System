from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    NotificationCampaign,
    NotificationPreference,
    NotificationRule,
    NotificationSubscription,
    NotificationTemplate,
)
from .serializers import (
    NotificationCampaignSerializer,
    NotificationPreferenceSerializer,
    NotificationRuleSerializer,
    NotificationSubscriptionSerializer,
    NotificationTemplateSerializer,
)


class NotificationCampaignListCreateView(generics.ListCreateAPIView):
    """List and create notification campaigns"""
    serializer_class = NotificationCampaignSerializer
    permission_classes = [IsAuthenticated]  # noqa: RUF012
    
    def get_queryset(self):
        return NotificationCampaign.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NotificationCampaignDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, delete notification campaign"""
    serializer_class = NotificationCampaignSerializer
    permission_classes = [IsAuthenticated]  # noqa: RUF012
    
    def get_queryset(self):
        return NotificationCampaign.objects.filter(user=self.request.user)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_campaign_view(request, pk):
    """Mark a campaign as sent and return delivery summary."""
    from django.utils import timezone
    campaign = get_object_or_404(NotificationCampaign, pk=pk, user=request.user)
    if hasattr(campaign, 'status'):
        campaign.status = 'sent'
    if hasattr(campaign, 'sent_at'):
        campaign.sent_at = timezone.now()
    campaign.save()
    recipients = 0
    if hasattr(campaign, 'recipients') and isinstance(campaign.recipients, list):
        recipients = len(campaign.recipients)
    return Response({
        'sent': recipients,
        'failed': 0,
        'campaign_id': str(campaign.id),
        'message': 'Campaign marked as sent. Connect an email provider to deliver messages.',
    })


class NotificationTemplateListCreateView(generics.ListCreateAPIView):
    """List and create notification templates"""
    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsAuthenticated]  # noqa: RUF012
    
    def get_queryset(self):
        return NotificationTemplate.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NotificationRuleListCreateView(generics.ListCreateAPIView):
    """List and create notification rules"""
    serializer_class = NotificationRuleSerializer
    permission_classes = [IsAuthenticated]  # noqa: RUF012
    
    def get_queryset(self):
        return NotificationRule.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_stats_view(request):
    """Get notification statistics from real campaign aggregates."""
    from django.db.models import Sum

    campaigns = NotificationCampaign.objects.filter(user=request.user)
    aggregates = campaigns.aggregate(
        total_sent=Sum('sent_count'),
        total_delivered=Sum('delivered_count'),
        total_opened=Sum('opened_count'),
        total_clicked=Sum('clicked_count'),
    )
    total_sent = aggregates['total_sent'] or 0
    total_delivered = aggregates['total_delivered'] or 0
    total_opened = aggregates['total_opened'] or 0
    total_clicked = aggregates['total_clicked'] or 0

    open_rate = (total_opened / total_delivered * 100) if total_delivered else 0
    click_rate = (total_clicked / total_delivered * 100) if total_delivered else 0

    return Response({
        'stats': {
            'total_sent': total_sent,
            'open_rate': round(open_rate, 2),
            'click_rate': round(click_rate, 2),
        }
    })


class NotificationPreferenceView(generics.RetrieveUpdateAPIView):
    """Retrieve and update notification preferences"""
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsAuthenticated]  # noqa: RUF012
    
    def get_object(self):
        prefs, created = NotificationPreference.objects.get_or_create(user=self.request.user)  # noqa: RUF059
        return prefs


class NotificationSubscriptionListCreateView(generics.ListCreateAPIView):
    """List and create notification subscriptions"""
    serializer_class = NotificationSubscriptionSerializer
    permission_classes = [IsAuthenticated]  # noqa: RUF012
    
    def get_queryset(self):
        return NotificationSubscription.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
