"""
Pytest configuration for the backend test suite.
"""

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")


def pytest_configure(config):
    os.environ.setdefault("JWT_SECRET", "test-secret-at-least-32-chars-long-enough")
    os.environ.setdefault("JWT_ISSUER", "test-issuer")
    os.environ.setdefault("JWT_AUDIENCE", "test-audience")
    django.setup()
