"""
JWT Authentication backend for Django REST Framework.

Validates the enterprise JWT (issued by jwt_service.py) from the
Authorization: Bearer <token> header.

Kept intentionally thin – all crypto logic lives in services/jwt_service.py.
"""

import logging

from django.contrib.auth import get_user_model
from rest_framework import authentication, exceptions

from authentication.services.jwt_service import decode_access_token

User = get_user_model()
logger = logging.getLogger(__name__)


class JWTAuthentication(authentication.BaseAuthentication):
    """DRF authentication class that validates enterprise JWTs."""

    keyword = "Bearer"

    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != self.keyword.lower():
            return None

        token = parts[1]
        return self._authenticate_credentials(request, token)

    def _authenticate_credentials(self, request, token: str):
        try:
            payload = decode_access_token(token)
        except exceptions.AuthenticationFailed:
            raise
        except Exception as exc:  # noqa: BLE001
            raise exceptions.AuthenticationFailed(str(exc))

        user_id = payload.get("sub")
        if not user_id:
            raise exceptions.AuthenticationFailed("Token missing sub claim.")

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed("User not found.")

        if not user.is_active:
            raise exceptions.AuthenticationFailed("User account is disabled.")

        if getattr(user, "account_locked", False):
            raise exceptions.AuthenticationFailed("User account is locked.")

        # Attach JWT claims to request for downstream use
        request.jwt_payload = payload
        request.auth_provider = payload.get("provider", "email")

        return user, token

    def authenticate_header(self, request):
        return 'Bearer realm="api"'


# ---------------------------------------------------------------------------
# WebSocket JWT middleware (token via query string)
# ---------------------------------------------------------------------------


class WebSocketJWTAuthMiddleware:
    """ASGI middleware: validates ?token=<jwt> for WebSocket connections."""

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        from urllib.parse import parse_qs

        from channels.db import database_sync_to_async
        from django.contrib.auth.models import AnonymousUser

        query_string = scope.get("query_string", b"").decode()
        params = parse_qs(query_string)
        token = params.get("token", [None])[0]

        scope["user"] = AnonymousUser()
        if token:
            try:
                payload = decode_access_token(token)
                user_id = payload.get("sub")
                user = await database_sync_to_async(
                    lambda: User.objects.filter(id=user_id, is_active=True).first()
                )()
                if user:
                    scope["user"] = user
            except Exception:  # noqa: BLE001, S110
                pass

        return await self.inner(scope, receive, send)


# ---------------------------------------------------------------------------
# Legacy helpers (kept for backward compatibility)
# ---------------------------------------------------------------------------


def generate_access_token(user, provider="email", session_id=None):
    from authentication.services.jwt_service import generate_access_token as _gen

    return _gen(user, provider=provider, session_id=session_id)


def generate_refresh_token(user):
    from authentication.services.jwt_service import generate_raw_refresh_token

    return generate_raw_refresh_token()


def refresh_access_token(refresh_token_raw):
    from authentication.services.jwt_service import rotate_refresh_token

    result = rotate_refresh_token(refresh_token_raw)
    return result["access_token"]
