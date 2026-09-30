"""Notion integration provider."""

from typing import Any

import requests

from ..models import APIIntegration
from .base import IntegrationProvider


class NotionProvider(IntegrationProvider):
    provider_key = "notion"
    display_name = "Notion"
    default_endpoint = "https://api.notion.com/v1"
    auth_type = "bearer"

    @classmethod
    def detect(cls, integration: APIIntegration) -> bool:
        text = f"{integration.name} {integration.description}".lower()
        return "notion" in text

    @classmethod
    def tool_definitions(cls) -> list[dict[str, Any]]:
        return [
            {
                "name": "notion.search",
                "description": "Search Notion pages and databases",
                "parameters": {"query": "string"},
            },
            {
                "name": "notion.get_page",
                "description": "Get a Notion page by ID",
                "parameters": {"page_id": "string"},
            },
            {
                "name": "notion.create_page",
                "description": "Create a page in a database",
                "parameters": {
                    "database_id": "string",
                    "title": "string",
                    "content": "string",
                },
            },
        ]

    @classmethod
    def _headers(cls, integration: APIIntegration) -> dict[str, str]:
        token = cls._token(integration)
        if not token:
            raise ValueError("Notion integration token required (secret_...)")
        return {
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }

    @classmethod
    def test_connection(cls, integration: APIIntegration) -> dict[str, Any]:
        try:
            resp = requests.get(
                "https://api.notion.com/v1/users/me",
                headers=cls._headers(integration),
                timeout=30,
            )
            if resp.status_code >= 400:
                raise ValueError(resp.json().get("message", resp.text))
            user = resp.json()
            return {
                "status": "success",
                "message": f"Connected as {user.get('name', 'Notion user')}",
                "data": user,
            }
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}

    @classmethod
    def execute_tool(
        cls, integration: APIIntegration, tool_name: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        try:
            headers = cls._headers(integration)
            if tool_name == "notion.search":
                body = {
                    "query": params.get("query", ""),
                    "page_size": min(int(params.get("limit", 10)), 25),
                }
                resp = requests.post(
                    "https://api.notion.com/v1/search",
                    headers=headers,
                    json=body,
                    timeout=30,
                )
                data = resp.json()
                if resp.status_code >= 400:
                    raise ValueError(data.get("message", resp.text))
                results = [
                    {
                        "id": r["id"],
                        "title": cls._title(r),
                        "type": r.get("object"),
                        "url": r.get("url"),
                    }
                    for r in data.get("results", [])
                ]
                return {"status": "success", "results": results}

            if tool_name == "notion.get_page":
                page_id = params.get("page_id")
                if not page_id:
                    return {"status": "error", "message": "page_id required"}
                resp = requests.get(
                    f"https://api.notion.com/v1/pages/{page_id}",
                    headers=headers,
                    timeout=30,
                )
                data = resp.json()
                if resp.status_code >= 400:
                    raise ValueError(data.get("message", resp.text))
                return {"status": "success", "page": data}

            if tool_name == "notion.create_page":
                db_id = params.get("database_id")
                title = params.get("title", "Untitled")
                content = params.get("content", "")
                if not db_id:
                    return {"status": "error", "message": "database_id required"}
                body = {
                    "parent": {"database_id": db_id},
                    "properties": {"Name": {"title": [{"text": {"content": title}}]}},
                    "children": [
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [{"text": {"content": content}}]
                            },
                        }
                    ],
                }
                resp = requests.post(
                    "https://api.notion.com/v1/pages",
                    headers=headers,
                    json=body,
                    timeout=30,
                )
                data = resp.json()
                if resp.status_code >= 400:
                    raise ValueError(data.get("message", resp.text))
                return {
                    "status": "success",
                    "page_id": data.get("id"),
                    "url": data.get("url"),
                }

            return {"status": "error", "message": f"Unknown Notion tool: {tool_name}"}
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}

    @classmethod
    def _title(cls, obj: dict) -> str:
        props = obj.get("properties", {})
        for val in props.values():
            if val.get("type") == "title":
                parts = val.get("title", [])
                return "".join(p.get("plain_text", "") for p in parts) or "Untitled"
        return obj.get("id", "Untitled")
