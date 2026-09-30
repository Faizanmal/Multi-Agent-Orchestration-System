"""Microsoft Graph helpers shared by Outlook, Teams, OneDrive."""
from typing import Any

import requests

from .base import IntegrationProvider

GRAPH = "https://graph.microsoft.com/v1.0"


def graph_token(provider: type, integration) -> str:
    auth = provider._auth(integration)
    token = auth.get("access_token") or provider._token(integration)
    if not token:
        raise ValueError("Microsoft Graph access_token required")
    return str(token)


def graph_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def graph_get(token: str, path: str, params: dict[str, Any] | None = None) -> tuple[bool, dict[str, Any], str]:
    resp = requests.get(f"{GRAPH}{path}", headers=graph_headers(token), params=params or {}, timeout=30)
    data = resp.json() if resp.content else {}
    err = "" if resp.ok else (data.get("error") or {}).get("message", resp.text[:300])
    return resp.ok, data, err


def graph_post(token: str, path: str, payload: dict[str, Any]) -> tuple[bool, dict[str, Any], str]:
    resp = requests.post(f"{GRAPH}{path}", headers=graph_headers(token), json=payload, timeout=30)
    data = resp.json() if resp.content else {}
    err = "" if resp.ok else (data.get("error") or {}).get("message", resp.text[:300])
    return resp.ok, data, err


def test_graph_me(provider: type, integration, label: str) -> dict[str, Any]:
    try:
        token = graph_token(provider, integration)
        ok, data, err = graph_get(token, "/me", {"$select": "displayName,mail,userPrincipalName"})
        if not ok:
            return {"status": "error", "message": err}
        name = data.get("displayName") or data.get("mail") or data.get("userPrincipalName")
        return {"status": "success", "message": f"Connected to {label} as {name}", "data": data}
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "message": str(e)}


# silence unused import lint for IntegrationProvider re-export style
_ = IntegrationProvider
