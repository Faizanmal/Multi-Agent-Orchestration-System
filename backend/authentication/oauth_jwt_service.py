from datetime import timezone

"""
OAuth2 and JWT Authentication Service
Enhanced security with token-based authentication
"""

import logging
import os
import secrets
from datetime import datetime, timedelta
from typing import Any

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

User = get_user_model()


class JWTService:
    """Service for JWT token management"""

    # JWT Configuration
    SECRET_KEY = getattr(
        settings, "JWT_SECRET_KEY", os.getenv("JWT_SECRET_KEY", settings.SECRET_KEY)
    )
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour
    REFRESH_TOKEN_EXPIRE_DAYS = 30  # 30 days

    @classmethod
    def create_access_token(
        cls, user_id: str, additional_claims: dict | None = None
    ) -> str:
        """
        Create JWT access token

        Args:
            user_id: User identifier
            additional_claims: Additional claims to include

        Returns:
            JWT token string
        """
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=cls.ACCESS_TOKEN_EXPIRE_MINUTES
        )

        payload = {
            "user_id": str(user_id),
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access",
        }

        if additional_claims:
            payload.update(additional_claims)

        token = jwt.encode(payload, cls.SECRET_KEY, algorithm=cls.ALGORITHM)

        logger.info(f"Access token created for user {user_id}")
        return token

    @classmethod
    def create_refresh_token(cls, user_id: str) -> str:
        """
        Create JWT refresh token

        Args:
            user_id: User identifier

        Returns:
            JWT refresh token string
        """
        expire = datetime.now(timezone.utc) + timedelta(
            days=cls.REFRESH_TOKEN_EXPIRE_DAYS
        )

        payload = {
            "user_id": str(user_id),
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh",
            "jti": secrets.token_urlsafe(32),  # Unique token ID
        }

        token = jwt.encode(payload, cls.SECRET_KEY, algorithm=cls.ALGORITHM)

        logger.info(f"Refresh token created for user {user_id}")
        return token

    @classmethod
    def verify_token(cls, token: str) -> dict[str, Any] | None:
        """
        Verify and decode JWT token

        Args:
            token: JWT token string

        Returns:
            Decoded payload or None if invalid
        """
        try:
            payload = jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None

    @classmethod
    def refresh_access_token(cls, refresh_token: str) -> dict[str, str] | None:
        """
        Generate new access token from refresh token

        Args:
            refresh_token: Valid refresh token

        Returns:
            New access token and refresh token
        """
        payload = cls.verify_token(refresh_token)

        if not payload or payload.get("type") != "refresh":
            return None

        user_id = payload.get("user_id")

        return {
            "access_token": cls.create_access_token(user_id),
            "refresh_token": cls.create_refresh_token(user_id),
            "token_type": "Bearer",
        }

    @classmethod
    def get_token_user(cls, token: str) -> User | None:
        """Get user from token"""
        payload = cls.verify_token(token)

        if not payload:
            return None

        user_id = payload.get("user_id")

        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None


class OAuth2Service:
    """Service for OAuth2 flows"""

    @staticmethod
    def generate_authorization_code() -> str:
        """Generate OAuth2 authorization code"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def generate_client_credentials() -> dict[str, str]:
        """Generate OAuth2 client credentials"""
        return {
            "client_id": secrets.token_urlsafe(24),
            "client_secret": secrets.token_urlsafe(48),
        }

    @classmethod
    def exchange_code_for_token(
        cls, code: str, client_id: str, client_secret: str
    ) -> dict[str, str] | None:
        """
        Exchange authorization code for access token

        Args:
            code: Authorization code
            client_id: Client ID
            client_secret: Client secret

        Returns:
            Token response or None
        """
        # Verify code and credentials (implement based on storage)
        # This is a simplified version

        from authentication.models import OAuthAuthorizationCode, OAuthClient

        try:
            # Verify client credentials
            client = OAuthClient.objects.get(
                client_id=client_id, client_secret=client_secret
            )

            # Verify authorization code
            auth_code = OAuthAuthorizationCode.objects.get(
                code=code,
                client=client,
                is_used=False,
                expires_at__gt=datetime.now(timezone.utc),
            )

            # Mark code as used
            auth_code.is_used = True
            auth_code.save()

            # Generate tokens
            access_token = JWTService.create_access_token(
                str(auth_code.user.id), {"client_id": client_id}
            )
            refresh_token = JWTService.create_refresh_token(str(auth_code.user.id))

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "expires_in": JWTService.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            }

        except Exception as e:  # noqa: BLE001
            logger.error(f"Token exchange failed: {e}")
            return None

    @classmethod
    def validate_client(cls, client_id: str, client_secret: str) -> bool:
        """Validate OAuth2 client credentials"""
        from authentication.models import OAuthClient

        try:
            OAuthClient.objects.get(
                client_id=client_id, client_secret=client_secret, is_active=True
            )
            return True
        except OAuthClient.DoesNotExist:
            return False


class APIKeyService:
    """Service for API key management"""

    @staticmethod
    def generate_api_key() -> str:
        """Generate secure API key"""
        return f"sk_{secrets.token_urlsafe(48)}"

    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash API key for storage"""
        import hashlib

        return hashlib.sha256(api_key.encode()).hexdigest()

    @classmethod
    def create_api_key(cls, user_id: str, name: str) -> dict[str, str]:
        """
        Create new API key for user

        Args:
            user_id: User identifier
            name: API key name

        Returns:
            API key details
        """
        from authentication.models import APIKey

        api_key = cls.generate_api_key()
        hashed_key = cls.hash_api_key(api_key)

        user = User.objects.get(id=user_id)

        APIKey.objects.create(user=user, name=name, key_hash=hashed_key, is_active=True)

        logger.info(f"API key created for user {user_id}: {name}")

        return {
            "api_key": api_key,  # Only shown once
            "name": name,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    @classmethod
    def verify_api_key(cls, api_key: str) -> User | None:
        """
        Verify API key and return associated user

        Args:
            api_key: API key to verify

        Returns:
            User object or None
        """
        from authentication.models import APIKey

        hashed_key = cls.hash_api_key(api_key)

        try:
            api_key_obj = APIKey.objects.get(key_hash=hashed_key, is_active=True)

            # Update last used timestamp
            api_key_obj.last_used = datetime.now(timezone.utc)
            api_key_obj.save(update_fields=["last_used"])

            return api_key_obj.user
        except APIKey.DoesNotExist:
            return None
