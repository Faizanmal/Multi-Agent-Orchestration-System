from datetime import timezone

"""
OAuth2 and API Key Models
"""

import uuid
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class OAuthClient(models.Model):
    """OAuth2 client applications"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="oauth_clients"
    )

    # Client credentials
    client_id = models.CharField(max_length=255, unique=True, db_index=True)
    client_secret = models.CharField(max_length=255)

    # Client info
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    redirect_uris = models.JSONField(default=list)
    allowed_scopes = models.JSONField(default=list)

    # Status
    is_active = models.BooleanField(default=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "oauth_clients"

    def __str__(self):
        return self.name


class OAuthAuthorizationCode(models.Model):
    """OAuth2 authorization codes"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(OAuthClient, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Code details
    code = models.CharField(max_length=255, unique=True, db_index=True)
    redirect_uri = models.URLField()
    scope = models.JSONField(default=list)

    # Status
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "oauth_authorization_codes"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        super().save(*args, **kwargs)


class APIKey(models.Model):
    """API Keys for authentication"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="api_keys")

    # Key details
    name = models.CharField(max_length=200)
    key_hash = models.CharField(max_length=255, unique=True, db_index=True)
    key_prefix = models.CharField(max_length=10)  # First few chars for identification

    # Permissions
    scopes = models.JSONField(default=list)
    rate_limit = models.IntegerField(default=1000, help_text="Requests per hour")

    # Status
    is_active = models.BooleanField(default=True)
    last_used = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "api_keys"
        ordering = ["-created_at"]  # noqa: RUF012

    def __str__(self):
        return f"{self.name} - {self.key_prefix}..."
