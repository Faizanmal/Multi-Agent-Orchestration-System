"""Slack integration provider."""

from typing import Any

import requests

from ..models import APIIntegration
from .base import IntegrationProvider


class SlackProvider(IntegrationProvider):
    provider_key = "slack"
    display_name = "Slack"
    default_endpoint = "https://slack.com/api"
    auth_type = "bearer"

    @classmethod
    def detect(cls, integration: APIIntegration) -> bool:
        text = f"{integration.name} {integration.description}".lower()
        return "slack" in text

    @classmethod
    def tool_definitions(cls) -> list[dict[str, Any]]:
        return [
            {
                "name": "slack.list_channels",
                "description": "List Slack channels",
                "parameters": {},
            },
            {
                "name": "slack.post_message",
                "description": "Post a message to a channel",
                "parameters": {"channel": "string", "text": "string"},
            },
            {
                "name": "slack.read_history",
                "description": "Read recent messages from a channel",
                "parameters": {"channel": "string", "limit": "int"},
            },
        ]

    @classmethod
    def _headers(cls, integration: APIIntegration) -> dict[str, str]:
        token = cls._token(integration)
        if not token:
            raise ValueError("Slack bot token required (xoxb-...)")
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    @classmethod
    def _api(cls, integration: APIIntegration, method: str, **kwargs) -> dict[str, Any]:
        url = f"https://slack.com/api/{method}"
        resp = requests.post(
            url, headers=cls._headers(integration), json=kwargs, timeout=30
        )
        data = resp.json()
        if not data.get("ok"):
            raise ValueError(data.get("error", "Slack API error"))
        return data

    @classmethod
    def test_connection(cls, integration: APIIntegration) -> dict[str, Any]:
        try:
            data = cls._api(integration, "auth.test")
            return {
                "status": "success",
                "message": f"Connected to workspace: {data.get('team', 'unknown')}",
                "data": {"team": data.get("team"), "user": data.get("user")},
            }
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}

    @classmethod
    def execute_tool(
        cls, integration: APIIntegration, tool_name: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        try:
            if tool_name == "slack.list_channels":
                data = cls._api(
                    integration,
                    "conversations.list",
                    types="public_channel,private_channel",
                    limit=50,
                )
                channels = [
                    {
                        "id": c["id"],
                        "name": c["name"],
                        "members": c.get("num_members", 0),
                    }
                    for c in data.get("channels", [])
                ]
                return {"status": "success", "channels": channels}

            if tool_name == "slack.post_message":
                channel = params.get("channel", "")
                text = params.get("text", "")
                if not channel or not text:
                    return {"status": "error", "message": "channel and text required"}
                data = cls._api(
                    integration, "chat.postMessage", channel=channel, text=text
                )
                return {"status": "success", "ts": data.get("ts"), "channel": channel}

            if tool_name == "slack.read_history":
                channel = params.get("channel", "")
                limit = min(int(params.get("limit", 10)), 50)
                data = cls._api(
                    integration, "conversations.history", channel=channel, limit=limit
                )
                messages = [
                    {"user": m.get("user"), "text": m.get("text"), "ts": m.get("ts")}
                    for m in data.get("messages", [])
                ]
                return {"status": "success", "messages": messages}

            return {"status": "error", "message": f"Unknown Slack tool: {tool_name}"}
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}
