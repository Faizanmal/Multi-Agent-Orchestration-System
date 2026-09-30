import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class CustomUser(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    avatar = models.URLField(blank=True, null=True)
    role = models.CharField(
        max_length=20, 
        choices=[('admin', 'Admin'), ('user', 'User'), ('viewer', 'Viewer')], 
        default='user'
    )
    subscription_tier = models.CharField(
        max_length=20,
        choices=[('free', 'Free'), ('pro', 'Pro'), ('enterprise', 'Enterprise')],
        default='free'
    )
    is_2fa_enabled = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    user_timezone = models.CharField(max_length=50, default='UTC')
    last_activity = models.DateTimeField(auto_now=True)
    
    # Enhanced fields
    email = models.EmailField(unique=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    
    # Account security
    last_password_change = models.DateTimeField(default=timezone.now)
    password_reset_required = models.BooleanField(default=False)
    account_locked = models.BooleanField(default=False)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    last_failed_login = models.DateTimeField(blank=True, null=True)
    
    # Preferences
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    marketing_emails = models.BooleanField(default=False)
    theme_preference = models.CharField(
        max_length=10, 
        choices=[('light', 'Light'), ('dark', 'Dark'), ('auto', 'Auto')],
        default='auto'
    )
    language = models.CharField(max_length=10, default='en')
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # noqa: RUF012
    
    def get_permissions(self):
        """Get user permissions based on role"""
        permission_map = {
            'admin': [
                'view_all', 'create_all', 'edit_all', 'delete_all',
                'manage_users', 'manage_system', 'manage_billing'
            ],
            'user': [
                'view_own', 'create_own', 'edit_own', 'delete_own',
                'execute_workflows', 'manage_agents'
            ],
            'viewer': [
                'view_own', 'view_shared'
            ]
        }
        return permission_map.get(self.role, [])

class UserSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=255, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    location = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    last_activity = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    # Enhanced fields
    device_info = models.JSONField(default=dict, blank=True)

class LoginAttempt(models.Model):
    email = models.EmailField()
    ip_address = models.GenericIPAddressField()
    success = models.BooleanField()
    failure_reason = models.CharField(max_length=255, blank=True, null=True)
    user_agent = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Enhanced fields
    suspicious = models.BooleanField(default=False)
    blocked = models.BooleanField(default=False)
    
class TwoFactorAuth(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='two_factor')
    secret_key = models.CharField(max_length=255)
    backup_codes = models.JSONField(default=list)
    is_enabled = models.BooleanField(default=False)
    last_used = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class PasswordReset(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    token = models.CharField(max_length=255, unique=True)
    ip_address = models.GenericIPAddressField()
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        return not self.used and not self.is_expired()

class APIKey(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='api_keys')
    name = models.CharField(max_length=255)
    key = models.CharField(max_length=255, unique=True)
    permissions = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    last_used = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Enhanced fields
    rate_limit = models.PositiveIntegerField(default=1000)  # Requests per hour
    usage_count = models.PositiveIntegerField(default=0)

class UserRole(models.Model):
    """User roles and permissions"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    permissions = models.JSONField(default=list)
    is_system_role = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class UserRoleAssignment(models.Model):
    """Assign roles to users"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='role_assignments')
    role = models.ForeignKey(UserRole, on_delete=models.CASCADE)
    
    assigned_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='role_assignments_made')
    assigned_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['user', 'role']  # noqa: RUF012
    
    def __str__(self):
        return f"{self.user.username} - {self.role.name}"

# ---------------------------------------------------------------------------
# Enterprise Authentication Models
# ---------------------------------------------------------------------------

PROVIDER_CHOICES = [
    ('email', 'Email/Password'),
    ('google', 'Google'),
    ('github', 'GitHub'),
    ('firebase', 'Firebase'),
]

AUDIT_ACTIONS = [
    ('login', 'Login'),
    ('logout', 'Logout'),
    ('login_failed', 'Login Failed'),
    ('register', 'Register'),
    ('password_reset', 'Password Reset'),
    ('password_change', 'Password Change'),
    ('email_verified', 'Email Verified'),
    ('oauth_login', 'OAuth Login'),
    ('oauth_login_failed', 'OAuth Login Failed'),
    ('provider_linked', 'Provider Linked'),
    ('provider_unlinked', 'Provider Unlinked'),
    ('token_refresh', 'Token Refresh'),
    ('logout_all', 'Logout All Devices'),
    ('session_revoked', 'Session Revoked'),
    ('account_deleted', 'Account Deleted'),
    ('admin_action', 'Admin Action'),
]


class AuthProvider(models.Model):
    """Linked OAuth/auth providers per user."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='auth_providers'
    )
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    provider_user_id = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    display_name = models.CharField(max_length=255, blank=True)
    avatar_url = models.URLField(blank=True, null=True)
    access_token_hint = models.CharField(max_length=10, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('provider', 'provider_user_id')]  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=['user', 'provider']),
            models.Index(fields=['provider', 'provider_user_id']),
        ]

    def __str__(self):
        return f"{self.user.email} – {self.provider}"


class OAuthState(models.Model):
    """Short-lived state tokens for OAuth CSRF prevention (PKCE + state)."""
    state = models.CharField(max_length=128, unique=True, db_index=True)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    code_verifier = models.CharField(max_length=128, blank=True)
    redirect_uri = models.URLField(blank=True)
    user_id = models.UUIDField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    def is_valid(self):
        return not self.used and timezone.now() < self.expires_at

    class Meta:
        indexes = [models.Index(fields=['state', 'provider'])]  # noqa: RUF012


class EnterpriseRefreshToken(models.Model):
    """Refresh tokens with rotation, revocation, and theft detection."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='enterprise_refresh_tokens'
    )
    hashed_token = models.CharField(max_length=64, unique=True, db_index=True)
    family = models.UUIDField(default=uuid.uuid4, db_index=True)
    session_id = models.UUIDField(null=True, blank=True)
    provider = models.CharField(max_length=20, default='email', choices=PROVIDER_CHOICES)

    device_name = models.CharField(max_length=255, blank=True)
    device_type = models.CharField(max_length=50, blank=True)
    browser = models.CharField(max_length=100, blank=True)
    os = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoke_reason = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()

    class Meta:
        indexes = [  # noqa: RUF012
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['family']),
        ]

    def is_valid(self):
        return self.is_active and timezone.now() < self.expires_at

    def revoke(self, reason='manual'):
        self.is_active = False
        self.revoked_at = timezone.now()
        self.revoke_reason = reason
        self.save(update_fields=['is_active', 'revoked_at', 'revoke_reason'])


class AuditLog(models.Model):
    """Immutable audit trail for all authentication events."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='audit_logs'
    )
    user_email = models.EmailField(blank=True)
    action = models.CharField(max_length=50, choices=AUDIT_ACTIONS)
    provider = models.CharField(max_length=20, blank=True, choices=PROVIDER_CHOICES)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_name = models.CharField(max_length=255, blank=True)
    browser = models.CharField(max_length=100, blank=True)
    os = models.CharField(max_length=100, blank=True)

    success = models.BooleanField(default=True)
    failure_reason = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    request_id = models.CharField(max_length=64, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
        ]

    def __str__(self):
        return f"[{self.timestamp}] {self.action} – {self.user_email}"


class BruteForceRecord(models.Model):
    """Track failed attempts per key (IP/email) for brute-force lockout."""
    key = models.CharField(max_length=255, unique=True, db_index=True)
    endpoint = models.CharField(max_length=100, blank=True)
    attempt_count = models.PositiveIntegerField(default=0)
    first_attempt = models.DateTimeField(auto_now_add=True)
    last_attempt = models.DateTimeField(auto_now=True)
    locked_until = models.DateTimeField(null=True, blank=True)

    def is_locked(self):
        if self.locked_until and timezone.now() < self.locked_until:  # noqa: SIM103
            return True
        return False

    def reset(self):
        self.attempt_count = 0
        self.locked_until = None
        self.save(update_fields=['attempt_count', 'locked_until'])

    class Meta:
        indexes = [models.Index(fields=['key', 'endpoint'])]  # noqa: RUF012


class Workspace(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)
    subscription_tier = models.CharField(
        max_length=20,
        choices=[('free', 'Free'), ('pro', 'Pro'), ('enterprise', 'Enterprise')],
        default='free'
    )
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class WorkspaceMembership(models.Model):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='workspace_memberships')
    role = models.CharField(
        max_length=20,
        choices=[('admin', 'Admin'), ('member', 'Member'), ('viewer', 'Viewer')],
        default='member'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['workspace', 'user']  # noqa: RUF012
        
    def __str__(self):
        return f"{self.user.username} - {self.workspace.name} ({self.role})"
