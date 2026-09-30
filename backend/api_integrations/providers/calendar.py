"""Google Calendar integration provider."""

from datetime import datetime, timedelta, timezone
from typing import Any

import requests

from ..models import APIIntegration
from .base import IntegrationProvider


class GoogleCalendarProvider(IntegrationProvider):
    provider_key = "calendar"
    display_name = "Google Calendar"
    default_endpoint = "https://www.googleapis.com/calendar/v3"
    auth_type = "oauth"

    @classmethod
    def detect(cls, integration: APIIntegration) -> bool:
        text = f"{integration.name} {integration.description}".lower()
        return "calendar" in text or "google calendar" in text

    @classmethod
    def tool_definitions(cls) -> list[dict[str, Any]]:
        return [
            {
                "name": "calendar.list_calendars",
                "description": "List calendars",
                "parameters": {},
            },
            {
                "name": "calendar.list_events",
                "description": "List upcoming events",
                "parameters": {"calendar_id": "string", "max_results": "int"},
            },
            {
                "name": "calendar.create_event",
                "description": "Create a calendar event",
                "parameters": {
                    "calendar_id": "string",
                    "summary": "string",
                    "start": "string",
                    "end": "string",
                },
            },
        ]

    @classmethod
    def _headers(cls, integration: APIIntegration) -> dict[str, str]:
        token = cls._token(integration)
        if not token:
            raise ValueError("Google OAuth access_token required")
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    @classmethod
    def test_connection(cls, integration: APIIntegration) -> dict[str, Any]:
        try:
            resp = requests.get(
                "https://www.googleapis.com/calendar/v3/users/me/calendarList",
                headers=cls._headers(integration),
                params={"maxResults": 1},
                timeout=20,
            )
            if resp.status_code >= 400:
                return {"status": "error", "message": resp.text[:200]}
            return {
                "status": "success",
                "message": "Connected to Google Calendar",
                "data": {"count": len(resp.json().get("items", []))},
            }
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}

    @classmethod
    def execute_tool(
        cls, integration: APIIntegration, tool_name: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        try:
            headers = cls._headers(integration)
            if tool_name == "calendar.list_calendars":
                resp = requests.get(
                    "https://www.googleapis.com/calendar/v3/users/me/calendarList",
                    headers=headers,
                    timeout=20,
                )
                items = resp.json().get("items", []) if resp.ok else []
                calendars = [
                    {
                        "id": i.get("id"),
                        "summary": i.get("summary"),
                        "primary": i.get("primary"),
                    }
                    for i in items
                ]
                return {
                    "status": "success" if resp.ok else "error",
                    "calendars": calendars,
                    "message": "" if resp.ok else resp.text[:200],
                }

            if tool_name == "calendar.list_events":
                calendar_id = params.get("calendar_id") or "primary"
                max_results = min(int(params.get("max_results", 10)), 50)
                now = datetime.now(timezone.utc).isoformat()
                resp = requests.get(
                    f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events",
                    headers=headers,
                    params={
                        "maxResults": max_results,
                        "timeMin": now,
                        "singleEvents": True,
                        "orderBy": "startTime",
                    },
                    timeout=20,
                )
                events = resp.json().get("items", []) if resp.ok else []
                return {
                    "status": "success" if resp.ok else "error",
                    "events": events,
                    "message": "" if resp.ok else resp.text[:200],
                }

            if tool_name == "calendar.create_event":
                calendar_id = params.get("calendar_id") or "primary"
                summary = params.get("summary", "")
                start = params.get("start")
                end = params.get("end")
                if not summary:
                    return {"status": "error", "message": "summary required"}
                if not start:
                    start = datetime.now(timezone.utc).isoformat()
                if not end:
                    end = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
                body = {
                    "summary": summary,
                    "description": params.get("description", ""),
                    "start": {"dateTime": start},
                    "end": {"dateTime": end},
                }
                resp = requests.post(
                    f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events",
                    headers=headers,
                    json=body,
                    timeout=20,
                )
                return {
                    "status": "success" if resp.ok else "error",
                    "event": resp.json() if resp.ok else {},
                    "message": "" if resp.ok else resp.text[:200],
                }

            return {"status": "error", "message": f"Unknown Calendar tool: {tool_name}"}
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}
