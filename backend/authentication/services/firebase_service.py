"""
Firebase Admin SDK integration.

Never trust client-side Firebase state – always verify ID tokens on the backend.
"""
import logging
import os

logger = logging.getLogger(__name__)

_firebase_app = None


def _get_app():
    """Lazy-initialise Firebase Admin SDK (once per process)."""
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app

    try:
        import firebase_admin
        from firebase_admin import credentials

        project_id = os.getenv('FIREBASE_PROJECT_ID')
        client_email = os.getenv('FIREBASE_CLIENT_EMAIL')
        private_key = os.getenv('FIREBASE_PRIVATE_KEY', '').replace('\\n', '\n')

        if not all([project_id, client_email, private_key]):
            logger.warning('Firebase env vars not configured – Firebase auth disabled.')
            return None

        cred_dict = {
            'type': 'service_account',
            'project_id': project_id,
            'private_key_id': os.getenv('FIREBASE_PRIVATE_KEY_ID', 'key'),
            'private_key': private_key,
            'client_email': client_email,
            'token_uri': 'https://oauth2.googleapis.com/token',
        }
        cred = credentials.Certificate(cred_dict)

        if firebase_admin._apps:
            _firebase_app = firebase_admin.get_app()
        else:
            _firebase_app = firebase_admin.initialize_app(cred)

        logger.info('Firebase Admin SDK initialised for project %s', project_id)
        return _firebase_app

    except Exception as exc:  # noqa: BLE001
        logger.error('Firebase init error: %s', exc)
        return None


def verify_firebase_token(id_token: str) -> dict | None:
    """
    Verify a Firebase ID token.

    Returns decoded token dict on success, raises ValueError with a safe message
    on any failure (expired, revoked, invalid, email-not-verified if required).
    """
    app = _get_app()
    if app is None:
        raise ValueError('Firebase authentication is not configured on this server.')

    try:
        from django.conf import settings
        from firebase_admin import auth as firebase_auth

        check_revoked = getattr(settings, 'FIREBASE_CHECK_REVOKED', True)
        decoded = firebase_auth.verify_id_token(
            id_token, app=app, check_revoked=check_revoked
        )
        return decoded

    except Exception as exc:  # noqa: BLE001
        code = getattr(exc, 'code', '')
        msg_map = {
            'ID_TOKEN_EXPIRED': 'Firebase token has expired.',
            'REVOKED_ID_TOKEN': 'Firebase token has been revoked.',
            'USER_DISABLED': 'Firebase user account is disabled.',
            'INVALID_ID_TOKEN': 'Firebase token is invalid.',
        }
        safe_msg = msg_map.get(code, 'Firebase token verification failed.')
        logger.warning('Firebase verify failed (code=%s): %s', code, exc)
        raise ValueError(safe_msg)


def get_or_create_user_from_firebase(decoded_token: dict, request=None):
    """
    Resolve a Django user from a verified Firebase decoded token.

    - If a user with the provider_user_id already exists → return it.
    - Else if a user with the same email exists → link provider.
    - Else create a new user.
    """
    from django.contrib.auth import get_user_model

    from authentication.models import AuthProvider
    from authentication.services.audit_service import log_event

    User = get_user_model()

    firebase_uid = decoded_token.get('uid') or decoded_token.get('sub')
    email = (decoded_token.get('email') or '').lower().strip()
    name = decoded_token.get('name', '')
    picture = decoded_token.get('picture', '')

    provider_record = AuthProvider.objects.filter(
        provider='firebase', provider_user_id=firebase_uid
    ).select_related('user').first()

    if provider_record:
        user = provider_record.user
        provider_record.avatar_url = picture or provider_record.avatar_url
        provider_record.display_name = name or provider_record.display_name
        provider_record.save(update_fields=['avatar_url', 'display_name', 'updated_at'])
        log_event('oauth_login', user=user, provider='firebase', request=request)
        return user, False

    created = False
    if email:
        user = User.objects.filter(email=email).first()
    else:
        user = None

    if user is None:
        username_base = email.split('@')[0] if email else f'firebase_{firebase_uid[:8]}'
        username = username_base
        suffix = 0
        while User.objects.filter(username=username).exists():
            suffix += 1
            username = f'{username_base}_{suffix}'

        user = User.objects.create_user(
            username=username,
            email=email or f'{firebase_uid}@firebase.placeholder',
            password=None,
            first_name=name.split()[0] if name else '',
            last_name=' '.join(name.split()[1:]) if name and ' ' in name else '',
        )
        if picture:
            user.avatar = picture
        user.save()
        created = True

    AuthProvider.objects.get_or_create(
        provider='firebase',
        provider_user_id=firebase_uid,
        defaults={
            'user': user,
            'email': email,
            'display_name': name,
            'avatar_url': picture,
        },
    )

    action = 'register' if created else 'provider_linked'
    log_event(action, user=user, provider='firebase', request=request)
    return user, created
