# Collaboration Models

import uuid

from django.conf import settings as django_settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

# Get the custom user model
User = get_user_model()


class CollaborationSession(models.Model):
    """Model for collaboration sessions."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # Session settings
    is_public = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    max_members = models.PositiveIntegerField(default=50)

    # Session data
    session_data = models.JSONField(
        default=dict, help_text="Session-specific data and state"
    )
    settings = models.JSONField(default=dict, help_text="Collaboration settings")

    # Relationships
    owner = models.ForeignKey(
        django_settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_sessions",
    )
    workflow_id = models.CharField(max_length=100, null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-last_activity"]  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=["owner", "is_active"]),
            models.Index(fields=["is_public", "is_active"]),
        ]

    def __str__(self):
        return f"Collaboration: {self.name}"


class TeamMember(models.Model):
    """Team members in collaboration sessions."""

    ROLE_CHOICES = [  # noqa: RUF012
        ("owner", "Owner"),
        ("editor", "Editor"),
        ("viewer", "Viewer"),
        ("commenter", "Commenter"),
    ]

    STATUS_CHOICES = [  # noqa: RUF012
        ("online", "Online"),
        ("away", "Away"),
        ("offline", "Offline"),
        ("busy", "Busy"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        CollaborationSession, on_delete=models.CASCADE, related_name="members"
    )
    user = models.ForeignKey(django_settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    # Member settings
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="viewer")
    permissions = models.JSONField(
        default=list, help_text="List of specific permissions"
    )

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="offline")
    last_active = models.DateTimeField(null=True, blank=True)
    cursor_position = models.JSONField(
        default=dict, help_text="Current cursor/selection position"
    )

    # Invitation details
    invited_by = models.ForeignKey(
        django_settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invited_members",
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["session", "user"]  # noqa: RUF012
        ordering = ["role", "user__username"]  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=["session", "status"]),
            models.Index(fields=["user", "last_active"]),
        ]

    def __str__(self):
        return f"{self.user.username} ({self.role}) in {self.session.name}"

    def update_activity(self):
        """Update last activity timestamp."""
        self.last_active = timezone.now()
        self.save(update_fields=["last_active"])


class Comment(models.Model):
    """Comments on workflows or specific nodes."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        CollaborationSession, on_delete=models.CASCADE, related_name="comments"
    )
    author = models.ForeignKey(
        django_settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )

    # Comment content
    content = models.TextField()
    node_id = models.CharField(
        max_length=100, null=True, blank=True, help_text="ID of specific workflow node"
    )

    # Comment state
    resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(
        django_settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_comments",
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=["session", "resolved"]),
            models.Index(fields=["node_id", "created_at"]),
            models.Index(fields=["author", "created_at"]),
        ]

    def __str__(self):
        return f"Comment by {self.author.username}: {self.content[:50]}..."

    def resolve(self, resolved_by_user):
        """Mark comment as resolved."""
        self.resolved = True
        self.resolved_by = resolved_by_user
        self.resolved_at = timezone.now()
        self.save()


class ActivityLog(models.Model):
    """Activity log for collaboration sessions."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        CollaborationSession, on_delete=models.CASCADE, related_name="activities"
    )
    user = models.ForeignKey(
        django_settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    # Activity details
    action = models.CharField(
        max_length=50
    )  # e.g., 'node_added', 'workflow_saved', 'member_joined'
    details = models.JSONField(default=dict, help_text="Additional activity details")

    # Metadata
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=["session", "timestamp"]),
            models.Index(fields=["user", "timestamp"]),
            models.Index(fields=["action", "timestamp"]),
        ]

    def __str__(self):
        user_name = self.user.username if self.user else "System"
        return f"{user_name}: {self.action} in {self.session.name}"


class Notification(models.Model):
    """Notifications for collaboration events."""

    NOTIFICATION_TYPES = [  # noqa: RUF012
        ("invitation", "Invitation"),
        ("comment", "Comment"),
        ("mention", "Mention"),
        ("workflow_update", "Workflow Update"),
        ("system", "System"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        django_settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="agent_notifications",
    )
    sender = models.ForeignKey(
        django_settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_notifications",
    )
    session = models.ForeignKey(
        CollaborationSession, on_delete=models.CASCADE, null=True, blank=True
    )

    # Notification content
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    data = models.JSONField(default=dict, help_text="Additional notification data")

    # Status
    read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=["recipient", "read"]),
            models.Index(fields=["notification_type", "created_at"]),
        ]

    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.title}"

    def mark_as_read(self):
        """Mark notification as read."""
        self.read = True
        self.read_at = timezone.now()
        self.save()


class WorkflowLock(models.Model):
    """Locks for workflow editing to prevent conflicts."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(CollaborationSession, on_delete=models.CASCADE)
    workflow_id = models.CharField(max_length=100)
    node_id = models.CharField(
        max_length=100, null=True, blank=True
    )  # Optional: lock specific nodes

    # Lock details
    locked_by = models.ForeignKey(
        django_settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    lock_type = models.CharField(max_length=20, default="edit")  # edit, view, delete

    # Lock timing
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    last_heartbeat = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["session", "workflow_id", "node_id"]  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=["session", "locked_by"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"Lock on {self.workflow_id} by {self.locked_by.username}"

    def is_expired(self):
        """Check if the lock has expired."""
        return timezone.now() > self.expires_at

    def refresh_lock(self):
        """Refresh the lock expiration."""
        self.expires_at = timezone.now() + timezone.timedelta(minutes=30)
        self.save()


class ChangeLog(models.Model):
    """Log of changes made to workflows for version control."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(CollaborationSession, on_delete=models.CASCADE)
    user = models.ForeignKey(django_settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    # Change details
    workflow_id = models.CharField(max_length=100)
    change_type = models.CharField(max_length=50)  # add, modify, delete, move
    target_id = models.CharField(max_length=100)  # node/connection ID

    # Change data
    before_data = models.JSONField(default=dict, help_text="State before change")
    after_data = models.JSONField(default=dict, help_text="State after change")
    metadata = models.JSONField(default=dict, help_text="Additional change metadata")

    # Metadata
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=["session", "timestamp"]),
            models.Index(fields=["workflow_id", "timestamp"]),
            models.Index(fields=["user", "timestamp"]),
        ]

    def __str__(self):
        return f"{self.change_type} on {self.target_id} by {self.user.username}"
