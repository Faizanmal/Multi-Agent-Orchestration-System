import stripe
from django.conf import settings

# Use a dummy key if not set in environment
stripe.api_key = getattr(settings, "STRIPE_SECRET_KEY", "sk_test_dummy")


def stripe_price_tiers():
    """Return the configured Stripe Price ID to workspace tier mapping."""
    prices = {
        getattr(settings, "STRIPE_PRICE_PRO", ""): "pro",
        getattr(settings, "STRIPE_PRICE_ENTERPRISE", ""): "enterprise",
    }
    return {price_id: tier for price_id, tier in prices.items() if price_id}


def tier_for_price(price_id):
    return stripe_price_tiers().get(price_id)


def create_checkout_session(workspace, price_id, success_url, cancel_url):
    """
    Creates a Stripe Checkout Session for a given workspace to subscribe to a plan.
    """
    if not tier_for_price(price_id):
        raise ValueError("Unknown or unconfigured Stripe price")

    # Create or get Stripe Customer ID
    if not workspace.stripe_customer_id:
        customer = stripe.Customer.create(
            email=(
                workspace.memberships.first().user.email
                if workspace.memberships.exists()
                else None
            ),
            name=workspace.name,
            metadata={"workspace_id": str(workspace.id)},
        )
        workspace.stripe_customer_id = customer.id
        workspace.save(update_fields=["stripe_customer_id", "updated_at"])

    session = stripe.checkout.Session.create(
        customer=workspace.stripe_customer_id,
        line_items=[
            {
                "price": price_id,
                "quantity": 1,
            }
        ],
        mode="subscription",
        success_url=success_url,
        cancel_url=cancel_url,
        client_reference_id=str(workspace.id),
        metadata={"workspace_id": str(workspace.id)},
        subscription_data={
            "metadata": {"workspace_id": str(workspace.id)},
        },
    )
    return session.url


def get_customer_portal(workspace, return_url):
    """
    Generate a Stripe Customer Portal link so users can manage their subscription.
    """
    if not workspace.stripe_customer_id:
        raise ValueError("Workspace does not have a Stripe Customer ID")

    session = stripe.billing_portal.Session.create(
        customer=workspace.stripe_customer_id, return_url=return_url
    )
    return session.url
