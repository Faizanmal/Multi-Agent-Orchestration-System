import logging
import uuid

from authentication.encryption_utils import encryption_util
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

logger = logging.getLogger(__name__)
User = get_user_model()


class APIIntegration(models.Model):
    TYPE_CHOICES = [  # noqa: RUF012
        ("REST", "REST API"),
        ("GraphQL", "GraphQL"),
        ("WebSocket", "WebSocket"),
        ("Webhook", "Webhook"),
    ]

    CATEGORY_CHOICES = [  # noqa: RUF012
        ("Database", "Database"),
        ("Cloud", "Cloud Services"),
        ("Payment", "Payment Processing"),
        ("Analytics", "Analytics"),
        ("Social", "Social Media"),
        ("AI/ML", "AI/ML Services"),
        ("Other", "Other"),
    ]

    AUTH_CHOICES = [  # noqa: RUF012
        ("none", "None"),
        ("api_key", "API Key"),
        ("bearer", "Bearer Token"),
        ("basic", "Basic Auth"),
        ("oauth2", "OAuth 2.0"),
    ]

    STATUS_CHOICES = [  # noqa: RUF012
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("error", "Error"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    endpoint = models.URLField()
    method = models.CharField(max_length=10, default="GET")
    headers = models.JSONField(default=dict)
    # Store encrypted authentication data
    encrypted_auth_data = models.TextField(blank=True)
    parameters = models.JSONField(default=list)
    rate_limit = models.JSONField(default=dict)
    retry_policy = models.JSONField(default=dict)
    timeout = models.IntegerField(default=30)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="inactive")
    last_tested = models.DateTimeField(null=True, blank=True)
    success_rate = models.FloatField(default=0.0)
    total_calls = models.BigIntegerField(default=0)
    avg_response_time = models.FloatField(default=0.0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="api_integrations",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]  # noqa: RUF012

    def set_auth_data(self, auth_data):
        """Encrypt and store authentication data"""
        if auth_data:
            import json

            # Convert dict to string for encryption using json.dumps for safe deserialization later
            auth_string = json.dumps(auth_data)
            self.encrypted_auth_data = encryption_util.encrypt(auth_string)
        else:
            self.encrypted_auth_data = ""

    def get_auth_data(self):
        """Retrieve and decrypt authentication data"""
        if self.encrypted_auth_data:
            try:
                decrypted_string = encryption_util.decrypt(self.encrypted_auth_data)
                if not decrypted_string:
                    return {}

                import json

                try:
                    return json.loads(decrypted_string)
                except json.JSONDecodeError:
                    # Fallback for old data encrypted with str(dict)
                    import ast

                    try:
                        return ast.literal_eval(decrypted_string)
                    except (ValueError, SyntaxError) as e:
                        logger.error(f"Failed to parse auth data with ast: {e!s}")
                        return {}

            except Exception as e:  # noqa: BLE001
                logger.error(f"Error retrieving auth data: {e!s}")
                return {}
        return {}


class APICallResult(models.Model):
    STATUS_CHOICES = [  # noqa: RUF012
        ("success", "Success"),
        ("error", "Error"),
        ("timeout", "Timeout"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    integration = models.ForeignKey(
        APIIntegration, on_delete=models.CASCADE, related_name="call_results"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    response_data = models.JSONField(null=True, blank=True)
    response_time = models.FloatField()
    error_message = models.TextField(blank=True)
    request_data = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)


class APITemplate(models.Model):
    CATEGORY_CHOICES = [  # noqa: RUF012
        ("popular", "Popular APIs"),
        ("database", "Database APIs"),
        ("cloud", "Cloud Services"),
        ("social", "Social Media"),
        ("payment", "Payment Services"),
        ("ai_ml", "AI/ML Services"),
        ("analytics", "Analytics"),
        ("other", "Other"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    provider = models.CharField(max_length=255)
    logo = models.URLField(blank=True)
    config_template = models.JSONField()
    popularity = models.IntegerField(default=0)
    tags = models.JSONField(default=list)
    is_public = models.BooleanField(default=True)
    documentation_url = models.URLField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class IntegrationUsage(models.Model):
    integration = models.ForeignKey(
        APIIntegration, on_delete=models.CASCADE, related_name="usage_stats"
    )
    date = models.DateField()
    total_calls = models.IntegerField(default=0)
    successful_calls = models.IntegerField(default=0)
    failed_calls = models.IntegerField(default=0)
    avg_response_time = models.FloatField(default=0.0)
    total_data_transferred = models.BigIntegerField(default=0)  # in bytes


class IntegrationAlert(models.Model):
    SEVERITY_CHOICES = [  # noqa: RUF012
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]

    integration = models.ForeignKey(
        APIIntegration, on_delete=models.CASCADE, related_name="alerts"
    )
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    message = models.TextField()
    rule_triggered = models.CharField(max_length=255)
    acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ScheduledAutomation(models.Model):
    """Scheduled automation jobs — inbox digest, Slack alerts, workflow runs."""

    AUTOMATION_TYPES = [  # noqa: RUF012
        ("inbox_digest", "Daily Inbox Digest"),
        ("slack_alert", "Slack Alert"),
        ("workflow_run", "Run Workflow"),
        ("integration_check", "Integration Health Check"),
    ]
    FREQUENCY_CHOICES = [  # noqa: RUF012
        ("hourly", "Every Hour"),
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("cron", "Custom Cron"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    automation_type = models.CharField(max_length=50, choices=AUTOMATION_TYPES)
    frequency = models.CharField(
        max_length=20, choices=FREQUENCY_CHOICES, default="daily"
    )
    cron_expression = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    config = models.JSONField(default=dict)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="scheduled_automations",
    )
    workflow = models.ForeignKey(
        "workflow_builder.VisualWorkflow",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="automations",
    )
    last_run_at = models.DateTimeField(null=True, blank=True)
    next_run_at = models.DateTimeField(null=True, blank=True)
    last_result = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]  # noqa: RUF012
