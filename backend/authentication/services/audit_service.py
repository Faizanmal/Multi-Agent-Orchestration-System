"""
Audit logging service – write immutable audit records.
Never logs: passwords, tokens, secrets, or any credential material.
"""

import logging

from authentication.services.session_service import parse_device_info

logger = logging.getLogger("authentication.audit")


def log_event(
    action: str,
    user=None,
    email: str = "",
    provider: str = "",
    success: bool = True,
    failure_reason: str = "",
    request=None,
    metadata: dict | None = None,
) -> None:
    """
    Persist an AuditLog record. Safe to call from any thread; any exceptions
    are caught and logged so they never propagate into the auth flow.
    """
    try:
        from authentication.models import AuditLog

        device = parse_device_info(request) if request else {}
        request_id = getattr(request, "request_id", "") if request else ""

        record = AuditLog(
            user=user,
            user_email=email or (user.email if user else ""),
            action=action,
            provider=provider or "",
            success=success,
            failure_reason=failure_reason or "",
            ip_address=device.get("ip_address"),
            user_agent=device.get("user_agent", ""),
            device_name=device.get("device_name", ""),
            browser=device.get("browser", ""),
            os=device.get("os", ""),
            metadata=metadata or {},
            request_id=request_id,
        )
        record.save()

        level = logging.INFO if success else logging.WARNING
        logger.log(
            level,
            "AUDIT action=%s user=%s provider=%s success=%s reason=%s ip=%s",
            action,
            record.user_email,
            provider,
            success,
            failure_reason,
            device.get("ip_address"),
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to write audit log for action=%s: %s", action, exc)
