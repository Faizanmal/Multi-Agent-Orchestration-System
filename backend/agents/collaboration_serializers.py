# Collaboration Serializers

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .collaboration_models import (
    ActivityLog,
    ChangeLog,
    CollaborationSession,
    Comment,
    Notification,
    TeamMember,
    WorkflowLock,
)

# Get the custom user model
User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Simple user serializer for collaboration features."""

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]  # noqa: RUF012
        read_only_fields = ["id"]  # noqa: RUF012


class CollaborationSessionSerializer(serializers.ModelSerializer):
    """Serializer for collaboration sessions."""

    owner = UserSerializer(read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = CollaborationSession
        fields = [  # noqa: RUF012
            "id",
            "name",
            "description",
            "is_public",
            "is_active",
            "max_members",
            "session_data",
            "settings",
            "owner",
            "workflow_id",
            "member_count",
            "created_at",
            "updated_at",
            "last_activity",
        ]
        read_only_fields = [
            "id",
            "owner",
            "member_count",
            "created_at",
            "updated_at",
            "last_activity",
        ]  # noqa: RUF012

    def get_member_count(self, obj):
        """Get the number of members in the session."""
        return obj.members.count()


class TeamMemberSerializer(serializers.ModelSerializer):
    """Serializer for team members."""

    user = UserSerializer(read_only=True)
    invited_by = UserSerializer(read_only=True)

    class Meta:
        model = TeamMember
        fields = [  # noqa: RUF012
            "id",
            "session",
            "user",
            "role",
            "permissions",
            "status",
            "last_active",
            "cursor_position",
            "invited_by",
            "joined_at",
        ]
        read_only_fields = ["id", "user", "invited_by", "joined_at"]  # noqa: RUF012


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for comments."""

    author = UserSerializer(read_only=True)
    resolved_by = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = [  # noqa: RUF012
            "id",
            "session",
            "author",
            "content",
            "node_id",
            "resolved",
            "resolved_by",
            "resolved_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "author",
            "resolved_by",
            "resolved_at",
            "created_at",
            "updated_at",
        ]  # noqa: RUF012


class ActivityLogSerializer(serializers.ModelSerializer):
    """Serializer for activity logs."""

    user = UserSerializer(read_only=True)

    class Meta:
        model = ActivityLog
        fields = [  # noqa: RUF012
            "id",
            "session",
            "user",
            "action",
            "details",
            "timestamp",
        ]
        read_only_fields = ["id", "timestamp"]  # noqa: RUF012


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notifications."""

    recipient = UserSerializer(read_only=True)
    sender = UserSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = [  # noqa: RUF012
            "id",
            "recipient",
            "sender",
            "session",
            "notification_type",
            "title",
            "message",
            "data",
            "read",
            "read_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "recipient",
            "sender",
            "read_at",
            "created_at",
        ]  # noqa: RUF012


class WorkflowLockSerializer(serializers.ModelSerializer):
    """Serializer for workflow locks."""

    locked_by = UserSerializer(read_only=True)

    class Meta:
        model = WorkflowLock
        fields = [  # noqa: RUF012
            "id",
            "session",
            "workflow_id",
            "node_id",
            "locked_by",
            "lock_type",
            "created_at",
            "expires_at",
            "last_heartbeat",
        ]
        read_only_fields = [
            "id",
            "locked_by",
            "created_at",
            "last_heartbeat",
        ]  # noqa: RUF012


class ChangeLogSerializer(serializers.ModelSerializer):
    """Serializer for change logs."""

    user = UserSerializer(read_only=True)

    class Meta:
        model = ChangeLog
        fields = [  # noqa: RUF012
            "id",
            "session",
            "user",
            "workflow_id",
            "change_type",
            "target_id",
            "before_data",
            "after_data",
            "metadata",
            "timestamp",
        ]
        read_only_fields = ["id", "timestamp"]  # noqa: RUF012
