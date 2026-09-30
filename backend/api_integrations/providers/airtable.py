"""Airtable integration provider."""
from typing import Any

import requests

from ..models import APIIntegration
from .base import IntegrationProvider


class AirtableProvider(IntegrationProvider):
    provider_key = "airtable"
    display_name = "Airtable"
    default_endpoint = "https://api.airtable.com/v0"
    auth_type = "bearer"

    @classmethod
    def detect(cls, integration: APIIntegration) -> bool:
        text = f"{integration.name} {integration.description}".lower()
        return "airtable" in text

    @classmethod
    def tool_definitions(cls) -> list[dict[str, Any]]:
        return [
            {"name": "airtable.list_records", "description": "List records from a table", "parameters": {"base_id": "string", "table": "string", "max_records": "int"}},
            {"name": "airtable.create_record", "description": "Create a record in a table", "parameters": {"base_id": "string", "table": "string", "fields": "object"}},
            {"name": "airtable.list_bases", "description": "List accessible Airtable bases", "parameters": {}},
        ]

    @classmethod
    def _headers(cls, integration: APIIntegration) -> dict[str, str]:
        token = cls._token(integration)
        if not token:
            raise ValueError("Airtable personal access token required")
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    @classmethod
    def test_connection(cls, integration: APIIntegration) -> dict[str, Any]:
        try:
            resp = requests.get(
                "https://api.airtable.com/v0/meta/bases",
                headers=cls._headers(integration),
                timeout=20,
            )
            if resp.status_code >= 400:
                return {"status": "error", "message": resp.text[:200]}
            bases = resp.json().get("bases", [])
            return {"status": "success", "message": f"Connected — {len(bases)} base(s) accessible", "data": {"count": len(bases)}}
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}

    @classmethod
    def execute_tool(cls, integration: APIIntegration, tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
        try:
            headers = cls._headers(integration)
            auth = cls._auth(integration)
            default_base = auth.get("base_id") or ""

            if tool_name == "airtable.list_bases":
                resp = requests.get("https://api.airtable.com/v0/meta/bases", headers=headers, timeout=20)
                return {"status": "success" if resp.ok else "error", "bases": resp.json().get("bases", []) if resp.ok else [], "message": "" if resp.ok else resp.text[:200]}

            if tool_name == "airtable.list_records":
                base_id = params.get("base_id") or default_base
                table = params.get("table")
                if not base_id or not table:
                    return {"status": "error", "message": "base_id and table required"}
                max_records = min(int(params.get("max_records", 20)), 100)
                resp = requests.get(
                    f"https://api.airtable.com/v0/{base_id}/{table}",
                    headers=headers,
                    params={"maxRecords": max_records},
                    timeout=30,
                )
                return {"status": "success" if resp.ok else "error", "records": resp.json().get("records", []) if resp.ok else [], "message": "" if resp.ok else resp.text[:200]}

            if tool_name == "airtable.create_record":
                base_id = params.get("base_id") or default_base
                table = params.get("table")
                fields = params.get("fields") or {}
                if not base_id or not table or not isinstance(fields, dict):
                    return {"status": "error", "message": "base_id, table, and fields object required"}
                resp = requests.post(
                    f"https://api.airtable.com/v0/{base_id}/{table}",
                    headers=headers,
                    json={"fields": fields},
                    timeout=30,
                )
                return {"status": "success" if resp.ok else "error", "record": resp.json() if resp.ok else {}, "message": "" if resp.ok else resp.text[:200]}

            return {"status": "error", "message": f"Unknown Airtable tool: {tool_name}"}
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}
