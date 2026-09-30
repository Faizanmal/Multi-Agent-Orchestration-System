"""Telegram Bot API integration provider."""
from typing import Any

import requests

from ..models import APIIntegration
from .base import IntegrationProvider


class TelegramProvider(IntegrationProvider):
    provider_key = "telegram"
    display_name = "Telegram"
    default_endpoint = "https://api.telegram.org"
    auth_type = "api_key"

    @classmethod
    def detect(cls, integration: APIIntegration) -> bool:
        text = f"{integration.name} {integration.description}".lower()
        return "telegram" in text

    @classmethod
    def tool_definitions(cls) -> list[dict[str, Any]]:
        return [
            {"name": "telegram.get_me", "description": "Get bot identity", "parameters": {}},
            {"name": "telegram.send_message", "description": "Send a message to a chat", "parameters": {"chat_id": "string", "text": "string"}},
            {"name": "telegram.get_updates", "description": "Read recent bot updates/messages", "parameters": {"limit": "int"}},
        ]

    @classmethod
    def _base(cls, integration: APIIntegration) -> str:
        token = cls._token(integration)
        if not token:
            raise ValueError("Telegram bot token required")
        return f"https://api.telegram.org/bot{token}"

    @classmethod
    def test_connection(cls, integration: APIIntegration) -> dict[str, Any]:
        try:
            resp = requests.get(f"{cls._base(integration)}/getMe", timeout=20)
            data = resp.json()
            if not data.get("ok"):
                return {"status": "error", "message": data.get("description", "Telegram auth failed")}
            bot = data.get("result", {})
            return {
                "status": "success",
                "message": f"Connected as @{bot.get('username', 'bot')}",
                "data": bot,
            }
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}

    @classmethod
    def execute_tool(cls, integration: APIIntegration, tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
        try:
            base = cls._base(integration)
            if tool_name == "telegram.get_me":
                data = requests.get(f"{base}/getMe", timeout=20).json()
                return {"status": "success" if data.get("ok") else "error", "bot": data.get("result"), "message": data.get("description", "")}

            if tool_name == "telegram.send_message":
                chat_id = params.get("chat_id")
                text = params.get("text", "")
                if not chat_id or not text:
                    return {"status": "error", "message": "chat_id and text required"}
                data = requests.post(
                    f"{base}/sendMessage",
                    json={"chat_id": chat_id, "text": text},
                    timeout=20,
                ).json()
                return {"status": "success" if data.get("ok") else "error", "result": data.get("result"), "message": data.get("description", "")}

            if tool_name == "telegram.get_updates":
                limit = min(int(params.get("limit", 20)), 100)
                data = requests.get(f"{base}/getUpdates", params={"limit": limit}, timeout=20).json()
                updates = data.get("result", []) if data.get("ok") else []
                return {"status": "success" if data.get("ok") else "error", "updates": updates, "message": data.get("description", "")}

            return {"status": "error", "message": f"Unknown Telegram tool: {tool_name}"}
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}
