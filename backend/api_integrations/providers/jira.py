"""Jira Cloud integration provider."""

from typing import Any

import requests

from ..models import APIIntegration
from .base import IntegrationProvider


class JiraProvider(IntegrationProvider):
    provider_key = "jira"
    display_name = "Jira"
    default_endpoint = "https://your-domain.atlassian.net"
    auth_type = "basic"

    @classmethod
    def detect(cls, integration: APIIntegration) -> bool:
        text = f"{integration.name} {integration.description} {integration.endpoint}".lower()
        return "jira" in text or "atlassian" in text

    @classmethod
    def tool_definitions(cls) -> list[dict[str, Any]]:
        return [
            {
                "name": "jira.list_projects",
                "description": "List Jira projects",
                "parameters": {},
            },
            {
                "name": "jira.list_issues",
                "description": "Search Jira issues with JQL",
                "parameters": {"jql": "string"},
            },
            {
                "name": "jira.create_issue",
                "description": "Create a Jira issue",
                "parameters": {
                    "project_key": "string",
                    "summary": "string",
                    "description": "string",
                },
            },
        ]

    @classmethod
    def _base_url(cls, integration: APIIntegration) -> str:
        return (
            integration.endpoint.rstrip("/")
            if integration.endpoint
            else "https://your-domain.atlassian.net"
        )

    @classmethod
    def _auth(cls, integration: APIIntegration):
        auth = super()._auth(integration)
        email = auth.get("email") or auth.get("username", "")
        token = auth.get("api_key") or auth.get("token") or cls._token(integration)
        if not email or not token:
            raise ValueError("Jira requires email + API token in authentication JSON")
        return (email, token)

    @classmethod
    def test_connection(cls, integration: APIIntegration) -> dict[str, Any]:
        try:
            resp = requests.get(
                f"{cls._base_url(integration)}/rest/api/3/myself",
                auth=cls._auth(integration),
                timeout=30,
            )
            if resp.status_code >= 400:
                raise ValueError(resp.text)
            user = resp.json()
            return {
                "status": "success",
                "message": f"Connected as {user.get('displayName')}",
                "data": {"accountId": user.get("accountId")},
            }
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}

    @classmethod
    def execute_tool(
        cls, integration: APIIntegration, tool_name: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        try:
            base = cls._base_url(integration)
            auth = cls._auth(integration)
            if tool_name == "jira.list_projects":
                resp = requests.get(
                    f"{base}/rest/api/3/project/search", auth=auth, timeout=30
                )
                data = resp.json()
                if resp.status_code >= 400:
                    raise ValueError(data.get("errorMessages", resp.text))
                projects = [
                    {"key": p["key"], "name": p["name"]} for p in data.get("values", [])
                ]
                return {"status": "success", "projects": projects}

            if tool_name == "jira.list_issues":
                jql = params.get(
                    "jql", "assignee = currentUser() ORDER BY updated DESC"
                )
                resp = requests.get(
                    f"{base}/rest/api/3/search",
                    auth=auth,
                    params={
                        "jql": jql,
                        "maxResults": min(int(params.get("limit", 20)), 50),
                    },
                    timeout=30,
                )
                data = resp.json()
                if resp.status_code >= 400:
                    raise ValueError(data.get("errorMessages", resp.text))
                issues = [
                    {
                        "key": i["key"],
                        "summary": i["fields"]["summary"],
                        "status": i["fields"]["status"]["name"],
                    }
                    for i in data.get("issues", [])
                ]
                return {"status": "success", "issues": issues, "jql": jql}

            if tool_name == "jira.create_issue":
                project_key = params.get("project_key")
                summary = params.get("summary", "")
                if not project_key or not summary:
                    return {
                        "status": "error",
                        "message": "project_key and summary required",
                    }
                body = {
                    "fields": {
                        "project": {"key": project_key},
                        "summary": summary,
                        "description": {
                            "type": "doc",
                            "version": 1,
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": params.get("description", ""),
                                        }
                                    ],
                                }
                            ],
                        },
                        "issuetype": {"name": "Task"},
                    }
                }
                resp = requests.post(
                    f"{base}/rest/api/3/issue", auth=auth, json=body, timeout=30
                )
                data = resp.json()
                if resp.status_code >= 400:
                    raise ValueError(data.get("errorMessages", resp.text))
                return {
                    "status": "success",
                    "issue_key": data.get("key"),
                    "id": data.get("id"),
                }

            return {"status": "error", "message": f"Unknown Jira tool: {tool_name}"}
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}
