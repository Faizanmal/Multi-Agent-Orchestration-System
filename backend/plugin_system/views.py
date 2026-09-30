import logging

from django.db.models import Avg, Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import CustomAgentPlugin, Plugin, PluginInstallation, PluginReview
from .serializers import (
    CustomAgentPluginSerializer,
    PluginInstallationSerializer,
    PluginReviewSerializer,
    PluginSerializer,
)

logger = logging.getLogger(__name__)


class PluginViewSet(viewsets.ModelViewSet):
    """Manage plugins in the marketplace"""

    queryset = Plugin.objects.all()
    serializer_class = PluginSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.query_params.get("category")
        search = self.request.query_params.get("search")
        verified_only = (
            self.request.query_params.get("verified", "false").lower() == "true"
        )

        if category:
            queryset = queryset.filter(category=category)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(description__icontains=search)
                | Q(author__icontains=search)
            )
        if verified_only:
            queryset = queryset.filter(is_verified=True)

        return queryset

    @action(detail=True, methods=["post"])
    def install(self, request, pk=None):
        """Install a plugin"""
        plugin = self.get_object()
        user = request.user

        try:
            # Check if already installed
            installation, created = PluginInstallation.objects.get_or_create(
                plugin=plugin,
                user=user,
                defaults={"custom_config": request.data.get("config", {})},
            )

            if not created:
                return Response(
                    {
                        "message": "Plugin already installed",
                        "installation_id": str(installation.id),
                    },
                    status=status.HTTP_200_OK,
                )

            # Update plugin stats
            plugin.download_count += 1
            plugin.is_installed = True
            plugin.save()

            return Response(
                {
                    "message": "Plugin installed successfully",
                    "installation": PluginInstallationSerializer(installation).data,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:  # noqa: BLE001
            logger.error(f"Error installing plugin: {e!s}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def uninstall(self, request, pk=None):
        """Uninstall a plugin"""
        plugin = self.get_object()
        user = request.user

        try:
            installation = PluginInstallation.objects.get(plugin=plugin, user=user)
            installation.delete()

            return Response({"message": "Plugin uninstalled successfully"})

        except PluginInstallation.DoesNotExist:
            return Response(
                {"error": "Plugin not installed"}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=["get"])
    def popular(self, request):
        """Get most popular plugins"""
        plugins = self.queryset.order_by("-download_count", "-rating")[:20]
        serializer = self.get_serializer(plugins, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def verified(self, request):
        """Get verified plugins only"""
        plugins = self.queryset.filter(is_verified=True)
        serializer = self.get_serializer(plugins, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def review(self, request, pk=None):
        """Submit a review for a plugin"""
        plugin = self.get_object()
        user = request.user

        try:
            rating = request.data.get("rating")
            review_text = request.data.get("review_text", "")

            if not rating or rating not in range(1, 6):
                return Response(
                    {"error": "Rating must be between 1 and 5"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            review, created = PluginReview.objects.update_or_create(  # noqa: RUF059
                plugin=plugin,
                user=user,
                defaults={"rating": rating, "review_text": review_text},
            )

            # Update plugin rating
            avg_rating = plugin.reviews.aggregate(Avg("rating"))["rating__avg"] or 0
            plugin.rating = avg_rating
            plugin.rating_count = plugin.reviews.count()
            plugin.save()

            return Response(
                {
                    "message": "Review submitted successfully",
                    "review": PluginReviewSerializer(review).data,
                }
            )

        except Exception as e:  # noqa: BLE001
            logger.error(f"Error submitting review: {e!s}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PluginInstallationViewSet(viewsets.ModelViewSet):
    """Manage user's plugin installations"""

    queryset = PluginInstallation.objects.all()
    serializer_class = PluginInstallationSerializer

    def get_queryset(self):
        user = self.request.user
        return self.queryset.filter(user=user)

    @action(detail=True, methods=["post"])
    def toggle_enable(self, request, pk=None):
        """Enable or disable a plugin"""
        installation = self.get_object()

        installation.is_enabled = not installation.is_enabled
        installation.save()

        return Response(
            {
                "message": f"Plugin {'enabled' if installation.is_enabled else 'disabled'}",
                "is_enabled": installation.is_enabled,
            }
        )

    @action(detail=True, methods=["put"])
    def configure(self, request, pk=None):
        """Update plugin configuration"""
        installation = self.get_object()

        try:
            custom_config = request.data.get("config", {})
            installation.custom_config = custom_config
            installation.save()

            return Response(
                {
                    "message": "Configuration updated successfully",
                    "config": installation.custom_config,
                }
            )

        except Exception as e:  # noqa: BLE001
            logger.error(f"Error updating config: {e!s}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CustomAgentPluginViewSet(viewsets.ModelViewSet):
    """Manage custom agents created from plugins"""

    queryset = CustomAgentPlugin.objects.all()
    serializer_class = CustomAgentPluginSerializer

    @action(detail=True, methods=["post"])
    def invoke(self, request, pk=None):
        """Invoke the custom agent"""
        custom_agent = self.get_object()

        try:
            # Update invocation stats
            custom_agent.total_invocations += 1
            custom_agent.save()

            # Execute the custom agent logic
            result = self._execute_plugin_agent(custom_agent, request.data)

            return Response(result)

        except Exception as e:  # noqa: BLE001
            logger.error(f"Error invoking custom agent: {e!s}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def _execute_plugin_agent(self, custom_agent, data):
        """Execute custom agent plugin logic"""
        # This would load and execute the plugin code
        # For now, return a placeholder
        return {
            "agent_name": custom_agent.agent.name,
            "status": "executed",
            "result": "Custom agent execution result would go here",
        }
