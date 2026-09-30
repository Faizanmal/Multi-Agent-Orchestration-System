"""GitHub integration provider."""

from typing import Any

import requests

from ..models import APIIntegration
from .base import IntegrationProvider


class GitHubProvider(IntegrationProvider):
    provider_key = "github"
    display_name = "GitHub"
    default_endpoint = "https://api.github.com"
    auth_type = "bearer"

    @classmethod
    def detect(cls, integration: APIIntegration) -> bool:
        text = f"{integration.name} {integration.description}".lower()
        return "github" in text or "git hub" in text

    @classmethod
    def tool_definitions(cls) -> list[dict[str, Any]]:
        return [
            {
                "name": "github.list_repos",
                "description": "List user repositories",
                "parameters": {"limit": "int"},
            },
            {
                "name": "github.list_issues",
                "description": "List open issues for a repo",
                "parameters": {"owner": "string", "repo": "string"},
            },
            {
                "name": "github.create_issue",
                "description": "Create a new issue",
                "parameters": {
                    "owner": "string",
                    "repo": "string",
                    "title": "string",
                    "body": "string",
                },
            },
            {
                "name": "github.get_readme",
                "description": "Get repository README content",
                "parameters": {"owner": "string", "repo": "string"},
            },
        ]

    @classmethod
    def _headers(cls, integration: APIIntegration) -> dict[str, str]:
        token = cls._token(integration)
        if not token:
            raise ValueError("GitHub personal access token required")
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    @classmethod
    def _get(
        cls, integration: APIIntegration, path: str, params: dict | None = None
    ) -> Any:
        resp = requests.get(
            f"https://api.github.com{path}",
            headers=cls._headers(integration),
            params=params or {},
            timeout=30,
        )
        if resp.status_code >= 400:
            raise ValueError(resp.json().get("message", resp.text))
        return resp.json()

    @classmethod
    def _post(cls, integration: APIIntegration, path: str, body: dict) -> Any:
        resp = requests.post(
            f"https://api.github.com{path}",
            headers=cls._headers(integration),
            json=body,
            timeout=30,
        )
        if resp.status_code >= 400:
            raise ValueError(resp.json().get("message", resp.text))
        return resp.json()

    @classmethod
    def test_connection(cls, integration: APIIntegration) -> dict[str, Any]:
        try:
            user = cls._get(integration, "/user")
            return {
                "status": "success",
                "message": f"Connected as {user.get('login')}",
                "data": {"login": user.get("login"), "repos": user.get("public_repos")},
            }
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}

    @classmethod
    def execute_tool(
        cls, integration: APIIntegration, tool_name: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        try:
            if tool_name == "github.list_repos":
                limit = min(int(params.get("limit", 10)), 30)
                repos = cls._get(
                    integration, "/user/repos", {"per_page": limit, "sort": "updated"}
                )
                return {
                    "status": "success",
                    "repos": [
                        {
                            "name": r["name"],
                            "full_name": r["full_name"],
                            "description": r.get("description"),
                            "stars": r.get("stargazers_count"),
                        }
                        for r in repos
                    ],
                }

            if tool_name == "github.list_issues":
                owner, repo = params.get("owner"), params.get("repo")
                if not owner or not repo:
                    return {"status": "error", "message": "owner and repo required"}
                issues = cls._get(
                    integration,
                    f"/repos/{owner}/{repo}/issues",
                    {"state": "open", "per_page": 20},
                )
                return {
                    "status": "success",
                    "issues": [
                        {
                            "number": i["number"],
                            "title": i["title"],
                            "state": i["state"],
                        }
                        for i in issues
                    ],
                }

            if tool_name == "github.create_issue":
                owner, repo = params.get("owner"), params.get("repo")
                title = params.get("title", "")
                if not all([owner, repo, title]):
                    return {
                        "status": "error",
                        "message": "owner, repo, and title required",
                    }
                issue = cls._post(
                    integration,
                    f"/repos/{owner}/{repo}/issues",
                    {
                        "title": title,
                        "body": params.get("body", ""),
                    },
                )
                return {
                    "status": "success",
                    "issue_number": issue.get("number"),
                    "url": issue.get("html_url"),
                }

            if tool_name == "github.get_readme":
                owner, repo = params.get("owner"), params.get("repo")
                if not owner or not repo:
                    return {"status": "error", "message": "owner and repo required"}
                import base64

                data = cls._get(integration, f"/repos/{owner}/{repo}/readme")
                content = base64.b64decode(data.get("content", "")).decode(
                    "utf-8", errors="replace"
                )
                return {"status": "success", "content": content[:8000]}

            return {"status": "error", "message": f"Unknown GitHub tool: {tool_name}"}
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}
