"""Billing API views — Stripe checkout and portal."""
from authentication.models import Workspace, WorkspaceMembership
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .services import create_checkout_session, get_customer_portal
from .usage import usage_summary


def _user_workspace(user):
    membership = (
        WorkspaceMembership.objects.filter(user=user)
        .select_related('workspace')
        .first()
    )
    if membership:
        return membership.workspace
    workspace = Workspace.objects.create(name=f"{user.username}'s Workspace")
    WorkspaceMembership.objects.create(
        workspace=workspace,
        user=user,
        role='admin',
    )
    return workspace


def _stripe_configured() -> bool:
    key = getattr(settings, 'STRIPE_SECRET_KEY', '') or ''
    return bool(key) and 'dummy' not in key.lower()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_checkout_session_view(request):
    """Create a Stripe Checkout session for upgrading a plan."""
    if not _stripe_configured():
        return Response({
            'error': 'Stripe is not configured. Set STRIPE_SECRET_KEY to enable checkout.',
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    price_id = request.data.get('priceId') or request.data.get('price_id')
    if not price_id:
        return Response({'error': 'priceId is required'}, status=status.HTTP_400_BAD_REQUEST)

    frontend = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    success_url = request.data.get('success_url') or f'{frontend}/settings/billing?success=1'
    cancel_url = request.data.get('cancel_url') or f'{frontend}/settings/billing?canceled=1'

    try:
        workspace = _user_workspace(request.user)
        url = create_checkout_session(workspace, price_id, success_url, cancel_url)
        return Response({'url': url})
    except ValueError as exc:
        return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as exc:  # noqa: BLE001
        return Response({'error': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def customer_portal_view(request):
    if not _stripe_configured():
        return Response({
            'error': 'Stripe is not configured. Set STRIPE_SECRET_KEY to enable the customer portal.',
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    frontend = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    return_url = request.data.get('return_url') or f'{frontend}/settings/billing'
    try:
        workspace = _user_workspace(request.user)
        url = get_customer_portal(workspace, return_url)
        return Response({'url': url})
    except Exception as exc:  # noqa: BLE001
        return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def billing_status_view(request):
    """Return current plan/usage summary for the billing UI."""
    user = request.user
    tier = getattr(user, 'subscription_tier', None) or 'free'
    subscription_status = None
    current_period_end = None
    cancel_at_period_end = False
    usage = {
        'used_tokens': 0,
        'total_tokens': 100,
        'percentage': 0,
        'unit': 'messages',
    }

    try:
        workspace = _user_workspace(user)
        tier = getattr(workspace, 'subscription_tier', None) or tier
        usage = usage_summary(workspace)
        from .models import Subscription
        subscription = Subscription.objects.filter(workspace=workspace).first()
        if subscription:
            subscription_status = subscription.status
            current_period_end = (
                subscription.current_period_end.isoformat()
                if subscription.current_period_end else None
            )
            cancel_at_period_end = subscription.cancel_at_period_end
    except Exception:  # noqa: BLE001, S110
        pass

    return Response({
        'plan': tier,
        'subscription_status': subscription_status,
        'current_period_end': current_period_end,
        'cancel_at_period_end': cancel_at_period_end,
        'usage': usage,
        'stripe_configured': _stripe_configured(),
    })
