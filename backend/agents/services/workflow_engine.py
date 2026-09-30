# agents/services/workflow_engine.py

import asyncio
import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any

from django.db import transaction
from django.utils import timezone

from ..models import Agent, Task, TaskPriority, TaskStatus
from .agent_selector import SmartAgentSelector
from .performance_tracker import PerformanceTracker

logger = logging.getLogger(__name__)


class WorkflowStep:
    """Represents a single step in a workflow."""

    def __init__(
        self,
        step_id: str,
        step_type: str,
        config: dict,
        dependencies: list[str] | None = None,
    ):
        self.step_id = step_id
        self.step_type = step_type
        self.config = config
        self.dependencies = dependencies or []
        self.status = "pending"
        self.result = None
        self.error = None
        self.start_time = None
        self.end_time = None


class WorkflowEngine:
    """
    Advanced workflow automation engine that orchestrates complex
    multi-agent workflows with dependency management, error handling,
    and performance optimization.
    """

    def __init__(self):
        self.agent_selector = SmartAgentSelector()
        self.performance_tracker = PerformanceTracker()
        self.step_executors = self._register_step_executors()
        self.running_workflows = {}

    async def execute_workflow(
        self,
        workflow_definition: dict,
        input_data: dict,
        user_id: str,
        session_id: str | None = None,
    ) -> dict:
        """
        Execute a complete workflow with dependency management and error handling.

        Args:
            workflow_definition: Workflow configuration and steps
            input_data: Initial data for the workflow
            user_id: User executing the workflow
            session_id: Optional session ID for context

        Returns:
            Workflow execution result with status and outputs
        """

        workflow_id = workflow_definition.get(
            "id", f"workflow_{int(datetime.now(timezone.utc).timestamp())}"
        )

        try:
            logger.info(f"Starting workflow execution: {workflow_id}")

            # Parse workflow steps
            steps = self._parse_workflow_steps(workflow_definition)

            # Create workflow execution context
            context = {
                "workflow_id": workflow_id,
                "user_id": user_id,
                "session_id": session_id,
                "input_data": input_data,
                "steps": steps,
                "results": {},
                "start_time": timezone.now(),
                "status": "running",
            }

            # Store running workflow
            self.running_workflows[workflow_id] = context

            # Execute workflow steps
            result = await self._execute_workflow_steps(context)

            # Update final status
            context["status"] = "completed" if result["success"] else "failed"
            context["end_time"] = timezone.now()

            logger.info(f"Workflow {workflow_id} completed: {context['status']}")

            return {
                "workflow_id": workflow_id,
                "success": result["success"],
                "results": context["results"],
                "execution_time": (
                    context["end_time"] - context["start_time"]
                ).total_seconds(),
                "error": result.get("error"),
                "steps_executed": len(
                    [s for s in steps.values() if s.status == "completed"]
                ),
                "total_steps": len(steps),
            }

        except Exception as e:  # noqa: BLE001
            logger.error(f"Error executing workflow {workflow_id}: {e}")
            return {
                "workflow_id": workflow_id,
                "success": False,
                "error": str(e),
                "results": {},
            }
        finally:
            # Clean up
            if workflow_id in self.running_workflows:
                del self.running_workflows[workflow_id]

    def _parse_workflow_steps(
        self, workflow_definition: dict
    ) -> dict[str, WorkflowStep]:
        """Parse workflow definition into executable steps."""

        steps = {}
        workflow_steps = workflow_definition.get("steps", [])

        for step_config in workflow_steps:
            step = WorkflowStep(
                step_id=step_config["id"],
                step_type=step_config["type"],
                config=step_config.get("config", {}),
                dependencies=step_config.get("dependencies", []),
            )
            steps[step.step_id] = step

        return steps

    async def _execute_workflow_steps(self, context: dict) -> dict:
        """Execute workflow steps with dependency management."""

        steps = context["steps"]
        results = context["results"]

        try:
            # Build dependency graph
            dependency_graph = self._build_dependency_graph(steps)

            # Execute steps in topological order
            execution_order = self._topological_sort(dependency_graph)

            for step_id in execution_order:
                step = steps[step_id]

                try:
                    # Check if dependencies are satisfied
                    if not self._are_dependencies_satisfied(step, results):
                        step.status = "skipped"
                        continue

                    # Execute step
                    step.start_time = timezone.now()
                    step.status = "running"

                    logger.info(f"Executing step: {step_id} ({step.step_type})")

                    step_result = await self._execute_step(step, context)

                    step.end_time = timezone.now()

                    if step_result["success"]:
                        step.status = "completed"
                        step.result = step_result["result"]
                        results[step_id] = step.result
                    else:
                        step.status = "failed"
                        step.error = step_result["error"]

                        # Check if this is a critical step
                        if step.config.get("critical", True):
                            return {
                                "success": False,
                                "error": f"Critical step {step_id} failed: {step.error}",
                            }
                        else:
                            logger.warning(
                                f"Non-critical step {step_id} failed: {step.error}"
                            )

                except Exception as e:  # noqa: BLE001
                    step.status = "failed"
                    step.error = str(e)
                    step.end_time = timezone.now()

                    logger.error(f"Error executing step {step_id}: {e}")

                    if step.config.get("critical", True):
                        return {
                            "success": False,
                            "error": f"Step {step_id} failed: {e!s}",
                        }

            return {"success": True}

        except Exception as e:  # noqa: BLE001
            logger.error(f"Error in workflow execution: {e}")
            return {"success": False, "error": str(e)}

    async def _execute_step(self, step: WorkflowStep, context: dict) -> dict:
        """Execute a single workflow step."""

        executor = self.step_executors.get(step.step_type)
        if not executor:
            return {
                "success": False,
                "error": f"No executor found for step type: {step.step_type}",
            }

        try:
            result = await executor(step, context)
            return {"success": True, "result": result}
        except Exception as e:  # noqa: BLE001
            return {"success": False, "error": str(e)}

    def _register_step_executors(self) -> dict[str, Callable]:
        """Register step executors for different step types."""

        return {
            "agent_task": self._execute_agent_task,
            "conditional": self._execute_conditional,
            "parallel": self._execute_parallel,
            "data_transform": self._execute_data_transform,
            "api_call": self._execute_api_call,
            "integration_call": self._execute_integration_call,
            "delay": self._execute_delay,
            "notification": self._execute_notification,
        }

    async def _execute_agent_task(self, step: WorkflowStep, context: dict) -> Any:
        """Execute a task using an agent."""

        config = step.config
        task_type = config.get("task_type", "general")
        task_description = config.get("description", "")
        requirements = config.get("requirements", {})

        # Select best agent for the task
        agent = self.agent_selector.select_best_agent(
            task_type=task_type,
            task_description=task_description,
            requirements=requirements,
        )

        if not agent:
            raise ValueError(f"No suitable agent found for task type: {task_type}")

        # Prepare input data
        input_data = self._prepare_step_input(step, context)

        # Create and execute task
        with transaction.atomic():
            task = Task.objects.create(
                title=config.get("title", f"Workflow step: {step.step_id}"),
                description=task_description,
                task_type=task_type,
                priority=TaskPriority.NORMAL,
                assigned_agent=agent,
                created_by_id=context["user_id"],
                session_id=context["session_id"],
                requirements=requirements,
                input_data=input_data,
            )

            # Execute the task via real Groq agent call
            task_result = await self._execute_agent_task_via_groq(agent, task)

            # Update task with results
            task.status = (
                TaskStatus.COMPLETED if task_result["success"] else TaskStatus.FAILED
            )
            task.completed_at = timezone.now()
            task.output_data = task_result.get("output", {})
            task.save()

            return task_result.get("output", {})

    async def _execute_conditional(self, step: WorkflowStep, context: dict) -> Any:
        """Execute conditional logic step."""

        config = step.config
        condition = config.get("condition", "")

        # Prepare condition evaluation context
        eval_context = {
            "results": context["results"],
            "input_data": context["input_data"],
        }

        # Evaluate condition (simplified - in production, use a safer evaluation method)
        try:
            condition_result = eval(condition, {"__builtins__": {}}, eval_context)
            return {
                "condition_met": bool(condition_result),
                "condition": condition,
                "result": condition_result,
            }
        except Exception as e:  # noqa: BLE001
            raise ValueError(f"Error evaluating condition '{condition}': {e}")

    async def _execute_parallel(self, step: WorkflowStep, context: dict) -> Any:
        """Execute multiple sub-steps in parallel."""

        config = step.config
        sub_steps = config.get("steps", [])

        # Execute sub-steps in parallel
        tasks = []
        for sub_step_config in sub_steps:
            sub_step = WorkflowStep(
                step_id=f"{step.step_id}_{sub_step_config['id']}",
                step_type=sub_step_config["type"],
                config=sub_step_config.get("config", {}),
            )

            task = asyncio.create_task(self._execute_step(sub_step, context))
            tasks.append((sub_step.step_id, task))

        # Wait for all tasks to complete
        results = {}
        for step_id, task in tasks:
            try:
                result = await task
                results[step_id] = result
            except Exception as e:  # noqa: BLE001
                results[step_id] = {"success": False, "error": str(e)}

        return results

    async def _execute_data_transform(self, step: WorkflowStep, context: dict) -> Any:
        """Execute data transformation step."""

        config = step.config
        input_data = self._prepare_step_input(step, context)

        # Apply transformations
        transformations = config.get("transformations", [])
        result = input_data

        for transform in transformations:
            transform_type = transform.get("type")

            if transform_type == "filter":
                # Filter data based on condition
                condition = transform.get("condition", "True")
                if isinstance(result, list):
                    result = [
                        item
                        for item in result
                        if eval(condition, {"__builtins__": {}}, {"item": item})
                    ]

            elif transform_type == "map":
                # Transform each item
                expression = transform.get("expression", "item")
                if isinstance(result, list):
                    result = [
                        eval(expression, {"__builtins__": {}}, {"item": item})
                        for item in result
                    ]

            elif transform_type == "aggregate":
                # Aggregate data
                operation = transform.get("operation", "count")
                if operation == "count":
                    result = len(result) if hasattr(result, "__len__") else 1
                elif operation == "sum" and isinstance(result, list):
                    result = sum(result)
                elif operation == "average" and isinstance(result, list):
                    result = sum(result) / len(result) if result else 0

        return result

    async def _execute_api_call(self, step: WorkflowStep, context: dict) -> Any:
        """Execute external API call."""

        import aiohttp

        config = step.config
        url = config.get("url", "")
        method = config.get("method", "GET").upper()
        headers = config.get("headers", {})

        # Prepare request data
        input_data = self._prepare_step_input(step, context)

        async with aiohttp.ClientSession() as session:
            if method == "GET":
                async with session.get(
                    url, headers=headers, params=input_data
                ) as response:
                    result = await response.json()
            else:
                async with session.request(
                    method, url, headers=headers, json=input_data
                ) as response:
                    result = await response.json()

        return result

    async def _execute_integration_call(self, step: WorkflowStep, context: dict) -> Any:
        """Execute a connected integration tool via IntegrationToolRegistry."""
        from api_integrations.registry import IntegrationToolRegistry
        from django.contrib.auth import get_user_model

        config = step.config
        tool_name = config.get("tool_name") or config.get("tool", "")
        params = config.get("params", {})
        if not tool_name and config.get("label"):
            tool_name = config.get("tool_name", "")

        user = None
        user_id = context.get("user_id")
        if user_id:
            User = get_user_model()
            user = await asyncio.get_event_loop().run_in_executor(
                None, lambda: User.objects.filter(id=user_id).first()
            )

        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: IntegrationToolRegistry.execute(tool_name, params, user=user),
        )
        if result.get("status") != "success":
            raise RuntimeError(result.get("message", "Integration call failed"))
        return result

    async def _execute_delay(self, step: WorkflowStep, context: dict) -> Any:
        """Execute delay/wait step."""

        config = step.config
        delay_seconds = config.get("seconds", 1)

        await asyncio.sleep(delay_seconds)

        return {
            "delayed_seconds": delay_seconds,
            "completed_at": timezone.now().isoformat(),
        }

    async def _execute_notification(self, step: WorkflowStep, context: dict) -> Any:
        """Execute notification step via the real NotificationService."""
        from ..webhook_service import NotificationService

        config = step.config
        message = config.get("message", "Workflow notification")
        title = config.get("title", "Workflow Update")
        channels = config.get("channels", ["in_app"])
        notification_type = config.get("notification_type", "info")
        user_id = context.get("user_id")

        if user_id:
            try:
                from django.contrib.auth import get_user_model

                User = get_user_model()
                user = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: User.objects.get(id=user_id)
                )
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: NotificationService.create_notification(
                        user=user,
                        title=title,
                        message=message,
                        notification_type=notification_type,
                        channels=channels,
                        metadata={
                            "workflow_id": context.get("workflow_id", ""),
                            "step_id": step.step_id,
                        },
                    ),
                )
                logger.info(f"Workflow notification sent to user {user_id}: {message}")
            except Exception as e:  # noqa: BLE001
                logger.warning(f"Notification delivery failed: {e}")
        else:
            logger.info(f"Workflow notification (no user): {message}")

        return {
            "title": title,
            "message": message,
            "channels": channels,
            "sent_at": timezone.now().isoformat(),
        }

    def _prepare_step_input(self, step: WorkflowStep, context: dict) -> dict:
        """Prepare input data for a step based on its configuration."""

        config = step.config
        input_mapping = config.get("input_mapping", {})

        step_input = {}

        # Map inputs from previous steps or initial data
        for key, source in input_mapping.items():
            if source.startswith("input."):
                # Get from initial input data
                source_key = source[6:]  # Remove 'input.' prefix
                step_input[key] = context["input_data"].get(source_key)
            elif source.startswith("step."):
                # Get from previous step result
                parts = source.split(".", 2)
                if len(parts) >= 2:
                    step_id = parts[1]
                    step_input[key] = context["results"].get(step_id, {})
                    if len(parts) == 3:
                        # Get specific field from step result
                        field = parts[2]
                        step_input[key] = (
                            step_input[key].get(field)
                            if isinstance(step_input[key], dict)
                            else None
                        )
            else:
                # Use literal value
                step_input[key] = source

        # If no input mapping specified, use all available data
        if not input_mapping:
            step_input = {
                "input_data": context["input_data"],
                "previous_results": context["results"],
            }

        return step_input

    def _build_dependency_graph(
        self, steps: dict[str, WorkflowStep]
    ) -> dict[str, list[str]]:
        """Build dependency graph for topological sorting."""

        graph = {}

        for step_id, step in steps.items():
            graph[step_id] = step.dependencies

        return graph

    def _topological_sort(self, graph: dict[str, list[str]]) -> list[str]:
        """Perform topological sort to determine execution order."""

        from collections import defaultdict, deque

        # Calculate in-degrees
        in_degree = defaultdict(int)
        for node in graph:
            in_degree[node] = 0

        for node, dependencies in graph.items():
            for dep in dependencies:
                in_degree[node] += 1

        # Initialize queue with nodes having no dependencies
        queue = deque([node for node, degree in in_degree.items() if degree == 0])
        result = []

        while queue:
            node = queue.popleft()
            result.append(node)

            # Update in-degrees of dependent nodes
            for other_node, dependencies in graph.items():
                if node in dependencies:
                    in_degree[other_node] -= 1
                    if in_degree[other_node] == 0:
                        queue.append(other_node)

        # Check for cycles
        if len(result) != len(graph):
            raise ValueError("Circular dependency detected in workflow")

        return result

    def _are_dependencies_satisfied(self, step: WorkflowStep, results: dict) -> bool:
        """Check if all step dependencies are satisfied."""

        for dep_id in step.dependencies:
            if dep_id not in results:
                return False

        return True

    async def _execute_agent_task_via_groq(self, agent: Agent, task: Task) -> dict:
        """
        Execute an agent task by calling the Groq API with the agent's role-specific
        system prompt. Runs the blocking Groq call in a thread-pool to avoid blocking
        the event loop.
        """
        from .groq_service import GroqService

        groq = GroqService()

        input_content: str = ""
        if task.input_data:
            input_content = (
                task.input_data.get("content", "") or str(task.input_data)[:2000]
            )
        if not input_content:
            input_content = task.description or task.title

        def _call_groq():
            return groq.generate_agent_response(
                agent_type=str(agent.type),
                context={
                    "agent_id": str(agent.id),
                    "agent_name": agent.name,
                    "task_id": str(task.id),
                    "task_type": (
                        str(task.task_type) if hasattr(task, "task_type") else "general"
                    ),
                    "requirements": (
                        task.requirements if hasattr(task, "requirements") else {}
                    ),
                },
                user_input=input_content,
            )

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, _call_groq)

        if response.get("error"):
            return {
                "success": False,
                "error": response["error"],
            }

        return {
            "success": True,
            "output": {
                "agent_id": str(agent.id),
                "agent_name": agent.name,
                "task_type": (
                    str(task.task_type) if hasattr(task, "task_type") else "general"
                ),
                "processed_at": timezone.now().isoformat(),
                "result": response.get("content", ""),
                "model": response.get("model", ""),
                "usage": response.get("usage", {}),
            },
        }

    def get_workflow_status(self, workflow_id: str) -> dict | None:
        """Get current status of a running workflow."""

        return self.running_workflows.get(workflow_id)

    def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow."""

        if workflow_id in self.running_workflows:
            context = self.running_workflows[workflow_id]
            context["status"] = "cancelled"
            context["end_time"] = timezone.now()
            return True

        return False
