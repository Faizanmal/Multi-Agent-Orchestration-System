"""Google Drive API integration provider."""

from typing import Any

import requests

from ..models import APIIntegration
from .base import IntegrationProvider


class GoogleDriveProvider(IntegrationProvider):
    provider_key = "google_drive"
    display_name = "Google Drive"
    default_endpoint = "https://www.googleapis.com/drive/v3"
    auth_type = "oauth"

    @classmethod
    def detect(cls, integration: APIIntegration) -> bool:
        text = f"{integration.name} {integration.description}".lower()
        return (
            "google drive" in text or "google_drive" in text or text.strip() == "drive"
        )

    @classmethod
    def tool_definitions(cls) -> list[dict[str, Any]]:
        return [
            {
                "name": "google_drive.list_files",
                "description": "List recent Drive files",
                "parameters": {"page_size": "int", "query": "string"},
            },
            {
                "name": "google_drive.get_file",
                "description": "Get file metadata by ID",
                "parameters": {"file_id": "string"},
            },
            {
                "name": "google_drive.search",
                "description": "Search Drive files by name/query",
                "parameters": {"query": "string", "page_size": "int"},
            },
            {
                "name": "google_drive.read_text",
                "description": "Export/download text content of a Google Doc or text file",
                "parameters": {"file_id": "string"},
            },
        ]

    @classmethod
    def _headers(cls, integration: APIIntegration) -> dict[str, str]:
        auth = cls._auth(integration)
        token = auth.get("access_token") or cls._token(integration)
        if not token:
            raise ValueError("Google Drive OAuth access_token required")
        return {"Authorization": f"Bearer {token}"}

    @classmethod
    def test_connection(cls, integration: APIIntegration) -> dict[str, Any]:
        try:
            resp = requests.get(
                "https://www.googleapis.com/drive/v3/about",
                headers=cls._headers(integration),
                params={"fields": "user,storageQuota"},
                timeout=20,
            )
            if resp.status_code >= 400:
                return {"status": "error", "message": resp.text[:300]}
            data = resp.json()
            email = (data.get("user") or {}).get("emailAddress", "Drive user")
            return {
                "status": "success",
                "message": f"Connected to Google Drive as {email}",
                "data": data.get("user"),
            }
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}

    @classmethod
    def execute_tool(
        cls, integration: APIIntegration, tool_name: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        try:
            headers = cls._headers(integration)
            page_size = min(int(params.get("page_size", 20)), 50)

            if tool_name in ("google_drive.list_files", "google_drive.search"):
                q = params.get("query") or (
                    "trashed=false" if tool_name == "google_drive.list_files" else None
                )
                if tool_name == "google_drive.search" and params.get("query"):
                    q = f"name contains '{params['query']}' and trashed=false"
                resp = requests.get(
                    "https://www.googleapis.com/drive/v3/files",
                    headers=headers,
                    params={
                        "pageSize": page_size,
                        "fields": "files(id,name,mimeType,modifiedTime,size,webViewLink)",
                        **({"q": q} if q else {}),
                    },
                    timeout=30,
                )
                data = resp.json() if resp.content else {}
                return {
                    "status": "success" if resp.ok else "error",
                    "files": data.get("files", []) if resp.ok else [],
                    "message": (
                        ""
                        if resp.ok
                        else data.get("error", {}).get("message", resp.text[:300])
                    ),
                }

            if tool_name == "google_drive.get_file":
                file_id = params.get("file_id")
                if not file_id:
                    return {"status": "error", "message": "file_id required"}
                resp = requests.get(
                    f"https://www.googleapis.com/drive/v3/files/{file_id}",
                    headers=headers,
                    params={
                        "fields": "id,name,mimeType,modifiedTime,size,webViewLink,owners"
                    },
                    timeout=20,
                )
                return {
                    "status": "success" if resp.ok else "error",
                    "file": resp.json() if resp.ok else {},
                    "message": "" if resp.ok else resp.text[:300],
                }

            if tool_name == "google_drive.read_text":
                file_id = params.get("file_id")
                if not file_id:
                    return {"status": "error", "message": "file_id required"}
                meta = requests.get(
                    f"https://www.googleapis.com/drive/v3/files/{file_id}",
                    headers=headers,
                    params={"fields": "id,name,mimeType"},
                    timeout=20,
                ).json()
                mime = meta.get("mimeType", "")
                if mime.startswith("application/vnd.google-apps."):
                    export_mime = "text/plain"
                    if "spreadsheet" in mime:
                        export_mime = "text/csv"
                    resp = requests.get(
                        f"https://www.googleapis.com/drive/v3/files/{file_id}/export",
                        headers=headers,
                        params={"mimeType": export_mime},
                        timeout=60,
                    )
                else:
                    resp = requests.get(
                        f"https://www.googleapis.com/drive/v3/files/{file_id}",
                        headers=headers,
                        params={"alt": "media"},
                        timeout=60,
                    )
                if not resp.ok:
                    return {"status": "error", "message": resp.text[:300]}
                text = resp.text[:50000]
                return {
                    "status": "success",
                    "name": meta.get("name"),
                    "content": text,
                    "message": "",
                }

            return {
                "status": "error",
                "message": f"Unknown Google Drive tool: {tool_name}",
            }
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}
