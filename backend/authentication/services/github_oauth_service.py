"""
GitHub OAuth 2.0 service.

Flow:
  1. POST /auth/github/initiate → returns authorization URL + state
  2. GitHub redirects to GET /auth/github/callback?code=...&state=...
  3. Backend exchanges code, fetches user + verified email, resolves user
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

GITHUB_AUTH_URL = 'https://github.com/login/oauth/authorize'
GITHUB_TOKEN_URL = 'https://github.com/login/oauth/access_token'
GITHUB_USER_URL = 'https://api.github.com/user'
GITHUB_EMAILS_URL = 'https://api.github.com/user/emails'


def _client_id() -> str:
    val = getattr(settings, 'GITHUB_CLIENT_ID', None) or os.getenv('GITHUB_CLIENT_ID')
    if not val:
        raise ValueError('GITHUB_CLIENT_ID is not configured.')
    return val


def _client_secret() -> str:
    val = getattr(settings, 'GITHUB_CLIENT_SECRET', None) or os.getenv('GITHUB_CLIENT_SECRET')
    if not val:
        raise ValueError('GITHUB_CLIENT_SECRET is not configured.')
    return val


def _callback_url() -> str:
    return (
        getattr(settings, 'GITHUB_REDIRECT_URI', None)
        or os.getenv('GITHUB_REDIRECT_URI')
        or f"{getattr(settings, 'BACKEND_URL', 'http://localhost:8000')}/api/auth/github/callback/"
    )


# ---------------------------------------------------------------------------
# Step 1 – authorization URL
# ---------------------------------------------------------------------------

def build_authorization_url(
    request=None,
    link_user_id: str | None = None,
) -> tuple[str, str]:
    from authentication.models import OAuthState

    state = secrets.token_urlsafe(32)

    OAuthState.objects.create(
        state=state,
        provider='github',
        redirect_uri=_callback_url(),
        user_id=uuid.UUID(link_user_id) if link_user_id else None,
        ip_address=_get_ip(request),
        expires_at=timezone.now() + timedelta(minutes=10),
    )

    params = {
        'client_id': _client_id(),
        'redirect_uri': _callback_url(),
        'scope': 'read:user user:email',
        'state': state,
        'allow_signup': 'true',
    }
    query = '&'.join(f'{k}={v}' for k, v in params.items())
    return f'{GITHUB_AUTH_URL}?{query}', state


# ---------------------------------------------------------------------------
# Step 2 – handle callback
# ---------------------------------------------------------------------------

def handle_callback(code: str, state: str, request=None):
    """
    Validate state, exchange code, fetch user profile + verified email.
    Returns (user, created).
    """
    from authentication.models import OAuthState

    try:
        state_record = OAuthState.objects.get(state=state, provider='github')
    except OAuthState.DoesNotExist:
        raise ValueError('Invalid OAuth state parameter.')

    if not state_record.is_valid():
        raise ValueError('OAuth state has expired or already been used.')

    state_record.used = True
    state_record.save(update_fields=['used'])

    access_token = _exchange_code(code)
    github_user = _fetch_user(access_token)
    email = _get_primary_verified_email(access_token, github_user)

    link_user_id = state_record.user_id
    return _resolve_user(github_user, email, link_user_id=link_user_id, request=request)


def _exchange_code(code: str) -> str:
    resp = http_requests.post(
        GITHUB_TOKEN_URL,
        data={
            'client_id': _client_id(),
            'client_secret': _client_secret(),
            'code': code,
            'redirect_uri': _callback_url(),
        },
        headers={'Accept': 'application/json'},
        timeout=10,
    )
    if not resp.ok:
        raise ValueError('GitHub token exchange failed.')
    data = resp.json()
    token = data.get('access_token')
    if not token:
        error = data.get('error_description', data.get('error', 'Unknown error'))
        raise ValueError(f'GitHub access token error: {error}')
    return token


def _fetch_user(access_token: str) -> dict:
    resp = http_requests.get(
        GITHUB_USER_URL,
        headers={
            'Authorization': f'token {access_token}',
            'Accept': 'application/vnd.github.v3+json',
        },
        timeout=10,
    )
    if not resp.ok:
        raise ValueError('Failed to fetch GitHub user profile.')
    return resp.json()


def _get_primary_verified_email(access_token: str, user_data: dict) -> str | None:
    """
    Fetch the primary verified email from GitHub.
    Falls back to the public email field, which may be None.
    """
    public_email = user_data.get('email')

    try:
        resp = http_requests.get(
            GITHUB_EMAILS_URL,
            headers={
                'Authorization': f'token {access_token}',
                'Accept': 'application/vnd.github.v3+json',
            },
            timeout=10,
        )
        if resp.ok:
            emails = resp.json()
            # Prefer primary + verified
            for e in emails:
                if e.get('primary') and e.get('verified'):
                    return e['email'].lower().strip()
            # Fall back to any verified
            for e in emails:
                if e.get('verified'):
                    return e['email'].lower().strip()
    except Exception:  # noqa: BLE001, S110
        pass

    return public_email.lower().strip() if public_email else None


def _resolve_user(github_user: dict, email: str | None, link_user_id=None, request=None):
    from django.contrib.auth import get_user_model

    from authentication.models import AuthProvider
    from authentication.services.audit_service import log_event

    User = get_user_model()

    github_id = str(github_user.get('id', ''))
    login = github_user.get('login', '')
    name = github_user.get('name', '') or login
    avatar = github_user.get('avatar_url', '')

    if not github_id:
        raise ValueError('GitHub user info missing id.')

    # Account linking
    if link_user_id:
        try:
            user = User.objects.get(id=link_user_id)
            AuthProvider.objects.get_or_create(
                provider='github',
                provider_user_id=github_id,
                defaults={
                    'user': user,
                    'email': email or '',
                    'display_name': name,
                    'avatar_url': avatar,
                },
            )
            log_event('provider_linked', user=user, provider='github', request=request)
            return user, False
        except User.DoesNotExist:
            raise ValueError('Link target user not found.')

    provider_record = AuthProvider.objects.filter(
        provider='github', provider_user_id=github_id
    ).select_related('user').first()

    if provider_record:
        user = provider_record.user
        provider_record.avatar_url = avatar
        provider_record.display_name = name
        provider_record.save(update_fields=['avatar_url', 'display_name', 'updated_at'])
        log_event('oauth_login', user=user, provider='github', request=request)
        return user, False

    created = False
    user = User.objects.filter(email=email).first() if email else None

    if user is None:
        username_base = login or f'github_{github_id[:8]}'
        username = username_base
        suffix = 0
        while User.objects.filter(username=username).exists():
            suffix += 1
            username = f'{username_base}_{suffix}'

        user = User.objects.create_user(
            username=username,
            email=email or f'{github_id}@github.placeholder',
            password=None,
            first_name=name.split()[0] if name else '',
            last_name=' '.join(name.split()[1:]) if name and ' ' in name else '',
        )
        if avatar:
            user.avatar = avatar
        user.save()
        created = True

    AuthProvider.objects.get_or_create(
        provider='github',
        provider_user_id=github_id,
        defaults={
            'user': user,
            'email': email or '',
            'display_name': name,
            'avatar_url': avatar,
        },
    )

    action = 'register' if created else 'oauth_login'
    log_event(action, user=user, provider='github', request=request)
    return user, created


def _get_ip(request) -> str | None:
    if request is None:
        return None
    xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    return xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR')
