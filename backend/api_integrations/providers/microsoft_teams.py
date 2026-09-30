"""Microsoft Teams (Graph) integration provider."""
from typing import Any

from ..models import APIIntegration
from .base import IntegrationProvider
from .ms_graph import graph_get, graph_post, graph_token, test_graph_me


class MicrosoftTeamsProvider(IntegrationProvider):
    provider_key = "microsoft_teams"
    display_name = "Microsoft Teams"
    default_endpoint = "https://graph.microsoft.com/v1.0"
    auth_type = "oauth"

    @classmethod
    def detect(cls, integration: APIIntegration) -> bool:
        text = f"{integration.name} {integration.description}".lower()
        return "microsoft teams" in text or "ms teams" in text or (
            "teams" in text and "microsoft" in text
        ) or text.strip() in ("teams", "microsoft_teams")

    @classmethod
    def tool_definitions(cls) -> list[dict[str, Any]]:
        return [
            {"name": "microsoft_teams.list_chats", "description": "List recent Teams chats", "parameters": {"top": "int"}},
            {"name": "microsoft_teams.list_joined_teams", "description": "List Teams the user has joined", "parameters": {}},
            {"name": "microsoft_teams.send_channel_message", "description": "Post a message to a Teams channel", "parameters": {"team_id": "string", "channel_id": "string", "text": "string"}},
        ]

    @classmethod
    def test_connection(cls, integration: APIIntegration) -> dict[str, Any]:
        return test_graph_me(cls, integration, "Microsoft Teams")

    @classmethod
    def execute_tool(cls, integration: APIIntegration, tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
        try:
            token = graph_token(cls, integration)
            top = min(int(params.get("top", 20)), 50)

            if tool_name == "microsoft_teams.list_chats":
                ok, data, err = graph_get(token, "/me/chats", {"$top": top})
                return {"status": "success" if ok else "error", "chats": data.get("value", []) if ok else [], "message": err}

            if tool_name == "microsoft_teams.list_joined_teams":
                ok, data, err = graph_get(token, "/me/joinedTeams")
                return {"status": "success" if ok else "error", "teams": data.get("value", []) if ok else [], "message": err}

            if tool_name == "microsoft_teams.send_channel_message":
                team_id = params.get("team_id")
                channel_id = params.get("channel_id")
                text = params.get("text", "")
                if not team_id or not channel_id or not text:
                    return {"status": "error", "message": "team_id, channel_id, and text required"}
                ok, data, err = graph_post(
                    token,
                    f"/teams/{team_id}/channels/{channel_id}/messages",
                    {"body": {"contentType": "text", "content": text}},
                )
                return {"status": "success" if ok else "error", "result": data if ok else {}, "message": err}

            return {"status": "error", "message": f"Unknown Teams tool: {tool_name}"}
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}
