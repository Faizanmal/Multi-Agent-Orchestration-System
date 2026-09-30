"""Dropbox API integration provider."""

from typing import Any

import requests

from ..models import APIIntegration
from .base import IntegrationProvider


class DropboxProvider(IntegrationProvider):
    provider_key = "dropbox"
    display_name = "Dropbox"
    default_endpoint = "https://api.dropboxapi.com/2"
    auth_type = "bearer"

    @classmethod
    def detect(cls, integration: APIIntegration) -> bool:
        text = f"{integration.name} {integration.description}".lower()
        return "dropbox" in text

    @classmethod
    def tool_definitions(cls) -> list[dict[str, Any]]:
        return [
            {
                "name": "dropbox.list_folder",
                "description": "List files in a Dropbox folder",
                "parameters": {"path": "string"},
            },
            {
                "name": "dropbox.search",
                "description": "Search Dropbox files by query",
                "parameters": {"query": "string"},
            },
            {
                "name": "dropbox.download_text",
                "description": "Download a text file from Dropbox",
                "parameters": {"path": "string"},
            },
            {
                "name": "dropbox.get_account",
                "description": "Get current Dropbox account info",
                "parameters": {},
            },
        ]

    @classmethod
    def _headers(
        cls, integration: APIIntegration, content_type: str = "application/json"
    ) -> dict[str, str]:
        token = cls._token(integration)
        if not token:
            raise ValueError("Dropbox access token required")
        h = {"Authorization": f"Bearer {token}"}
        if content_type:
            h["Content-Type"] = content_type
        return h

    @classmethod
    def test_connection(cls, integration: APIIntegration) -> dict[str, Any]:
        try:
            resp = requests.post(
                "https://api.dropboxapi.com/2/users/get_current_account",
                headers=cls._headers(integration),
                json=None,
                timeout=20,
            )
            # Dropbox expects empty body; requests may send "null"
            if resp.status_code >= 400:
                resp = requests.post(
                    "https://api.dropboxapi.com/2/users/get_current_account",
                    headers={"Authorization": f"Bearer {cls._token(integration)}"},
                    timeout=20,
                )
            if resp.status_code >= 400:
                return {"status": "error", "message": resp.text[:300]}
            data = resp.json()
            name = (data.get("name") or {}).get("display_name") or data.get(
                "email", "Dropbox user"
            )
            return {
                "status": "success",
                "message": f"Connected to Dropbox as {name}",
                "data": {"email": data.get("email")},
            }
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}

    @classmethod
    def execute_tool(
        cls, integration: APIIntegration, tool_name: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        try:
            token = cls._token(integration)
            auth = {"Authorization": f"Bearer {token}"}

            if tool_name == "dropbox.get_account":
                resp = requests.post(
                    "https://api.dropboxapi.com/2/users/get_current_account",
                    headers=auth,
                    timeout=20,
                )
                return {
                    "status": "success" if resp.ok else "error",
                    "account": resp.json() if resp.ok else {},
                    "message": "" if resp.ok else resp.text[:300],
                }

            if tool_name == "dropbox.list_folder":
                path = params.get("path", "")
                resp = requests.post(
                    "https://api.dropboxapi.com/2/files/list_folder",
                    headers={**auth, "Content-Type": "application/json"},
                    json={"path": path, "limit": 50},
                    timeout=30,
                )
                data = resp.json() if resp.content else {}
                entries = data.get("entries", []) if resp.ok else []
                return {
                    "status": "success" if resp.ok else "error",
                    "entries": entries,
                    "message": (
                        "" if resp.ok else data.get("error_summary", resp.text[:300])
                    ),
                }

            if tool_name == "dropbox.search":
                query = params.get("query", "")
                if not query:
                    return {"status": "error", "message": "query required"}
                resp = requests.post(
                    "https://api.dropboxapi.com/2/files/search_v2",
                    headers={**auth, "Content-Type": "application/json"},
                    json={"query": query, "options": {"max_results": 20}},
                    timeout=30,
                )
                data = resp.json() if resp.content else {}
                matches = data.get("matches", []) if resp.ok else []
                return {
                    "status": "success" if resp.ok else "error",
                    "matches": matches,
                    "message": (
                        "" if resp.ok else data.get("error_summary", resp.text[:300])
                    ),
                }

            if tool_name == "dropbox.download_text":
                path = params.get("path")
                if not path:
                    return {"status": "error", "message": "path required"}
                import json as _json

                resp = requests.post(
                    "https://content.dropboxapi.com/2/files/download",
                    headers={
                        **auth,
                        "Dropbox-API-Arg": _json.dumps({"path": path}),
                    },
                    timeout=60,
                )
                if not resp.ok:
                    return {"status": "error", "message": resp.text[:300]}
                return {
                    "status": "success",
                    "path": path,
                    "content": resp.text[:50000],
                    "message": "",
                }

            return {"status": "error", "message": f"Unknown Dropbox tool: {tool_name}"}
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}
