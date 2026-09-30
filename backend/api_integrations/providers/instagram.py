"""Instagram Graph API (Meta) integration provider."""
from typing import Any

import requests

from ..models import APIIntegration
from .base import IntegrationProvider

GRAPH_VERSION = "v21.0"
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_VERSION}"


class InstagramProvider(IntegrationProvider):
    provider_key = "instagram"
    display_name = "Instagram"
    default_endpoint = GRAPH_BASE
    auth_type = "bearer"

    @classmethod
    def detect(cls, integration: APIIntegration) -> bool:
        text = f"{integration.name} {integration.description}".lower()
        return "instagram" in text or text.strip() in ("insta", "ig")

    @classmethod
    def tool_definitions(cls) -> list[dict[str, Any]]:
        return [
            {
                "name": "instagram.get_profile",
                "description": "Get Instagram Business/Creator profile info",
                "parameters": {},
            },
            {
                "name": "instagram.list_media",
                "description": "List recent Instagram media posts",
                "parameters": {"limit": "int"},
            },
            {
                "name": "instagram.send_message",
                "description": "Send an Instagram Direct message (requires Messaging API access)",
                "parameters": {"recipient_id": "string", "text": "string"},
            },
        ]

    @classmethod
    def _creds(cls, integration: APIIntegration):
        auth = cls._auth(integration)
        token = cls._token(integration)
        ig_user_id = (
            auth.get("ig_user_id")
            or auth.get("instagram_account_id")
            or auth.get("user_id")
            or ""
        )
        if not token:
            raise ValueError("Instagram access token required")
        if not ig_user_id:
            raise ValueError("Instagram ig_user_id required")
        return str(token), str(ig_user_id)

    @classmethod
    def _headers(cls, token: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    @classmethod
    def test_connection(cls, integration: APIIntegration) -> dict[str, Any]:
        try:
            token, ig_user_id = cls._creds(integration)
            resp = requests.get(
                f"{GRAPH_BASE}/{ig_user_id}",
                headers=cls._headers(token),
                params={"fields": "id,username,name,profile_picture_url,followers_count,media_count"},
                timeout=20,
            )
            if resp.status_code >= 400:
                return {"status": "error", "message": resp.text[:300]}
            data = resp.json()
            username = data.get("username") or ig_user_id
            return {
                "status": "success",
                "message": f"Connected to Instagram @{username}",
                "data": data,
            }
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}

    @classmethod
    def execute_tool(
        cls, integration: APIIntegration, tool_name: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        try:
            token, ig_user_id = cls._creds(integration)
            headers = cls._headers(token)

            if tool_name == "instagram.get_profile":
                resp = requests.get(
                    f"{GRAPH_BASE}/{ig_user_id}",
                    headers=headers,
                    params={
                        "fields": "id,username,name,biography,website,followers_count,follows_count,media_count,profile_picture_url"
                    },
                    timeout=20,
                )
                return {
                    "status": "success" if resp.ok else "error",
                    "profile": resp.json() if resp.ok else {},
                    "message": "" if resp.ok else resp.text[:300],
                }

            if tool_name == "instagram.list_media":
                limit = min(int(params.get("limit", 10)), 50)
                resp = requests.get(
                    f"{GRAPH_BASE}/{ig_user_id}/media",
                    headers=headers,
                    params={
                        "fields": "id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count",
                        "limit": limit,
                    },
                    timeout=30,
                )
                data = resp.json() if resp.content else {}
                return {
                    "status": "success" if resp.ok else "error",
                    "media": data.get("data", []) if resp.ok else [],
                    "message": "" if resp.ok else data.get("error", {}).get("message", resp.text[:300]),
                }

            if tool_name == "instagram.send_message":
                recipient_id = params.get("recipient_id") or params.get("to")
                text = params.get("text", "")
                if not recipient_id or not text:
                    return {"status": "error", "message": "recipient_id and text required"}
                payload = {
                    "recipient": {"id": str(recipient_id)},
                    "message": {"text": text},
                }
                resp = requests.post(
                    f"{GRAPH_BASE}/{ig_user_id}/messages",
                    headers=headers,
                    json=payload,
                    timeout=30,
                )
                data = resp.json() if resp.content else {}
                return {
                    "status": "success" if resp.ok else "error",
                    "result": data,
                    "message": "" if resp.ok else data.get("error", {}).get("message", resp.text[:300]),
                }

            return {"status": "error", "message": f"Unknown Instagram tool: {tool_name}"}
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}
