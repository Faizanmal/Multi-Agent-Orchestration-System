"""Base class for third-party integration providers."""

import time
from abc import ABC, abstractmethod
from typing import Any

from ..models import APICallResult, APIIntegration


class IntegrationProvider(ABC):
    """Each provider implements real API calls for one service (Gmail, Slack, etc.)."""

    provider_key: str = ""
    display_name: str = ""
    default_endpoint: str = ""
    auth_type: str = "api_key"

    @classmethod
    @abstractmethod
    def detect(cls, integration: APIIntegration) -> bool:
        """Return True if this provider handles the given integration."""

    @classmethod
    @abstractmethod
    def tool_definitions(cls) -> list[dict[str, Any]]:
        """Tool schemas exposed to agents (name, description, parameters)."""

    @classmethod
    @abstractmethod
    def test_connection(cls, integration: APIIntegration) -> dict[str, Any]:
        """Verify credentials and API access."""

    @classmethod
    @abstractmethod
    def execute_tool(
        cls, integration: APIIntegration, tool_name: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Run a namespaced tool, e.g. gmail.read_inbox."""

    @classmethod
    def sub_agents(cls) -> list[dict[str, Any]]:
        """Sub-agent definitions created when this integration is connected."""
        return [
            {
                "name": f"{cls.display_name} Reader",
                "type": "action",
                "capabilities": [f"{cls.provider_key}.read"],
                "role": "reader",
            },
            {
                "name": f"{cls.display_name} Analyst",
                "type": "reasoning",
                "capabilities": [f"{cls.provider_key}.analyze"],
                "role": "analyst",
            },
            {
                "name": f"{cls.display_name} Writer",
                "type": "action",
                "capabilities": [f"{cls.provider_key}.write"],
                "role": "writer",
            },
        ]

    @classmethod
    def log_call(
        cls,
        integration: APIIntegration,
        status: str,
        response_time: float,
        response_data: dict | None = None,
        error_message: str = "",
        request_data: dict | None = None,
    ) -> None:
        APICallResult.objects.create(
            integration=integration,
            status=status,
            response_time=response_time,
            response_data=response_data,
            error_message=error_message,
            request_data=request_data or {},
        )
        integration.total_calls += 1
        if status == "success":
            prev = integration.avg_response_time or 0
            integration.avg_response_time = (
                prev * (integration.total_calls - 1) + response_time
            ) / integration.total_calls
            integration.success_rate = (
                integration.success_rate * (integration.total_calls - 1) + 100
            ) / integration.total_calls
        integration.save(
            update_fields=["total_calls", "avg_response_time", "success_rate"]
        )

    @classmethod
    def timed_execute(
        cls, integration: APIIntegration, tool_name: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        start = time.time()
        try:
            result = cls.execute_tool(integration, tool_name, params)
            elapsed = (time.time() - start) * 1000
            status = "success" if result.get("status") == "success" else "error"
            cls.log_call(
                integration,
                status,
                elapsed,
                response_data=result,
                error_message=result.get("message", ""),
                request_data={"tool": tool_name, "params": params},
            )
            return result
        except Exception as e:  # noqa: BLE001
            elapsed = (time.time() - start) * 1000
            cls.log_call(
                integration,
                "error",
                elapsed,
                error_message=str(e),
                request_data={"tool": tool_name, "params": params},
            )
            return {"status": "error", "message": str(e)}

    @classmethod
    def _auth(cls, integration: APIIntegration) -> dict[str, Any]:
        return integration.get_auth_data() or {}

    @classmethod
    def _token(cls, integration: APIIntegration) -> str:
        auth = cls._auth(integration)
        for key in ("api_key", "bearer_token", "access_token", "token"):
            if auth.get(key):
                return str(auth[key])
        return ""
