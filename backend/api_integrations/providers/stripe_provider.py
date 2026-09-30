"""Stripe API integration (customer ops — invoices, customers, subscriptions)."""

from typing import Any

import requests

from ..models import APIIntegration
from .base import IntegrationProvider


class StripeProvider(IntegrationProvider):
    provider_key = "stripe"
    display_name = "Stripe"
    default_endpoint = "https://api.stripe.com/v1"
    auth_type = "bearer"

    @classmethod
    def detect(cls, integration: APIIntegration) -> bool:
        text = f"{integration.name} {integration.description}".lower()
        return "stripe" in text

    @classmethod
    def tool_definitions(cls) -> list[dict[str, Any]]:
        return [
            {
                "name": "stripe.list_customers",
                "description": "List Stripe customers",
                "parameters": {"limit": "int"},
            },
            {
                "name": "stripe.list_invoices",
                "description": "List recent invoices",
                "parameters": {"limit": "int", "customer": "string"},
            },
            {
                "name": "stripe.list_subscriptions",
                "description": "List subscriptions",
                "parameters": {"limit": "int", "status": "string"},
            },
            {
                "name": "stripe.balance",
                "description": "Get Stripe account balance",
                "parameters": {},
            },
        ]

    @classmethod
    def _auth_header(cls, integration: APIIntegration) -> tuple:
        token = cls._token(integration)
        if not token:
            raise ValueError("Stripe secret key required (sk_...)")
        return (token, "")

    @classmethod
    def test_connection(cls, integration: APIIntegration) -> dict[str, Any]:
        try:
            resp = requests.get(
                "https://api.stripe.com/v1/balance",
                auth=cls._auth_header(integration),
                timeout=20,
            )
            if resp.status_code >= 400:
                return {"status": "error", "message": resp.text[:300]}
            return {
                "status": "success",
                "message": "Connected to Stripe",
                "data": resp.json(),
            }
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}

    @classmethod
    def execute_tool(
        cls, integration: APIIntegration, tool_name: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        try:
            auth = cls._auth_header(integration)
            limit = min(int(params.get("limit", 10)), 50)

            if tool_name == "stripe.balance":
                resp = requests.get(
                    "https://api.stripe.com/v1/balance", auth=auth, timeout=20
                )
                return {
                    "status": "success" if resp.ok else "error",
                    "balance": resp.json() if resp.ok else {},
                    "message": "" if resp.ok else resp.text[:300],
                }

            if tool_name == "stripe.list_customers":
                resp = requests.get(
                    "https://api.stripe.com/v1/customers",
                    auth=auth,
                    params={"limit": limit},
                    timeout=30,
                )
                data = resp.json() if resp.content else {}
                return {
                    "status": "success" if resp.ok else "error",
                    "customers": data.get("data", []) if resp.ok else [],
                    "message": (
                        ""
                        if resp.ok
                        else data.get("error", {}).get("message", resp.text[:300])
                    ),
                }

            if tool_name == "stripe.list_invoices":
                q = {"limit": limit}
                if params.get("customer"):
                    q["customer"] = params["customer"]
                resp = requests.get(
                    "https://api.stripe.com/v1/invoices",
                    auth=auth,
                    params=q,
                    timeout=30,
                )
                data = resp.json() if resp.content else {}
                return {
                    "status": "success" if resp.ok else "error",
                    "invoices": data.get("data", []) if resp.ok else [],
                    "message": (
                        ""
                        if resp.ok
                        else data.get("error", {}).get("message", resp.text[:300])
                    ),
                }

            if tool_name == "stripe.list_subscriptions":
                q = {"limit": limit}
                if params.get("status"):
                    q["status"] = params["status"]
                resp = requests.get(
                    "https://api.stripe.com/v1/subscriptions",
                    auth=auth,
                    params=q,
                    timeout=30,
                )
                data = resp.json() if resp.content else {}
                return {
                    "status": "success" if resp.ok else "error",
                    "subscriptions": data.get("data", []) if resp.ok else [],
                    "message": (
                        ""
                        if resp.ok
                        else data.get("error", {}).get("message", resp.text[:300])
                    ),
                }

            return {"status": "error", "message": f"Unknown Stripe tool: {tool_name}"}
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}
