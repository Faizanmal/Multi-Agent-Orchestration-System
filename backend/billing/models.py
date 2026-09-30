import uuid

from django.db import models


class MonthlyUsage(models.Model):
    """Durable monthly message usage for a workspace."""

    workspace = models.ForeignKey(
        "authentication.Workspace",
        on_delete=models.CASCADE,
        related_name="monthly_usage",
    )
    period = models.DateField(help_text="First day of the metered month")
    message_count = models.PositiveBigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=["workspace", "period"],
                name="unique_workspace_usage_period",
            ),
        ]
        ordering = ["-period"]  # noqa: RUF012

    def __str__(self):
        return f"{self.workspace.name} - {self.period:%Y-%m}: {self.message_count}"


class Subscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.OneToOneField(
        "authentication.Workspace",
        on_delete=models.CASCADE,
        related_name="subscription",
    )
    stripe_subscription_id = models.CharField(
        max_length=255, blank=True, null=True, unique=True
    )
    status = models.CharField(
        max_length=50, default="inactive"
    )  # e.g. active, past_due, canceled
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Subscription for {self.workspace.name} - {self.status}"


class Invoice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(
        "authentication.Workspace", on_delete=models.CASCADE, related_name="invoices"
    )
    stripe_invoice_id = models.CharField(max_length=255, unique=True)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50)  # paid, open, uncollectible
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invoice {self.stripe_invoice_id} - {self.status}"
