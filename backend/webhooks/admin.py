from django.contrib import admin

from .models import (
    EventLog,
    NotificationChannel,
    WebhookDelivery,
    WebhookEndpoint,
    WebhookNotification,
)


@admin.register(WebhookEndpoint)
class WebhookEndpointAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'url', 'is_active', 'total_deliveries', 'successful_deliveries', 'last_triggered']  # noqa: RUF012
    list_filter = ['is_active', 'created_at']  # noqa: RUF012
    search_fields = ['name', 'user__username', 'url']  # noqa: RUF012
    readonly_fields = ['id', 'total_deliveries', 'successful_deliveries', 'failed_deliveries', 'created_at', 'updated_at']  # noqa: RUF012


@admin.register(WebhookDelivery)
class WebhookDeliveryAdmin(admin.ModelAdmin):
    list_display = ['webhook', 'event_type', 'success', 'status_code', 'attempt_number', 'duration_ms', 'created_at']  # noqa: RUF012
    list_filter = ['success', 'event_type', 'created_at']  # noqa: RUF012
    search_fields = ['webhook__name', 'event_type']  # noqa: RUF012
    readonly_fields = ['id', 'created_at']  # noqa: RUF012


@admin.register(NotificationChannel)
class NotificationChannelAdmin(admin.ModelAdmin):
    list_display = ['channel_name', 'user', 'channel_type', 'is_active', 'created_at']  # noqa: RUF012
    list_filter = ['channel_type', 'is_active', 'created_at']  # noqa: RUF012
    search_fields = ['channel_name', 'user__username']  # noqa: RUF012
    readonly_fields = ['id', 'created_at', 'updated_at']  # noqa: RUF012


@admin.register(WebhookNotification)
class WebhookNotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'event_type', 'priority', 'is_read', 'is_sent', 'created_at']  # noqa: RUF012
    list_filter = ['priority', 'is_read', 'is_sent', 'event_type', 'created_at']  # noqa: RUF012
    search_fields = ['title', 'message', 'user__username']  # noqa: RUF012
    readonly_fields = ['id', 'created_at']  # noqa: RUF012


@admin.register(EventLog)
class EventLogAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'session', 'user', 'source', 'created_at']  # noqa: RUF012
    list_filter = ['event_type', 'created_at', 'source']  # noqa: RUF012
    search_fields = ['event_type', 'user__username', 'source']  # noqa: RUF012
    readonly_fields = ['id', 'created_at']  # noqa: RUF012
