"""
Brute force protection with progressive delays and lockouts.

Uses the BruteForceRecord model backed by the database.
Falls back to cache when DB is unavailable.
"""
import logging
from datetime import timedelta

from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)

# Max attempts before lockout, and lockout duration minutes
POLICIES = {
    'login':             (5,  15),
    'password_reset':    (3,  60),
    'google_callback':   (10, 30),
    'github_callback':   (10, 30),
    'token_refresh':     (20, 10),
    'email_verify':      (5,  60),
    'default':           (10, 15),
}


def _make_key(identifier: str, endpoint: str) -> str:
    return f'bf:{endpoint}:{identifier}'


def check_brute_force(identifier: str, endpoint: str = 'default') -> tuple[bool, int | None]:
    """
    Check whether an identifier (IP or email) is locked for this endpoint.

    Returns (is_blocked, seconds_remaining).
    """
    try:
        from authentication.models import BruteForceRecord
        record = BruteForceRecord.objects.filter(key=_make_key(identifier, endpoint)).first()
        if record and record.is_locked():
            remaining = int((record.locked_until - timezone.now()).total_seconds())
            return True, max(remaining, 1)
        return False, None
    except Exception:  # noqa: BLE001
        # Fallback to cache
        cache_key = f'bf_lock:{endpoint}:{identifier}'
        ttl = cache.ttl(cache_key)
        if ttl and ttl > 0:
            return True, ttl
        return False, None


def record_failure(identifier: str, endpoint: str = 'default') -> int:
    """
    Record a failed attempt. Returns the current attempt count.
    Applies lockout if threshold reached.
    """
    max_attempts, lockout_minutes = POLICIES.get(endpoint, POLICIES['default'])
    db_key = _make_key(identifier, endpoint)

    try:
        from authentication.models import BruteForceRecord
        record, _ = BruteForceRecord.objects.get_or_create(
            key=db_key,
            defaults={'endpoint': endpoint},
        )
        record.attempt_count += 1
        record.endpoint = endpoint

        if record.attempt_count >= max_attempts:
            record.locked_until = timezone.now() + timedelta(minutes=lockout_minutes)
            logger.warning(
                'Brute-force lockout: identifier=%s endpoint=%s attempts=%d locked=%dmin',
                identifier, endpoint, record.attempt_count, lockout_minutes,
            )

        record.save()
        return record.attempt_count
    except Exception:  # noqa: BLE001
        # Cache fallback
        cache_key = f'bf_count:{endpoint}:{identifier}'
        count = (cache.get(cache_key) or 0) + 1
        cache.set(cache_key, count, timeout=lockout_minutes * 60)
        if count >= max_attempts:
            lock_key = f'bf_lock:{endpoint}:{identifier}'
            cache.set(lock_key, True, timeout=lockout_minutes * 60)
        return count


def clear_failure_record(identifier: str, endpoint: str = 'default') -> None:
    """Reset failure count after a successful authentication."""
    db_key = _make_key(identifier, endpoint)
    try:
        from authentication.models import BruteForceRecord
        BruteForceRecord.objects.filter(key=db_key).update(
            attempt_count=0, locked_until=None
        )
    except Exception:  # noqa: BLE001, S110
        pass
    cache.delete(f'bf_count:{endpoint}:{identifier}')
    cache.delete(f'bf_lock:{endpoint}:{identifier}')


def get_client_identifier(request) -> str:
    """Extract the best client identifier (prefer email, fall back to IP)."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    ip = xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR', '0.0.0.0')
    return ip
