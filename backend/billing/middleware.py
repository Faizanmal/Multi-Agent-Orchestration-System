from django.http import JsonResponse

from .usage import get_message_usage, get_tier_limit, increment_message_usage


class QuotaEnforcementMiddleware:
    """
    Enforce monthly message quotas based on the workspace subscription tier.

    Counts successful POSTs on the chat paths used by the product:
    - /agents/api/messages/
    - /agents/api/sessions/<id>/send_message/
    """

    def __init__(self, get_response):
        self.get_response = get_response

    @staticmethod
    def is_billable_message_request(request) -> bool:
        if request.method != "POST":
            return False
        path = request.path.rstrip("/")
        if path == "/agents/api/messages":
            return True
        return path.startswith("/agents/api/sessions/") and path.endswith(
            "/send_message"
        )

    def __call__(self, request):
        if not self.is_billable_message_request(request):
            return self.get_response(request)

        if not getattr(request.user, "is_authenticated", False):
            return self.get_response(request)

        membership = request.user.workspace_memberships.select_related(
            "workspace"
        ).first()
        if not membership:
            return self.get_response(request)

        workspace = membership.workspace
        tier = workspace.subscription_tier or "free"
        limit = get_tier_limit(tier)
        used = get_message_usage(workspace.id)

        if used >= limit:
            return JsonResponse(
                {
                    "error": "Payment Required",
                    "message": (
                        f"You have used {used}/{limit} messages this month on the "
                        f"{tier} plan. Upgrade to continue."
                    ),
                    "usage": {"used": used, "limit": limit, "tier": tier},
                },
                status=402,
            )

        response = self.get_response(request)
        if 200 <= response.status_code < 300:
            increment_message_usage(workspace.id)
        return response
