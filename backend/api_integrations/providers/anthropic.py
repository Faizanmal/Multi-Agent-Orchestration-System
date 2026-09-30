"""Anthropic Claude integration provider."""
from typing import Any

import requests

from ..models import APIIntegration
from .base import IntegrationProvider


class AnthropicProvider(IntegrationProvider):
    provider_key = "anthropic"
    display_name = "Anthropic"
    default_endpoint = "https://api.anthropic.com/v1"
    auth_type = "api_key"

    @classmethod
    def detect(cls, integration: APIIntegration) -> bool:
        text = f"{integration.name} {integration.description}".lower()
        return "anthropic" in text or "claude" in text

    @classmethod
    def tool_definitions(cls) -> list[dict[str, Any]]:
        return [
            {
                "name": "anthropic.chat",
                "description": "Send a message to Claude",
                "parameters": {"prompt": "string", "model": "string"},
            },
        ]

    @classmethod
    def _headers(cls, integration: APIIntegration) -> dict[str, str]:
        token = cls._token(integration)
        if not token:
            raise ValueError("Anthropic API key required (sk-ant-...)")
        return {
            "x-api-key": token,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

    @classmethod
    def test_connection(cls, integration: APIIntegration) -> dict[str, Any]:
        try:
            result = cls.execute_tool(integration, "anthropic.chat", {"prompt": "Reply with OK only.", "model": "claude-3-5-haiku-20241022"})
            if result.get("status") == "success":
                return {"status": "success", "message": "Anthropic API connected", "data": result}
            return result
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}

    @classmethod
    def execute_tool(cls, integration: APIIntegration, tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
        try:
            if tool_name == "anthropic.chat":
                prompt = params.get("prompt", "Hello")
                model = params.get("model", "claude-3-5-haiku-20241022")
                resp = requests.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=cls._headers(integration),
                    json={
                        "model": model,
                        "max_tokens": 1024,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                    timeout=60,
                )
                if resp.status_code >= 400:
                    raise ValueError(resp.json().get("error", {}).get("message", resp.text))
                content = resp.json()["content"][0]["text"]
                return {"status": "success", "content": content, "model": model}
            return {"status": "error", "message": f"Unknown Anthropic tool: {tool_name}"}
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}
