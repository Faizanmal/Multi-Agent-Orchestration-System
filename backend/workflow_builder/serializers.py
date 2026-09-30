from rest_framework import serializers

from .models import (
    VisualWorkflow,
    WorkflowExecution,
    WorkflowNode,
    WorkflowTemplate,
    WorkflowVersion,
)


class WorkflowTemplateSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(
        source="created_by.username", read_only=True
    )

    class Meta:
        model = WorkflowTemplate
        fields = "__all__"
        read_only_fields = ("id", "usage_count", "rating", "created_at", "updated_at")


class WorkflowNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowNode
        fields = "__all__"
        read_only_fields = ("id", "created_at")


class VisualWorkflowSerializer(serializers.ModelSerializer):
    workflow_nodes = WorkflowNodeSerializer(many=True, read_only=True)
    template_name = serializers.CharField(source="template.name", read_only=True)
    user_username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = VisualWorkflow
        fields = "__all__"
        read_only_fields = (
            "id",
            "user",
            "execution_count",
            "last_executed",
            "created_at",
            "updated_at",
        )


class WorkflowExecutionSerializer(serializers.ModelSerializer):
    workflow_name = serializers.CharField(source="workflow.name", read_only=True)

    class Meta:
        model = WorkflowExecution
        fields = "__all__"
        read_only_fields = ("id", "created_at")


class WorkflowVersionSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(
        source="created_by.username", read_only=True
    )

    class Meta:
        model = WorkflowVersion
        fields = "__all__"
        read_only_fields = ("id", "created_at")
