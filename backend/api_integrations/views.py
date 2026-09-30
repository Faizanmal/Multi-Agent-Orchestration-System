from authentication.permissions_util import public_or_authenticated
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import APICallResult, APIIntegration, APITemplate, ScheduledAutomation
from .registry import IntegrationToolRegistry
from .serializers import (
    APICallResultSerializer,
    APIIntegrationSerializer,
    APITemplateSerializer,
    ScheduledAutomationSerializer,
)
from .services import ensure_integration_agents


def _integration_queryset(request):
    if settings.DEBUG and getattr(request.user, "is_anonymous", True):
        return APIIntegration.objects.all()
    return APIIntegration.objects.filter(created_by=request.user)


class APIIntegrationListCreateView(generics.ListCreateAPIView):
    """List and create API integrations"""

    serializer_class = APIIntegrationSerializer
    permission_classes = public_or_authenticated()

    def get_queryset(self):
        return _integration_queryset(self.request)

    def perform_create(self, serializer):
        auth_data = serializer.validated_data.pop("authentication", {})

        from django.contrib.auth import get_user_model

        User = get_user_model()

        if not settings.DEBUG and self.request.user.is_authenticated:
            created_by = self.request.user
        else:
            created_by, _ = User.objects.get_or_create(
                email="default@example.com",
                defaults={
                    "username": "default_user",
                    "first_name": "Default",
                    "last_name": "User",
                },
            )

        integration = serializer.save(created_by=created_by)
        integration.set_auth_data(auth_data)
        integration.status = "active"
        integration.save()

        # Auto-provision integration parent + sub-agents
        ensure_integration_agents(integration)


class APIIntegrationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, delete API integration"""

    serializer_class = APIIntegrationSerializer
    permission_classes = public_or_authenticated()

    def get_queryset(self):
        return _integration_queryset(self.request)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        auth_data = serializer.validated_data.pop("authentication", {})
        self.perform_update(serializer)

        if auth_data:
            instance.set_auth_data(auth_data)
        instance.save()
        ensure_integration_agents(instance)

        return Response(serializer.data)


@api_view(["POST"])
@permission_classes(public_or_authenticated())
def test_integration_view(request, pk):
    """Test API integration connection with real provider."""
    integration = get_object_or_404(_integration_queryset(request), pk=pk)
    result = IntegrationToolRegistry.test_integration(integration)
    integration.last_tested = timezone.now()
    if result.get("status") == "success":
        integration.status = "active"
    else:
        integration.status = "error"
    integration.save(update_fields=["last_tested", "status"])
    return Response(
        {
            "success": result.get("status") == "success",
            "message": result.get("message", ""),
            "data": result.get("data"),
        }
    )


@api_view(["POST"])
@permission_classes(public_or_authenticated())
def execute_integration_view(request, pk):
    """Execute a provider tool on an integration."""
    integration = get_object_or_404(_integration_queryset(request), pk=pk)
    tool_name = request.data.get("tool") or request.data.get("action", "")
    params = request.data.get("params", {})
    provider = IntegrationToolRegistry.get_provider(integration)
    if not provider:
        return Response(
            {"success": False, "error": "Unknown integration type"}, status=400
        )
    result = provider.timed_execute(integration, tool_name, params)
    return Response({"success": result.get("status") == "success", "result": result})


@api_view(["GET"])
@permission_classes(public_or_authenticated())
def integration_activity_view(request):
    """Real activity logs from APICallResult."""
    qs = APICallResult.objects.select_related("integration").order_by("-timestamp")[:50]
    if not settings.DEBUG or request.user.is_authenticated:
        qs = qs.filter(integration__created_by=request.user)
    serializer = APICallResultSerializer(qs, many=True)
    return Response({"results": serializer.data})


class IntegrationTemplateListView(generics.ListAPIView):
    """List integration templates"""

    serializer_class = APITemplateSerializer
    queryset = APITemplate.objects.filter(is_public=True)
    permission_classes = public_or_authenticated()


class ScheduledAutomationListCreateView(generics.ListCreateAPIView):
    serializer_class = ScheduledAutomationSerializer
    permission_classes = public_or_authenticated()

    def get_queryset(self):
        if settings.DEBUG and getattr(self.request.user, "is_anonymous", True):
            return ScheduledAutomation.objects.all()
        return ScheduledAutomation.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        if settings.DEBUG and getattr(self.request.user, "is_anonymous", True):
            user, _ = User.objects.get_or_create(
                email="default@example.com",
                defaults={
                    "username": "default_user",
                    "first_name": "Default",
                    "last_name": "User",
                },
            )
        else:
            user = self.request.user
        automation = serializer.save(user=user)
        from django.utils import timezone

        automation.next_run_at = timezone.now()
        automation.save(update_fields=["next_run_at"])


class ScheduledAutomationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ScheduledAutomationSerializer
    permission_classes = public_or_authenticated()

    def get_queryset(self):
        if settings.DEBUG and getattr(self.request.user, "is_anonymous", True):
            return ScheduledAutomation.objects.all()
        return ScheduledAutomation.objects.filter(user=self.request.user)


@api_view(["POST"])
@permission_classes(public_or_authenticated())
def run_automation_now_view(request, pk):
    from django.shortcuts import get_object_or_404

    from .automation_runner import run_automation

    qs = (
        ScheduledAutomation.objects.all()
        if settings.DEBUG
        else ScheduledAutomation.objects.filter(user=request.user)
    )
    automation = get_object_or_404(qs, pk=pk)
    result = run_automation(automation)
    return Response({"success": result.get("status") == "success", "result": result})


@api_view(["GET"])
@permission_classes(public_or_authenticated())
def integration_tools_view(request):
    user = request.user if request.user.is_authenticated else None
    if settings.DEBUG and not user:
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user, _ = User.objects.get_or_create(
            email="default@example.com",
            defaults={
                "username": "default_user",
                "first_name": "Default",
                "last_name": "User",
            },
        )
    return Response({"results": IntegrationToolRegistry.all_tool_definitions(user)})
