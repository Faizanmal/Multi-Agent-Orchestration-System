from datetime import timezone

"""
API Versioning System for Applications
Supports:
- Multiple API versions (v1, v2, etc.)
- Deprecation warnings
- Backward compatibility
- Version negotiation
"""
import logging
from datetime import datetime
from functools import wraps

from rest_framework import status
from rest_framework.response import Response
from rest_framework.versioning import URLPathVersioning

logger = logging.getLogger(__name__)


class AdvancedAPIVersioning(URLPathVersioning):
    """
    Custom API versioning with deprecation support
    """

    default_version = "v1"
    allowed_versions = ["v1", "v2"]  # noqa: RUF012
    version_param = "version"

    # Deprecation schedule
    DEPRECATED_VERSIONS = {  # noqa: RUF012
        # 'v1': datetime(2025, 12, 31),  # Example: v1 deprecated on Dec 31, 2025
    }

    def determine_version(self, request, *args, **kwargs):
        """Determine API version and check deprecation"""
        version = super().determine_version(request, *args, **kwargs)

        # Check if version is deprecated
        if version in self.DEPRECATED_VERSIONS:
            deprecation_date = self.DEPRECATED_VERSIONS[version]
            days_until_deprecated = (deprecation_date - datetime.now(timezone.utc)).days

            if days_until_deprecated <= 0:
                logger.warning(f"API version {version} is deprecated")
            else:
                logger.info(
                    f"API version {version} will be deprecated in {days_until_deprecated} days"
                )

            # Add deprecation header
            request.META["HTTP_X_API_DEPRECATED"] = "true"
            request.META["HTTP_X_API_DEPRECATION_DATE"] = deprecation_date.isoformat()

        return version


def api_version(versions: list):
    """
    Decorator to mark endpoints for specific API versions

    Usage:
        @api_version(['v1', 'v2'])
        def my_view(request):
            ...
    """

    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            current_version = getattr(request, "version", "v1")

            if current_version not in versions:
                return Response(
                    {
                        "error": "API version not supported",
                        "requested_version": current_version,
                        "supported_versions": versions,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return func(request, *args, **kwargs)

        wrapper.supported_versions = versions
        return wrapper

    return decorator


def deprecated(sunset_date: str, alternative: str | None = None):
    """
    Decorator to mark endpoints as deprecated

    Args:
        sunset_date: ISO format date when endpoint will be removed
        alternative: Alternative endpoint to use
    """

    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # Add deprecation headers
            response = func(request, *args, **kwargs)

            if hasattr(response, "__setitem__"):
                response["Deprecation"] = "true"
                response["Sunset"] = sunset_date
                if alternative:
                    response["Link"] = f'<{alternative}>; rel="alternate"'

                # Log deprecation warning
                logger.warning(
                    f"Deprecated endpoint called: {request.path} "
                    f"(sunset: {sunset_date})"
                )

            return response

        wrapper.is_deprecated = True
        wrapper.sunset_date = sunset_date
        wrapper.alternative = alternative
        return wrapper

    return decorator


class APIVersionMiddleware:
    """
    Middleware to handle API versioning headers and deprecation warnings
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Add API version header
        if hasattr(request, "version"):
            response["X-API-Version"] = request.version

        # Add deprecation warnings if applicable
        if request.META.get("HTTP_X_API_DEPRECATED"):
            response["X-API-Deprecated"] = "true"
            response["X-API-Deprecation-Date"] = request.META.get(
                "HTTP_X_API_DEPRECATION_DATE", ""
            )
            response["Warning"] = (
                '299 - "This API version is deprecated. '
                'Please upgrade to the latest version."'
            )

        return response


class VersionTransformer:
    """
    Transform requests/responses between API versions
    """

    @staticmethod
    def transform_request_v1_to_v2(data: dict) -> dict:
        """Transform v1 request to v2 format"""
        # Example transformation
        transformed = data.copy()

        # Rename fields
        if "user_id" in transformed:
            transformed["userId"] = transformed.pop("user_id")

        # Add new required fields
        transformed.setdefault("apiVersion", "v2")

        return transformed

    @staticmethod
    def transform_response_v2_to_v1(data: dict) -> dict:
        """Transform v2 response to v1 format"""
        transformed = data.copy()

        # Rename fields back
        if "userId" in transformed:
            transformed["user_id"] = transformed.pop("userId")

        # Remove v2-only fields
        transformed.pop("apiVersion", None)

        return transformed

    @staticmethod
    def auto_transform(data: dict, from_version: str, to_version: str) -> dict:
        """Automatically transform data between versions"""
        if from_version == to_version:
            return data

        if from_version == "v1" and to_version == "v2":
            return VersionTransformer.transform_request_v1_to_v2(data)
        elif from_version == "v2" and to_version == "v1":
            return VersionTransformer.transform_response_v2_to_v1(data)

        logger.warning(f"No transformer available for {from_version} -> {to_version}")
        return data


def versioned_response(request, data: dict) -> Response:
    """
    Create versioned response based on request version

    Args:
        request: HTTP request with version info
        data: Response data

    Returns:
        Versioned response
    """
    version = getattr(request, "version", "v1")

    # Transform data based on version
    if version == "v1":
        # Transform to v1 format if needed
        data = VersionTransformer.transform_response_v2_to_v1(data)

    response = Response(data)
    response["X-API-Version"] = version

    return response


class APIVersionRegistry:
    """
    Registry for tracking API versions and their features
    """

    def __init__(self):
        self.versions = {}

    def register_version(
        self,
        version: str,
        features: list,
        deprecated: bool = False,
        sunset_date: str | None = None,
    ):
        """Register an API version"""
        self.versions[version] = {
            "version": version,
            "features": features,
            "deprecated": deprecated,
            "sunset_date": sunset_date,
            "registered_at": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(f"Registered API version: {version}")

    def get_version_info(self, version: str) -> dict:
        """Get information about a specific version"""
        return self.versions.get(version, {})

    def list_versions(self) -> list:
        """List all registered versions"""
        return list(self.versions.values())

    def get_latest_version(self) -> str:
        """Get the latest non-deprecated version"""
        non_deprecated = [
            v for v in self.versions.values() if not v.get("deprecated", False)
        ]

        if non_deprecated:
            # Sort by version number
            sorted_versions = sorted(
                non_deprecated, key=lambda x: x["version"], reverse=True
            )
            return sorted_versions[0]["version"]

        return "v1"


# Global version registry
version_registry = APIVersionRegistry()

# Register API versions
version_registry.register_version(
    "v1",
    features=[
        "Basic agent management",
        "Session handling",
        "Message processing",
        "Authentication",
    ],
    deprecated=False,
)

version_registry.register_version(
    "v2",
    features=[
        "Enhanced agent coordination",
        "Advanced workflow orchestration",
        "RAG support",
        "Vector database integration",
        "Improved analytics",
        "WebSocket enhancements",
    ],
    deprecated=False,
)
