import uuid

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class IntegrationType(models.TextChoices):
    """Types of integrations"""

    AZURE_COSMOSDB = "azure_cosmosdb", "Azure CosmosDB"
    AZURE_FUNCTIONS = "azure_functions", "Azure Functions"
    ZAPIER = "zapier", "Zapier"
    MAKE = "make", "Make"
    WEBHOOK = "webhook", "Webhook"
    API = "api", "API"


class Integration(models.Model):
    """Integration configurations"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="integrations"
    )
    name = models.CharField(max_length=200)
    integration_type = models.CharField(max_length=50, choices=IntegrationType.choices)

    # Configuration
    config = models.JSONField(default=dict)
    credentials = models.JSONField(default=dict, help_text="Encrypted credentials")

    # Status
    is_active = models.BooleanField(default=True)
    last_sync = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "integrations"
        ordering = ["-created_at"]  # noqa: RUF012

    def __str__(self):
        return f"{self.name} ({self.integration_type})"


class IntegrationExecution(models.Model):
    """Track integration execution history"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    integration = models.ForeignKey(
        Integration, on_delete=models.CASCADE, related_name="executions"
    )

    # Execution details
    action = models.CharField(max_length=100)
    input_data = models.JSONField(default=dict)
    output_data = models.JSONField(default=dict)

    # Status
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    duration_ms = models.IntegerField(default=0)

    # Metadata
    executed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "integration_executions"
        ordering = ["-executed_at"]  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=["integration", "executed_at"]),
            models.Index(fields=["success", "executed_at"]),
        ]

    def __str__(self):
        return f"{self.integration.name} - {self.action}"


class AutomationWorkflow(models.Model):
    """Automation workflows for Zapier/Make integrations"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="automation_workflows"
    )
    name = models.CharField(max_length=200)
    platform = models.CharField(
        max_length=50, choices=[("zapier", "Zapier"), ("make", "Make")]
    )

    # Workflow configuration
    webhook_url = models.URLField()
    trigger_events = models.JSONField(
        default=list, help_text="Events that trigger this workflow"
    )
    filters = models.JSONField(default=dict, help_text="Event filters")

    # Status
    is_active = models.BooleanField(default=True)
    execution_count = models.IntegerField(default=0)
    last_executed = models.DateTimeField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "automation_workflows"
        ordering = ["-created_at"]  # noqa: RUF012

    def __str__(self):
        return f"{self.name} ({self.platform})"
