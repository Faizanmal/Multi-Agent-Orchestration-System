"""Shared DRF permission helpers."""

from django.conf import settings
from rest_framework.permissions import AllowAny, IsAuthenticated


def public_or_authenticated():
    """AllowAny in DEBUG for local UX; require auth in production."""
    return [AllowAny] if settings.DEBUG else [IsAuthenticated]
