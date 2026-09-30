from django.db.models import Avg, Count, Q
from django.utils.html import escape
from rest_framework import serializers

from .models import (
    Agent,
    AgentMemory,
    Message,
    PerformanceMetric,
    Session,
    Task,
    TaskExecution,
    TaskStatus,
)


class AgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agent
        fields = [  # noqa: RUF012
            "id",
            "name",
            "type",
            "status",
            "capabilities",
            "configuration",
            "created_at",
            "updated_at",
            "is_active",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]  # noqa: RUF012

    def validate_name(self, value):
        if value:
            return escape(value)
        return value


class SessionSerializer(serializers.ModelSerializer):
    agents = AgentSerializer(many=True, read_only=True)
    agent_count = serializers.SerializerMethodField()
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = Session
        fields = [  # noqa: RUF012
            "id",
            "name",
            "user",
            "agents",
            "context",
            "created_at",
            "updated_at",
            "is_active",
            "agent_count",
            "message_count",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at"]  # noqa: RUF012

    def get_agent_count(self, obj):
        return obj.agents.count()

    def get_message_count(self, obj):
        return obj.messages.count()


class TaskSerializer(serializers.ModelSerializer):
    assigned_agent = AgentSerializer(read_only=True)
    assigned_agent_id = serializers.UUIDField(write_only=True)
    subtasks = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [  # noqa: RUF012
            "id",
            "title",
            "description",
            "input_data",
            "output_data",
            "status",
            "priority",
            "assigned_agent",
            "assigned_agent_id",
            "parent_task",
            "subtasks",
            "created_at",
            "started_at",
            "completed_at",
            "error_message",
            "duration",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "started_at",
            "completed_at",
        ]  # noqa: RUF012

    def get_subtasks(self, obj):
        subtasks = obj.subtasks.all()
        return TaskSerializer(subtasks, many=True).data

    def get_duration(self, obj):
        if obj.started_at and obj.completed_at:
            return (obj.completed_at - obj.started_at).total_seconds()
        return None


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    sender_agent_name = serializers.SerializerMethodField()
    recipient_agent_name = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [  # noqa: RUF012
            "id",
            "content",
            "message_type",
            "metadata",
            "created_at",
            "processed_at",
            "sender_name",
            "sender_agent_name",
            "recipient_agent_name",
            "file_attachment",
            "file_url",
        ]
        read_only_fields = ["id", "created_at", "processed_at"]  # noqa: RUF012

    def get_sender_name(self, obj):
        return obj.sender.username if obj.sender else None

    def get_sender_agent_name(self, obj):
        return obj.sender_agent.name if obj.sender_agent else None

    def get_recipient_agent_name(self, obj):
        return obj.recipient_agent.name if obj.recipient_agent else None

    def get_file_url(self, obj):
        if obj.file_attachment:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.file_attachment.url)
        return None


class AgentMemorySerializer(serializers.ModelSerializer):
    agent_name = serializers.SerializerMethodField()

    class Meta:
        model = AgentMemory
        fields = [  # noqa: RUF012
            "id",
            "key",
            "value",
            "created_at",
            "accessed_at",
            "importance_score",
            "agent_name",
        ]
        read_only_fields = ["id", "created_at", "accessed_at"]  # noqa: RUF012

    def get_agent_name(self, obj):
        return obj.agent.name


class PerformanceMetricSerializer(serializers.ModelSerializer):
    agent_name = serializers.SerializerMethodField()

    class Meta:
        model = PerformanceMetric
        fields = [  # noqa: RUF012
            "id",
            "metric_name",
            "metric_value",
            "timestamp",
            "metadata",
            "agent_name",
        ]
        read_only_fields = ["id", "timestamp"]  # noqa: RUF012

    def get_agent_name(self, obj):
        return obj.agent.name


class AgentCreateSerializer(serializers.ModelSerializer):
    """Specialized serializer for agent creation with validation"""

    class Meta:
        model = Agent
        fields = ["name", "type", "capabilities", "configuration"]  # noqa: RUF012

    def validate_capabilities(self, value):
        """Validate that capabilities are appropriate for agent type"""
        agent_type = self.initial_data.get("type")

        required_capabilities = {
            "orchestrator": ["task_coordination", "agent_management"],
            "vision": ["image_processing", "object_detection"],
            "reasoning": ["logical_analysis", "decision_making"],
            "action": ["api_calls", "task_execution"],
            "memory": ["context_storage", "retrieval"],
        }

        if agent_type in required_capabilities:
            missing_caps = set(required_capabilities[agent_type]) - set(value)
            if missing_caps:
                raise serializers.ValidationError(
                    f"Missing required capabilities for {agent_type}: {list(missing_caps)}"
                )

        return value


class SessionCreateSerializer(serializers.ModelSerializer):
    """Specialized serializer for session creation"""

    class Meta:
        model = Session
        fields = ["name", "context"]  # noqa: RUF012

    def validate_name(self, value):
        """Ensure session name is unique for the user"""
        user = self.context["request"].user
        if Session.objects.filter(user=user, name=value, is_active=True).exists():
            raise serializers.ValidationError("Session with this name already exists")
        return value


class MultiModalMessageSerializer(serializers.Serializer):
    """Serializer for multimodal message processing"""

    content = serializers.CharField(required=False, allow_blank=True)
    message_type = serializers.ChoiceField(
        choices=["text", "image", "audio", "video", "file"], default="text"
    )
    file_attachment = serializers.FileField(required=False)
    metadata = serializers.JSONField(default=dict)
    session_id = serializers.UUIDField()

    def validate_file_attachment(self, value):
        """Validate file attachment based on message type"""
        if not value:
            return value

        message_type = self.initial_data.get("message_type", "text")

        # File size validation (50MB max)
        max_size = 50 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("File size cannot exceed 50MB")

        # File type validation
        allowed_types = {
            "image": ["jpg", "jpeg", "png", "gif", "bmp", "webp"],
            "audio": ["mp3", "wav", "ogg", "m4a", "flac"],
            "video": ["mp4", "avi", "mov", "wmv", "flv"],
            "file": [],  # Allow any file type for generic files
        }

        if allowed_types.get(message_type):
            file_extension = value.name.split(".")[-1].lower()
            if file_extension not in allowed_types[message_type]:
                raise serializers.ValidationError(
                    f"File type {file_extension} not allowed for {message_type} messages"
                )

        return value


class AgentPerformanceSerializer(serializers.Serializer):
    """Serializer for agent performance analytics"""

    agent_id = serializers.UUIDField()
    agent_name = serializers.CharField()
    total_tasks = serializers.IntegerField()
    completed_tasks = serializers.IntegerField()
    failed_tasks = serializers.IntegerField()
    average_response_time = serializers.FloatField(allow_null=True)
    success_rate = serializers.FloatField(allow_null=True)
    last_active = serializers.DateTimeField()
    status = serializers.CharField()

    def to_representation(self, instance):
        """Calculate performance metrics from related tasks/executions."""
        task_stats = Task.objects.filter(assigned_agent=instance).aggregate(
            total=Count("id"),
            completed=Count("id", filter=Q(status=TaskStatus.COMPLETED)),
            failed=Count("id", filter=Q(status=TaskStatus.FAILED)),
            avg_duration=Avg("actual_duration"),
        )
        total = task_stats["total"] or 0
        completed = task_stats["completed"] or 0
        failed = task_stats["failed"] or 0

        avg_response = task_stats["avg_duration"]
        if avg_response is None:
            exec_avg = TaskExecution.objects.filter(agent=instance).aggregate(
                avg_time=Avg("execution_time")
            )["avg_time"]
            avg_response = exec_avg

        success_rate = None
        if total > 0:
            success_rate = round((completed / total) * 100, 2)

        return {
            "agent_id": str(instance.id),
            "agent_name": instance.name,
            "total_tasks": total,
            "completed_tasks": completed,
            "failed_tasks": failed,
            "average_response_time": (
                float(avg_response) if avg_response is not None else None
            ),
            "success_rate": success_rate,
            "last_active": instance.updated_at,
            "status": instance.status,
        }
