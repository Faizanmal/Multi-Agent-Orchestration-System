"""Shopify Admin API integration provider."""

from typing import Any

import requests

from ..models import APIIntegration
from .base import IntegrationProvider


class ShopifyProvider(IntegrationProvider):
    provider_key = "shopify"
    display_name = "Shopify"
    default_endpoint = "https://YOUR_SHOP.myshopify.com/admin/api/2024-10"
    auth_type = "bearer"

    @classmethod
    def detect(cls, integration: APIIntegration) -> bool:
        text = f"{integration.name} {integration.description} {integration.endpoint}".lower()
        return "shopify" in text

    @classmethod
    def tool_definitions(cls) -> list[dict[str, Any]]:
        return [
            {
                "name": "shopify.list_orders",
                "description": "List recent Shopify orders",
                "parameters": {"limit": "int", "status": "string"},
            },
            {
                "name": "shopify.list_products",
                "description": "List Shopify products",
                "parameters": {"limit": "int"},
            },
            {
                "name": "shopify.get_order",
                "description": "Get a Shopify order by ID",
                "parameters": {"order_id": "string"},
            },
            {
                "name": "shopify.shop",
                "description": "Get shop details",
                "parameters": {},
            },
        ]

    @classmethod
    def _base_and_token(cls, integration: APIIntegration):
        auth = cls._auth(integration)
        token = cls._token(integration)
        shop = auth.get("shop_domain") or auth.get("shop") or ""
        base = (integration.endpoint or "").rstrip("/")
        if shop and ("YOUR_SHOP" in base or not base):
            shop = shop.replace("https://", "").replace("http://", "").strip("/")
            if not shop.endswith(".myshopify.com"):
                shop = f"{shop}.myshopify.com"
            base = f"https://{shop}/admin/api/2024-10"
        if not base or "YOUR_SHOP" in base:
            raise ValueError("Shopify shop domain / endpoint required")
        if not token:
            raise ValueError("Shopify Admin API access token required")
        return base, str(token)

    @classmethod
    def _headers(cls, token: str) -> dict[str, str]:
        return {
            "X-Shopify-Access-Token": token,
            "Content-Type": "application/json",
        }

    @classmethod
    def test_connection(cls, integration: APIIntegration) -> dict[str, Any]:
        try:
            base, token = cls._base_and_token(integration)
            resp = requests.get(
                f"{base}/shop.json", headers=cls._headers(token), timeout=20
            )
            if resp.status_code >= 400:
                return {"status": "error", "message": resp.text[:300]}
            shop = (resp.json() or {}).get("shop", {})
            return {
                "status": "success",
                "message": f"Connected to Shopify store {shop.get('name') or shop.get('domain')}",
                "data": {"domain": shop.get("domain"), "plan": shop.get("plan_name")},
            }
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}

    @classmethod
    def execute_tool(
        cls, integration: APIIntegration, tool_name: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        try:
            base, token = cls._base_and_token(integration)
            headers = cls._headers(token)
            limit = min(int(params.get("limit", 10)), 50)

            if tool_name == "shopify.shop":
                resp = requests.get(f"{base}/shop.json", headers=headers, timeout=20)
                return {
                    "status": "success" if resp.ok else "error",
                    "shop": (resp.json() or {}).get("shop") if resp.ok else {},
                    "message": "" if resp.ok else resp.text[:300],
                }

            if tool_name == "shopify.list_products":
                resp = requests.get(
                    f"{base}/products.json",
                    headers=headers,
                    params={"limit": limit},
                    timeout=30,
                )
                data = resp.json() if resp.content else {}
                return {
                    "status": "success" if resp.ok else "error",
                    "products": data.get("products", []) if resp.ok else [],
                    "message": "" if resp.ok else resp.text[:300],
                }

            if tool_name == "shopify.list_orders":
                q = {"limit": limit, "status": params.get("status", "any")}
                resp = requests.get(
                    f"{base}/orders.json", headers=headers, params=q, timeout=30
                )
                data = resp.json() if resp.content else {}
                return {
                    "status": "success" if resp.ok else "error",
                    "orders": data.get("orders", []) if resp.ok else [],
                    "message": "" if resp.ok else resp.text[:300],
                }

            if tool_name == "shopify.get_order":
                order_id = params.get("order_id")
                if not order_id:
                    return {"status": "error", "message": "order_id required"}
                resp = requests.get(
                    f"{base}/orders/{order_id}.json", headers=headers, timeout=20
                )
                data = resp.json() if resp.content else {}
                return {
                    "status": "success" if resp.ok else "error",
                    "order": data.get("order") if resp.ok else {},
                    "message": "" if resp.ok else resp.text[:300],
                }

            return {"status": "error", "message": f"Unknown Shopify tool: {tool_name}"}
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}
