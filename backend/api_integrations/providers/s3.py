"""AWS S3 integration provider."""

import json
from typing import Any

from ..models import APIIntegration
from .base import IntegrationProvider


class S3Provider(IntegrationProvider):
    provider_key = "s3"
    display_name = "AWS S3"
    default_endpoint = "https://s3.amazonaws.com"
    auth_type = "api_key"

    @classmethod
    def detect(cls, integration: APIIntegration) -> bool:
        text = f"{integration.name} {integration.description}".lower()
        return "s3" in text or "aws" in text

    @classmethod
    def tool_definitions(cls) -> list[dict[str, Any]]:
        return [
            {
                "name": "s3.list_buckets",
                "description": "List S3 buckets",
                "parameters": {},
            },
            {
                "name": "s3.list_objects",
                "description": "List objects in a bucket",
                "parameters": {"bucket": "string", "prefix": "string"},
            },
            {
                "name": "s3.get_object_text",
                "description": "Read a text object from S3",
                "parameters": {"bucket": "string", "key": "string"},
            },
        ]

    @classmethod
    def _client(cls, integration: APIIntegration):
        import boto3

        auth = cls._auth(integration)
        if isinstance(auth.get("api_key"), str) and auth["api_key"].startswith("{"):
            creds = json.loads(auth["api_key"])
        else:
            creds = auth
        access_key = creds.get("access_key_id") or creds.get("aws_access_key_id")
        secret_key = creds.get("secret_access_key") or creds.get(
            "aws_secret_access_key"
        )
        region = creds.get("region", "us-east-1")
        if not access_key or not secret_key:
            raise ValueError(
                "S3 requires access_key_id and secret_access_key in authentication JSON"
            )
        return boto3.client(
            "s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )

    @classmethod
    def test_connection(cls, integration: APIIntegration) -> dict[str, Any]:
        try:
            client = cls._client(integration)
            buckets = client.list_buckets()
            names = [b["Name"] for b in buckets.get("Buckets", [])[:5]]
            return {
                "status": "success",
                "message": f"Connected — {len(names)} bucket(s) visible",
                "data": {"buckets": names},
            }
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}

    @classmethod
    def execute_tool(
        cls, integration: APIIntegration, tool_name: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        try:
            client = cls._client(integration)
            if tool_name == "s3.list_buckets":
                resp = client.list_buckets()
                buckets = [
                    {"name": b["Name"], "created": b["CreationDate"].isoformat()}
                    for b in resp.get("Buckets", [])
                ]
                return {"status": "success", "buckets": buckets}

            if tool_name == "s3.list_objects":
                bucket = params.get("bucket")
                if not bucket:
                    return {"status": "error", "message": "bucket required"}
                resp = client.list_objects_v2(
                    Bucket=bucket,
                    Prefix=params.get("prefix", ""),
                    MaxKeys=min(int(params.get("limit", 50)), 100),
                )
                objects = [
                    {"key": o["Key"], "size": o["Size"]}
                    for o in resp.get("Contents", [])
                ]
                return {"status": "success", "objects": objects}

            if tool_name == "s3.get_object_text":
                bucket, key = params.get("bucket"), params.get("key")
                if not bucket or not key:
                    return {"status": "error", "message": "bucket and key required"}
                obj = client.get_object(Bucket=bucket, Key=key)
                body = obj["Body"].read().decode("utf-8", errors="replace")[:16000]
                return {"status": "success", "content": body}

            return {"status": "error", "message": f"Unknown S3 tool: {tool_name}"}
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "message": str(e)}
