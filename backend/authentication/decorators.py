"""
Custom decorators for authentication security
"""

from functools import wraps

from django.core.cache import cache
from django.http import JsonResponse
from rest_framework import status


def rate_limit_password_reset(max_attempts=3, window_minutes=60):
    """
    Decorator to rate limit password reset requests per IP address

    Args:
        max_attempts (int): Maximum attempts allowed
        window_minutes (int): Time window in minutes
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Get client IP
            x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
            if x_forwarded_for:
                ip = x_forwarded_for.split(",")[0]
            else:
                ip = request.META.get("REMOTE_ADDR")

            # Create cache key
            cache_key = f"password_reset_limit_{ip}"

            # Get current attempt count
            attempt_count = cache.get(cache_key, 0)

            # Check if limit exceeded
            if attempt_count >= max_attempts:
                return JsonResponse(
                    {
                        "error": "Too many requests",
                        "message": "Password reset limit exceeded. Please try again later.",
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )

            # Increment attempt count
            cache.set(cache_key, attempt_count + 1, window_minutes * 60)

            # Call the original function
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
