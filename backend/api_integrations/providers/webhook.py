"""Generic outbound webhook integration provider."""
from typing import Any

import requests

from ..models import APIIntegration
from .base import IntegrationProvider


class WebhookProvider(IntegrationProvider):
    provider_key = "webhook"
    display_name = "Webhook"
    default_endpoint = "https://example.com/webhook"
    auth_type = "none"

    @classmethod
    def detect(cls, integration: APIIntegration) -> bool:
        text = f"{integration.name} {integration.description} {integration.type}".lower()
        return "webhook" in text or integration.type == "Webhook"

    @classmethod
    def tool_definitions(cls) -> list[dict[str, Any]]:
        return [
            {"name": "webhook.post", "description": "POST JSON payload to the webhook URL", "parameters": {"payload": "object", "path": "string"}},
            {"name": "webhook.get", "description": "GET from the webhook/base URL", "parameters": {"path": "string"}},
        ]

    @classmethod
    def _url(cls, integration: APIIntegration, path: str = "") -> str:
        base = (integration.endpoint or cls.default_endpoint).rstrip("/")
        if path:
            return f"{base}/{path.lstrip('/')}"
        return base

    @classmethod
    def _headers(cls, integration: APIIntegration) -> dict[str, str]:
        headers = {"Content-Type": "application/json", **(integration.headers or {})}
        token = cls._token(integration)
        if token:
            headers["Authorization"] = f"Bearer {token}"
        auth = cls._auth(integration)
        if auth.get("header_name") and auth.get("header_value"):
            headers[str(auth["header_name"])] = str(auth["header_value"])
        return headers

    @classmethod
    def test_connection(cls, integration: APIIntegration) -> dict[str, Any]:
        try:
            url = cls._url(integration)
            # Prefer HEAD/GET; many webhooks only accept POST — treat 405 as reachable
            resp = requests.get(url, headers=cls._headers(integration), timeout=15)
            if resp.status_code in (200, 201, 202, 204, 401, 403, 405):
                return {"status": "success", "message": f"Endpoint reachable ({resp.status_code})", "data": {"status_code": resp.status_code}}
            return {"status": "error", "message": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}

    @classmethod
    def execute_tool(cls, integration: APIIntegration, tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
        try:
            path = params.get("path", "")
            url = cls._url(integration, path)
            headers = cls._headers(integration)

            if tool_name == "webhook.get":
                resp = requests.get(url, headers=headers, timeout=30)
                try:
                    body = resp.json()
                except Exception:  # noqa: BLE001
                    body = {"raw": resp.text[:2000]}
                return {"status": "success" if resp.ok else "error", "status_code": resp.status_code, "body": body}

            if tool_name == "webhook.post":
                payload = params.get("payload")
                if payload is None:
                    payload = {k: v for k, v in params.items() if k != "path"}
                resp = requests.post(url, headers=headers, json=payload, timeout=30)
                try:
                    body = resp.json()
                except Exception:  # noqa: BLE001
                    body = {"raw": resp.text[:2000]}
                return {"status": "success" if resp.ok else "error", "status_code": resp.status_code, "body": body}

            return {"status": "error", "message": f"Unknown Webhook tool: {tool_name}"}
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}
