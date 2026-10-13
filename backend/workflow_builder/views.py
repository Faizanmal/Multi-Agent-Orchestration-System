from django.conf import settings
from django.db import models, transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import VisualWorkflow, WorkflowExecution, WorkflowTemplate, WorkflowVersion
from .serializers import (
    VisualWorkflowSerializer,
    WorkflowExecutionSerializer,
    WorkflowTemplateSerializer,
    WorkflowVersionSerializer,
)


class WorkflowTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for workflow templates"""

    queryset = WorkflowTemplate.objects.all()
    serializer_class = WorkflowTemplateSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """Filter public templates or user's own templates"""
        if self.request.user.is_staff:
            return WorkflowTemplate.objects.all()
        return WorkflowTemplate.objects.filter(
            models.Q(is_public=True) | models.Q(created_by=self.request.user)
        )

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def use_template(self, request, pk=None):
        """Create a workflow from a template"""
        template = self.get_object()

        # Create workflow from template
        workflow = VisualWorkflow.objects.create(
            name=f"{template.name} (Copy)",
            description=template.description,
            user=request.user,
            template=template,
            nodes=template.workflow_definition.get("nodes", []),
            edges=template.workflow_definition.get("edges", []),
            variables=template.workflow_definition.get("variables", {}),
            settings=template.workflow_definition.get("settings", {}),
        )

        # Increment usage count
        template.usage_count += 1
        template.save()

        serializer = VisualWorkflowSerializer(workflow)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def rate(self, request, pk=None):
        """Rate a template"""
        template = self.get_object()
        rating = request.data.get("rating")

        if not rating or not (1 <= rating <= 5):
            return Response(
                {"error": "Rating must be between 1 and 5"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Simple average rating update
        current_total = template.rating * template.usage_count
        new_total = current_total + rating
        template.rating = new_total / (template.usage_count + 1)
        template.save()

        return Response({"rating": template.rating})

    @action(detail=True, methods=["post"])
    def execute(self, request, pk=None):
        """Execute a template's workflow_definition via VisualWorkflowExecutor."""
        from agents.services.workflow_executor import (
            VisualWorkflowExecutor,
            WorkflowExecutionError,
        )

        template = self.get_object()
        definition = template.workflow_definition or {}
        input_data = request.data.get("input_data") or request.data.get("trigger") or {}
        if not isinstance(input_data, dict):
            input_data = {"trigger": input_data}

        # Ensure ReactFlow-shaped nodes/edges
        nodes = definition.get("nodes") or []
        edges = definition.get("edges") or []
        if not nodes and definition.get("workflow_definition"):
            nested = definition["workflow_definition"]
            nodes = nested.get("nodes", [])
            edges = nested.get("edges", [])

        try:
            executor = VisualWorkflowExecutor(
                {"nodes": nodes, "edges": edges},
                context={"input_data": input_data, "template_id": str(template.id)},
            )
            result = executor.execute()
        except WorkflowExecutionError as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:  # noqa: BLE001
            return Response(
                {"error": f"Execution failed: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        template.usage_count += 1
        template.save(update_fields=["usage_count"])

        return Response(
            {
                "status": result.get("status"),
                "result": result,
                "template_id": str(template.id),
            }
        )


class VisualWorkflowViewSet(viewsets.ModelViewSet):
    """ViewSet for visual workflows"""

    queryset = VisualWorkflow.objects.all()
    serializer_class = VisualWorkflowSerializer
    permission_classes = [AllowAny] if settings.DEBUG else [IsAuthenticated]

    def get_queryset(self):
        """Filter by user"""
        if settings.DEBUG and getattr(self.request.user, "is_anonymous", True):
            return VisualWorkflow.objects.all()
        if self.request.user.is_staff:
            return VisualWorkflow.objects.all()
        return VisualWorkflow.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        if settings.DEBUG and getattr(self.request.user, "is_anonymous", True):
            from django.contrib.auth import get_user_model

            User = get_user_model()
            user, _ = User.objects.get_or_create(
                email="default@example.com",
                defaults={
                    "username": "default_user",
                    "first_name": "Default",
                    "last_name": "User",
                },
            )
            serializer.save(user=user)
        else:
            serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def execute(self, request, pk=None):
        """Execute a workflow"""
        from agents.services.workflow_executor import VisualWorkflowExecutor

        workflow = self.get_object()
        input_data = request.data.get("input_data", {})

        # Create execution record
        execution = WorkflowExecution.objects.create(
            workflow=workflow, input_data=input_data, status="queued"
        )

        # Update workflow metadata
        workflow.execution_count += 1
        workflow.last_executed = timezone.now()
        workflow.save()

        try:
            # Execute workflow using the visual workflow executor
            execution.status = "running"
            execution.started_at = timezone.now()
            execution.save()

            # Build workflow definition from visual workflow
            workflow_definition = {
                "nodes": workflow.nodes,
                "edges": workflow.edges,
            }

            # Initial context for execution
            context = {"input_data": input_data}

            executor = VisualWorkflowExecutor(
                workflow_definition=workflow_definition, context=context
            )

            result = executor.execute()

            execution.status = (
                "completed" if result.get("status") == "completed" else "failed"
            )
            execution.completed_at = timezone.now()
            execution.output_data = result.get("context", {})
            execution.error_message = (
                "" if result.get("status") == "completed" else "Partial execution"
            )

            # Record analytics-friendly execution metrics when possible
            try:
                from agents.models import Agent, PerformanceMetric

                duration_ms = 0.0
                if execution.started_at and execution.completed_at:
                    duration_ms = (
                        execution.completed_at - execution.started_at
                    ).total_seconds() * 1000
                agent = (
                    Agent.objects.filter(owner=request.user).order_by("-created_at").first()
                    if getattr(request.user, "is_authenticated", False)
                    else None
                )
                if agent:
                    PerformanceMetric.objects.create(
                        agent=agent,
                        metric_name="workflow_execution_ms",
                        metric_value=duration_ms,
                        metadata={
                            "workflow_id": str(workflow.id),
                            "execution_id": str(execution.id),
                            "status": execution.status,
                            "nodes_executed": result.get("nodes_executed", 0),
                        },
                    )
            except Exception:  # noqa: BLE001
                pass
            execution.save()

            serializer = WorkflowExecutionSerializer(execution)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:  # noqa: BLE001
            execution.status = "failed"
            execution.completed_at = timezone.now()
            execution.error_message = str(e)
            execution.save()

            return Response(
                {"error": f"Workflow execution failed: {e!s}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _convert_nodes_to_steps(self, nodes, edges):
        """Convert visual workflow nodes and edges to workflow steps"""
        steps = []

        # Create dependency map from edges
        dependency_map = {}
        for edge in edges:
            target = edge.get("target")
            source = edge.get("source")
            if target not in dependency_map:
                dependency_map[target] = []
            dependency_map[target].append(source)

        # Convert nodes to steps
        for node in nodes:
            data = node.get("data", {})
            node_type = data.get("nodeType") or node.get("type", "agent")
            step = {
                "id": node.get("id"),
                "type": self._map_node_type_to_step_type(node_type),
                "config": data,
                "dependencies": dependency_map.get(node.get("id"), []),
            }
            steps.append(step)

        return steps

    def _map_node_type_to_step_type(self, node_type):
        """Map visual node types to workflow engine step types"""
        mapping = {
            "agent": "agent_task",
            "condition": "conditional",
            "action": "agent_task",
            "trigger": "agent_task",
            "transform": "data_transform",
            "integration": "integration_call",
            "integration_call": "integration_call",
            "delay": "delay",
            "loop": "parallel",
        }
        return mapping.get(node_type, "agent_task")

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def create_version(self, request, pk=None):
        """Create a new version of the workflow"""
        workflow = self.get_object()
        change_description = request.data.get("change_description", "")

        # Create version snapshot
        version = WorkflowVersion.objects.create(
            workflow=workflow,
            version_number=workflow.version + 1,
            nodes_snapshot=workflow.nodes,
            edges_snapshot=workflow.edges,
            variables_snapshot=workflow.variables,
            settings_snapshot=workflow.settings,
            change_description=change_description,
            created_by=request.user,
        )

        # Update workflow version
        workflow.version += 1
        workflow.save()

        serializer = WorkflowVersionSerializer(version)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def restore_version(self, request, pk=None):
        """Restore workflow to a previous version"""
        workflow = self.get_object()
        version_number = request.data.get("version_number")

        if not version_number:
            return Response(
                {"error": "version_number is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            version = WorkflowVersion.objects.get(
                workflow=workflow, version_number=version_number
            )
        except WorkflowVersion.DoesNotExist:
            return Response(
                {"error": "Version not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Create new version with current state before restoring
        WorkflowVersion.objects.create(
            workflow=workflow,
            version_number=workflow.version + 1,
            nodes_snapshot=workflow.nodes,
            edges_snapshot=workflow.edges,
            variables_snapshot=workflow.variables,
            settings_snapshot=workflow.settings,
            change_description=f"Restored from version {version_number}",
            created_by=request.user,
        )

        # Restore workflow state
        workflow.nodes = version.nodes_snapshot
        workflow.edges = version.edges_snapshot
        workflow.variables = version.variables_snapshot
        workflow.settings = version.settings_snapshot
        workflow.version += 1
        workflow.save()

        serializer = self.get_serializer(workflow)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def versions(self, request, pk=None):
        """Get version history"""
        workflow = self.get_object()
        versions = workflow.version_history.all()
        serializer = WorkflowVersionSerializer(versions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def duplicate(self, request, pk=None):
        """Duplicate a workflow"""
        workflow = self.get_object()

        new_workflow = VisualWorkflow.objects.create(
            name=f"{workflow.name} (Copy)",
            description=workflow.description,
            user=request.user,
            nodes=workflow.nodes,
            edges=workflow.edges,
            variables=workflow.variables,
            settings=workflow.settings,
            status="draft",
        )

        serializer = self.get_serializer(new_workflow)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def save_as_template(self, request, pk=None):
        """Save workflow as a template"""
        workflow = self.get_object()

        template_data = {
            "name": request.data.get("name", workflow.name),
            "description": request.data.get("description", workflow.description),
            "category": request.data.get("category", "custom"),
            "is_public": request.data.get("is_public", False),
            "workflow_definition": {
                "nodes": workflow.nodes,
                "edges": workflow.edges,
                "variables": workflow.variables,
                "settings": workflow.settings,
            },
        }

        template = WorkflowTemplate.objects.create(
            **template_data, created_by=request.user
        )

        serializer = WorkflowTemplateSerializer(template)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class WorkflowExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for workflow executions (read-only)"""

    queryset = WorkflowExecution.objects.all()
    serializer_class = WorkflowExecutionSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """Filter by user's workflows"""
        if self.request.user.is_staff:
            return WorkflowExecution.objects.all()
        return WorkflowExecution.objects.filter(workflow__user=self.request.user)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel a running execution"""
        execution = self.get_object()

        if execution.status not in ["queued", "running"]:
            return Response(
                {"error": "Execution cannot be cancelled"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        execution.status = "cancelled"
        execution.completed_at = timezone.now()
        execution.save()

        return Response({"status": "cancelled"})
