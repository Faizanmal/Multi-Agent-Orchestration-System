# MCP Integration Services

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any


class MCPToolRegistry:
    """Registry for managing available MCP tools."""

    def __init__(self):
        self.tools = {
            "file_system": {
                "name": "file_system",
                "description": "File system operations (read, write, list)",
                "category": "system",
                "parameters_schema": {
                    "operation": {
                        "type": "string",
                        "enum": ["read", "write", "list", "delete"],
                    },
                    "path": {"type": "string"},
                    "content": {"type": "string", "required": False},
                },
                "capabilities": ["file_read", "file_write", "directory_list"],
            },
            "web_search": {
                "name": "web_search",
                "description": "Search the web for information",
                "category": "search",
                "parameters_schema": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer", "default": 10},
                },
                "capabilities": ["web_search", "information_retrieval"],
            },
            "calculator": {
                "name": "calculator",
                "description": "Perform mathematical calculations",
                "category": "computation",
                "parameters_schema": {
                    "expression": {"type": "string"},
                    "precision": {"type": "integer", "default": 6},
                },
                "capabilities": ["math_calculation", "numerical_computation"],
            },
            "database": {
                "name": "database",
                "description": "Database operations (query, insert, update)",
                "category": "data",
                "parameters_schema": {
                    "operation": {
                        "type": "string",
                        "enum": ["query", "insert", "update", "delete"],
                    },
                    "table": {"type": "string"},
                    "data": {"type": "object", "required": False},
                    "where": {"type": "object", "required": False},
                },
                "capabilities": ["database_query", "data_management"],
            },
            "email": {
                "name": "email",
                "description": "Send and manage emails",
                "category": "communication",
                "parameters_schema": {
                    "operation": {"type": "string", "enum": ["send", "read", "list"]},
                    "to": {"type": "string", "required": False},
                    "subject": {"type": "string", "required": False},
                    "body": {"type": "string", "required": False},
                },
                "capabilities": ["email_send", "email_management"],
            },
            "calendar": {
                "name": "calendar",
                "description": "Calendar and scheduling operations",
                "category": "productivity",
                "parameters_schema": {
                    "operation": {
                        "type": "string",
                        "enum": ["create_event", "list_events", "update_event"],
                    },
                    "title": {"type": "string", "required": False},
                    "start_time": {"type": "string", "required": False},
                    "end_time": {"type": "string", "required": False},
                },
                "capabilities": ["calendar_management", "event_scheduling"],
            },
        }

    def get_available_tools(self) -> list[dict]:
        """Get list of all available tools."""
        return list(self.tools.values())

    def get_tool(self, tool_name: str) -> dict | None:
        """Get specific tool by name."""
        return self.tools.get(tool_name)

    def get_tools_by_category(self, category: str) -> list[dict]:
        """Get tools filtered by category."""
        return [tool for tool in self.tools.values() if tool["category"] == category]

    def get_tools_by_capability(self, capability: str) -> list[dict]:
        """Get tools that have a specific capability."""
        return [
            tool for tool in self.tools.values() if capability in tool["capabilities"]
        ]


class MCPService:
    """Core service for MCP tool execution and management."""

    def __init__(self):
        self.registry = MCPToolRegistry()
        self.executor = ThreadPoolExecutor(max_workers=5)

    def execute_tool(
        self, tool_name: str, parameters: dict, session_id: str | None = None
    ) -> dict:
        """Execute a single MCP tool."""
        start_time = time.time()

        try:
            tool_config = self.registry.get_tool(tool_name)
            if not tool_config:
                return {
                    "success": False,
                    "error": f"Tool {tool_name} not found",
                    "execution_time": time.time() - start_time,
                }

            # Validate parameters (basic validation)
            if not self._validate_parameters(
                parameters, tool_config["parameters_schema"]
            ):
                return {
                    "success": False,
                    "error": "Invalid parameters",
                    "execution_time": time.time() - start_time,
                }

            # Execute tool based on type
            result = self._execute_tool_implementation(tool_name, parameters)

            execution_time = time.time() - start_time

            return {
                "success": True,
                "result": result,
                "execution_time": execution_time,
                "tool_name": tool_name,
                "session_id": session_id,
            }

        except Exception as e:  # noqa: BLE001
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time,
                "tool_name": tool_name,
                "session_id": session_id,
            }

    def execute_tools_sequential(
        self, tools_config: list[dict], session_id: str | None = None
    ) -> list[dict]:
        """Execute multiple tools sequentially."""
        results = []

        for tool_config in tools_config:
            tool_name = tool_config.get("tool_name")
            parameters = tool_config.get("parameters", {})

            result = self.execute_tool(tool_name, parameters, session_id)
            results.append(result)

            # Stop execution if a critical tool fails
            if not result["success"] and tool_config.get("critical", False):
                break

        return results

    def execute_tools_parallel(
        self, tools_config: list[dict], session_id: str | None = None
    ) -> list[dict]:
        """Execute multiple tools in parallel."""
        futures = []

        for tool_config in tools_config:
            tool_name = tool_config.get("tool_name")
            parameters = tool_config.get("parameters", {})

            future = self.executor.submit(
                self.execute_tool, tool_name, parameters, session_id
            )
            futures.append(future)

        results = []
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:  # noqa: BLE001
                results.append({"success": False, "error": str(e), "execution_time": 0})

        return results

    def recommend_tools_for_task(
        self, task_description: str, task_type: str, agent_capabilities: list[str]
    ) -> list[dict]:
        """Recommend tools based on task description and type."""
        recommendations = []

        # Simple keyword-based recommendation (could be enhanced with ML)
        task_lower = task_description.lower()

        for tool in self.registry.get_available_tools():
            score = 0

            # Check category match
            if task_type.lower() in tool["category"].lower():
                score += 0.5

            # Check capability keywords
            for capability in tool["capabilities"]:
                if any(keyword in task_lower for keyword in capability.split("_")):
                    score += 0.3

            # Check description keywords
            if any(
                keyword in task_lower for keyword in tool["description"].lower().split()
            ):
                score += 0.2

            if score > 0:
                recommendations.append(
                    {
                        "tool": tool,
                        "score": score,
                        "reason": f"Matches {task_type} tasks with relevant capabilities",
                    }
                )

        # Sort by score descending
        recommendations.sort(key=lambda x: x["score"], reverse=True)

        return recommendations[:5]  # Return top 5 recommendations

    def execute_tool_with_context(
        self, tool_name: str, parameters: dict, context: dict
    ) -> dict:
        """Execute tool with additional context (agent memory, session data)."""
        # Enhance parameters with context
        enhanced_parameters = parameters.copy()
        enhanced_parameters["_context"] = context

        return self.execute_tool(tool_name, enhanced_parameters)

    def _validate_parameters(self, parameters: dict, schema: dict) -> bool:
        """Basic parameter validation against schema."""
        # This is a simplified validation - in production, use jsonschema library
        for param_name, param_config in schema.items():
            if param_name.startswith("_"):  # Skip internal parameters
                continue

            if param_config.get("required", True) and param_name not in parameters:
                return False

        return True

    def _execute_tool_implementation(self, tool_name: str, parameters: dict) -> Any:
        """Execute the actual tool implementation."""

        if tool_name == "calculator":
            expression = parameters.get("expression", "")
            precision = parameters.get("precision", 6)

            try:
                # Safe evaluation (in production, use more secure evaluation)
                result = eval(expression)  # WARNING: This is unsafe in production
                return {
                    "result": round(float(result), precision),
                    "expression": expression,
                }
            except Exception as e:  # noqa: BLE001
                return {"error": f"Calculation error: {e!s}"}

        elif tool_name == "file_system":
            operation = parameters.get("operation")
            path = parameters.get("path", "")

            if operation == "list":
                import os

                try:
                    files = os.listdir(path if path else ".")
                    return {"files": files, "path": path}
                except Exception as e:  # noqa: BLE001
                    return {"error": f"File system error: {e!s}"}

            return {
                "message": f"File system operation {operation} simulated",
                "path": path,
            }

        elif tool_name == "web_search":
            query = parameters.get("query", "")
            max_results = parameters.get("max_results", 10)

            # Simulated search results
            return {
                "query": query,
                "results": [
                    {
                        "title": f"Result {i+1} for: {query}",
                        "url": f"https://example.com/result-{i+1}",
                    }
                    for i in range(min(max_results, 3))
                ],
            }

        elif tool_name == "database":
            operation = parameters.get("operation")
            table = parameters.get("table", "")

            return {
                "message": f"Database operation {operation} on table {table} simulated",
                "operation": operation,
                "table": table,
            }

        elif tool_name == "email":
            operation = parameters.get("operation")

            if operation == "send":
                to = parameters.get("to", "")
                subject = parameters.get("subject", "")

                return {
                    "message": f"Email sent to {to}",
                    "subject": subject,
                    "status": "sent",
                }

            return {"message": f"Email operation {operation} simulated"}

        elif tool_name == "calendar":
            operation = parameters.get("operation")

            if operation == "create_event":
                title = parameters.get("title", "")
                start_time = parameters.get("start_time", "")

                return {
                    "message": f'Event "{title}" created',
                    "event_id": f"event_{int(time.time())}",
                    "start_time": start_time,
                }

            return {"message": f"Calendar operation {operation} simulated"}

        else:
            return {
                "message": f"Tool {tool_name} executed with parameters",
                "parameters": parameters,
            }
