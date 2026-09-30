from django.contrib import admin

from .models import (
    VisualWorkflow,
    WorkflowExecution,
    WorkflowNode,
    WorkflowTemplate,
    WorkflowVersion,
)


@admin.register(WorkflowTemplate)
class WorkflowTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'usage_count', 'rating', 'is_public', 'created_by', 'created_at']  # noqa: RUF012
    list_filter = ['category', 'is_public', 'created_at']  # noqa: RUF012
    search_fields = ['name', 'description', 'tags']  # noqa: RUF012


@admin.register(VisualWorkflow)
class VisualWorkflowAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'status', 'version', 'execution_count', 'updated_at']  # noqa: RUF012
    list_filter = ['status', 'created_at', 'updated_at']  # noqa: RUF012
    search_fields = ['name', 'description']  # noqa: RUF012


@admin.register(WorkflowNode)
class WorkflowNodeAdmin(admin.ModelAdmin):
    list_display = ['label', 'workflow', 'node_type', 'created_at']  # noqa: RUF012
    list_filter = ['node_type', 'created_at']  # noqa: RUF012
    search_fields = ['label']  # noqa: RUF012


@admin.register(WorkflowExecution)
class WorkflowExecutionAdmin(admin.ModelAdmin):
    list_display = ['workflow', 'status', 'duration_ms', 'started_at', 'completed_at']  # noqa: RUF012
    list_filter = ['status', 'created_at']  # noqa: RUF012


@admin.register(WorkflowVersion)
class WorkflowVersionAdmin(admin.ModelAdmin):
    list_display = ['workflow', 'version_number', 'created_by', 'created_at']  # noqa: RUF012
    list_filter = ['created_at']  # noqa: RUF012
    search_fields = ['change_description']  # noqa: RUF012
