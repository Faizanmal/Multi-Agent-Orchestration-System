"""Linear issue tracker integration provider."""

from typing import Any

import requests

from ..models import APIIntegration
from .base import IntegrationProvider


class LinearProvider(IntegrationProvider):
    provider_key = "linear"
    display_name = "Linear"
    default_endpoint = "https://api.linear.app/graphql"
    auth_type = "api_key"

    @classmethod
    def detect(cls, integration: APIIntegration) -> bool:
        text = f"{integration.name} {integration.description}".lower()
        return "linear" in text

    @classmethod
    def tool_definitions(cls) -> list[dict[str, Any]]:
        return [
            {
                "name": "linear.viewer",
                "description": "Get authenticated Linear user",
                "parameters": {},
            },
            {
                "name": "linear.list_issues",
                "description": "List recent Linear issues",
                "parameters": {"first": "int"},
            },
            {
                "name": "linear.create_issue",
                "description": "Create a Linear issue",
                "parameters": {
                    "team_id": "string",
                    "title": "string",
                    "description": "string",
                },
            },
        ]

    @classmethod
    def _headers(cls, integration: APIIntegration) -> dict[str, str]:
        token = cls._token(integration)
        if not token:
            raise ValueError("Linear API key required")
        return {"Authorization": token, "Content-Type": "application/json"}

    @classmethod
    def _gql(
        cls,
        integration: APIIntegration,
        query: str,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        resp = requests.post(
            "https://api.linear.app/graphql",
            headers=cls._headers(integration),
            json={"query": query, "variables": variables or {}},
            timeout=30,
        )
        data = resp.json()
        if data.get("errors"):
            raise ValueError(data["errors"][0].get("message", "Linear GraphQL error"))
        return data.get("data") or {}

    @classmethod
    def test_connection(cls, integration: APIIntegration) -> dict[str, Any]:
        try:
            data = cls._gql(integration, "{ viewer { id name email } }")
            viewer = data.get("viewer") or {}
            return {
                "status": "success",
                "message": f"Connected as {viewer.get('name') or viewer.get('email')}",
                "data": viewer,
            }
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}

    @classmethod
    def execute_tool(
        cls, integration: APIIntegration, tool_name: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        try:
            if tool_name == "linear.viewer":
                data = cls._gql(integration, "{ viewer { id name email } }")
                return {"status": "success", "viewer": data.get("viewer")}

            if tool_name == "linear.list_issues":
                first = min(int(params.get("first", 20)), 50)
                data = cls._gql(
                    integration,
                    """
                    query($first: Int!) {
                      issues(first: $first) {
                        nodes { id identifier title state { name } url }
                      }
                    }
                    """,
                    {"first": first},
                )
                return {
                    "status": "success",
                    "issues": (data.get("issues") or {}).get("nodes", []),
                }

            if tool_name == "linear.create_issue":
                team_id = params.get("team_id")
                title = params.get("title", "")
                if not team_id or not title:
                    return {"status": "error", "message": "team_id and title required"}
                data = cls._gql(
                    integration,
                    """
                    mutation($teamId: String!, $title: String!, $description: String) {
                      issueCreate(input: { teamId: $teamId, title: $title, description: $description }) {
                        success
                        issue { id identifier title url }
                      }
                    }
                    """,
                    {
                        "teamId": team_id,
                        "title": title,
                        "description": params.get("description", ""),
                    },
                )
                created = data.get("issueCreate") or {}
                return {
                    "status": "success" if created.get("success") else "error",
                    "issue": created.get("issue"),
                }

            return {"status": "error", "message": f"Unknown Linear tool: {tool_name}"}
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}
