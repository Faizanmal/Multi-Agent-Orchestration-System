"""WhatsApp Cloud API (Meta) integration provider."""

from typing import Any

import requests

from ..models import APIIntegration
from .base import IntegrationProvider

GRAPH_VERSION = "v21.0"
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_VERSION}"


class WhatsAppProvider(IntegrationProvider):
    provider_key = "whatsapp"
    display_name = "WhatsApp"
    default_endpoint = GRAPH_BASE
    auth_type = "bearer"

    @classmethod
    def detect(cls, integration: APIIntegration) -> bool:
        text = f"{integration.name} {integration.description}".lower()
        return "whatsapp" in text or "wa cloud" in text

    @classmethod
    def tool_definitions(cls) -> list[dict[str, Any]]:
        return [
            {
                "name": "whatsapp.get_phone_number",
                "description": "Get WhatsApp Business phone number details",
                "parameters": {},
            },
            {
                "name": "whatsapp.send_text",
                "description": "Send a WhatsApp text message (E.164 recipient)",
                "parameters": {"to": "string", "text": "string"},
            },
            {
                "name": "whatsapp.send_template",
                "description": "Send a pre-approved WhatsApp template message",
                "parameters": {
                    "to": "string",
                    "template_name": "string",
                    "language_code": "string",
                },
            },
        ]

    @classmethod
    def _creds(cls, integration: APIIntegration):
        auth = cls._auth(integration)
        token = cls._token(integration)
        phone_id = (
            auth.get("phone_number_id")
            or auth.get("phone_id")
            or auth.get("from_number_id")
            or ""
        )
        if not token:
            raise ValueError("WhatsApp access token required")
        if not phone_id:
            raise ValueError("WhatsApp phone_number_id required")
        return str(token), str(phone_id)

    @classmethod
    def _headers(cls, token: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    @classmethod
    def test_connection(cls, integration: APIIntegration) -> dict[str, Any]:
        try:
            token, phone_id = cls._creds(integration)
            resp = requests.get(
                f"{GRAPH_BASE}/{phone_id}",
                headers=cls._headers(token),
                params={
                    "fields": "id,display_phone_number,verified_name,quality_rating"
                },
                timeout=20,
            )
            if resp.status_code >= 400:
                return {"status": "error", "message": resp.text[:300]}
            data = resp.json()
            label = (
                data.get("verified_name")
                or data.get("display_phone_number")
                or phone_id
            )
            return {
                "status": "success",
                "message": f"Connected to WhatsApp Business: {label}",
                "data": data,
            }
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}

    @classmethod
    def execute_tool(
        cls, integration: APIIntegration, tool_name: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        try:
            token, phone_id = cls._creds(integration)
            headers = cls._headers(token)

            if tool_name == "whatsapp.get_phone_number":
                resp = requests.get(
                    f"{GRAPH_BASE}/{phone_id}",
                    headers=headers,
                    params={
                        "fields": "id,display_phone_number,verified_name,quality_rating"
                    },
                    timeout=20,
                )
                return {
                    "status": "success" if resp.ok else "error",
                    "phone": resp.json() if resp.ok else {},
                    "message": "" if resp.ok else resp.text[:300],
                }

            if tool_name == "whatsapp.send_text":
                to = params.get("to", "").lstrip("+")
                text = params.get("text", "")
                if not to or not text:
                    return {"status": "error", "message": "to and text required"}
                payload = {
                    "messaging_product": "whatsapp",
                    "to": to,
                    "type": "text",
                    "text": {"preview_url": False, "body": text},
                }
                resp = requests.post(
                    f"{GRAPH_BASE}/{phone_id}/messages",
                    headers=headers,
                    json=payload,
                    timeout=30,
                )
                data = resp.json() if resp.content else {}
                return {
                    "status": "success" if resp.ok else "error",
                    "result": data,
                    "message": (
                        ""
                        if resp.ok
                        else data.get("error", {}).get("message", resp.text[:300])
                    ),
                }

            if tool_name == "whatsapp.send_template":
                to = params.get("to", "").lstrip("+")
                template_name = params.get("template_name", "")
                language_code = params.get("language_code", "en_US")
                if not to or not template_name:
                    return {
                        "status": "error",
                        "message": "to and template_name required",
                    }
                payload = {
                    "messaging_product": "whatsapp",
                    "to": to,
                    "type": "template",
                    "template": {
                        "name": template_name,
                        "language": {"code": language_code},
                    },
                }
                resp = requests.post(
                    f"{GRAPH_BASE}/{phone_id}/messages",
                    headers=headers,
                    json=payload,
                    timeout=30,
                )
                data = resp.json() if resp.content else {}
                return {
                    "status": "success" if resp.ok else "error",
                    "result": data,
                    "message": (
                        ""
                        if resp.ok
                        else data.get("error", {}).get("message", resp.text[:300])
                    ),
                }

            return {"status": "error", "message": f"Unknown WhatsApp tool: {tool_name}"}
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}
