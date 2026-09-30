import uuid

from django.conf import settings as django_settings
from django.contrib.auth import get_user_model
from django.db import models

# Get the custom user model
User = get_user_model()


class AgentType(models.TextChoices):
    ORCHESTRATOR = "orchestrator", "Orchestrator"
    VISION = "vision", "Vision"
    REASONING = "reasoning", "Reasoning"
    ACTION = "action", "Action"
    MEMORY = "memory", "Memory"
    CUSTOM = "custom", "Custom"


class AgentStatus(models.TextChoices):
    IDLE = "idle", "Idle"
    ACTIVE = "active", "Active"
    PROCESSING = "processing", "Processing"
    ERROR = "error", "Error"
    OFFLINE = "offline", "Offline"


class Agent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=AgentType.choices)
    status = models.CharField(
        max_length=20, choices=AgentStatus.choices, default=AgentStatus.IDLE
    )
    capabilities = models.JSONField(default=list)
    configuration = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(
        django_settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="agents"
    )
    workspace = models.ForeignKey(
        "authentication.Workspace",
        on_delete=models.CASCADE,
        related_name="agents",
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]  # noqa: RUF012

    def __str__(self):
        return f"{self.name} ({self.type})"


class Session(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    user = models.ForeignKey(
        django_settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="agent_sessions",
    )
    workspace = models.ForeignKey(
        "authentication.Workspace",
        on_delete=models.CASCADE,
        related_name="sessions",
        null=True,
        blank=True,
    )
    agents = models.ManyToManyField(Agent, related_name="sessions")
    context = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-updated_at"]  # noqa: RUF012

    def __str__(self):
        return self.name


class MessageType(models.TextChoices):
    TEXT = "text", "Text"
    IMAGE = "image", "Image"
    AUDIO = "audio", "Audio"
    VIDEO = "video", "Video"
    FILE = "file", "File"
    SYSTEM = "system", "System"


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        Session, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        django_settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    )
    sender_agent = models.ForeignKey(
        Agent, on_delete=models.CASCADE, null=True, blank=True
    )
    recipient_agent = models.ForeignKey(
        Agent,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="received_messages",
    )
    content = models.TextField()
    message_type = models.CharField(
        max_length=20, choices=MessageType.choices, default=MessageType.TEXT
    )
    metadata = models.JSONField(default=dict)
    file_attachment = models.FileField(upload_to="attachments/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]  # noqa: RUF012

    def __str__(self):
        sender_name = (
            self.sender.username
            if self.sender
            else self.sender_agent.name if self.sender_agent else "System"
        )
        return f"{sender_name}: {self.content[:50]}"


class AgentMemory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="memories")
    session = models.ForeignKey(
        Session, on_delete=models.CASCADE, related_name="memories"
    )
    key = models.CharField(max_length=200)
    value = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    accessed_at = models.DateTimeField(auto_now=True)
    importance_score = models.FloatField(default=1.0)

    class Meta:
        unique_together = ["agent", "session", "key"]  # noqa: RUF012
        ordering = ["-importance_score", "-accessed_at"]  # noqa: RUF012

    def __str__(self):
        return f"{self.agent.name} - {self.key}"


class PerformanceMetric(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="metrics")
    session = models.ForeignKey(
        Session, on_delete=models.CASCADE, null=True, blank=True
    )
    metric_name = models.CharField(max_length=100)
    metric_value = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict)

    class Meta:
        ordering = ["-timestamp"]  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=["agent", "metric_name"]),
            models.Index(fields=["timestamp"]),
        ]

    def __str__(self):
        return f"{self.agent.name} - {self.metric_name}: {self.metric_value}"


class TaskStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    IN_PROGRESS = "in_progress", "In Progress"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"


class TaskPriority(models.TextChoices):
    LOW = "low", "Low"
    NORMAL = "normal", "Normal"
    HIGH = "high", "High"
    URGENT = "urgent", "Urgent"


class Task(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    task_type = models.CharField(max_length=50)
    priority = models.CharField(
        max_length=20, choices=TaskPriority.choices, default=TaskPriority.NORMAL
    )
    status = models.CharField(
        max_length=20, choices=TaskStatus.choices, default=TaskStatus.PENDING
    )
    assigned_agent = models.ForeignKey(
        Agent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
    )
    created_by = models.ForeignKey(
        django_settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_tasks",
    )
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="tasks")
    requirements = models.JSONField(default=dict)
    input_data = models.JSONField(default=dict)
    output_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    estimated_duration = models.IntegerField(
        null=True, blank=True, help_text="Estimated duration in seconds"
    )
    actual_duration = models.IntegerField(
        null=True, blank=True, help_text="Actual duration in seconds"
    )

    class Meta:
        ordering = ["-created_at"]  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=["status", "priority"]),
            models.Index(fields=["assigned_agent", "status"]),
            models.Index(fields=["task_type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.status}"


class TaskExecution(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="executions")
    agent = models.ForeignKey(
        Agent, on_delete=models.CASCADE, related_name="task_executions"
    )
    # task_id = models.CharField(max_length=100, help_text="Task identifier for tracking")
    execution_identifier = models.CharField(
        max_length=100, help_text="Task execution identifier for tracking", default=""
    )
    task_type = models.CharField(max_length=50)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    execution_time = models.FloatField(help_text="Execution time in seconds")
    success = models.BooleanField()
    accuracy = models.FloatField(
        null=True, blank=True, help_text="Task accuracy score (0-1)"
    )
    error_message = models.TextField(null=True, blank=True)
    resource_usage = models.JSONField(
        default=dict, help_text="CPU, memory, and other resource usage"
    )
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_time"]  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=["agent", "task_type"]),
            models.Index(fields=["start_time"]),
            models.Index(fields=["success"]),
            models.Index(fields=["task_type", "success"]),
        ]

    def __str__(self):
        return f"{self.agent.name} - {self.task_type} ({self.execution_time:.2f}s)"


class WorkflowTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=100)
    tags = models.JSONField(default=list)
    workflow_definition = models.JSONField(
        help_text="JSON definition of the workflow steps"
    )
    created_by = models.ForeignKey(
        django_settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="workflow_templates",
    )
    is_public = models.BooleanField(default=False)
    usage_count = models.IntegerField(default=0)
    average_rating = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-usage_count", "-average_rating"]  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=["category"]),
            models.Index(fields=["is_public"]),
            models.Index(fields=["usage_count"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.category})"


class AgentSkill(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="skills")
    skill_name = models.CharField(max_length=100)
    proficiency_level = models.FloatField(help_text="Skill proficiency (0-1)")
    confidence_score = models.FloatField(
        help_text="Confidence in skill assessment (0-1)"
    )
    last_used = models.DateTimeField(null=True, blank=True)
    usage_count = models.IntegerField(default=0)
    success_rate = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["agent", "skill_name"]  # noqa: RUF012
        ordering = ["-proficiency_level"]  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=["agent", "skill_name"]),
            models.Index(fields=["proficiency_level"]),
        ]

    def __str__(self):
        return f"{self.agent.name} - {self.skill_name} ({self.proficiency_level:.2f})"
