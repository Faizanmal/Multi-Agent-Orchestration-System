"""
Enterprise JWT Service – single source of truth for all JWT operations.

Access token:  15-minute lifespan, signed HS256, full OIDC-style claims.
Refresh token: opaque 64-byte random, SHA-256 hashed in DB, rotated on use.
"""
import hashlib
import logging
import os
import secrets
import uuid
from datetime import datetime, timedelta
from datetime import timezone as dt_timezone

import jwt
from django.conf import settings
from django.utils import timezone
from rest_framework import exceptions

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_secret(key_name: str, fallback: str | None = None) -> str:
    val = getattr(settings, key_name, None) or os.getenv(key_name) or fallback
    if not val:
        raise RuntimeError(f"Missing required setting: {key_name}")
    return val


def _jwt_secret() -> str:
    return _get_secret('JWT_SECRET')


def _jwt_refresh_secret() -> str:
    return getattr(settings, 'JWT_REFRESH_SECRET', None) or _jwt_secret()


def _issuer() -> str:
    return getattr(settings, 'JWT_ISSUER', 'multiagent-ai')


def _audience() -> str:
    return getattr(settings, 'JWT_AUDIENCE', 'multiagent-ai-client')


# ---------------------------------------------------------------------------
# Access token
# ---------------------------------------------------------------------------

def generate_access_token(
    user,
    provider: str = 'email',
    session_id: str | None = None,
) -> str:
    """Return a signed JWT access token valid for 15 minutes."""
    now = datetime.now(dt_timezone.utc)
    jti = str(uuid.uuid4())
    payload = {
        'sub': str(user.id),
        'email': user.email,
        'role': getattr(user, 'role', 'user'),
        'sessionId': session_id or jti,
        'provider': provider,
        'jti': jti,
        'iss': _issuer(),
        'aud': _audience(),
        'iat': now,
        'exp': now + timedelta(minutes=15),
        'type': 'access',
    }
    return jwt.encode(payload, _jwt_secret(), algorithm='HS256')


def decode_access_token(token: str) -> dict:
    """Validate and decode an access token; raise AuthenticationFailed on any error."""
    try:
        payload = jwt.decode(
            token,
            _jwt_secret(),
            algorithms=['HS256'],
            audience=_audience(),
            issuer=_issuer(),
            options={"require": ["sub", "email", "jti", "exp", "iss", "aud"]},
        )
        if payload.get('type') != 'access':
            raise exceptions.AuthenticationFailed('Invalid token type.')
        return payload
    except jwt.ExpiredSignatureError:
        raise exceptions.AuthenticationFailed('Access token has expired.')
    except jwt.InvalidAudienceError:
        raise exceptions.AuthenticationFailed('Invalid token audience.')
    except jwt.InvalidIssuerError:
        raise exceptions.AuthenticationFailed('Invalid token issuer.')
    except jwt.MissingRequiredClaimError as exc:
        raise exceptions.AuthenticationFailed(f'Missing claim: {exc}')
    except jwt.InvalidTokenError as exc:
        raise exceptions.AuthenticationFailed(f'Invalid token: {exc}')


# ---------------------------------------------------------------------------
# Opaque refresh token helpers
# ---------------------------------------------------------------------------

def generate_raw_refresh_token() -> str:
    """Return a 64-byte URL-safe random refresh token (never persisted directly)."""
    return secrets.token_urlsafe(64)


def hash_refresh_token(raw: str) -> str:
    """SHA-256 digest of the raw refresh token (safe to persist)."""
    return hashlib.sha256(raw.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Full token pair
# ---------------------------------------------------------------------------

def issue_token_pair(
    user,
    provider: str = 'email',
    request=None,
    revoke_existing: bool = False,
) -> dict:
    """
    Mint and persist an access + refresh token pair.

    Returns a dict with:
        access_token, refresh_token, token_type, expires_in,
        user (serialized lightweight profile)
    """
    from authentication.models import EnterpriseRefreshToken
    from authentication.services.session_service import parse_device_info

    if revoke_existing:
        EnterpriseRefreshToken.objects.filter(
            user=user, is_active=True
        ).update(
            is_active=False,
            revoked_at=timezone.now(),
            revoke_reason='new_login_revoke_all',
        )

    device = parse_device_info(request) if request else {}
    family = uuid.uuid4()
    session_id = str(uuid.uuid4())

    access = generate_access_token(user, provider=provider, session_id=session_id)

    raw_refresh = generate_raw_refresh_token()
    hashed = hash_refresh_token(raw_refresh)

    EnterpriseRefreshToken.objects.create(
        user=user,
        hashed_token=hashed,
        family=family,
        session_id=uuid.UUID(session_id),
        provider=provider,
        device_name=device.get('device_name', ''),
        device_type=device.get('device_type', ''),
        browser=device.get('browser', ''),
        os=device.get('os', ''),
        ip_address=device.get('ip_address'),
        user_agent=device.get('user_agent', ''),
        expires_at=timezone.now() + timedelta(days=30),
    )

    return {
        'access_token': access,
        'refresh_token': raw_refresh,
        'token_type': 'Bearer',
        'expires_in': 900,
        'session_id': session_id,
    }


def rotate_refresh_token(raw_token: str, request=None) -> dict:
    """
    Validate the incoming refresh token, revoke it, and mint a fresh pair.

    Implements the "refresh token family" theft-detection pattern:
    if the token was already revoked, the entire family is revoked.
    """
    from authentication.models import EnterpriseRefreshToken
    from authentication.services.session_service import parse_device_info

    hashed = hash_refresh_token(raw_token)

    try:
        record = EnterpriseRefreshToken.objects.select_related('user').get(
            hashed_token=hashed
        )
    except EnterpriseRefreshToken.DoesNotExist:
        raise exceptions.AuthenticationFailed('Refresh token not found.')

    if not record.is_active:
        # Possible token theft – revoke entire family
        EnterpriseRefreshToken.objects.filter(
            family=record.family, is_active=True
        ).update(
            is_active=False,
            revoked_at=timezone.now(),
            revoke_reason='theft_detected',
        )
        logger.warning(
            'Refresh token reuse detected for user %s – family %s revoked.',
            record.user_id, record.family,
        )
        raise exceptions.AuthenticationFailed(
            'Refresh token reuse detected. All sessions revoked.'
        )

    if timezone.now() >= record.expires_at:
        record.revoke('expired')
        raise exceptions.AuthenticationFailed('Refresh token expired.')

    user = record.user
    provider = record.provider
    family = record.family

    record.revoke('rotated')

    device = parse_device_info(request) if request else {}
    session_id = str(record.session_id) if record.session_id else str(uuid.uuid4())

    access = generate_access_token(user, provider=provider, session_id=session_id)
    new_raw = generate_raw_refresh_token()
    new_hashed = hash_refresh_token(new_raw)

    EnterpriseRefreshToken.objects.create(
        user=user,
        hashed_token=new_hashed,
        family=family,
        session_id=record.session_id,
        provider=provider,
        device_name=device.get('device_name', record.device_name),
        device_type=device.get('device_type', record.device_type),
        browser=device.get('browser', record.browser),
        os=device.get('os', record.os),
        ip_address=device.get('ip_address', record.ip_address),
        user_agent=device.get('user_agent', record.user_agent),
        expires_at=timezone.now() + timedelta(days=30),
    )

    return {
        'access_token': access,
        'refresh_token': new_raw,
        'token_type': 'Bearer',
        'expires_in': 900,
        'session_id': session_id,
    }


def revoke_refresh_token(raw_token: str, reason: str = 'logout') -> bool:
    """Revoke a single refresh token. Returns True if found and revoked."""
    from authentication.models import EnterpriseRefreshToken
    hashed = hash_refresh_token(raw_token)
    updated = EnterpriseRefreshToken.objects.filter(
        hashed_token=hashed, is_active=True
    ).update(
        is_active=False,
        revoked_at=timezone.now(),
        revoke_reason=reason,
    )
    return updated > 0


def revoke_all_user_tokens(user, reason: str = 'logout_all') -> int:
    """Revoke every active refresh token for a user. Returns count revoked."""
    from authentication.models import EnterpriseRefreshToken
    updated = EnterpriseRefreshToken.objects.filter(
        user=user, is_active=True
    ).update(
        is_active=False,
        revoked_at=timezone.now(),
        revoke_reason=reason,
    )
    return updated
