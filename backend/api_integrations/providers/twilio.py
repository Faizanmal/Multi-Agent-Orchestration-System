"""Twilio SMS/voice integration provider."""
from typing import Any

import requests

from ..models import APIIntegration
from .base import IntegrationProvider


class TwilioProvider(IntegrationProvider):
    provider_key = "twilio"
    display_name = "Twilio"
    default_endpoint = "https://api.twilio.com"
    auth_type = "basic"

    @classmethod
    def detect(cls, integration: APIIntegration) -> bool:
        text = f"{integration.name} {integration.description}".lower()
        return "twilio" in text or "sms" in text

    @classmethod
    def tool_definitions(cls) -> list[dict[str, Any]]:
        return [
            {"name": "twilio.send_sms", "description": "Send an SMS message", "parameters": {"to": "string", "body": "string", "from": "string"}},
            {"name": "twilio.list_messages", "description": "List recent SMS messages", "parameters": {"limit": "int"}},
            {"name": "twilio.account", "description": "Get Twilio account info", "parameters": {}},
        ]

    @classmethod
    def _creds(cls, integration: APIIntegration):
        auth = cls._auth(integration)
        sid = auth.get("account_sid") or auth.get("username") or ""
        token = auth.get("auth_token") or auth.get("api_key") or auth.get("token") or ""
        if not sid or not token:
            raise ValueError("Twilio account_sid and auth_token required")
        return str(sid), str(token)

    @classmethod
    def test_connection(cls, integration: APIIntegration) -> dict[str, Any]:
        try:
            sid, token = cls._creds(integration)
            resp = requests.get(
                f"https://api.twilio.com/2010-04-01/Accounts/{sid}.json",
                auth=(sid, token),
                timeout=20,
            )
            if resp.status_code >= 400:
                return {"status": "error", "message": resp.text[:200]}
            data = resp.json()
            return {"status": "success", "message": f"Connected to Twilio account {data.get('friendly_name') or sid}", "data": {"status": data.get("status")}}
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}

    @classmethod
    def execute_tool(cls, integration: APIIntegration, tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
        try:
            sid, token = cls._creds(integration)
            auth = (sid, token)
            if tool_name == "twilio.account":
                resp = requests.get(f"https://api.twilio.com/2010-04-01/Accounts/{sid}.json", auth=auth, timeout=20)
                return {"status": "success" if resp.ok else "error", "account": resp.json() if resp.ok else {}, "message": "" if resp.ok else resp.text[:200]}

            if tool_name == "twilio.send_sms":
                to = params.get("to")
                body = params.get("body", "")
                from_number = params.get("from") or cls._auth(integration).get("from_number") or ""
                if not to or not body or not from_number:
                    return {"status": "error", "message": "to, body, and from (or from_number in auth) required"}
                resp = requests.post(
                    f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
                    auth=auth,
                    data={"To": to, "From": from_number, "Body": body},
                    timeout=30,
                )
                return {"status": "success" if resp.ok else "error", "message_sid": resp.json().get("sid") if resp.ok else None, "message": "" if resp.ok else resp.text[:200]}

            if tool_name == "twilio.list_messages":
                limit = min(int(params.get("limit", 20)), 50)
                resp = requests.get(
                    f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
                    auth=auth,
                    params={"PageSize": limit},
                    timeout=20,
                )
                msgs = resp.json().get("messages", []) if resp.ok else []
                return {"status": "success" if resp.ok else "error", "messages": msgs, "message": "" if resp.ok else resp.text[:200]}

            return {"status": "error", "message": f"Unknown Twilio tool: {tool_name}"}
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}
