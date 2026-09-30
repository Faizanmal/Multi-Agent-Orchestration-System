"""Fast, isolated settings for automated checks."""

from .settings import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
}

# Several legacy apps predate a consistent migration history. Checks create
# their current model state directly while production continues to use the
# checked-in migrations.
MIGRATION_MODULES = {
    app_label: None
    for app_label in (
        "agents",
        "Mcp_Integration",
        "models",
        "Multi_agents_cordination",
        "Multi_model_Intelligence",
        "real_time_performance",
        "use_case",
        "authentication",
        "api_integrations",
        "reporting",
        "notifications",
        "data_pipelines",
        "agent_learning",
        "plugin_system",
        "webhooks",
        "analytics",
        "workflow_builder",
        "integrations",
        "feedback",
        "billing",
    )
}
