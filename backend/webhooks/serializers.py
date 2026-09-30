from rest_framework import serializers

from .models import (
    EventLog,
    NotificationChannel,
    WebhookDelivery,
    WebhookEndpoint,
    WebhookNotification,
)


class WebhookEndpointSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    success_rate = serializers.SerializerMethodField()

    class Meta:
        model = WebhookEndpoint
        fields = "__all__"
        read_only_fields = [
            "user",
            "total_deliveries",
            "successful_deliveries",
            "failed_deliveries",
        ]  # noqa: RUF012

    def get_success_rate(self, obj):
        if obj.total_deliveries == 0:
            return 0.0
        return obj.successful_deliveries / obj.total_deliveries


class WebhookDeliverySerializer(serializers.ModelSerializer):
    webhook_name = serializers.CharField(source="webhook.name", read_only=True)
    webhook_url = serializers.CharField(source="webhook.url", read_only=True)

    class Meta:
        model = WebhookDelivery
        fields = "__all__"


class NotificationChannelSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = NotificationChannel
        fields = "__all__"
        read_only_fields = ["user"]  # noqa: RUF012


class WebhookNotificationSerializer(serializers.ModelSerializer):
    channel_name = serializers.CharField(
        source="channel.channel_name", read_only=True, allow_null=True
    )

    class Meta:
        model = WebhookNotification
        fields = "__all__"
        read_only_fields = ["user", "is_sent", "sent_at", "read_at"]  # noqa: RUF012


class EventLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        source="user.username", read_only=True, allow_null=True
    )
    session_name = serializers.CharField(
        source="session.name", read_only=True, allow_null=True
    )

    class Meta:
        model = EventLog
        fields = "__all__"
