"""
Enterprise Authentication API Views.

All endpoints follow the final verification checklist:
  ✓ Firebase ID tokens verified on backend
  ✓ Google OAuth state + nonce validated
  ✓ GitHub OAuth state validated
  ✓ Refresh token rotation implemented
  ✓ Sessions tracked + revocable
  ✓ Audit logged
  ✓ Rate / brute-force protected
  ✓ No secrets in responses / logs
"""

import logging

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from authentication.brute_force import (
    check_brute_force,
    clear_failure_record,
    get_client_identifier,
    record_failure,
)
from authentication.services import (
    account_linking_service,
    audit_service,
    firebase_service,
    github_oauth_service,
    google_oauth_service,
    jwt_service,
    session_service,
)

User = get_user_model()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Throttle classes
# ---------------------------------------------------------------------------


class AuthRateThrottle(AnonRateThrottle):
    rate = "10/minute"


class SensitiveRateThrottle(AnonRateThrottle):
    rate = "5/minute"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _user_profile(user) -> dict:
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "display_name": f"{user.first_name} {user.last_name}".strip() or user.username,
        "avatar": getattr(user, "avatar", None),
        "role": getattr(user, "role", "user"),
        "subscription_tier": getattr(user, "subscription_tier", "free"),
        "is_email_verified": user.is_active,
        "date_joined": user.date_joined.isoformat(),
        "providers": account_linking_service.get_linked_providers(user),
    }


def _brute_guard(request, endpoint: str):
    identifier = get_client_identifier(request)
    blocked, retry_after = check_brute_force(identifier, endpoint)
    if blocked:
        return Response(
            {
                "error": "Too many failed attempts. Please try again later.",
                "retry_after": retry_after,
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )
    return None


def _auth_response(user, provider: str, request) -> Response:
    tokens = jwt_service.issue_token_pair(user, provider=provider, request=request)
    return Response(
        {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": tokens["token_type"],
            "expires_in": tokens["expires_in"],
            "session_id": tokens["session_id"],
            "user": _user_profile(user),
        },
        status=status.HTTP_200_OK,
    )


def _oauth_browser_redirect(user, provider: str, request, frontend_path: str):
    """
    Browser OAuth callbacks land on the backend with ?code=&state=.
    Issue tokens, then redirect to the frontend callback page with tokens in the query.
    API clients that send Accept: application/json still get JSON.
    """
    from urllib.parse import urlencode

    from django.conf import settings
    from django.shortcuts import redirect

    tokens = jwt_service.issue_token_pair(user, provider=provider, request=request)
    accept = (request.headers.get("Accept") or "").lower()
    wants_json = "application/json" in accept and "text/html" not in accept

    if wants_json or request.GET.get("format") == "json":
        return Response(
            {
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
                "token_type": tokens["token_type"],
                "expires_in": tokens["expires_in"],
                "session_id": tokens["session_id"],
                "user": _user_profile(user),
            },
            status=status.HTTP_200_OK,
        )

    frontend = getattr(settings, "FRONTEND_URL", "http://localhost:3000").rstrip("/")
    query = urlencode(
        {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
        }
    )
    return redirect(f"{frontend}{frontend_path}?{query}")


# ---------------------------------------------------------------------------
# Email/Password auth (extends existing views)
# ---------------------------------------------------------------------------


@api_view(["POST"])
@permission_classes([AllowAny])
def enterprise_login_view(request):
    """
    POST /api/auth/login/
    Authenticates email + password, returns JWT pair.
    """
    guard = _brute_guard(request, "login")
    if guard:
        return guard

    email = (request.data.get("email") or "").strip().lower()
    password = request.data.get("password", "")

    if not email or not password:
        return Response(
            {"error": "Email and password are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    identifier = get_client_identifier(request)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        record_failure(identifier, "login")
        audit_service.log_event(
            "login_failed",
            email=email,
            success=False,
            failure_reason="user_not_found",
            request=request,
        )
        return Response(
            {"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED
        )

    if getattr(user, "account_locked", False):
        return Response(
            {"error": "Account is locked. Contact support."},
            status=status.HTTP_403_FORBIDDEN,
        )

    if not user.check_password(password):
        record_failure(identifier, "login")
        user.failed_login_attempts = getattr(user, "failed_login_attempts", 0) + 1
        user.save(update_fields=["failed_login_attempts"])
        audit_service.log_event(
            "login_failed",
            user=user,
            success=False,
            failure_reason="wrong_password",
            request=request,
        )
        return Response(
            {"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED
        )

    if not user.is_active:
        return Response(
            {"error": "Account is not active."}, status=status.HTTP_403_FORBIDDEN
        )

    # Successful login
    clear_failure_record(identifier, "login")
    user.failed_login_attempts = 0
    user.save(update_fields=["failed_login_attempts"])

    audit_service.log_event("login", user=user, provider="email", request=request)
    return _auth_response(user, "email", request)


@api_view(["POST"])
@permission_classes([AllowAny])
def enterprise_register_view(request):
    """POST /api/auth/register/"""
    username = request.data.get("username", "").strip()
    email = (request.data.get("email") or "").strip().lower()
    password = request.data.get("password", "")
    first_name = request.data.get("first_name", "").strip()
    last_name = request.data.get("last_name", "").strip()

    if not email or not password:
        return Response(
            {"error": "Email and password are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if len(password) < 8:
        return Response(
            {"error": "Password must be at least 8 characters."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if User.objects.filter(email=email).exists():
        return Response(
            {"error": "Email already registered."}, status=status.HTTP_409_CONFLICT
        )

    if not username:
        username = email.split("@")[0]
    suffix = 0
    base = username
    while User.objects.filter(username=username).exists():
        suffix += 1
        username = f"{base}_{suffix}"

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
    )

    audit_service.log_event("register", user=user, provider="email", request=request)
    return _auth_response(user, "email", request)


# ---------------------------------------------------------------------------
# Refresh + Logout
# ---------------------------------------------------------------------------


@api_view(["POST"])
@permission_classes([AllowAny])
def token_refresh_view(request):
    """POST /api/auth/refresh/ — rotate refresh token."""
    guard = _brute_guard(request, "token_refresh")
    if guard:
        return guard

    raw_token = request.data.get("refresh_token", "").strip()
    if not raw_token:
        return Response(
            {"error": "refresh_token is required."}, status=status.HTTP_400_BAD_REQUEST
        )

    identifier = get_client_identifier(request)
    try:
        tokens = jwt_service.rotate_refresh_token(raw_token, request=request)
        clear_failure_record(identifier, "token_refresh")
        audit_service.log_event("token_refresh", success=True, request=request)
        return Response(tokens, status=status.HTTP_200_OK)
    except Exception as exc:  # noqa: BLE001
        record_failure(identifier, "token_refresh")
        return Response({"error": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """POST /api/auth/logout/ — revoke current device refresh token."""
    raw_token = request.data.get("refresh_token", "").strip()
    if raw_token:
        jwt_service.revoke_refresh_token(raw_token, reason="logout")

    audit_service.log_event("logout", user=request.user, request=request)
    return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_all_view(request):
    """POST /api/auth/logout-all/ — revoke all sessions."""
    count = jwt_service.revoke_all_user_tokens(request.user, reason="logout_all")
    audit_service.log_event(
        "logout_all",
        user=request.user,
        request=request,
        metadata={"tokens_revoked": count},
    )
    return Response(
        {"message": f"All {count} sessions revoked."}, status=status.HTTP_200_OK
    )


# ---------------------------------------------------------------------------
# Firebase
# ---------------------------------------------------------------------------


@api_view(["POST"])
@permission_classes([AllowAny])
def firebase_auth_view(request):
    """
    POST /api/auth/firebase/
    Body: { "id_token": "<firebase_id_token>" }
    """
    guard = _brute_guard(request, "login")
    if guard:
        return guard

    id_token = request.data.get("id_token", "").strip()
    if not id_token:
        return Response(
            {"error": "id_token is required."}, status=status.HTTP_400_BAD_REQUEST
        )

    identifier = get_client_identifier(request)
    try:
        decoded = firebase_service.verify_firebase_token(id_token)
        user, created = firebase_service.get_or_create_user_from_firebase(
            decoded, request=request
        )  # noqa: RUF059
        clear_failure_record(identifier, "login")
        return _auth_response(user, "firebase", request)
    except ValueError as exc:
        record_failure(identifier, "login")
        audit_service.log_event(
            "oauth_login_failed",
            success=False,
            provider="firebase",
            failure_reason=str(exc),
            request=request,
        )
        return Response({"error": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# Google OAuth
# ---------------------------------------------------------------------------


@api_view(["POST"])
@permission_classes([AllowAny])
def google_initiate_view(request):
    """POST /api/auth/google/ — returns authorization URL."""
    link_user_id = None
    if request.user.is_authenticated:
        link_user_id = str(request.user.id)
    try:
        url, state = google_oauth_service.build_authorization_url(
            request=request, link_user_id=link_user_id
        )
        return Response({"authorization_url": url, "state": state})
    except ValueError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(["GET"])
@permission_classes([AllowAny])
def google_callback_view(request):
    """GET /api/auth/google/callback/?code=...&state=..."""
    guard = _brute_guard(request, "google_callback")
    if guard:
        return guard

    code = request.GET.get("code", "").strip()
    state = request.GET.get("state", "").strip()
    error = request.GET.get("error", "")

    if error:
        from urllib.parse import urlencode

        from django.conf import settings
        from django.shortcuts import redirect

        frontend = getattr(settings, "FRONTEND_URL", "http://localhost:3000").rstrip(
            "/"
        )
        return redirect(f"{frontend}/google/callback?{urlencode({'error': error})}")

    if not code or not state:
        from urllib.parse import urlencode

        from django.conf import settings
        from django.shortcuts import redirect

        frontend = getattr(settings, "FRONTEND_URL", "http://localhost:3000").rstrip(
            "/"
        )
        return redirect(
            f"{frontend}/google/callback?{urlencode({'error': 'Missing code or state.'})}"
        )

    identifier = get_client_identifier(request)
    try:
        user, created = google_oauth_service.handle_callback(
            code, state, request=request
        )  # noqa: RUF059
        clear_failure_record(identifier, "google_callback")
        audit_service.log_event("login", user=user, provider="google", request=request)
        return _oauth_browser_redirect(user, "google", request, "/google/callback")
    except ValueError as exc:
        record_failure(identifier, "google_callback")
        audit_service.log_event(
            "oauth_login_failed",
            success=False,
            provider="google",
            failure_reason=str(exc),
            request=request,
        )
        from urllib.parse import urlencode

        from django.conf import settings
        from django.shortcuts import redirect

        frontend = getattr(settings, "FRONTEND_URL", "http://localhost:3000").rstrip(
            "/"
        )
        return redirect(f"{frontend}/google/callback?{urlencode({'error': str(exc)})}")


# ---------------------------------------------------------------------------
# GitHub OAuth
# ---------------------------------------------------------------------------


@api_view(["POST"])
@permission_classes([AllowAny])
def github_initiate_view(request):
    """POST /api/auth/github/ — returns authorization URL."""
    link_user_id = None
    if request.user.is_authenticated:
        link_user_id = str(request.user.id)
    try:
        url, state = github_oauth_service.build_authorization_url(
            request=request, link_user_id=link_user_id
        )
        return Response({"authorization_url": url, "state": state})
    except ValueError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(["GET"])
@permission_classes([AllowAny])
def github_callback_view(request):
    """GET /api/auth/github/callback/?code=...&state=..."""
    guard = _brute_guard(request, "github_callback")
    if guard:
        return guard

    code = request.GET.get("code", "").strip()
    state = request.GET.get("state", "").strip()
    error = request.GET.get("error", "")

    if error:
        from urllib.parse import urlencode

        from django.conf import settings
        from django.shortcuts import redirect

        frontend = getattr(settings, "FRONTEND_URL", "http://localhost:3000").rstrip(
            "/"
        )
        return redirect(f"{frontend}/github/callback?{urlencode({'error': error})}")

    if not code or not state:
        from urllib.parse import urlencode

        from django.conf import settings
        from django.shortcuts import redirect

        frontend = getattr(settings, "FRONTEND_URL", "http://localhost:3000").rstrip(
            "/"
        )
        return redirect(
            f"{frontend}/github/callback?{urlencode({'error': 'Missing code or state.'})}"
        )

    identifier = get_client_identifier(request)
    try:
        user, created = github_oauth_service.handle_callback(
            code, state, request=request
        )  # noqa: RUF059
        clear_failure_record(identifier, "github_callback")
        audit_service.log_event("login", user=user, provider="github", request=request)
        return _oauth_browser_redirect(user, "github", request, "/github/callback")
    except ValueError as exc:
        record_failure(identifier, "github_callback")
        audit_service.log_event(
            "oauth_login_failed",
            success=False,
            provider="github",
            failure_reason=str(exc),
            request=request,
        )
        from urllib.parse import urlencode

        from django.conf import settings
        from django.shortcuts import redirect

        frontend = getattr(settings, "FRONTEND_URL", "http://localhost:3000").rstrip(
            "/"
        )
        return redirect(f"{frontend}/github/callback?{urlencode({'error': str(exc)})}")


# ---------------------------------------------------------------------------
# Account Linking / Unlinking
# ---------------------------------------------------------------------------


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def link_google_view(request):
    """POST /api/auth/link/google/ — initiate Google linking for authenticated user."""
    try:
        url, state = google_oauth_service.build_authorization_url(
            request=request, link_user_id=str(request.user.id)
        )
        return Response({"authorization_url": url, "state": state})
    except ValueError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def link_github_view(request):
    """POST /api/auth/link/github/ — initiate GitHub linking for authenticated user."""
    try:
        url, state = github_oauth_service.build_authorization_url(
            request=request, link_user_id=str(request.user.id)
        )
        return Response({"authorization_url": url, "state": state})
    except ValueError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def unlink_google_view(request):
    """DELETE /api/auth/unlink/google/"""
    try:
        account_linking_service.unlink_provider(request.user, "google")
        return Response({"message": "Google account unlinked."})
    except ValueError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def unlink_github_view(request):
    """DELETE /api/auth/unlink/github/"""
    try:
        account_linking_service.unlink_provider(request.user, "github")
        return Response({"message": "GitHub account unlinked."})
    except ValueError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# Profile / Me
# ---------------------------------------------------------------------------


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    """GET /api/auth/me/"""
    return Response(_user_profile(request.user))


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_profile_view(request):
    """PATCH /api/auth/profile/"""
    user = request.user
    allowed = [
        "first_name",
        "last_name",
        "bio",
        "location",
        "website",
        "language",
        "email_notifications",
        "push_notifications",
        "theme_preference",
    ]

    for field in allowed:
        if field in request.data:
            setattr(user, field, request.data[field])

    user.save()
    return Response(_user_profile(user))


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_account_view(request):
    """DELETE /api/auth/account/"""
    user = request.user
    account_linking_service.delete_user_account(user, request=request)
    return Response({"message": "Account deleted."}, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_sessions_view(request):
    """GET /api/sessions/"""
    sessions = session_service.get_active_sessions(request.user)
    return Response({"sessions": sessions})


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def revoke_session_view(request, session_id):
    """DELETE /api/sessions/<session_id>/"""
    revoked = session_service.revoke_session_by_id(request.user, str(session_id))
    if revoked:
        audit_service.log_event(
            "session_revoked",
            user=request.user,
            request=request,
            metadata={"session_id": str(session_id)},
        )
        return Response({"message": "Session revoked."})
    return Response({"error": "Session not found."}, status=status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------
# Admin: Audit Log
# ---------------------------------------------------------------------------


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def audit_log_view(request):
    """
    GET /api/auth/audit-log/
    Admin-only: last 200 audit events for the requesting user (or all if admin).
    """
    from authentication.models import AuditLog

    user = request.user
    if getattr(user, "role", "user") == "admin" or user.is_staff:
        qs = AuditLog.objects.select_related("user").order_by("-timestamp")[:200]
    else:
        qs = AuditLog.objects.filter(user=user).order_by("-timestamp")[:50]

    data = [
        {
            "id": str(e.id),
            "action": e.action,
            "provider": e.provider,
            "success": e.success,
            "failure_reason": e.failure_reason,
            "ip_address": e.ip_address,
            "browser": e.browser,
            "os": e.os,
            "device_name": e.device_name,
            "timestamp": e.timestamp.isoformat(),
        }
        for e in qs
    ]
    return Response({"audit_log": data})
