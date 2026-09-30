"""Discord integration provider."""
from typing import Any

import requests

from ..models import APIIntegration
from .base import IntegrationProvider


class DiscordProvider(IntegrationProvider):
    provider_key = "discord"
    display_name = "Discord"
    default_endpoint = "https://discord.com/api/v10"
    auth_type = "bearer"

    @classmethod
    def detect(cls, integration: APIIntegration) -> bool:
        text = f"{integration.name} {integration.description}".lower()
        return "discord" in text

    @classmethod
    def tool_definitions(cls) -> list[dict[str, Any]]:
        return [
            {"name": "discord.list_channels", "description": "List guild text channels", "parameters": {}},
            {"name": "discord.send_message", "description": "Send a message to a channel", "parameters": {"channel_id": "string", "content": "string"}},
            {"name": "discord.read_messages", "description": "Read recent messages from a channel", "parameters": {"channel_id": "string", "limit": "int"}},
        ]

    @classmethod
    def _headers(cls, integration: APIIntegration) -> dict[str, str]:
        token = cls._token(integration)
        if not token:
            raise ValueError("Discord bot token required")
        return {"Authorization": f"Bot {token}", "Content-Type": "application/json"}

    @classmethod
    def _guild_id(cls, integration: APIIntegration) -> str:
        auth = cls._auth(integration)
        gid = auth.get("guild_id") or auth.get("server_id")
        if not gid:
            raise ValueError("guild_id required in authentication JSON")
        return str(gid)

    @classmethod
    def test_connection(cls, integration: APIIntegration) -> dict[str, Any]:
        try:
            resp = requests.get("https://discord.com/api/v10/users/@me", headers=cls._headers(integration), timeout=30)
            if resp.status_code >= 400:
                raise ValueError(resp.text)
            bot = resp.json()
            return {"status": "success", "message": f"Connected as {bot.get('username')}", "data": bot}
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}

    @classmethod
    def execute_tool(cls, integration: APIIntegration, tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
        try:
            headers = cls._headers(integration)
            if tool_name == "discord.list_channels":
                gid = cls._guild_id(integration)
                resp = requests.get(f"https://discord.com/api/v10/guilds/{gid}/channels", headers=headers, timeout=30)
                data = resp.json()
                if resp.status_code >= 400:
                    raise ValueError(str(data))
                channels = [
                    {"id": c["id"], "name": c["name"], "type": c.get("type")}
                    for c in data if c.get("type") == 0
                ]
                return {"status": "success", "channels": channels}

            if tool_name == "discord.send_message":
                channel_id = params.get("channel_id")
                content = params.get("content", "")
                if not channel_id or not content:
                    return {"status": "error", "message": "channel_id and content required"}
                resp = requests.post(
                    f"https://discord.com/api/v10/channels/{channel_id}/messages",
                    headers=headers,
                    json={"content": content[:2000]},
                    timeout=30,
                )
                data = resp.json()
                if resp.status_code >= 400:
                    raise ValueError(str(data))
                return {"status": "success", "message_id": data.get("id")}

            if tool_name == "discord.read_messages":
                channel_id = params.get("channel_id")
                limit = min(int(params.get("limit", 10)), 50)
                if not channel_id:
                    return {"status": "error", "message": "channel_id required"}
                resp = requests.get(
                    f"https://discord.com/api/v10/channels/{channel_id}/messages",
                    headers=headers,
                    params={"limit": limit},
                    timeout=30,
                )
                data = resp.json()
                if resp.status_code >= 400:
                    raise ValueError(str(data))
                messages = [{"author": m["author"]["username"], "content": m["content"], "id": m["id"]} for m in data]
                return {"status": "success", "messages": messages}

            return {"status": "error", "message": f"Unknown Discord tool: {tool_name}"}
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}
