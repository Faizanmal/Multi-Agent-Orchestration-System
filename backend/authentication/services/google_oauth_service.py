"""
Google OAuth 2.0 / OpenID Connect service.

Flow:
  1. Frontend calls POST /auth/google/initiate → gets authorization URL + state
  2. User is redirected to Google
  3. Google redirects to GET /auth/google/callback?code=...&state=...
  4. Backend exchanges code, verifies ID token, resolves user, issues JWT pair
"""
import logging
import os
import secrets
import uuid
from datetime import timedelta

import requests as http_requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_USERINFO_URL = 'https://openidconnect.googleapis.com/v1/userinfo'
GOOGLE_CERTS_URL = 'https://www.googleapis.com/oauth2/v3/certs'


def _client_id() -> str:
    val = getattr(settings, 'GOOGLE_CLIENT_ID', None) or os.getenv('GOOGLE_CLIENT_ID')
    if not val:
        raise ValueError('GOOGLE_CLIENT_ID is not configured.')
    return val


def _client_secret() -> str:
    val = getattr(settings, 'GOOGLE_CLIENT_SECRET', None) or os.getenv('GOOGLE_CLIENT_SECRET')
    if not val:
        raise ValueError('GOOGLE_CLIENT_SECRET is not configured.')
    return val


def _callback_url() -> str:
    return (
        getattr(settings, 'GOOGLE_REDIRECT_URI', None)
        or os.getenv('GOOGLE_REDIRECT_URI')
        or f"{getattr(settings, 'BACKEND_URL', 'http://localhost:8000')}/api/auth/google/callback/"
    )


# ---------------------------------------------------------------------------
# Step 1 – build the authorization URL
# ---------------------------------------------------------------------------

def build_authorization_url(
    request=None,
    link_user_id: str | None = None,
) -> tuple[str, str]:
    """
    Return (authorization_url, state).
    Persists an OAuthState record for CSRF validation.
    """
    from authentication.models import OAuthState

    state = secrets.token_urlsafe(32)
    code_verifier = secrets.token_urlsafe(64)

    OAuthState.objects.create(
        state=state,
        provider='google',
        code_verifier=code_verifier,
        redirect_uri=_callback_url(),
        user_id=uuid.UUID(link_user_id) if link_user_id else None,
        ip_address=_get_ip(request),
        expires_at=timezone.now() + timedelta(minutes=10),
    )

    params = {
        'client_id': _client_id(),
        'redirect_uri': _callback_url(),
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'access_type': 'offline',
        'prompt': 'select_account',
        'nonce': secrets.token_urlsafe(16),
    }
    query = '&'.join(f'{k}={v}' for k, v in params.items())
    return f'{GOOGLE_AUTH_URL}?{query}', state


# ---------------------------------------------------------------------------
# Step 2 – exchange code for tokens + verify
# ---------------------------------------------------------------------------

def handle_callback(code: str, state: str, request=None):
    """
    Validate state, exchange code for tokens, verify ID token,
    resolve/create user. Returns (user, created).
    """
    from authentication.models import OAuthState

    try:
        state_record = OAuthState.objects.get(state=state, provider='google')
    except OAuthState.DoesNotExist:
        raise ValueError('Invalid OAuth state parameter.')

    if not state_record.is_valid():
        raise ValueError('OAuth state has expired or already been used.')

    state_record.used = True
    state_record.save(update_fields=['used'])

    token_data = _exchange_code(code, state_record.redirect_uri or _callback_url())
    id_token = token_data.get('id_token')
    if not id_token:
        raise ValueError('No id_token in Google response.')

    user_info = _verify_id_token(id_token)
    link_user_id = state_record.user_id

    return _resolve_user(user_info, link_user_id=link_user_id, request=request)


def _exchange_code(code: str, redirect_uri: str) -> dict:
    resp = http_requests.post(
        GOOGLE_TOKEN_URL,
        data={
            'code': code,
            'client_id': _client_id(),
            'client_secret': _client_secret(),
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code',
        },
        timeout=10,
    )
    if not resp.ok:
        logger.warning('Google token exchange failed: %s', resp.text)
        raise ValueError('Google token exchange failed.')
    return resp.json()


def _verify_id_token(id_token: str) -> dict:
    """Verify Google ID token using google-auth library."""
    try:
        from google.auth.transport import requests as google_requests
        from google.oauth2 import id_token as google_id_token

        request_obj = google_requests.Request()
        info = google_id_token.verify_oauth2_token(
            id_token, request_obj, _client_id()
        )
        return info
    except Exception as exc:  # noqa: BLE001
        logger.warning('Google ID token verification failed: %s', exc)
        raise ValueError(f'Google ID token is invalid: {exc}')


def _resolve_user(user_info: dict, link_user_id=None, request=None):
    from django.contrib.auth import get_user_model

    from authentication.models import AuthProvider
    from authentication.services.audit_service import log_event

    User = get_user_model()

    google_sub = user_info.get('sub')
    email = (user_info.get('email') or '').lower().strip()
    name = user_info.get('name', '')
    picture = user_info.get('picture', '')

    if not google_sub:
        raise ValueError('Google user info missing sub claim.')

    # Account linking (logged-in user wants to link Google)
    if link_user_id:
        try:
            user = User.objects.get(id=link_user_id)
            AuthProvider.objects.get_or_create(
                provider='google',
                provider_user_id=google_sub,
                defaults={
                    'user': user,
                    'email': email,
                    'display_name': name,
                    'avatar_url': picture,
                },
            )
            log_event('provider_linked', user=user, provider='google', request=request)
            return user, False
        except User.DoesNotExist:
            raise ValueError('Link target user not found.')

    provider_record = AuthProvider.objects.filter(
        provider='google', provider_user_id=google_sub
    ).select_related('user').first()

    if provider_record:
        user = provider_record.user
        provider_record.avatar_url = picture
        provider_record.display_name = name
        provider_record.save(update_fields=['avatar_url', 'display_name', 'updated_at'])
        log_event('oauth_login', user=user, provider='google', request=request)
        return user, False

    created = False
    user = User.objects.filter(email=email).first() if email else None

    if user is None:
        username_base = email.split('@')[0] if email else f'google_{google_sub[:8]}'
        username = username_base
        suffix = 0
        while User.objects.filter(username=username).exists():
            suffix += 1
            username = f'{username_base}_{suffix}'

        user = User.objects.create_user(
            username=username,
            email=email,
            password=None,
            first_name=name.split()[0] if name else '',
            last_name=' '.join(name.split()[1:]) if name and ' ' in name else '',
        )
        if picture:
            user.avatar = picture
        user.save()
        created = True

    AuthProvider.objects.get_or_create(
        provider='google',
        provider_user_id=google_sub,
        defaults={
            'user': user,
            'email': email,
            'display_name': name,
            'avatar_url': picture,
        },
    )

    action = 'register' if created else 'oauth_login'
    log_event(action, user=user, provider='google', request=request)
    return user, created


def _get_ip(request) -> str | None:
    if request is None:
        return None
    xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')
