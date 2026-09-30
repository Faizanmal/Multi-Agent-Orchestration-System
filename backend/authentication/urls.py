"""
Authentication URL configuration.

Mounted at both /authentication/api/ (legacy) and /api/auth/ (frontend).

Existing endpoints are preserved; enterprise endpoints are added below.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

# Enterprise views
from .enterprise_views import (
    audit_log_view,
    delete_account_view,
    enterprise_login_view,
    enterprise_register_view,
    firebase_auth_view,
    github_callback_view,
    github_initiate_view,
    google_callback_view,
    google_initiate_view,
    link_github_view,
    link_google_view,
    list_sessions_view,
    logout_all_view,
    me_view,
    revoke_session_view,
    token_refresh_view,
    unlink_github_view,
    unlink_google_view,
    update_profile_view,
)
from .enterprise_views import (
    logout_view as enterprise_logout_view,
)

# Legacy views (unchanged)
from .views import (
    APIKeyViewSet,
    UserProfileView,
    UserRegistrationView,
    UserSessionListView,
    change_password_view,
    delete_api_key_view,
    forgot_password_view,
    login_view,
    logout_view,
    reset_password_view,
)

app_name = "authentication"

urlpatterns = [
    # -----------------------------------------------------------------------
    # Legacy endpoints (preserved for backward compatibility)
    # -----------------------------------------------------------------------
    path("register/", UserRegistrationView.as_view(), name="register_legacy"),
    path("login/", login_view, name="login_legacy"),
    path("logout/", logout_view, name="logout_legacy"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh_simplejwt"),
    path("profile/", UserProfileView.as_view(), name="profile_legacy"),
    path("change-password/", change_password_view, name="change_password"),
    path("forgot-password/", forgot_password_view, name="forgot_password"),
    path("reset-password/", reset_password_view, name="reset_password"),
    path("api-keys/", APIKeyViewSet.as_view(), name="api_keys"),
    path("api-keys/<uuid:key_id>/", delete_api_key_view, name="delete_api_key"),
    path("sessions/", UserSessionListView.as_view(), name="user_sessions_legacy"),
    # -----------------------------------------------------------------------
    # Enterprise endpoints
    # -----------------------------------------------------------------------
    # Email / password
    path("v2/register/", enterprise_register_view, name="register"),
    path("v2/login/", enterprise_login_view, name="login"),
    # Token management
    path("refresh/", token_refresh_view, name="token_refresh"),
    path("logout-current/", enterprise_logout_view, name="logout_current"),
    path("logout-all/", logout_all_view, name="logout_all"),
    # Firebase
    path("firebase/", firebase_auth_view, name="firebase_auth"),
    # Google OAuth
    path("google/", google_initiate_view, name="google_initiate"),
    path("google/callback/", google_callback_view, name="google_callback"),
    # GitHub OAuth
    path("github/", github_initiate_view, name="github_initiate"),
    path("github/callback/", github_callback_view, name="github_callback"),
    # Account linking
    path("link/google/", link_google_view, name="link_google"),
    path("link/github/", link_github_view, name="link_github"),
    path("unlink/google/", unlink_google_view, name="unlink_google"),
    path("unlink/github/", unlink_github_view, name="unlink_github"),
    # Profile
    path("me/", me_view, name="me"),
    path("profile/update/", update_profile_view, name="profile_update"),
    path("account/", delete_account_view, name="delete_account"),
    # Sessions
    path("sessions/list/", list_sessions_view, name="sessions_list"),
    path(
        "sessions/<uuid:session_id>/revoke/", revoke_session_view, name="session_revoke"
    ),
    # Audit
    path("audit-log/", audit_log_view, name="audit_log"),
]
