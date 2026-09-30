"""Seed APITemplate records for all supported integrations."""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from api_integrations.models import APITemplate
from api_integrations.providers import (
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

User = get_user_model()

TEMPLATES = [
    {
        "provider": GmailProvider,
        "category": "social",
        "tags": ["email", "communication", "google"],
        "description": "Read, analyze, search, and draft Gmail messages",
    },
    {
        "provider": SlackProvider,
        "category": "social",
        "tags": ["chat", "communication", "team"],
        "description": "Read channels, post messages, and monitor Slack workspace",
    },
    {
        "provider": GitHubProvider,
        "category": "cloud",
        "tags": ["devops", "code", "issues"],
        "description": "Manage repositories, issues, and README files",
    },
    {
        "provider": OpenAIProvider,
        "category": "ai_ml",
        "tags": ["ai", "llm", "gpt"],
        "description": "Chat completions and model listing via OpenAI API",
    },
    {
        "provider": AnthropicProvider,
        "category": "ai_ml",
        "tags": ["ai", "llm", "claude"],
        "description": "Chat with Claude via Anthropic API",
    },
    {
        "provider": NotionProvider,
        "category": "other",
        "tags": ["notes", "wiki", "docs"],
        "description": "Search, read, and create Notion pages",
    },
    {
        "provider": JiraProvider,
        "category": "cloud",
        "tags": ["project", "issues", "atlassian"],
        "description": "Manage Jira projects and issues",
    },
    {
        "provider": DiscordProvider,
        "category": "social",
        "tags": ["chat", "community", "bot"],
        "description": "Send messages and read Discord channels",
    },
    {
        "provider": S3Provider,
        "category": "cloud",
        "tags": ["storage", "aws", "files"],
        "description": "List and read objects from AWS S3 buckets",
    },
    {
        "provider": TelegramProvider,
        "category": "social",
        "tags": ["chat", "bot", "messaging"],
        "description": "Send messages and read updates via Telegram Bot API",
    },
    {
        "provider": WhatsAppProvider,
        "category": "social",
        "tags": ["chat", "messaging", "meta", "whatsapp"],
        "description": "Send WhatsApp Business texts and templates via Meta Cloud API",
    },
    {
        "provider": InstagramProvider,
        "category": "social",
        "tags": ["social", "messaging", "meta", "instagram"],
        "description": "Read Instagram profile/media and send DMs via Graph API",
    },
    {
        "provider": GoogleDriveProvider,
        "category": "cloud",
        "tags": ["files", "docs", "google", "storage"],
        "description": "List, search, and read Google Drive files and Docs",
    },
    {
        "provider": DropboxProvider,
        "category": "cloud",
        "tags": ["files", "storage", "dropbox"],
        "description": "List, search, and download Dropbox files",
    },
    {
        "provider": OutlookProvider,
        "category": "social",
        "tags": ["email", "microsoft", "outlook"],
        "description": "Read and send Outlook mail via Microsoft Graph",
    },
    {
        "provider": MicrosoftTeamsProvider,
        "category": "social",
        "tags": ["chat", "microsoft", "teams"],
        "description": "List Teams chats and post channel messages",
    },
    {
        "provider": OneDriveProvider,
        "category": "cloud",
        "tags": ["files", "microsoft", "onedrive"],
        "description": "List, search, and read OneDrive files",
    },
    {
        "provider": StripeProvider,
        "category": "other",
        "tags": ["billing", "payments", "invoices"],
        "description": "List customers, invoices, subscriptions, and balance",
    },
    {
        "provider": SupabaseProvider,
        "category": "database",
        "tags": ["postgres", "database", "supabase"],
        "description": "Query and insert rows via Supabase PostgREST",
    },
    {
        "provider": ShopifyProvider,
        "category": "other",
        "tags": ["ecommerce", "orders", "shopify"],
        "description": "List Shopify products and orders",
    },
    {
        "provider": TrelloProvider,
        "category": "cloud",
        "tags": ["boards", "cards", "project"],
        "description": "Manage Trello boards, lists, and cards",
    },
    {
        "provider": LinearProvider,
        "category": "cloud",
        "tags": ["issues", "project", "engineering"],
        "description": "List and create Linear issues via GraphQL",
    },
    {
        "provider": HubSpotProvider,
        "category": "other",
        "tags": ["crm", "contacts", "sales"],
        "description": "List, search, and create HubSpot CRM contacts",
    },
    {
        "provider": TwilioProvider,
        "category": "social",
        "tags": ["sms", "voice", "messaging"],
        "description": "Send SMS and manage Twilio messaging",
    },
    {
        "provider": AirtableProvider,
        "category": "database",
        "tags": ["spreadsheet", "database", "records"],
        "description": "List and create Airtable records",
    },
    {
        "provider": GoogleCalendarProvider,
        "category": "social",
        "tags": ["calendar", "events", "google"],
        "description": "List calendars and create Google Calendar events",
    },
    {
        "provider": WebhookProvider,
        "category": "other",
        "tags": ["webhook", "http", "custom"],
        "description": "POST/GET to any custom webhook endpoint",
    },
]


class Command(BaseCommand):
    help = "Seed integration templates and ensure default agents exist"

    def handle(self, *args, **options):
        user, _ = User.objects.get_or_create(
            email="default@example.com",
            defaults={"username": "default_user", "first_name": "Default", "last_name": "User"},
        )

        for i, tpl in enumerate(TEMPLATES):
            provider = tpl["provider"]
            template, created = APITemplate.objects.update_or_create(
                name=provider.display_name,
                provider=provider.provider_key,
                defaults={
                    "description": tpl["description"],
                    "category": tpl["category"],
                    "tags": tpl["tags"],
                    "is_public": True,
                    "popularity": 100 - i,
                    "created_by": user,
                    "config_template": {
                        "provider_key": provider.provider_key,
                        "auth_type": provider.auth_type,
                        "default_endpoint": provider.default_endpoint,
                        "tools": provider.tool_definitions(),
                        "sub_agents": provider.sub_agents(),
                    },
                },
            )
            action = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{action} template: {template.name}"))

        self.stdout.write(self.style.SUCCESS("Integration templates seeded."))

        from api_integrations.models import APIIntegration
        from api_integrations.services import ensure_integration_agents

        for integration in APIIntegration.objects.filter(status="active"):
            agents = ensure_integration_agents(integration)
            if agents:
                self.stdout.write(self.style.SUCCESS(
                    f"Provisioned {len(agents)} agent(s) for {integration.name}"
                ))
