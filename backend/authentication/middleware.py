"""
Authentication Middleware for JWT and API Keys
"""

import logging

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from django.utils.functional import SimpleLazyObject

logger = logging.getLogger()


class JWTAuthenticationMiddleware:
    """Django middleware for JWT authentication"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get token from Authorization header
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")

        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            request.user = SimpleLazyObject(lambda: self._get_user_from_token(token))
        elif auth_header.startswith("ApiKey "):
            api_key = auth_header.split(" ")[1]
            request.user = SimpleLazyObject(
                lambda: self._get_user_from_api_key(api_key)
            )

        response = self.get_response(request)
        return response

    def _get_user_from_token(self, token):
        """Get user from JWT token"""
        from .oauth_jwt_service import JWTService

        user = JWTService.get_token_user(token)
        return user if user else AnonymousUser()

    def _get_user_from_api_key(self, api_key):
        """Get user from API key"""
        from .oauth_jwt_service import APIKeyService

        user = APIKeyService.verify_api_key(api_key)
        return user if user else AnonymousUser()


class WebSocketJWTAuthMiddleware(BaseMiddleware):
    """WebSocket middleware for JWT authentication"""

    async def __call__(self, scope, receive, send):
        # Get token from query string or headers
        query_string = scope.get("query_string", b"").decode()
        params = dict(x.split("=") for x in query_string.split("&") if "=" in x)

        token = params.get("token")

        if token:
            scope["user"] = await self._get_user_from_token(token)
        else:
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def _get_user_from_token(self, token):
        """Get user from JWT token (async)"""
        from .oauth_jwt_service import JWTService

        user = JWTService.get_token_user(token)
        return user if user else AnonymousUser()


class RateLimitMiddleware:
    """Rate limiting middleware"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from real_time_performance.services import get_cache_service

        # Get user identifier
        user_id = (
            str(request.user.id)
            if request.user.is_authenticated
            else request.META.get("REMOTE_ADDR")
        )

        if user_id:
            cache = get_cache_service()

            # Check rate limit
            key = f"ratelimit:{user_id}:hour"
            count = cache.increment_counter(key, 1)

            if count == 1:
                # Set expiry on first request
                cache.set(key, 1, 3600)  # 1 hour TTL

            # Get limit based on user tier
            limit = self._get_rate_limit(request.user)

            if count > limit:
                from django.http import JsonResponse

                return JsonResponse(
                    {"error": "Rate limit exceeded", "limit": limit}, status=429
                )

        response = self.get_response(request)
        return response

    def _get_rate_limit(self, user):
        """Get rate limit for user"""
        if not user.is_authenticated:
            return 100  # Anonymous users

        # Based on subscription tier
        tier_limits = {"free": 1000, "pro": 10000, "enterprise": 100000}

        return tier_limits.get(getattr(user, "subscription_tier", "free"), 1000)
