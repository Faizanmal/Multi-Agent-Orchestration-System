"""Trello integration provider."""
from typing import Any

import requests

from ..models import APIIntegration
from .base import IntegrationProvider


class TrelloProvider(IntegrationProvider):
    provider_key = "trello"
    display_name = "Trello"
    default_endpoint = "https://api.trello.com/1"
    auth_type = "api_key"

    @classmethod
    def detect(cls, integration: APIIntegration) -> bool:
        text = f"{integration.name} {integration.description}".lower()
        return "trello" in text

    @classmethod
    def tool_definitions(cls) -> list[dict[str, Any]]:
        return [
            {"name": "trello.list_boards", "description": "List Trello boards", "parameters": {}},
            {"name": "trello.list_cards", "description": "List cards on a board", "parameters": {"board_id": "string"}},
            {"name": "trello.create_card", "description": "Create a card on a list", "parameters": {"list_id": "string", "name": "string", "desc": "string"}},
        ]

    @classmethod
    def _auth_params(cls, integration: APIIntegration) -> dict[str, str]:
        auth = cls._auth(integration)
        key = auth.get("api_key") or auth.get("key") or ""
        token = auth.get("token") or auth.get("access_token") or ""
        if not key or not token:
            raise ValueError("Trello api_key and token required")
        return {"key": str(key), "token": str(token)}

    @classmethod
    def test_connection(cls, integration: APIIntegration) -> dict[str, Any]:
        try:
            params = cls._auth_params(integration)
            resp = requests.get("https://api.trello.com/1/members/me", params=params, timeout=20)
            if resp.status_code >= 400:
                return {"status": "error", "message": resp.text[:200]}
            me = resp.json()
            return {"status": "success", "message": f"Connected as {me.get('fullName') or me.get('username')}", "data": me}
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}

    @classmethod
    def execute_tool(cls, integration: APIIntegration, tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
        try:
            auth = cls._auth_params(integration)
            if tool_name == "trello.list_boards":
                resp = requests.get("https://api.trello.com/1/members/me/boards", params={**auth, "fields": "name,url,closed"}, timeout=20)
                boards = resp.json() if resp.ok else []
                return {"status": "success" if resp.ok else "error", "boards": boards, "message": "" if resp.ok else resp.text[:200]}

            if tool_name == "trello.list_cards":
                board_id = params.get("board_id")
                if not board_id:
                    return {"status": "error", "message": "board_id required"}
                resp = requests.get(
                    f"https://api.trello.com/1/boards/{board_id}/cards",
                    params={**auth, "fields": "name,desc,idList,url"},
                    timeout=20,
                )
                return {"status": "success" if resp.ok else "error", "cards": resp.json() if resp.ok else [], "message": "" if resp.ok else resp.text[:200]}

            if tool_name == "trello.create_card":
                list_id = params.get("list_id")
                name = params.get("name", "")
                if not list_id or not name:
                    return {"status": "error", "message": "list_id and name required"}
                resp = requests.post(
                    "https://api.trello.com/1/cards",
                    params={**auth, "idList": list_id, "name": name, "desc": params.get("desc", "")},
                    timeout=20,
                )
                return {"status": "success" if resp.ok else "error", "card": resp.json() if resp.ok else {}, "message": "" if resp.ok else resp.text[:200]}

            return {"status": "error", "message": f"Unknown Trello tool: {tool_name}"}
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}
