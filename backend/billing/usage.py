"""Durable workspace usage metering for monthly message quotas."""

from django.db import IntegrityError
from django.db.models import F
from django.utils import timezone

from .models import MonthlyUsage

# Monthly message limits by subscription tier
TIER_MESSAGE_LIMITS = {
    "free": 100,
    "pro": 10_000,
    "enterprise": 1_000_000,
}


def _period():
    today = timezone.now().date()
    return today.replace(day=1)


def _period_key() -> str:
    return _period().strftime("%Y-%m")


def get_message_usage(workspace_id) -> int:
    return int(
        MonthlyUsage.objects.filter(
            workspace_id=workspace_id,
            period=_period(),
        )
        .values_list("message_count", flat=True)
        .first()
        or 0
    )


def increment_message_usage(workspace_id, amount: int = 1) -> int:
    if amount < 1:
        raise ValueError("Usage increment must be positive")

    try:
        usage, _ = MonthlyUsage.objects.get_or_create(
            workspace_id=workspace_id,
            period=_period(),
        )
    except IntegrityError:
        # Two first requests may race to create the same monthly row.
        usage = MonthlyUsage.objects.get(
            workspace_id=workspace_id,
            period=_period(),
        )

    MonthlyUsage.objects.filter(pk=usage.pk).update(
        message_count=F("message_count") + amount,
    )
    usage.refresh_from_db(fields=["message_count"])
    return int(usage.message_count)


def get_tier_limit(tier: str) -> int:
    return TIER_MESSAGE_LIMITS.get(tier or "free", TIER_MESSAGE_LIMITS["free"])


def usage_summary(workspace) -> dict:
    tier = getattr(workspace, "subscription_tier", None) or "free"
    used = get_message_usage(workspace.id)
    limit = get_tier_limit(tier)
    percentage = min(100, round((used / limit) * 100)) if limit else 0
    return {
        "used_tokens": used,
        "total_tokens": limit,
        "percentage": percentage,
        "unit": "messages",
        "period": _period_key(),
    }
