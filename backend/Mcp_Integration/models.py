# MCP Integration Models

import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

# Get the custom user model
User = get_user_model()


class MCPTool(models.Model):
    """Model for MCP tools available in the system."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    category = models.CharField(max_length=50, default="general")
    version = models.CharField(max_length=20, default="1.0.0")

    # Tool configuration
    parameters_schema = models.JSONField(
        default=dict, help_text="JSON schema for tool parameters"
    )
    capabilities = models.JSONField(
        default=list, help_text="List of capabilities this tool provides"
    )
    requirements = models.JSONField(
        default=dict, help_text="System requirements for this tool"
    )

    # Availability and permissions
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=True)
    is_system_tool = models.BooleanField(default=False)

    # Usage tracking
    usage_count = models.PositiveIntegerField(default=0)
    success_rate = models.FloatField(default=1.0)
    average_execution_time = models.FloatField(default=0.0)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["category", "name"]  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=["category", "is_active"]),
            models.Index(fields=["is_public", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.category})"

    def update_usage_stats(self, execution_time: float, success: bool):
        """Update tool usage statistics."""
        self.usage_count += 1

        # Update success rate
        total_successes = self.success_rate * (self.usage_count - 1)
        if success:
            total_successes += 1
        self.success_rate = total_successes / self.usage_count

        # Update average execution time
        total_time = self.average_execution_time * (self.usage_count - 1)
        total_time += execution_time
        self.average_execution_time = total_time / self.usage_count

        self.save(
            update_fields=["usage_count", "success_rate", "average_execution_time"]
        )


class MCPSession(models.Model):
    """Model for MCP sessions with context persistence."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)

    # Session configuration
    enabled_tools = models.JSONField(
        default=list, help_text="List of enabled tool names"
    )
    context_data = models.JSONField(
        default=dict, help_text="Session context and memory"
    )
    configuration = models.JSONField(
        default=dict, help_text="Session-specific configuration"
    )

    # Session state
    is_active = models.BooleanField(default=True)
    last_activity = models.DateTimeField(auto_now=True)

    # Relationships
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-last_activity"]  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=["created_by", "is_active"]),
            models.Index(fields=["last_activity"]),
        ]

    def __str__(self):
        return f"MCP Session: {self.name}"

    def add_to_context(self, key: str, value: any):
        """Add data to session context."""
        if not isinstance(self.context_data, dict):
            self.context_data = {}
        self.context_data[key] = value
        self.save(update_fields=["context_data", "updated_at"])

    def get_from_context(self, key: str, default=None):
        """Get data from session context."""
        if not isinstance(self.context_data, dict):
            return default
        return self.context_data.get(key, default)


class MCPToolExecution(models.Model):
    """Model for tracking MCP tool executions."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tool = models.ForeignKey(
        MCPTool, on_delete=models.CASCADE, related_name="executions"
    )
    session_id = models.CharField(max_length=100, null=True, blank=True)

    # Execution details
    parameters = models.JSONField(
        default=dict, help_text="Parameters passed to the tool"
    )
    result = models.JSONField(default=dict, help_text="Tool execution result")
    error_message = models.TextField(blank=True)

    # Execution metrics
    success = models.BooleanField(default=False)
    execution_time = models.FloatField(
        default=0.0, help_text="Execution time in seconds"
    )
    memory_usage = models.FloatField(default=0.0, help_text="Memory usage in MB")

    # Context
    agent_id = models.CharField(max_length=100, null=True, blank=True)
    context_used = models.JSONField(
        default=dict, help_text="Context data used in execution"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["-created_at"]  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=["tool", "success"]),
            models.Index(fields=["session_id", "-created_at"]),
            models.Index(fields=["agent_id", "-created_at"]),
        ]

    def __str__(self):
        status = "✓" if self.success else "✗"
        return f"{status} {self.tool.name} ({self.execution_time:.2f}s)"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update tool statistics
        if self.pk and self.tool:
            self.tool.update_usage_stats(self.execution_time, self.success)


class MCPToolRegistry(models.Model):
    """Registry for available MCP tools and their configurations."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Registry information
    registry_name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    version = models.CharField(max_length=20)

    # Registry configuration
    tools_config = models.JSONField(
        default=dict, help_text="Configuration for all tools in registry"
    )
    default_settings = models.JSONField(
        default=dict, help_text="Default settings for tools"
    )

    # Status
    is_active = models.BooleanField(default=True)
    last_sync = models.DateTimeField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["registry_name"]  # noqa: RUF012

    def __str__(self):
        return f"MCP Registry: {self.registry_name} v{self.version}"


class MCPAgentToolBinding(models.Model):
    """Binding between agents and MCP tools for personalized tool selection."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Binding details
    agent_id = models.CharField(max_length=100)
    tool = models.ForeignKey(MCPTool, on_delete=models.CASCADE)

    # Configuration
    is_preferred = models.BooleanField(default=False)
    priority = models.IntegerField(default=0)
    custom_parameters = models.JSONField(
        default=dict, help_text="Agent-specific tool parameters"
    )

    # Performance tracking
    success_rate = models.FloatField(default=1.0)
    average_execution_time = models.FloatField(default=0.0)
    usage_count = models.PositiveIntegerField(default=0)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["agent_id", "tool"]  # noqa: RUF012
        ordering = ["-priority", "tool__name"]  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=["agent_id", "is_preferred"]),
            models.Index(fields=["tool", "success_rate"]),
        ]

    def __str__(self):
        return f"Agent {self.agent_id} -> {self.tool.name} (Priority: {self.priority})"

    def update_performance(self, execution_time: float, success: bool):
        """Update performance metrics for this agent-tool binding."""
        self.usage_count += 1

        # Update success rate
        total_successes = self.success_rate * (self.usage_count - 1)
        if success:
            total_successes += 1
        self.success_rate = total_successes / self.usage_count

        # Update average execution time
        total_time = self.average_execution_time * (self.usage_count - 1)
        total_time += execution_time
        self.average_execution_time = total_time / self.usage_count

        self.save(
            update_fields=["usage_count", "success_rate", "average_execution_time"]
        )
