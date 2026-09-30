import logging
from datetime import datetime, timezone
from decimal import Decimal

import stripe
from authentication.models import Workspace
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Invoice, Subscription
from .services import tier_for_price

logger = logging.getLogger(__name__)


def _value(obj, key, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _workspace_for(obj):
    metadata = _value(obj, "metadata", {}) or {}
    workspace_id = _value(metadata, "workspace_id")
    if workspace_id:
        workspace = Workspace.objects.filter(id=workspace_id).first()
        if workspace:
            return workspace

    customer = _value(obj, "customer")
    customer_id = _value(customer, "id", customer)
    if customer_id:
        return Workspace.objects.filter(stripe_customer_id=customer_id).first()
    return None


def _subscription_price_id(subscription):
    items = _value(subscription, "items", {}) or {}
    data = _value(items, "data", []) or []
    if not data:
        return None
    price = _value(data[0], "price", {}) or {}
    return _value(price, "id")


def _as_datetime(timestamp):
    if not timestamp:
        return None
    return datetime.fromtimestamp(int(timestamp), tz=timezone.utc)


def _sync_subscription(subscription, workspace=None):
    workspace = workspace or _workspace_for(subscription)
    if not workspace:
        logger.warning("Stripe subscription could not be matched to a workspace")
        return

    status = _value(subscription, "status", "inactive")
    price_id = _subscription_price_id(subscription)
    paid_tier = tier_for_price(price_id)
    entitled = status in {"active", "trialing"}
    tier = paid_tier if entitled and paid_tier else "free"

    Subscription.objects.update_or_create(
        workspace=workspace,
        defaults={
            "stripe_subscription_id": _value(subscription, "id"),
            "status": status,
            "current_period_end": _as_datetime(
                _value(subscription, "current_period_end")
            ),
            "cancel_at_period_end": bool(
                _value(subscription, "cancel_at_period_end", False)
            ),
        },
    )
    workspace.subscription_tier = tier
    customer = _value(subscription, "customer")
    customer_id = _value(customer, "id", customer)
    update_fields = ["subscription_tier", "updated_at"]
    if customer_id and workspace.stripe_customer_id != customer_id:
        workspace.stripe_customer_id = customer_id
        update_fields.append("stripe_customer_id")
    workspace.save(update_fields=update_fields)


def _sync_invoice(invoice):
    workspace = _workspace_for(invoice)
    invoice_id = _value(invoice, "id")
    if not workspace or not invoice_id:
        return
    Invoice.objects.update_or_create(
        stripe_invoice_id=invoice_id,
        defaults={
            "workspace": workspace,
            "amount_due": Decimal(_value(invoice, "amount_due", 0)) / 100,
            "amount_paid": Decimal(_value(invoice, "amount_paid", 0)) / 100,
            "status": _value(invoice, "status", "open"),
        },
    )


@require_POST
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", "whsec_dummy")

    if not endpoint_secret or endpoint_secret == "whsec_dummy":
        logger.error(
            "Stripe webhook rejected because STRIPE_WEBHOOK_SECRET is not configured"
        )
        return HttpResponse(status=503)

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    event_type = _value(event, "type")
    data = _value(event, "data", {}) or {}
    obj = _value(data, "object", {}) or {}

    try:
        if event_type == "checkout.session.completed":
            workspace = _workspace_for(obj)
            subscription_id = _value(obj, "subscription")
            if workspace and subscription_id:
                subscription = stripe.Subscription.retrieve(subscription_id)
                _sync_subscription(subscription, workspace)
        elif event_type in {
            "customer.subscription.created",
            "customer.subscription.updated",
            "customer.subscription.deleted",
        }:
            _sync_subscription(obj)
        elif event_type in {"invoice.paid", "invoice.payment_failed"}:
            _sync_invoice(obj)
    except Exception:
        logger.exception("Failed to process Stripe event %s", event_type)
        return HttpResponse(status=500)

    return HttpResponse(status=200)
