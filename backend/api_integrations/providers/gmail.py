from datetime import timezone

"""Gmail integration provider — real Gmail API."""
import json
import re
from datetime import datetime, timedelta
from typing import Any

from ..models import APIIntegration
from .base import IntegrationProvider


class GmailProvider(IntegrationProvider):
    provider_key = "gmail"
    display_name = "Gmail"
    default_endpoint = "https://gmail.googleapis.com/gmail/v1"
    auth_type = "oauth"

    GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]  # noqa: RUF012
    WRITE_SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]  # noqa: RUF012

    @classmethod
    def detect(cls, integration: APIIntegration) -> bool:
        text = f"{integration.name} {integration.description}".lower()
        return "gmail" in text or "google mail" in text

    @classmethod
    def tool_definitions(cls) -> list[dict[str, Any]]:
        return [
            {
                "name": "gmail.read_inbox",
                "description": "Read latest emails from the user's Gmail inbox",
                "parameters": {"max_results": "int (default 5, max 20)"},
            },
            {
                "name": "gmail.get_message",
                "description": "Get full details of a specific email by message ID",
                "parameters": {"message_id": "string"},
            },
            {
                "name": "gmail.search",
                "description": "Search emails with a Gmail query (from:, subject:, is:unread)",
                "parameters": {"query": "string", "max_results": "int"},
            },
            {
                "name": "gmail.create_draft",
                "description": "Create a draft email (requires gmail.compose scope)",
                "parameters": {"to": "string", "subject": "string", "body": "string"},
            },
        ]

    @classmethod
    def _build_credentials(cls, auth_data: dict[str, Any]):
        from google.oauth2 import service_account
        from google.oauth2.credentials import Credentials

        candidates: list[Any] = []
        for field in ("oauth_token", "credentials", "token", "api_key", "bearer_token", "access_token"):
            val = auth_data.get(field)
            if val:
                candidates.append(val)
        if {"refresh_token", "client_id", "client_secret", "access_token", "token"} & auth_data.keys():
            candidates.append(auth_data)

        last_error = "No valid OAuth JSON found"
        for raw in candidates:
            try:
                if isinstance(raw, dict):
                    creds_dict = raw
                elif isinstance(raw, str) and raw.strip().startswith("{"):
                    creds_dict = json.loads(raw)
                else:
                    continue

                if "client_email" in creds_dict:
                    return service_account.Credentials.from_service_account_info(
                        creds_dict, scopes=cls.GMAIL_SCOPES
                    ), None

                access_token = creds_dict.get("access_token") or creds_dict.get("token")
                if not access_token:
                    continue

                scope_val = creds_dict.get("scope") or creds_dict.get("scopes")
                scopes = scope_val.split() if isinstance(scope_val, str) else list(cls.GMAIL_SCOPES)

                if creds_dict.get("refresh_token") and creds_dict.get("client_id") and creds_dict.get("client_secret"):
                    normalized = dict(creds_dict)
                    normalized["token"] = access_token
                    normalized.setdefault("token_uri", "https://oauth2.googleapis.com/token")
                    return Credentials.from_authorized_user_info(normalized, scopes=scopes), None

                expiry = None
                if creds_dict.get("expires_in"):
                    expiry = datetime.now(timezone.utc) + timedelta(seconds=int(creds_dict["expires_in"]))
                return Credentials(token=access_token, scopes=scopes, expiry=expiry), None
            except Exception as e:  # noqa: BLE001
                last_error = str(e)
        return None, last_error

    @classmethod
    def _format_error(cls, exc: Exception) -> str:
        err = str(exc).lower()
        if "accessnotconfigured" in err or "gmail api has not been used" in err:
            m = re.search(r"project\s+(\d+)", str(exc))
            pid = m.group(1) if m else None
            url = (
                f"https://console.developers.google.com/apis/api/gmail.googleapis.com/overview?project={pid}"
                if pid else "https://console.cloud.google.com/apis/library/gmail.googleapis.com"
            )
            return f"Gmail API not enabled. Enable at: {url}"
        if "401" in err or "unauthorized" in err:
            return "Gmail token expired. Paste a fresh OAuth JSON."
        return str(exc)

    @classmethod
    def _service(cls, integration: APIIntegration):
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        creds, err = cls._build_credentials(cls._auth(integration))
        if not creds:
            raise ValueError(err or "Invalid Gmail credentials")
        if creds.expired and getattr(creds, "refresh_token", None):
            creds.refresh(Request())
        return build("gmail", "v1", credentials=creds)

    @classmethod
    def test_connection(cls, integration: APIIntegration) -> dict[str, Any]:
        try:
            service = cls._service(integration)
            profile = service.users().getProfile(userId="me").execute()
            return {
                "status": "success",
                "message": f"Connected as {profile.get('emailAddress', 'unknown')}",
                "data": {"email": profile.get("emailAddress"), "messages_total": profile.get("messagesTotal")},
            }
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": cls._format_error(e)}

    @classmethod
    def _parse_message(cls, service, msg_id: str, full: bool = False) -> dict[str, Any]:
        fmt = "full" if full else "metadata"
        meta_headers = ["Subject", "From", "To", "Date"] if not full else None
        msg_data = service.users().messages().get(
            userId="me", id=msg_id, format=fmt,
            metadataHeaders=meta_headers,
        ).execute()
        headers = msg_data.get("payload", {}).get("headers", [])
        result = {
            "id": msg_id,
            "subject": next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject"),
            "from": next((h["value"] for h in headers if h["name"] == "From"), "Unknown"),
            "to": next((h["value"] for h in headers if h["name"] == "To"), ""),
            "date": next((h["value"] for h in headers if h["name"] == "Date"), ""),
            "snippet": msg_data.get("snippet", ""),
        }
        if full:
            result["body"] = cls._extract_body(msg_data.get("payload", {}))
        return result

    @classmethod
    def _extract_body(cls, payload: dict) -> str:
        import base64
        if payload.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
        for part in payload.get("parts", []):
            if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
        for part in payload.get("parts", []):
            text = cls._extract_body(part)
            if text:
                return text
        return ""

    @classmethod
    def execute_tool(cls, integration: APIIntegration, tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
        try:
            service = cls._service(integration)
            if tool_name in ("gmail.read_inbox", "read_gmail", "gmail.read"):
                max_results = min(int(params.get("max_results", 5)), 20)
                results = service.users().messages().list(userId="me", maxResults=max_results).execute()
                emails = [
                    cls._parse_message(service, m["id"])
                    for m in results.get("messages", [])
                ]
                return {"status": "success", "emails": emails}

            if tool_name == "gmail.get_message":
                msg_id = params.get("message_id")
                if not msg_id:
                    return {"status": "error", "message": "message_id required"}
                return {"status": "success", "email": cls._parse_message(service, msg_id, full=True)}

            if tool_name == "gmail.search":
                query = params.get("query", "")
                max_results = min(int(params.get("max_results", 10)), 20)
                results = service.users().messages().list(
                    userId="me", q=query, maxResults=max_results
                ).execute()
                emails = [cls._parse_message(service, m["id"]) for m in results.get("messages", [])]
                return {"status": "success", "emails": emails, "query": query}

            if tool_name == "gmail.create_draft":
                import base64
                to = params.get("to", "")
                subject = params.get("subject", "")
                body = params.get("body", "")
                raw = base64.urlsafe_b64encode(
                    f"To: {to}\r\nSubject: {subject}\r\n\r\n{body}".encode()
                ).decode()
                draft = service.users().drafts().create(
                    userId="me", body={"message": {"raw": raw}}
                ).execute()
                return {"status": "success", "draft_id": draft.get("id"), "message": "Draft created"}

            return {"status": "error", "message": f"Unknown Gmail tool: {tool_name}"}
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": cls._format_error(e)}
