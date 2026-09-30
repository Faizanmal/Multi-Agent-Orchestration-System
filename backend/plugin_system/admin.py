from django.contrib import admin

from .models import (
    CustomAgentPlugin,
    Plugin,
    PluginAPIKey,
    PluginInstallation,
    PluginReview,
)


@admin.register(Plugin)
class PluginAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "version",
        "category",
        "author",
        "is_verified",
        "is_active",
        "rating",
        "download_count",
    ]  # noqa: RUF012
    list_filter = ["category", "is_verified", "is_active", "created_at"]  # noqa: RUF012
    search_fields = ["name", "author", "description"]  # noqa: RUF012
    readonly_fields = [
        "id",
        "download_count",
        "rating",
        "rating_count",
        "created_at",
        "updated_at",
    ]  # noqa: RUF012
    prepopulated_fields = {"slug": ("name",)}  # noqa: RUF012


@admin.register(PluginInstallation)
class PluginInstallationAdmin(admin.ModelAdmin):
    list_display = [
        "plugin",
        "user",
        "is_enabled",
        "usage_count",
        "installed_at",
    ]  # noqa: RUF012
    list_filter = ["is_enabled", "installed_at"]  # noqa: RUF012
    search_fields = ["plugin__name", "user__username"]  # noqa: RUF012
    readonly_fields = ["id", "installed_at", "updated_at"]  # noqa: RUF012


@admin.register(CustomAgentPlugin)
class CustomAgentPluginAdmin(admin.ModelAdmin):
    list_display = [
        "agent",
        "plugin",
        "total_invocations",
        "success_rate",
        "created_at",
    ]  # noqa: RUF012
    list_filter = ["created_at"]  # noqa: RUF012
    search_fields = ["agent__name", "plugin__name"]  # noqa: RUF012
    readonly_fields = ["id", "created_at", "updated_at"]  # noqa: RUF012


@admin.register(PluginReview)
class PluginReviewAdmin(admin.ModelAdmin):
    list_display = [
        "plugin",
        "user",
        "rating",
        "helpful_count",
        "created_at",
    ]  # noqa: RUF012
    list_filter = ["rating", "created_at"]  # noqa: RUF012
    search_fields = ["plugin__name", "user__username", "review_text"]  # noqa: RUF012
    readonly_fields = ["id", "created_at", "updated_at"]  # noqa: RUF012


@admin.register(PluginAPIKey)
class PluginAPIKeyAdmin(admin.ModelAdmin):
    list_display = [
        "installation",
        "service_name",
        "is_active",
        "expires_at",
        "created_at",
    ]  # noqa: RUF012
    list_filter = ["is_active", "created_at"]  # noqa: RUF012
    search_fields = ["service_name", "installation__plugin__name"]  # noqa: RUF012
    readonly_fields = ["id", "created_at", "updated_at"]  # noqa: RUF012
