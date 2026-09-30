"""Supabase (Postgres REST) integration provider."""

from typing import Any

import requests

from ..models import APIIntegration
from .base import IntegrationProvider


class SupabaseProvider(IntegrationProvider):
    provider_key = "supabase"
    display_name = "Supabase"
    default_endpoint = "https://YOUR_PROJECT.supabase.co"
    auth_type = "bearer"

    @classmethod
    def detect(cls, integration: APIIntegration) -> bool:
        text = f"{integration.name} {integration.description} {integration.endpoint}".lower()
        return "supabase" in text

    @classmethod
    def tool_definitions(cls) -> list[dict[str, Any]]:
        return [
            {
                "name": "supabase.list_rows",
                "description": "List rows from a table via PostgREST",
                "parameters": {"table": "string", "limit": "int", "select": "string"},
            },
            {
                "name": "supabase.insert_row",
                "description": "Insert a JSON row into a table",
                "parameters": {"table": "string", "row": "object"},
            },
            {
                "name": "supabase.query",
                "description": "Filter rows with a simple eq filter",
                "parameters": {
                    "table": "string",
                    "column": "string",
                    "value": "string",
                    "limit": "int",
                },
            },
        ]

    @classmethod
    def _base_and_key(cls, integration: APIIntegration):
        auth = cls._auth(integration)
        base = (integration.endpoint or "").rstrip("/")
        if not base or "YOUR_PROJECT" in base:
            base = (auth.get("project_url") or "").rstrip("/")
        key = (
            auth.get("service_role_key")
            or auth.get("anon_key")
            or cls._token(integration)
        )
        if not base:
            raise ValueError("Supabase project URL required as endpoint")
        if not key:
            raise ValueError("Supabase anon or service_role key required")
        return base, str(key)

    @classmethod
    def _headers(cls, key: str) -> dict[str, str]:
        return {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    @classmethod
    def test_connection(cls, integration: APIIntegration) -> dict[str, Any]:
        try:
            base, key = cls._base_and_key(integration)
            # Hit REST root — 200 or 404 with JSON still means reachable + auth accepted often
            resp = requests.get(
                f"{base}/rest/v1/", headers=cls._headers(key), timeout=20
            )
            if resp.status_code in (200, 404) or resp.headers.get(
                "content-type", ""
            ).startswith("application/openapi"):
                return {
                    "status": "success",
                    "message": f"Connected to Supabase at {base}",
                }
            if resp.status_code == 401:
                return {"status": "error", "message": "Invalid Supabase API key"}
            # Some projects return 200 on /rest/v1 with openapi
            if resp.ok:
                return {
                    "status": "success",
                    "message": f"Connected to Supabase at {base}",
                }
            return {"status": "error", "message": resp.text[:300]}
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}

    @classmethod
    def execute_tool(
        cls, integration: APIIntegration, tool_name: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        try:
            base, key = cls._base_and_key(integration)
            headers = cls._headers(key)
            table = params.get("table")
            limit = min(int(params.get("limit", 20)), 100)

            if tool_name == "supabase.list_rows":
                if not table:
                    return {"status": "error", "message": "table required"}
                select = params.get("select") or "*"
                resp = requests.get(
                    f"{base}/rest/v1/{table}",
                    headers=headers,
                    params={"select": select, "limit": limit},
                    timeout=30,
                )
                return {
                    "status": "success" if resp.ok else "error",
                    "rows": resp.json() if resp.ok else [],
                    "message": "" if resp.ok else resp.text[:300],
                }

            if tool_name == "supabase.query":
                if not table or not params.get("column"):
                    return {"status": "error", "message": "table and column required"}
                col = params["column"]
                val = params.get("value", "")
                resp = requests.get(
                    f"{base}/rest/v1/{table}",
                    headers=headers,
                    params={"select": "*", "limit": limit, col: f"eq.{val}"},
                    timeout=30,
                )
                return {
                    "status": "success" if resp.ok else "error",
                    "rows": resp.json() if resp.ok else [],
                    "message": "" if resp.ok else resp.text[:300],
                }

            if tool_name == "supabase.insert_row":
                if not table:
                    return {"status": "error", "message": "table required"}
                row = params.get("row") or params.get("data") or {}
                if isinstance(row, str):
                    import json

                    row = json.loads(row)
                resp = requests.post(
                    f"{base}/rest/v1/{table}",
                    headers=headers,
                    json=row,
                    timeout=30,
                )
                return {
                    "status": "success" if resp.ok else "error",
                    "result": resp.json() if resp.content else {},
                    "message": "" if resp.ok else resp.text[:300],
                }

            return {"status": "error", "message": f"Unknown Supabase tool: {tool_name}"}
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}
