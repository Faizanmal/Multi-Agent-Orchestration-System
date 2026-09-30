from datetime import timezone

"""
Azure Functions Integration
Serverless agent execution with Azure Functions
"""

import logging
import os
from datetime import datetime
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class AzureFunctionsConfig:
    """Configuration for Azure Functions"""

    # Function App settings
    FUNCTION_APP_NAME = getattr(
        settings, "AZURE_FUNCTION_APP_NAME", os.getenv("AZURE_FUNCTION_APP_NAME")
    )
    FUNCTION_APP_KEY = getattr(
        settings, "AZURE_FUNCTION_APP_KEY", os.getenv("AZURE_FUNCTION_APP_KEY")
    )
    FUNCTION_APP_URL = (
        f"https://{FUNCTION_APP_NAME}.azurewebsites.net" if FUNCTION_APP_NAME else None
    )

    # Function definitions
    FUNCTIONS = {  # noqa: RUF012
        "agent_executor": {
            "path": "/api/ExecuteAgent",
            "method": "POST",
            "timeout": 30,
            "description": "Execute agent task serverlessly",
        },
        "workflow_processor": {
            "path": "/api/ProcessWorkflow",
            "method": "POST",
            "timeout": 60,
            "description": "Process complex workflows",
        },
        "batch_analyzer": {
            "path": "/api/BatchAnalyze",
            "method": "POST",
            "timeout": 120,
            "description": "Batch analysis tasks",
        },
        "data_transformer": {
            "path": "/api/TransformData",
            "method": "POST",
            "timeout": 30,
            "description": "Data transformation operations",
        },
    }


class AzureFunctionsService:
    """
    Service for executing serverless agents via Azure Functions
    """

    def __init__(self):
        """Initialize Azure Functions service"""
        self.function_app_url = AzureFunctionsConfig.FUNCTION_APP_URL
        self.function_app_key = AzureFunctionsConfig.FUNCTION_APP_KEY

        if not self.function_app_url or not self.function_app_key:
            logger.warning("Azure Functions not configured")
            self.enabled = False
        else:
            self.enabled = True
            logger.info(f"Azure Functions service initialized: {self.function_app_url}")

    def execute_agent_function(
        self,
        agent_id: str,
        task_data: dict[str, Any],
        function_name: str = "agent_executor",
        async_execution: bool = False,
    ) -> dict[str, Any]:
        """
        Execute agent task via Azure Function

        Args:
            agent_id: Agent identifier
            task_data: Task data to process
            function_name: Function to invoke
            async_execution: Whether to execute asynchronously

        Returns:
            Execution result
        """
        if not self.enabled:
            return {"error": "Azure Functions not configured"}

        function_config = AzureFunctionsConfig.FUNCTIONS.get(function_name)
        if not function_config:
            return {"error": f"Function {function_name} not found"}

        try:
            url = f"{self.function_app_url}{function_config['path']}"

            headers = {
                "Content-Type": "application/json",
                "x-functions-key": self.function_app_key,
            }

            payload = {
                "agent_id": agent_id,
                "task_data": task_data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "async": async_execution,
            }

            logger.info(
                f"Invoking Azure Function: {function_name} for agent {agent_id}"
            )

            response = requests.post(
                url, json=payload, headers=headers, timeout=function_config["timeout"]
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"Function {function_name} executed successfully")

            return {
                "success": True,
                "function": function_name,
                "result": result,
                "execution_time": response.elapsed.total_seconds(),
            }

        except requests.Timeout:
            logger.error(f"Function {function_name} timed out")
            return {"success": False, "error": "Function execution timed out"}
        except requests.RequestException as e:
            logger.error(f"Function {function_name} request failed: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:  # noqa: BLE001
            logger.error(f"Function {function_name} execution error: {e}")
            return {"success": False, "error": str(e)}

    def execute_workflow(
        self,
        workflow_id: str,
        workflow_data: dict[str, Any],
        callback_url: str | None = None,
    ) -> dict[str, Any]:
        """
        Execute workflow via Azure Function

        Args:
            workflow_id: Workflow identifier
            workflow_data: Workflow definition and inputs
            callback_url: Optional callback URL for async results

        Returns:
            Execution result
        """
        return self.execute_agent_function(
            agent_id=workflow_id,
            task_data={"workflow_data": workflow_data, "callback_url": callback_url},
            function_name="workflow_processor",
            async_execution=callback_url is not None,
        )

    def batch_analyze(
        self, items: list[dict[str, Any]], analysis_type: str = "general"
    ) -> dict[str, Any]:
        """
        Batch analyze items via Azure Function

        Args:
            items: List of items to analyze
            analysis_type: Type of analysis to perform

        Returns:
            Analysis results
        """
        return self.execute_agent_function(
            agent_id="batch_analyzer",
            task_data={"items": items, "analysis_type": analysis_type},
            function_name="batch_analyzer",
            async_execution=len(items) > 100,
        )

    def transform_data(
        self, data: Any, transformation_rules: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Transform data via Azure Function

        Args:
            data: Data to transform
            transformation_rules: Transformation rules

        Returns:
            Transformed data
        """
        return self.execute_agent_function(
            agent_id="data_transformer",
            task_data={"data": data, "rules": transformation_rules},
            function_name="data_transformer",
        )

    def get_function_status(self, execution_id: str) -> dict[str, Any]:
        """
        Get status of async function execution

        Args:
            execution_id: Execution identifier

        Returns:
            Execution status
        """
        if not self.enabled:
            return {"error": "Azure Functions not configured"}

        try:
            url = f"{self.function_app_url}/api/GetExecutionStatus/{execution_id}"

            headers = {"x-functions-key": self.function_app_key}

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            return response.json()

        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to get function status: {e}")
            return {"error": str(e)}

    def list_functions(self) -> list[dict[str, Any]]:
        """List all available functions"""
        return [
            {
                "name": name,
                "description": config["description"],
                "path": config["path"],
                "method": config["method"],
                "timeout": config["timeout"],
            }
            for name, config in AzureFunctionsConfig.FUNCTIONS.items()
        ]


# Singleton instance
_azure_functions_service = None


def get_azure_functions_service() -> AzureFunctionsService:
    """Get or create Azure Functions service singleton"""
    global _azure_functions_service
    if _azure_functions_service is None:
        _azure_functions_service = AzureFunctionsService()
    return _azure_functions_service
