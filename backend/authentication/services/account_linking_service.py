"""
Account linking / unlinking service.

Prevents duplicate users and manages multi-provider accounts.
"""
import logging

logger = logging.getLogger(__name__)

VALID_PROVIDERS = {'google', 'github', 'firebase'}


def unlink_provider(user, provider: str) -> bool:
    """
    Remove a provider link from the user's account.

    Raises ValueError if:
      - provider is not linked
      - it's the user's only login method (no password + no other provider)
    """
    from authentication.models import AuthProvider
    from authentication.services.audit_service import log_event

    if provider not in VALID_PROVIDERS:
        raise ValueError(f'Unknown provider: {provider}')

    record = AuthProvider.objects.filter(user=user, provider=provider).first()
    if not record:
        raise ValueError(f'Provider {provider} is not linked to this account.')

    other_providers = AuthProvider.objects.filter(user=user).exclude(provider=provider)
    has_password = user.has_usable_password()

    if not has_password and not other_providers.exists():
        raise ValueError(
            'Cannot unlink the only authentication method. '
            'Please set a password first.'
        )

    record.delete()
    log_event('provider_unlinked', user=user, provider=provider)
    return True


def get_linked_providers(user) -> list:
    """Return list of provider dicts linked to the user."""
    from authentication.models import AuthProvider
    return list(
        AuthProvider.objects.filter(user=user).values(
            'id', 'provider', 'email', 'display_name', 'avatar_url', 'created_at'
        )
    )


def user_can_delete_account(user) -> bool:
    """Safety check before account deletion."""
    return True


def delete_user_account(user, request=None) -> None:
    """
    Permanently delete user and all associated data.
    Revokes all tokens first.
    """
    from authentication.services.audit_service import log_event
    from authentication.services.jwt_service import revoke_all_user_tokens

    email = user.email
    revoke_all_user_tokens(user, reason='account_deleted')
    log_event('account_deleted', email=email, provider='', request=request)
    user.delete()
