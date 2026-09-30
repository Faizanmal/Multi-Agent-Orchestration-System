"""HubSpot CRM integration provider."""
from typing import Any

import requests

from ..models import APIIntegration
from .base import IntegrationProvider


class HubSpotProvider(IntegrationProvider):
    provider_key = "hubspot"
    display_name = "HubSpot"
    default_endpoint = "https://api.hubapi.com"
    auth_type = "api_key"

    @classmethod
    def detect(cls, integration: APIIntegration) -> bool:
        text = f"{integration.name} {integration.description}".lower()
        return "hubspot" in text or "hub spot" in text

    @classmethod
    def tool_definitions(cls) -> list[dict[str, Any]]:
        return [
            {"name": "hubspot.list_contacts", "description": "List HubSpot contacts", "parameters": {"limit": "int"}},
            {"name": "hubspot.create_contact", "description": "Create a HubSpot contact", "parameters": {"email": "string", "firstname": "string", "lastname": "string"}},
            {"name": "hubspot.search_contacts", "description": "Search contacts by email", "parameters": {"email": "string"}},
        ]

    @classmethod
    def _headers(cls, integration: APIIntegration) -> dict[str, str]:
        token = cls._token(integration)
        if not token:
            raise ValueError("HubSpot private app token required")
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    @classmethod
    def test_connection(cls, integration: APIIntegration) -> dict[str, Any]:
        try:
            resp = requests.get(
                "https://api.hubapi.com/crm/v3/objects/contacts",
                headers=cls._headers(integration),
                params={"limit": 1},
                timeout=20,
            )
            if resp.status_code >= 400:
                return {"status": "error", "message": resp.text[:200]}
            return {"status": "success", "message": "Connected to HubSpot CRM", "data": {"total": resp.json().get("total")}}
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}

    @classmethod
    def execute_tool(cls, integration: APIIntegration, tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
        try:
            headers = cls._headers(integration)
            if tool_name == "hubspot.list_contacts":
                limit = min(int(params.get("limit", 20)), 100)
                resp = requests.get(
                    "https://api.hubapi.com/crm/v3/objects/contacts",
                    headers=headers,
                    params={"limit": limit, "properties": "email,firstname,lastname"},
                    timeout=20,
                )
                return {"status": "success" if resp.ok else "error", "contacts": resp.json().get("results", []) if resp.ok else [], "message": "" if resp.ok else resp.text[:200]}

            if tool_name == "hubspot.create_contact":
                email = params.get("email")
                if not email:
                    return {"status": "error", "message": "email required"}
                props = {"email": email}
                for key in ("firstname", "lastname", "phone", "company"):
                    if params.get(key):
                        props[key] = params[key]
                resp = requests.post(
                    "https://api.hubapi.com/crm/v3/objects/contacts",
                    headers=headers,
                    json={"properties": props},
                    timeout=20,
                )
                return {"status": "success" if resp.ok else "error", "contact": resp.json() if resp.ok else {}, "message": "" if resp.ok else resp.text[:200]}

            if tool_name == "hubspot.search_contacts":
                email = params.get("email")
                if not email:
                    return {"status": "error", "message": "email required"}
                resp = requests.post(
                    "https://api.hubapi.com/crm/v3/objects/contacts/search",
                    headers=headers,
                    json={
                        "filterGroups": [{
                            "filters": [{"propertyName": "email", "operator": "EQ", "value": email}]
                        }],
                        "properties": ["email", "firstname", "lastname"],
                    },
                    timeout=20,
                )
                return {"status": "success" if resp.ok else "error", "contacts": resp.json().get("results", []) if resp.ok else [], "message": "" if resp.ok else resp.text[:200]}

            return {"status": "error", "message": f"Unknown HubSpot tool: {tool_name}"}
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}
