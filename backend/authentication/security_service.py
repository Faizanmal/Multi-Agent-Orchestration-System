from datetime import timezone

"""
OAuth2 and JWT Authentication Middleware
Enhanced security with token-based authentication
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Any

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from rest_framework import authentication, exceptions

User = get_user_model()
logger = logging.getLogger(__name__)


class JWTConfig:
    """JWT Configuration"""

    SECRET_KEY = getattr(settings, "JWT_SECRET_KEY", settings.SECRET_KEY)
    ALGORITHM = "HS256"
    ACCESS_TOKEN_LIFETIME = timedelta(hours=1)
    REFRESH_TOKEN_LIFETIME = timedelta(days=7)

    # Token claims
    ISSUER = "MultiAgentSystem"
    AUDIENCE = "api"


class JWTService:
    """Service for JWT token management"""

    @staticmethod
    def generate_access_token(user: User) -> str:
        """
        Generate JWT access token

        Args:
            user: User instance

        Returns:
            JWT token string
        """
        payload = {
            "user_id": str(user.id),
            "email": user.email,
            "username": user.username,
            "role": user.role,
            "exp": datetime.now(timezone.utc) + JWTConfig.ACCESS_TOKEN_LIFETIME,
            "iat": datetime.now(timezone.utc),
            "iss": JWTConfig.ISSUER,
            "aud": JWTConfig.AUDIENCE,
            "type": "access",
        }

        token = jwt.encode(payload, JWTConfig.SECRET_KEY, algorithm=JWTConfig.ALGORITHM)
        logger.debug(f"Generated access token for user {user.email}")

        return token

    @staticmethod
    def generate_refresh_token(user: User) -> str:
        """
        Generate JWT refresh token

        Args:
            user: User instance

        Returns:
            JWT refresh token string
        """
        payload = {
            "user_id": str(user.id),
            "exp": datetime.now(timezone.utc) + JWTConfig.REFRESH_TOKEN_LIFETIME,
            "iat": datetime.now(timezone.utc),
            "iss": JWTConfig.ISSUER,
            "aud": JWTConfig.AUDIENCE,
            "type": "refresh",
        }

        token = jwt.encode(payload, JWTConfig.SECRET_KEY, algorithm=JWTConfig.ALGORITHM)
        logger.debug(f"Generated refresh token for user {user.email}")

        return token

    @staticmethod
    def verify_token(token: str) -> dict[str, Any] | None:
        """
        Verify and decode JWT token

        Args:
            token: JWT token string

        Returns:
            Decoded payload or None
        """
        try:
            payload = jwt.decode(
                token,
                JWTConfig.SECRET_KEY,
                algorithms=[JWTConfig.ALGORITHM],
                audience=JWTConfig.AUDIENCE,
                issuer=JWTConfig.ISSUER,
            )

            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None

    @staticmethod
    def refresh_access_token(refresh_token: str) -> str | None:
        """
        Generate new access token from refresh token

        Args:
            refresh_token: Refresh token string

        Returns:
            New access token or None
        """
        payload = JWTService.verify_token(refresh_token)

        if not payload or payload.get("type") != "refresh":
            return None

        try:
            user = User.objects.get(id=payload["user_id"])
            return JWTService.generate_access_token(user)
        except User.DoesNotExist:
            return None


class JWTAuthentication(authentication.BaseAuthentication):
    """
    DRF Authentication class for JWT tokens
    """

    def authenticate(self, request):
        """Authenticate request using JWT token"""
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")

        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header.replace("Bearer ", "")

        payload = JWTService.verify_token(token)

        if not payload or payload.get("type") != "access":
            raise exceptions.AuthenticationFailed("Invalid or expired token")

        try:
            user = User.objects.get(id=payload["user_id"])

            if not user.is_active:
                raise exceptions.AuthenticationFailed("User account is disabled")

            # Update last activity
            user.last_activity = datetime.now(timezone.utc)
            user.save(update_fields=["last_activity"])

            return (user, token)

        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed("User not found")


class RateLimitMiddleware:
    """
    Middleware for API rate limiting
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limits = {
            "free": {"requests": 100, "window": 3600},  # 100 requests per hour
            "pro": {"requests": 1000, "window": 3600},  # 1000 requests per hour
            "premium": {"requests": 10000, "window": 3600},  # 10k requests per hour
        }

    def __call__(self, request):
        """Process request with rate limiting"""
        # Skip rate limiting for non-API paths
        if not request.path.startswith("/api/"):
            return self.get_response(request)

        # Get user tier
        user = getattr(request, "user", None)

        if not user or not user.is_authenticated:
            tier = "free"
        else:
            tier = user.subscription_tier

        # Check rate limit
        if not self._check_rate_limit(request, user, tier):
            return JsonResponse(
                {
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Upgrade to increase limits.",
                },
                status=429,
            )

        response = self.get_response(request)

        # Add rate limit headers
        limit = self.rate_limits[tier]["requests"]
        remaining = self._get_remaining_requests(request, user, tier)

        response["X-RateLimit-Limit"] = limit
        response["X-RateLimit-Remaining"] = remaining
        response["X-RateLimit-Reset"] = self._get_reset_time(tier)

        return response

    def _check_rate_limit(self, request, user, tier):
        """Check if request is within rate limit"""
        # Implementation would use Redis to track request counts
        # For now, always allow
        return True

    def _get_remaining_requests(self, request, user, tier):
        """Get remaining requests in current window"""
        return self.rate_limits[tier]["requests"]

    def _get_reset_time(self, tier):
        """Get time when rate limit resets"""
        return int(
            (
                datetime.now(timezone.utc)
                + timedelta(seconds=self.rate_limits[tier]["window"])
            ).timestamp()
        )


class SecurityMiddleware:
    """
    Enhanced security middleware
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """Add security headers"""
        response = self.get_response(request)

        # Security headers
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"
        response["X-XSS-Protection"] = "1; mode=block"
        response["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # CORS headers (if needed)
        if request.path.startswith("/api/"):
            response["Access-Control-Allow-Credentials"] = "true"

        return response


class OAuth2Service:
    """
    Service for OAuth2 authentication with external providers
    """

    def __init__(self):
        self.providers = {
            "google": {
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_url": "https://oauth2.googleapis.com/token",
                "user_info_url": "https://www.googleapis.com/oauth2/v2/userinfo",
            },
            "github": {
                "client_id": os.getenv("GITHUB_CLIENT_ID"),
                "client_secret": os.getenv("GITHUB_CLIENT_SECRET"),
                "auth_url": "https://github.com/login/oauth/authorize",
                "token_url": "https://github.com/login/oauth/access_token",
                "user_info_url": "https://api.github.com/user",
            },
        }

    def get_authorization_url(
        self, provider: str, redirect_uri: str, state: str
    ) -> str:
        """
        Get OAuth2 authorization URL

        Args:
            provider: OAuth provider name
            redirect_uri: Redirect URI after auth
            state: State parameter for CSRF protection

        Returns:
            Authorization URL
        """
        config = self.providers.get(provider)
        if not config:
            raise ValueError(f"Unknown provider: {provider}")

        params = {
            "client_id": config["client_id"],
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "email profile",
            "state": state,
        }

        from urllib.parse import urlencode

        return f"{config['auth_url']}?{urlencode(params)}"

    def exchange_code_for_token(
        self, provider: str, code: str, redirect_uri: str
    ) -> dict[str, Any]:
        """
        Exchange authorization code for access token

        Args:
            provider: OAuth provider name
            code: Authorization code
            redirect_uri: Redirect URI

        Returns:
            Token response
        """
        import requests

        config = self.providers.get(provider)
        if not config:
            raise ValueError(f"Unknown provider: {provider}")

        data = {
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }

        response = requests.post(config["token_url"], data=data)
        response.raise_for_status()

        return response.json()

    def get_user_info(self, provider: str, access_token: str) -> dict[str, Any]:
        """
        Get user info from OAuth provider

        Args:
            provider: OAuth provider name
            access_token: Access token

        Returns:
            User info
        """
        import requests

        config = self.providers.get(provider)
        if not config:
            raise ValueError(f"Unknown provider: {provider}")

        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(config["user_info_url"], headers=headers)
        response.raise_for_status()

        return response.json()


# Singleton instances
_jwt_service = JWTService()
_oauth2_service = OAuth2Service()


def get_jwt_service() -> JWTService:
    """Get JWT service singleton"""
    return _jwt_service


def get_oauth2_service() -> OAuth2Service:
    """Get OAuth2 service singleton"""
    return _oauth2_service
