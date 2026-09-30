import uuid

from agents.models import Session, Task
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class EventType(models.TextChoices):
    """Types of events that can trigger webhooks"""

    SESSION_CREATED = "session.created", "Session Created"
    SESSION_COMPLETED = "session.completed", "Session Completed"
    SESSION_FAILED = "session.failed", "Session Failed"
    TASK_CREATED = "task.created", "Task Created"
    TASK_COMPLETED = "task.completed", "Task Completed"
    TASK_FAILED = "task.failed", "Task Failed"
    AGENT_RESPONSE = "agent.response", "Agent Response"
    WORKFLOW_STARTED = "workflow.started", "Workflow Started"
    WORKFLOW_COMPLETED = "workflow.completed", "Workflow Completed"
    ERROR_OCCURRED = "error.occurred", "Error Occurred"


class WebhookEndpoint(models.Model):
    """Webhook endpoints registered by users"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="webhooks")

    name = models.CharField(max_length=200)
    url = models.URLField()
    description = models.TextField(blank=True)

    # Event subscriptions
    subscribed_events = models.JSONField(default=list)  # List of EventType values

    # Security
    secret_key = models.CharField(max_length=500)  # For signature verification

    # Configuration
    is_active = models.BooleanField(default=True)
    retry_on_failure = models.BooleanField(default=True)
    max_retries = models.IntegerField(default=3)
    timeout_seconds = models.IntegerField(default=30)

    # Headers and authentication
    custom_headers = models.JSONField(default=dict)

    # Stats
    total_deliveries = models.IntegerField(default=0)
    successful_deliveries = models.IntegerField(default=0)
    failed_deliveries = models.IntegerField(default=0)
    last_triggered = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "webhook_endpoint"
        ordering = ["-created_at"]  # noqa: RUF012

    def __str__(self):
        return f"{self.name} - {self.url}"


class WebhookDelivery(models.Model):
    """Record of webhook delivery attempts"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    webhook = models.ForeignKey(
        WebhookEndpoint, on_delete=models.CASCADE, related_name="deliveries"
    )

    event_type = models.CharField(max_length=50, choices=EventType.choices)
    payload = models.JSONField()

    # Delivery status
    status_code = models.IntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True)
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)

    # Retry tracking
    attempt_number = models.IntegerField(default=1)
    retry_at = models.DateTimeField(null=True, blank=True)

    # Timing
    duration_ms = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "webhook_delivery"
        ordering = ["-created_at"]  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=["webhook", "-created_at"]),
            models.Index(fields=["event_type", "success"]),
        ]

    def __str__(self):
        return (
            f"{self.event_type} to {self.webhook.name} - {'✓' if self.success else '✗'}"
        )


class NotificationChannel(models.Model):
    """Notification channels for real-time alerts"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notification_channels"
    )

    channel_type = models.CharField(max_length=50)  # email, slack, discord, telegram
    channel_name = models.CharField(max_length=200)
    channel_config = (
        models.JSONField()
    )  # Channel-specific config (webhook URL, email, etc.)

    # Event filtering
    subscribed_events = models.JSONField(default=list)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "notification_channel"
        ordering = ["-created_at"]  # noqa: RUF012

    def __str__(self):
        return f"{self.channel_type} - {self.channel_name}"


class WebhookNotification(models.Model):
    """Individual notifications sent to users via webhooks"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="webhook_notifications"
    )
    channel = models.ForeignKey(
        NotificationChannel, on_delete=models.SET_NULL, null=True, blank=True
    )

    event_type = models.CharField(max_length=50, choices=EventType.choices)
    title = models.CharField(max_length=200)
    message = models.TextField()
    data = models.JSONField(default=dict)  # Additional contextual data

    # Status
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    # Priority
    priority = models.CharField(
        max_length=20,
        choices=[
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("urgent", "Urgent"),
        ],
        default="medium",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "webhook_notification"
        ordering = ["-created_at"]  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["is_read", "user"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.user.username}"


class EventLog(models.Model):
    """Log of all system events"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    event_type = models.CharField(max_length=50, choices=EventType.choices)
    event_data = models.JSONField()

    # Related objects
    session = models.ForeignKey(
        Session,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="event_logs",
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="event_logs",
    )

    # Context
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    source = models.CharField(max_length=100)  # Where the event originated

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "event_log"
        ordering = ["-created_at"]  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=["event_type", "-created_at"]),
            models.Index(fields=["session", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.event_type} at {self.created_at}"
