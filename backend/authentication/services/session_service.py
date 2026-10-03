"""
Session / device parsing utilities.
"""

import logging

logger = logging.getLogger(__name__)


def _get_client_ip(request) -> str | None:
    """Return the real client IP, respecting X-Forwarded-For."""
    xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def parse_device_info(request) -> dict:
    """Extract device/browser/OS info from a Django request."""
    if request is None:
        return {}

    ua_string = request.META.get("HTTP_USER_AGENT", "")
    ip = _get_client_ip(request)

    device_name = "Unknown"
    device_type = "unknown"
    browser = "Unknown"
    os_name = "Unknown"

    try:
        from user_agents import parse as ua_parse

        ua = ua_parse(ua_string)
        device_name = ua.device.family or "Unknown"
        device_type = (
            "mobile"
            if ua.is_mobile
            else "tablet" if ua.is_tablet else "bot" if ua.is_bot else "desktop"
        )
        browser = f"{ua.browser.family} {ua.browser.version_string}".strip()
        os_name = f"{ua.os.family} {ua.os.version_string}".strip()
    except Exception:  # noqa: BLE001, S110
        pass

    return {
        "device_name": device_name,
        "device_type": device_type,
        "browser": browser,
        "os": os_name,
        "ip_address": ip,
        "user_agent": ua_string,
    }


def get_active_sessions(user) -> list:
    """Return serialised list of active refresh token records as session view."""
    from django.utils import timezone

    from authentication.models import RefreshToken

    tokens = (
        RefreshToken.objects.filter(user=user, is_active=True)
        .exclude(expires_at__lt=timezone.now())
        .order_by("-created_at")
    )

    return [
        {
            "id": str(t.id),
            "session_id": str(t.session_id) if t.session_id else None,
            "provider": t.provider,
            "device_name": t.device_name,
            "device_type": t.device_type,
            "browser": t.browser,
            "os": t.os,
            "ip_address": t.ip_address,
            "created_at": t.created_at.isoformat(),
            "last_used_at": t.last_used_at.isoformat() if t.last_used_at else None,
            "expires_at": t.expires_at.isoformat(),
        }
        for t in tokens
    ]


def revoke_session_by_id(user, session_record_id: str) -> bool:
    """Revoke a specific refresh token record belonging to the user."""
    import uuid

    from authentication.models import RefreshToken

    try:
        token = RefreshToken.objects.get(
            id=uuid.UUID(session_record_id), user=user, is_active=True
        )
        token.revoke("session_revoked_by_user")
        return True
    except (RefreshToken.DoesNotExist, ValueError):
        return False
