"""
Role-Based Access Control (RBAC) for enterprise security
"""

import logging

from django.core.cache import cache
from rest_framework import permissions

logger = logging.getLogger(__name__)


class RBACPermission(permissions.BasePermission):
    """
    Advanced Role-Based Access Control
    Supports:
    - Role hierarchy
    - Resource-level permissions
    - Dynamic permission checking
    - Permission caching
    """

    # Define role hierarchy (higher number = more privileges)
    ROLE_HIERARCHY = {  # noqa: RUF012
        "viewer": 1,
        "user": 2,
        "developer": 3,
        "analyst": 3,
        "admin": 4,
        "super_admin": 5,
        "system": 6,
    }

    # Define permissions for each role
    ROLE_PERMISSIONS = {  # noqa: RUF012
        "viewer": [
            "view_agent",
            "view_session",
            "view_message",
            "view_dashboard",
            "view_analytics",
        ],
        "user": [
            "view_agent",
            "view_session",
            "view_message",
            "create_session",
            "send_message",
            "view_dashboard",
        ],
        "developer": [
            "view_agent",
            "create_agent",
            "update_agent",
            "view_session",
            "create_session",
            "delete_session",
            "view_message",
            "send_message",
            "execute_workflow",
            "view_workflow",
            "create_workflow",
            "view_api_integration",
            "create_api_integration",
        ],
        "analyst": [
            "view_agent",
            "view_session",
            "view_message",
            "view_dashboard",
            "view_analytics",
            "export_data",
            "create_report",
            "view_report",
        ],
        "admin": [
            "view_agent",
            "create_agent",
            "update_agent",
            "delete_agent",
            "view_session",
            "create_session",
            "delete_session",
            "view_message",
            "send_message",
            "delete_message",
            "manage_users",
            "view_users",
            "update_users",
            "view_dashboard",
            "view_analytics",
            "execute_workflow",
            "create_workflow",
            "delete_workflow",
            "manage_api_integration",
            "manage_settings",
        ],
        "super_admin": ["*"],  # All permissions
        "system": ["*"],  # All permissions (for system processes)
    }

    def has_permission(self, request, view):
        """
        Check if user has permission to access this view
        """
        if not request.user or not request.user.is_authenticated:
            return False

        # Super users always have access
        if request.user.is_superuser:
            return True

        # Get required permission from view
        required_permission = self._get_required_permission(request, view)

        if not required_permission:
            # No specific permission required
            return True

        # Check if user has required permission
        return self._user_has_permission(request.user, required_permission)

    def has_object_permission(self, request, view, obj):
        """
        Check if user has permission to access this specific object
        """
        if not request.user or not request.user.is_authenticated:
            return False

        # Super users always have access
        if request.user.is_superuser:
            return True

        # Check object ownership
        if hasattr(obj, "owner") and obj.owner == request.user:
            return True

        if hasattr(obj, "user") and obj.user == request.user:
            return True

        # Check role-based permissions
        required_permission = self._get_required_permission(request, view)
        if required_permission:
            return self._user_has_permission(request.user, required_permission)

        return False

    def _get_required_permission(self, request, view):
        """
        Determine required permission based on request method and view
        """
        # Check if view has explicit permission requirements
        if hasattr(view, "required_permission"):
            return view.required_permission

        # Derive permission from view action
        action_permission_map = {
            "list": "view",
            "retrieve": "view",
            "create": "create",
            "update": "update",
            "partial_update": "update",
            "destroy": "delete",
        }

        if hasattr(view, "action"):
            action = view.action
            permission_type = action_permission_map.get(action, action)
        else:
            # Derive from HTTP method
            method_permission_map = {
                "GET": "view",
                "POST": "create",
                "PUT": "update",
                "PATCH": "update",
                "DELETE": "delete",
            }
            permission_type = method_permission_map.get(request.method, "view")

        # Get resource name from view
        if hasattr(view, "queryset") and hasattr(view.queryset, "model"):
            resource = view.queryset.model.__name__.lower()
        elif hasattr(view, "basename"):
            resource = view.basename
        else:
            resource = (
                view.__class__.__name__.lower()
                .replace("viewset", "")
                .replace("view", "")
            )

        return f"{permission_type}_{resource}"

    def _user_has_permission(self, user, permission):
        """
        Check if user has specific permission based on their role
        """
        # Check cache first
        cache_key = f"rbac:user_{user.id}:perm_{permission}"
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        # Get user role
        user_role = self._get_user_role(user)

        # Get permissions for role
        role_permissions = self.ROLE_PERMISSIONS.get(user_role, [])

        # Check if role has all permissions
        if "*" in role_permissions:
            cache.set(cache_key, True, 300)  # Cache for 5 minutes
            return True

        # Check if specific permission is granted
        has_perm = permission in role_permissions

        # If not found, check role hierarchy
        if not has_perm:
            has_perm = self._check_inherited_permissions(user_role, permission)

        cache.set(cache_key, has_perm, 300)  # Cache for 5 minutes
        return has_perm

    def _get_user_role(self, user):
        """
        Get user's primary role
        """
        # Check if user has role attribute
        if hasattr(user, "role"):
            return user.role

        # Check user groups
        if user.groups.exists():
            role_name = user.groups.first().name.lower()
            if role_name in self.ROLE_HIERARCHY:
                return role_name

        # Default role
        return "user"

    def _check_inherited_permissions(self, role, permission):
        """
        Check if permission is inherited from lower-level roles
        """
        current_level = self.ROLE_HIERARCHY.get(role, 0)

        for other_role, level in self.ROLE_HIERARCHY.items():
            if level < current_level:
                other_permissions = self.ROLE_PERMISSIONS.get(other_role, [])
                if permission in other_permissions:
                    return True

        return False


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission to only allow owners or admins to access objects
    """

    def has_object_permission(self, request, view, obj):
        # Admins have full access
        if request.user.is_staff or request.user.is_superuser:
            return True

        # Check ownership
        if hasattr(obj, "owner"):
            return obj.owner == request.user

        if hasattr(obj, "user"):
            return obj.user == request.user

        return False


class IsAdminUser(permissions.BasePermission):
    """
    Permission to only allow admin users
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (request.user.is_staff or request.user.is_superuser)
        )


class ReadOnly(permissions.BasePermission):
    """
    Permission to only allow read-only access
    """

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS
