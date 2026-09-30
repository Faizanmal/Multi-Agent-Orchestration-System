import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class NotificationCampaign(models.Model):
    """Email and notification campaigns"""
    CAMPAIGN_TYPES = [  # noqa: RUF012
        ('email', 'Email Campaign'),
        ('push', 'Push Notification'),
        ('sms', 'SMS Campaign'),
        ('in_app', 'In-App Notification'),
        ('webhook', 'Webhook'),
    ]
    
    STATUS_CHOICES = [  # noqa: RUF012
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('paused', 'Paused'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_notifications')
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    campaign_type = models.CharField(max_length=20, choices=CAMPAIGN_TYPES)
    
    # Content
    subject = models.CharField(max_length=255, blank=True)
    content = models.TextField()
    template = models.ForeignKey('NotificationTemplate', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Recipients
    recipient_list = models.JSONField(default=list)
    recipient_filters = models.JSONField(default=dict)
    
    # Scheduling
    scheduled_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Analytics
    total_recipients = models.PositiveIntegerField(default=0)
    sent_count = models.PositiveIntegerField(default=0)
    delivered_count = models.PositiveIntegerField(default=0)
    opened_count = models.PositiveIntegerField(default=0)
    clicked_count = models.PositiveIntegerField(default=0)
    bounced_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'notifications_campaigns'
        ordering = ['-created_at']  # noqa: RUF012
    
    def __str__(self):
        return f"{self.name} ({self.campaign_type})"
    
    def open_rate(self):
        if self.delivered_count == 0:
            return 0
        return (self.opened_count / self.delivered_count) * 100
    
    def click_rate(self):
        if self.delivered_count == 0:
            return 0
        return (self.clicked_count / self.delivered_count) * 100


class NotificationTemplate(models.Model):
    """Email and notification templates"""
    TEMPLATE_TYPES = [  # noqa: RUF012
        ('email', 'Email Template'),
        ('push', 'Push Notification Template'),
        ('sms', 'SMS Template'),
        ('in_app', 'In-App Template'),
    ]
    
    CATEGORIES = [  # noqa: RUF012
        ('welcome', 'Welcome'),
        ('alert', 'Alert'),
        ('reminder', 'Reminder'),
        ('update', 'Update'),
        ('marketing', 'Marketing'),
        ('system', 'System'),
        ('custom', 'Custom'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='templates')
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES)
    category = models.CharField(max_length=20, choices=CATEGORIES)
    
    # Content
    subject = models.CharField(max_length=255, blank=True)
    content = models.TextField()
    html_content = models.TextField(blank=True)
    variables = models.JSONField(default=list)  # Available template variables
    
    # Design
    design_config = models.JSONField(default=dict)
    
    # Usage tracking
    usage_count = models.PositiveIntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
    is_system_template = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notifications_templates'
    
    def __str__(self):
        return f"{self.name} ({self.template_type})"


class NotificationRule(models.Model):
    """Automated notification rules"""
    TRIGGER_TYPES = [  # noqa: RUF012
        ('user_action', 'User Action'),
        ('system_event', 'System Event'),
        ('schedule', 'Scheduled'),
        ('condition', 'Conditional'),
        ('api_event', 'API Event'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_rules')
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    trigger_type = models.CharField(max_length=20, choices=TRIGGER_TYPES)
    
    # Rule configuration
    conditions = models.JSONField(default=dict)
    actions = models.JSONField(default=list)
    
    # Template
    template = models.ForeignKey(NotificationTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Settings
    is_active = models.BooleanField(default=True)
    priority = models.PositiveIntegerField(default=1)  # 1=high, 5=low
    
    # Usage tracking
    trigger_count = models.PositiveIntegerField(default=0)
    last_triggered = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notifications_rules'
    
    def __str__(self):
        return f"{self.name} ({self.trigger_type})"


class Notification(models.Model):
    """Individual notifications"""
    NOTIFICATION_TYPES = [  # noqa: RUF012
        ('info', 'Info'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('system', 'System'),
    ]
    
    STATUS_CHOICES = [  # noqa: RUF012
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    campaign = models.ForeignKey(NotificationCampaign, on_delete=models.SET_NULL, null=True, blank=True)
    rule = models.ForeignKey(NotificationRule, on_delete=models.SET_NULL, null=True, blank=True)
    
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='info')
    
    # Metadata
    data = models.JSONField(default=dict, blank=True)
    action_url = models.URLField(blank=True)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    read_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']  # noqa: RUF012
    
    def __str__(self):
        return f"{self.title} for {self.user.username}"
    
    def mark_as_read(self):
        if not self.read_at:
            self.read_at = timezone.now()
            self.status = 'read'
            self.save()


class NotificationSubscription(models.Model):
    """User notification subscriptions"""
    SUBSCRIPTION_TYPES = [  # noqa: RUF012
        ('email', 'Email'),
        ('push', 'Push Notification'),
        ('sms', 'SMS'),
        ('in_app', 'In-App'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions')
    
    subscription_type = models.CharField(max_length=20, choices=SUBSCRIPTION_TYPES)
    endpoint = models.URLField(blank=True)  # For push notifications
    token = models.TextField(blank=True)  # For push/SMS tokens
    
    # Preferences
    categories = models.JSONField(default=list)  # Which categories to receive
    frequency = models.CharField(max_length=20, default='immediate')
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_subscriptions'
        unique_together = ['user', 'subscription_type']  # noqa: RUF012
    
    def __str__(self):
        return f"{self.user.username} - {self.subscription_type}"


class NotificationPreference(models.Model):
    """User notification preferences"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Email preferences
    email_enabled = models.BooleanField(default=True)
    email_marketing = models.BooleanField(default=False)
    email_system = models.BooleanField(default=True)
    email_frequency = models.CharField(max_length=20, default='immediate')
    
    # Push preferences
    push_enabled = models.BooleanField(default=True)
    push_marketing = models.BooleanField(default=False)
    push_system = models.BooleanField(default=True)
    
    # SMS preferences
    sms_enabled = models.BooleanField(default=False)
    sms_marketing = models.BooleanField(default=False)
    sms_system = models.BooleanField(default=False)
    
    # In-app preferences
    in_app_enabled = models.BooleanField(default=True)
    in_app_sound = models.BooleanField(default=True)
    
    # Quiet hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(blank=True, null=True)
    quiet_hours_end = models.TimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_preferences'
    
    def __str__(self):
        return f"Preferences for {self.user.username}"
