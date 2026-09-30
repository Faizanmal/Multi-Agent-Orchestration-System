"""OpenAI integration provider."""

from typing import Any

import requests

from ..models import APIIntegration
from .base import IntegrationProvider


class OpenAIProvider(IntegrationProvider):
    provider_key = "openai"
    display_name = "OpenAI"
    default_endpoint = "https://api.openai.com/v1"
    auth_type = "api_key"

    @classmethod
    def detect(cls, integration: APIIntegration) -> bool:
        text = f"{integration.name} {integration.description}".lower()
        return "openai" in text or "gpt" in text

    @classmethod
    def tool_definitions(cls) -> list[dict[str, Any]]:
        return [
            {
                "name": "openai.chat",
                "description": "Send a chat completion request",
                "parameters": {"messages": "array", "model": "string"},
            },
            {
                "name": "openai.list_models",
                "description": "List available models",
                "parameters": {},
            },
        ]

    @classmethod
    def _headers(cls, integration: APIIntegration) -> dict[str, str]:
        token = cls._token(integration)
        if not token:
            raise ValueError("OpenAI API key required (sk-...)")
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    @classmethod
    def test_connection(cls, integration: APIIntegration) -> dict[str, Any]:
        try:
            resp = requests.get(
                "https://api.openai.com/v1/models",
                headers=cls._headers(integration),
                timeout=30,
            )
            if resp.status_code >= 400:
                raise ValueError(resp.json().get("error", {}).get("message", resp.text))
            models = [m["id"] for m in resp.json().get("data", [])[:5]]
            return {
                "status": "success",
                "message": "OpenAI API connected",
                "data": {"sample_models": models},
            }
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}

    @classmethod
    def execute_tool(
        cls, integration: APIIntegration, tool_name: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        try:
            if tool_name == "openai.list_models":
                resp = requests.get(
                    "https://api.openai.com/v1/models",
                    headers=cls._headers(integration),
                    timeout=30,
                )
                data = resp.json()
                return {
                    "status": "success",
                    "models": [m["id"] for m in data.get("data", [])[:20]],
                }

            if tool_name == "openai.chat":
                messages = params.get(
                    "messages",
                    [{"role": "user", "content": params.get("prompt", "Hello")}],
                )
                model = params.get("model", "gpt-4o-mini")
                resp = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=cls._headers(integration),
                    json={"model": model, "messages": messages, "max_tokens": 1024},
                    timeout=60,
                )
                if resp.status_code >= 400:
                    raise ValueError(
                        resp.json().get("error", {}).get("message", resp.text)
                    )
                content = resp.json()["choices"][0]["message"]["content"]
                return {"status": "success", "content": content, "model": model}

            return {"status": "error", "message": f"Unknown OpenAI tool: {tool_name}"}
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}
