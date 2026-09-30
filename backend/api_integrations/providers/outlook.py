"""Microsoft Outlook (Graph Mail) integration provider."""

from typing import Any

from ..models import APIIntegration
from .base import IntegrationProvider
from .ms_graph import graph_get, graph_post, graph_token, test_graph_me


class OutlookProvider(IntegrationProvider):
    provider_key = "outlook"
    display_name = "Microsoft Outlook"
    default_endpoint = "https://graph.microsoft.com/v1.0"
    auth_type = "oauth"

    @classmethod
    def detect(cls, integration: APIIntegration) -> bool:
        text = f"{integration.name} {integration.description}".lower()
        return "outlook" in text or "microsoft mail" in text

    @classmethod
    def tool_definitions(cls) -> list[dict[str, Any]]:
        return [
            {
                "name": "outlook.list_messages",
                "description": "List recent Outlook inbox messages",
                "parameters": {"top": "int"},
            },
            {
                "name": "outlook.search",
                "description": "Search Outlook messages",
                "parameters": {"query": "string", "top": "int"},
            },
            {
                "name": "outlook.send_mail",
                "description": "Send an email via Outlook",
                "parameters": {"to": "string", "subject": "string", "body": "string"},
            },
        ]

    @classmethod
    def test_connection(cls, integration: APIIntegration) -> dict[str, Any]:
        return test_graph_me(cls, integration, "Outlook")

    @classmethod
    def execute_tool(
        cls, integration: APIIntegration, tool_name: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        try:
            token = graph_token(cls, integration)
            top = min(int(params.get("top", 10)), 50)

            if tool_name == "outlook.list_messages":
                ok, data, err = graph_get(
                    token,
                    "/me/mailFolders/Inbox/messages",
                    {
                        "$top": top,
                        "$select": "id,subject,from,receivedDateTime,bodyPreview,isRead",
                    },
                )
                return {
                    "status": "success" if ok else "error",
                    "messages": data.get("value", []) if ok else [],
                    "message": err,
                }

            if tool_name == "outlook.search":
                query = params.get("query", "")
                if not query:
                    return {"status": "error", "message": "query required"}
                ok, data, err = graph_get(
                    token,
                    "/me/messages",
                    {
                        "$search": f'"{query}"',
                        "$top": top,
                        "$select": "id,subject,from,receivedDateTime,bodyPreview",
                    },
                )
                return {
                    "status": "success" if ok else "error",
                    "messages": data.get("value", []) if ok else [],
                    "message": err,
                }

            if tool_name == "outlook.send_mail":
                to = params.get("to")
                subject = params.get("subject", "")
                body = params.get("body", "")
                if not to or not subject:
                    return {"status": "error", "message": "to and subject required"}
                payload = {
                    "message": {
                        "subject": subject,
                        "body": {"contentType": "Text", "content": body},
                        "toRecipients": [{"emailAddress": {"address": to}}],
                    },
                    "saveToSentItems": True,
                }
                ok, data, err = graph_post(token, "/me/sendMail", payload)
                # sendMail returns 202 empty
                if ok or err == "":
                    return {"status": "success", "message": "Email sent"}
                return {"status": "error", "message": err or str(data)}

            return {"status": "error", "message": f"Unknown Outlook tool: {tool_name}"}
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}
