import uuid

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class WorkflowTemplate(models.Model):
    """Pre-built workflow templates"""

    CATEGORY_CHOICES = [  # noqa: RUF012
        ("data_processing", "Data Processing"),
        ("content_generation", "Content Generation"),
        ("analysis", "Analysis"),
        ("automation", "Automation"),
        ("integration", "Integration"),
        ("custom", "Custom"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    workflow_definition = models.JSONField()
    thumbnail_url = models.URLField(blank=True, null=True)
    tags = models.JSONField(default=list)
    usage_count = models.IntegerField(default=0)
    rating = models.FloatField(default=0.0)
    is_public = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_workflow_templates"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "workflow_templates"
        ordering = ("-usage_count", "-rating")


class VisualWorkflow(models.Model):
    """Visual workflow definitions with drag-and-drop support"""

    STATUS_CHOICES = [  # noqa: RUF012
        ("draft", "Draft"),
        ("active", "Active"),
        ("paused", "Paused"),
        ("archived", "Archived"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="visual_workflows"
    )
    template = models.ForeignKey(
        WorkflowTemplate, on_delete=models.SET_NULL, null=True, blank=True
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    # Visual workflow definition
    nodes = models.JSONField(default=list)  # Node definitions with positions
    edges = models.JSONField(default=list)  # Connections between nodes
    variables = models.JSONField(default=dict)  # Workflow variables
    settings = models.JSONField(default=dict)  # Workflow settings

    # Version control
    version = models.IntegerField(default=1)
    parent_version = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="versions",
    )

    # Metadata
    execution_count = models.IntegerField(default=0)
    last_executed = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "visual_workflows"
        ordering = ("-updated_at",)


class WorkflowNode(models.Model):
    """Individual nodes in a workflow"""

    NODE_TYPE_CHOICES = [  # noqa: RUF012
        ("trigger", "Trigger"),
        ("agent", "Agent"),
        ("condition", "Condition"),
        ("action", "Action"),
        ("transform", "Transform"),
        ("integration", "Integration"),
        ("delay", "Delay"),
        ("loop", "Loop"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(
        VisualWorkflow, on_delete=models.CASCADE, related_name="workflow_nodes"
    )
    node_type = models.CharField(max_length=50, choices=NODE_TYPE_CHOICES)
    label = models.CharField(max_length=200)

    # Node configuration
    config = models.JSONField(default=dict)

    # Visual position
    position_x = models.FloatField(default=0)
    position_y = models.FloatField(default=0)

    # Connections
    inputs = models.JSONField(default=list)
    outputs = models.JSONField(default=list)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "workflow_nodes"


class WorkflowExecution(models.Model):
    """Execution history for visual workflows"""

    STATUS_CHOICES = [  # noqa: RUF012
        ("queued", "Queued"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(
        VisualWorkflow, on_delete=models.CASCADE, related_name="executions"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="queued")

    # Execution data
    input_data = models.JSONField(default=dict)
    output_data = models.JSONField(default=dict, null=True, blank=True)
    node_results = models.JSONField(default=dict)  # Results from each node

    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_ms = models.IntegerField(null=True, blank=True)

    # Error tracking
    error_message = models.TextField(blank=True)
    error_node_id = models.UUIDField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "workflow_executions"
        ordering = ("-created_at",)


class WorkflowVersion(models.Model):
    """Version control for workflows"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(
        VisualWorkflow, on_delete=models.CASCADE, related_name="version_history"
    )
    version_number = models.IntegerField()

    # Snapshot of workflow state
    nodes_snapshot = models.JSONField()
    edges_snapshot = models.JSONField()
    variables_snapshot = models.JSONField()
    settings_snapshot = models.JSONField()

    # Version metadata
    change_description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "workflow_versions"
        ordering = ["-version_number"]  # noqa: RUF012
        unique_together = ["workflow", "version_number"]  # noqa: RUF012
