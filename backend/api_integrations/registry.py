"""Integration provider registry and tool router."""

from typing import Any

from .models import APIIntegration
from .providers import (
    AirtableProvider,
    AnthropicProvider,
    DiscordProvider,
    DropboxProvider,
    GitHubProvider,
    GmailProvider,
    GoogleCalendarProvider,
    GoogleDriveProvider,
    HubSpotProvider,
    InstagramProvider,
    IntegrationProvider,
    JiraProvider,
    LinearProvider,
    MicrosoftTeamsProvider,
    NotionProvider,
    OneDriveProvider,
    OpenAIProvider,
    OutlookProvider,
    S3Provider,
    ShopifyProvider,
    SlackProvider,
    StripeProvider,
    SupabaseProvider,
    TelegramProvider,
    TrelloProvider,
    TwilioProvider,
    WebhookProvider,
    WhatsAppProvider,
)

ALL_PROVIDERS: list[type[IntegrationProvider]] = [
    GmailProvider,
    SlackProvider,
    GitHubProvider,
    OpenAIProvider,
    AnthropicProvider,
    NotionProvider,
    JiraProvider,
    DiscordProvider,
    S3Provider,
    TelegramProvider,
    TrelloProvider,
    LinearProvider,
    HubSpotProvider,
    TwilioProvider,
    AirtableProvider,
    GoogleCalendarProvider,
    WebhookProvider,
    WhatsAppProvider,
    InstagramProvider,
    GoogleDriveProvider,
    DropboxProvider,
    OutlookProvider,
    MicrosoftTeamsProvider,
    OneDriveProvider,
    StripeProvider,
    SupabaseProvider,
    ShopifyProvider,
]


class IntegrationToolRegistry:
    """Resolve integrations to providers and execute tools for agents."""

    @classmethod
    def get_provider(
        cls, integration: APIIntegration
    ) -> type[IntegrationProvider] | None:
        for provider in ALL_PROVIDERS:
            if provider.detect(integration):
                return provider
        return None

    @classmethod
    def get_provider_key(cls, integration: APIIntegration) -> str | None:
        provider = cls.get_provider(integration)
        return provider.provider_key if provider else None

    @classmethod
    def list_integrations(cls, user=None) -> list[APIIntegration]:
        qs = APIIntegration.objects.filter(status="active")
        if user and getattr(user, "is_authenticated", False):
            qs = qs.filter(created_by=user)
        return list(qs)

    @classmethod
    def all_tool_definitions(cls, user=None) -> list[dict[str, Any]]:
        tools = []
        for integration in cls.list_integrations(user):
            provider = cls.get_provider(integration)
            if not provider:
                continue
            for tool in provider.tool_definitions():
                tools.append(
                    {
                        **tool,
                        "integration_id": str(integration.id),
                        "integration_name": integration.name,
                        "provider": provider.provider_key,
                    }
                )
        return tools

    @classmethod
    def tools_prompt(cls, user=None) -> str:
        lines = []
        for tool in cls.all_tool_definitions(user):
            params = tool.get("parameters", {})
            param_str = (
                ", ".join(f"{k}: {v}" for k, v in params.items()) if params else "none"
            )
            lines.append(
                f"  {tool['name']}({param_str}) — {tool['description']} [{tool['integration_name']}]"
            )
        return "\n".join(lines) if lines else "  (no integrations connected)"

    @classmethod
    def execute(
        cls, tool_name: str, params: dict[str, Any], user=None
    ) -> dict[str, Any]:
        """Execute a namespaced tool against the matching connected integration."""
        aliases = {"read_gmail": "gmail.read_inbox"}
        tool_name = aliases.get(tool_name, tool_name)

        provider_key = tool_name.split(".")[0] if "." in tool_name else None
        if not provider_key:
            return {"status": "error", "message": f"Invalid tool name: {tool_name}"}

        # Support compound keys like google_drive / microsoft_teams
        for integration in cls.list_integrations(user):
            provider = cls.get_provider(integration)
            if not provider:
                continue
            if tool_name.startswith(provider.provider_key + "."):
                return provider.timed_execute(integration, tool_name, params)

        return {
            "status": "error",
            "message": f"No active {provider_key} integration found. Connect it in Integrations first.",
        }

    @classmethod
    def test_integration(cls, integration: APIIntegration) -> dict[str, Any]:
        provider = cls.get_provider(integration)
        if not provider:
            return {
                "status": "error",
                "message": "No provider handler for this integration type",
            }
        return provider.test_connection(integration)

    @classmethod
    def detect_intent(cls, content: str) -> str | None:
        """Map user message to likely provider key."""
        c = content.lower()
        if (
            any(w in c for w in ("email", "gmail", "inbox", "mail"))
            and "outlook" not in c
        ):
            return "gmail"
        if "outlook" in c:
            return "outlook"
        if "google drive" in c or ("drive" in c and "onedrive" not in c):
            return "google_drive"
        if "dropbox" in c:
            return "dropbox"
        if "onedrive" in c or "one drive" in c:
            return "onedrive"
        if "teams" in c and ("microsoft" in c or "ms " in c or "channel" in c):
            return "microsoft_teams"
        if "telegram" in c:
            return "telegram"
        if "whatsapp" in c or "wa message" in c:
            return "whatsapp"
        if "instagram" in c or "insta" in c:
            return "instagram"
        if "shopify" in c or "store order" in c:
            return "shopify"
        if "supabase" in c or "postgres" in c:
            return "supabase"
        if "stripe" in c or "invoice" in c or "subscription" in c:
            return "stripe"
        if "slack" in c:
            return "slack"
        if "discord" in c:
            return "discord"
        if "twilio" in c or "sms" in c:
            return "twilio"
        if "trello" in c:
            return "trello"
        if "linear" in c:
            return "linear"
        if "jira" in c:
            return "jira"
        if "hubspot" in c or "crm" in c:
            return "hubspot"
        if "airtable" in c:
            return "airtable"
        if "calendar" in c or "schedule" in c or "meeting" in c:
            return "calendar"
        if "webhook" in c:
            return "webhook"
        if "github" in c or "repository" in c or "repo" in c:
            return "github"
        if "openai" in c or "gpt" in c:
            return "openai"
        if "claude" in c or "anthropic" in c:
            return "anthropic"
        if "notion" in c:
            return "notion"
        if "s3" in c or "bucket" in c:
            return "s3"
        return None
