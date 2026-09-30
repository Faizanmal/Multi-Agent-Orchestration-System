"""
Webhook and Notification Models
Real-time event notifications and external integrations
"""
import hashlib
import hmac
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import URLValidator
from django.db import models

User = get_user_model()


class WebhookEventType(models.TextChoices):
    # Agent events
    AGENT_CREATED = 'agent.created', 'Agent Created'
    AGENT_UPDATED = 'agent.updated', 'Agent Updated'
    AGENT_DELETED = 'agent.deleted', 'Agent Deleted'
    AGENT_STATUS_CHANGED = 'agent.status_changed', 'Agent Status Changed'
    
    # Session events
    SESSION_STARTED = 'session.started', 'Session Started'
    SESSION_COMPLETED = 'session.completed', 'Session Completed'
    SESSION_FAILED = 'session.failed', 'Session Failed'
    
    # Task events
    TASK_CREATED = 'task.created', 'Task Created'
    TASK_COMPLETED = 'task.completed', 'Task Completed'
    TASK_FAILED = 'task.failed', 'Task Failed'
    
    # Workflow events
    WORKFLOW_STARTED = 'workflow.started', 'Workflow Started'
    WORKFLOW_STEP_COMPLETED = 'workflow.step_completed', 'Workflow Step Completed'
    WORKFLOW_COMPLETED = 'workflow.completed', 'Workflow Completed'
    WORKFLOW_FAILED = 'workflow.failed', 'Workflow Failed'
    
    # Collaboration events
    MEMBER_JOINED = 'member.joined', 'Member Joined'
    MEMBER_LEFT = 'member.left', 'Member Left'
    PERMISSION_CHANGED = 'permission.changed', 'Permission Changed'
    
    # System events
    ALERT_TRIGGERED = 'alert.triggered', 'Alert Triggered'
    THRESHOLD_EXCEEDED = 'threshold.exceeded', 'Threshold Exceeded'
    ERROR_OCCURRED = 'error.occurred', 'Error Occurred'


class Webhook(models.Model):
    """Webhook endpoint for event notifications"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic info
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    url = models.URLField(validators=[URLValidator()])
    
    # Owner
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='webhooks')
    
    # Events to subscribe to
    subscribed_events = models.JSONField(default=list, help_text="List of event types to receive")
    
    # Filters
    filter_conditions = models.JSONField(default=dict, help_text="Conditions to filter events")
    
    # Security
    secret = models.CharField(max_length=255, help_text="Secret for HMAC signature")
    signature_header = models.CharField(max_length=100, default='X-Webhook-Signature')
    
    # Authentication
    auth_type = models.CharField(max_length=20, choices=[
        ('none', 'None'),
        ('bearer', 'Bearer Token'),
        ('basic', 'Basic Auth'),
        ('api_key', 'API Key')
    ], default='none')
    auth_token = models.CharField(max_length=500, blank=True)
    
    # Custom headers
    custom_headers = models.JSONField(default=dict, help_text="Additional headers to send")
    
    # Retry configuration
    max_retries = models.IntegerField(default=3)
    retry_delay_seconds = models.IntegerField(default=60)
    timeout_seconds = models.IntegerField(default=30)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    last_triggered_at = models.DateTimeField(null=True, blank=True)
    
    # Statistics
    total_deliveries = models.IntegerField(default=0)
    successful_deliveries = models.IntegerField(default=0)
    failed_deliveries = models.IntegerField(default=0)
    average_response_time_ms = models.IntegerField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['-last_triggered_at']),
        ]
    
    def __str__(self):
        return f"{self.name} -> {self.url}"
    
    def generate_signature(self, payload: str) -> str:
        """Generate HMAC signature for payload"""
        return hmac.new(
            self.secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def should_trigger(self, event_type: str, event_data: dict) -> bool:
        """Check if webhook should trigger for this event"""
        if not self.is_active:
            return False
        
        # Check if event type is subscribed
        if self.subscribed_events and event_type not in self.subscribed_events:
            return False
        
        # Apply filter conditions
        if self.filter_conditions:
            for key, value in self.filter_conditions.items():
                if event_data.get(key) != value:
                    return False
        
        return True
    
    def update_stats(self, success: bool, response_time_ms: int | None = None):
        """Update delivery statistics"""
        from django.utils import timezone
        
        self.total_deliveries += 1
        self.last_triggered_at = timezone.now()
        
        if success:
            self.successful_deliveries += 1
        else:
            self.failed_deliveries += 1
        
        # Update average response time
        if response_time_ms and success:
            if self.average_response_time_ms:
                alpha = 0.2
                new_avg = alpha * response_time_ms + (1 - alpha) * self.average_response_time_ms
                self.average_response_time_ms = int(new_avg)
            else:
                self.average_response_time_ms = response_time_ms
        
        self.save()


class WebhookDelivery(models.Model):
    """Record of webhook delivery attempts"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    webhook = models.ForeignKey(Webhook, on_delete=models.CASCADE, related_name='deliveries')
    
    # Event details
    event_type = models.CharField(max_length=100)
    event_id = models.UUIDField()
    event_data = models.JSONField()
    
    # Request details
    request_url = models.URLField()
    request_method = models.CharField(max_length=10, default='POST')
    request_headers = models.JSONField(default=dict)
    request_payload = models.JSONField()
    
    # Response details
    response_status_code = models.IntegerField(null=True, blank=True)
    response_headers = models.JSONField(default=dict, null=True, blank=True)
    response_body = models.TextField(blank=True)
    response_time_ms = models.IntegerField(null=True, blank=True)
    
    # Delivery status
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('retrying', 'Retrying')
    ], default='pending')
    
    # Error details
    error_message = models.TextField(blank=True)
    error_trace = models.TextField(blank=True)
    
    # Retry tracking
    attempt_number = models.IntegerField(default=1)
    max_attempts = models.IntegerField(default=3)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=['webhook', '-created_at']),
            models.Index(fields=['status', 'next_retry_at']),
            models.Index(fields=['event_type', '-created_at']),
        ]
        verbose_name_plural = 'Webhook deliveries'
    
    def __str__(self):
        return f"{self.webhook.name} - {self.event_type} ({self.status})"


class NotificationType(models.TextChoices):
    INFO = 'info', 'Information'
    SUCCESS = 'success', 'Success'
    WARNING = 'warning', 'Warning'
    ERROR = 'error', 'Error'
    ALERT = 'alert', 'Alert'


class NotificationChannel(models.TextChoices):
    IN_APP = 'in_app', 'In-App'
    EMAIL = 'email', 'Email'
    PUSH = 'push', 'Push Notification'
    SMS = 'sms', 'SMS'
    SLACK = 'slack', 'Slack'
    WEBHOOK = 'webhook', 'Webhook'


class Notification(models.Model):
    """User notifications"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Recipient
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    
    # Notification content
    type = models.CharField(max_length=20, choices=NotificationType.choices, default=NotificationType.INFO)
    title = models.CharField(max_length=200)
    message = models.TextField()
    icon = models.CharField(max_length=50, blank=True)
    
    # Delivery channels
    channels = models.JSONField(default=list, help_text="Channels to deliver notification")
    
    # Action
    action_url = models.URLField(blank=True)
    action_text = models.CharField(max_length=100, blank=True)
    
    # Related resource
    resource_type = models.CharField(max_length=50, blank=True)
    resource_id = models.UUIDField(null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict)
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Priority
    priority = models.IntegerField(default=0, help_text="Higher = more important")
    
    # Expiry
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-priority', '-created_at']  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=['user', 'is_read', '-created_at']),
            models.Index(fields=['user', '-priority', '-created_at']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        from django.utils import timezone
        
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()


class NotificationPreference(models.Model):
    """User preferences for notifications"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Channel preferences
    enable_email = models.BooleanField(default=True)
    enable_push = models.BooleanField(default=True)
    enable_sms = models.BooleanField(default=False)
    enable_slack = models.BooleanField(default=False)
    
    # Event type preferences
    notify_agent_events = models.BooleanField(default=True)
    notify_session_events = models.BooleanField(default=True)
    notify_task_events = models.BooleanField(default=True)
    notify_collaboration_events = models.BooleanField(default=True)
    notify_system_alerts = models.BooleanField(default=True)
    
    # Quiet hours
    enable_quiet_hours = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)
    quiet_hours_timezone = models.CharField(max_length=50, default='UTC')
    
    # Digest preferences
    enable_daily_digest = models.BooleanField(default=False)
    daily_digest_time = models.TimeField(null=True, blank=True)
    enable_weekly_digest = models.BooleanField(default=False)
    weekly_digest_day = models.IntegerField(default=1, help_text="1=Monday, 7=Sunday")
    
    # Contact info
    slack_webhook_url = models.URLField(blank=True)
    slack_channel = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} Notification Preferences"
    
    def is_in_quiet_hours(self) -> bool:
        """Check if currently in quiet hours"""
        if not self.enable_quiet_hours or not self.quiet_hours_start or not self.quiet_hours_end:
            return False
        
        import pytz
        from django.utils import timezone
        
        tz = pytz.timezone(self.quiet_hours_timezone)
        now = timezone.now().astimezone(tz).time()
        
        start = self.quiet_hours_start
        end = self.quiet_hours_end
        
        if start < end:
            return start <= now <= end
        else:  # Crosses midnight
            return now >= start or now <= end


class AlertRule(models.Model):
    """Rules for triggering alerts"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic info
    name = models.CharField(max_length=200)
    description = models.TextField()
    
    # Owner
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='alert_rules')
    
    # Condition
    metric = models.CharField(max_length=100, help_text="Metric to monitor")
    operator = models.CharField(max_length=20, choices=[
        ('gt', 'Greater Than'),
        ('gte', 'Greater Than or Equal'),
        ('lt', 'Less Than'),
        ('lte', 'Less Than or Equal'),
        ('eq', 'Equal'),
        ('neq', 'Not Equal')
    ])
    threshold = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Evaluation
    evaluation_window_minutes = models.IntegerField(default=5)
    check_interval_minutes = models.IntegerField(default=1)
    
    # Alert settings
    severity = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], default='medium')
    
    notification_channels = models.JSONField(default=list)
    
    # Cooldown
    cooldown_minutes = models.IntegerField(default=30, help_text="Wait time before re-alerting")
    
    # Status
    is_active = models.BooleanField(default=True)
    last_triggered_at = models.DateTimeField(null=True, blank=True)
    last_evaluated_at = models.DateTimeField(null=True, blank=True)
    
    # Statistics
    trigger_count = models.IntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['is_active', 'last_evaluated_at']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.metric} {self.operator} {self.threshold}"
    
    def evaluate(self, current_value: float) -> bool:
        """Evaluate if alert should trigger"""
        operators = {
            'gt': lambda x, y: x > y,
            'gte': lambda x, y: x >= y,
            'lt': lambda x, y: x < y,
            'lte': lambda x, y: x <= y,
            'eq': lambda x, y: x == y,
            'neq': lambda x, y: x != y
        }
        
        return operators[self.operator](current_value, float(self.threshold))
    
    def can_trigger(self) -> bool:
        """Check if alert is out of cooldown"""
        from datetime import timedelta

        from django.utils import timezone
        
        if not self.is_active:
            return False
        
        if not self.last_triggered_at:
            return True
        
        cooldown_until = self.last_triggered_at + timedelta(minutes=self.cooldown_minutes)
        return timezone.now() >= cooldown_until


class AlertInstance(models.Model):
    """Individual alert occurrences"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    rule = models.ForeignKey(AlertRule, on_delete=models.CASCADE, related_name='instances')
    
    # Alert details
    metric_value = models.DecimalField(max_digits=10, decimal_places=2)
    message = models.TextField()
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved')
    ], default='active')
    
    acknowledged_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                       null=True, blank=True, related_name='acknowledged_alerts')
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_note = models.TextField(blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=['rule', 'status', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.rule.name} - {self.created_at}"
    
    def acknowledge(self, user):
        """Acknowledge the alert"""
        from django.utils import timezone
        
        self.status = 'acknowledged'
        self.acknowledged_by = user
        self.acknowledged_at = timezone.now()
        self.save()
    
    def resolve(self, note: str = ""):
        """Resolve the alert"""
        from django.utils import timezone
        
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        self.resolution_note = note
        self.save()
