"""Microsoft OneDrive (Graph) integration provider."""
from typing import Any

import requests

from ..models import APIIntegration
from .base import IntegrationProvider
from .ms_graph import graph_get, graph_token, test_graph_me


class OneDriveProvider(IntegrationProvider):
    provider_key = "onedrive"
    display_name = "OneDrive"
    default_endpoint = "https://graph.microsoft.com/v1.0"
    auth_type = "oauth"

    @classmethod
    def detect(cls, integration: APIIntegration) -> bool:
        text = f"{integration.name} {integration.description}".lower()
        return "onedrive" in text or "one drive" in text

    @classmethod
    def tool_definitions(cls) -> list[dict[str, Any]]:
        return [
            {"name": "onedrive.list_files", "description": "List files in OneDrive root or a folder", "parameters": {"folder_path": "string"}},
            {"name": "onedrive.search", "description": "Search OneDrive files", "parameters": {"query": "string"}},
            {"name": "onedrive.read_text", "description": "Download text content of a OneDrive file by item ID", "parameters": {"item_id": "string"}},
        ]

    @classmethod
    def test_connection(cls, integration: APIIntegration) -> dict[str, Any]:
        return test_graph_me(cls, integration, "OneDrive")

    @classmethod
    def execute_tool(cls, integration: APIIntegration, tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
        try:
            token = graph_token(cls, integration)

            if tool_name == "onedrive.list_files":
                folder = (params.get("folder_path") or "").strip("/")
                path = "/me/drive/root/children" if not folder else f"/me/drive/root:/{folder}:/children"
                ok, data, err = graph_get(
                    token,
                    path,
                    {"$top": 50, "$select": "id,name,size,lastModifiedDateTime,webUrl,file,folder"},
                )
                return {"status": "success" if ok else "error", "items": data.get("value", []) if ok else [], "message": err}

            if tool_name == "onedrive.search":
                query = params.get("query", "")
                if not query:
                    return {"status": "error", "message": "query required"}
                ok, data, err = graph_get(token, f"/me/drive/root/search(q='{query}')")
                return {"status": "success" if ok else "error", "items": data.get("value", []) if ok else [], "message": err}

            if tool_name == "onedrive.read_text":
                item_id = params.get("item_id")
                if not item_id:
                    return {"status": "error", "message": "item_id required"}
                resp = requests.get(
                    f"https://graph.microsoft.com/v1.0/me/drive/items/{item_id}/content",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=60,
                )
                if not resp.ok:
                    return {"status": "error", "message": resp.text[:300]}
                return {"status": "success", "content": resp.text[:50000], "message": ""}

            return {"status": "error", "message": f"Unknown OneDrive tool: {tool_name}"}
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}
