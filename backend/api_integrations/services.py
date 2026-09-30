"""Integration services — agent provisioning and lifecycle."""
import logging

from agents.models import Agent, AgentStatus
from django.contrib.auth import get_user_model

from .models import APIIntegration
from .registry import IntegrationToolRegistry

logger = logging.getLogger(__name__)
User = get_user_model()


def ensure_integration_agents(integration: APIIntegration) -> list[Agent]:
    """Create parent + sub-agents for a connected integration."""
    provider = IntegrationToolRegistry.get_provider(integration)
    if not provider:
        return []

    owner = integration.created_by
    provider_key = provider.provider_key
    created: list[Agent] = []

    parent_name = f"{provider.display_name} Agent"
    parent, _ = Agent.objects.get_or_create(
        name=parent_name,
        owner=owner,
        defaults={
            "type": "custom",
            "status": AgentStatus.IDLE,
            "capabilities": [f"{provider_key}.read", f"{provider_key}.analyze", f"{provider_key}.write"],
            "configuration": {
                "integration_id": str(integration.id),
                "provider": provider_key,
                "role": "integration_parent",
            },
            "is_active": True,
        },
    )
    if str(integration.id) not in str(parent.configuration.get("integration_id", "")):
        parent.configuration = {
            "integration_id": str(integration.id),
            "provider": provider_key,
            "role": "integration_parent",
        }
        parent.save(update_fields=["configuration"])
    created.append(parent)

    for sub in provider.sub_agents():
        agent, was_created = Agent.objects.get_or_create(
            name=sub["name"],
            owner=owner,
            defaults={
                "type": sub["type"],
                "status": AgentStatus.IDLE,
                "capabilities": sub["capabilities"],
                "configuration": {
                    "integration_id": str(integration.id),
                    "provider": provider_key,
                    "role": sub["role"],
                    "parent_agent": str(parent.id),
                },
                "is_active": True,
            },
        )
        if was_created:
            created.append(agent)

    logger.info("Ensured %s agents for integration %s", len(created), integration.name)
    return created


def get_default_user():
    return User.objects.get_or_create(
        email="default@example.com",
        defaults={"username": "default_user", "first_name": "Default", "last_name": "User"},
    )[0]
