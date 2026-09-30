import uuid

from agents.models import Agent
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class PluginCategory(models.TextChoices):
    """Plugin categories"""
    INTEGRATION = 'integration', 'Integration'
    TOOL = 'tool', 'Tool'
    DATA_SOURCE = 'data_source', 'Data Source'
    NOTIFICATION = 'notification', 'Notification'
    ANALYTICS = 'analytics', 'Analytics'
    CUSTOM_AGENT = 'custom_agent', 'Custom Agent'


class Plugin(models.Model):
    """Represents a plugin that extends system capabilities"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=PluginCategory.choices)
    
    # Plugin metadata
    version = models.CharField(max_length=50)
    author = models.CharField(max_length=200)
    homepage = models.URLField(blank=True)
    repository = models.URLField(blank=True)
    
    # Plugin configuration
    config_schema = models.JSONField(default=dict)  # JSON schema for configuration
    default_config = models.JSONField(default=dict)
    
    # Plugin code/manifest
    manifest = models.JSONField()  # Main plugin manifest
    entry_point = models.CharField(max_length=500)  # Path to main plugin file/class
    
    # Installation & status
    is_installed = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)  # Official/verified plugin
    
    # Stats
    download_count = models.IntegerField(default=0)
    rating = models.FloatField(default=0.0)
    rating_count = models.IntegerField(default=0)
    
    # Dependencies
    dependencies = models.JSONField(default=list)  # List of required plugins
    python_requirements = models.TextField(blank=True)  # pip requirements
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'plugin'
        ordering = ['-rating', '-download_count']  # noqa: RUF012
    
    def __str__(self):
        return f"{self.name} v{self.version}"


class PluginInstallation(models.Model):
    """Tracks plugin installations"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plugin = models.ForeignKey(Plugin, on_delete=models.CASCADE, related_name='installations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='plugin_installations')
    
    # Installation config
    custom_config = models.JSONField(default=dict)
    
    # Status
    is_enabled = models.BooleanField(default=True)
    last_used = models.DateTimeField(null=True, blank=True)
    usage_count = models.IntegerField(default=0)
    
    installed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'plugin_installation'
        unique_together = ['plugin', 'user']  # noqa: RUF012
        ordering = ['-installed_at']  # noqa: RUF012
    
    def __str__(self):
        return f"{self.plugin.name} - {self.user.username}"


class CustomAgentPlugin(models.Model):
    """Custom agent created via plugin system"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plugin = models.ForeignKey(Plugin, on_delete=models.CASCADE, related_name='custom_agents')
    agent = models.OneToOneField(Agent, on_delete=models.CASCADE, related_name='plugin_config')
    
    # Plugin-specific configuration
    plugin_config = models.JSONField(default=dict)
    capabilities = models.JSONField(default=list)
    
    # Performance
    total_invocations = models.IntegerField(default=0)
    success_rate = models.FloatField(default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'custom_agent_plugin'
    
    def __str__(self):
        return f"{self.agent.name} (Plugin: {self.plugin.name})"


class PluginReview(models.Model):
    """User reviews for plugins"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plugin = models.ForeignKey(Plugin, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='plugin_reviews')
    
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 stars
    review_text = models.TextField()
    helpful_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'plugin_review'
        unique_together = ['plugin', 'user']  # noqa: RUF012
        ordering = ['-created_at']  # noqa: RUF012
    
    def __str__(self):
        return f"{self.plugin.name} - {self.rating}★ by {self.user.username}"


class PluginAPIKey(models.Model):
    """API keys for plugin integrations"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    installation = models.ForeignKey(PluginInstallation, on_delete=models.CASCADE, related_name='api_keys')
    
    service_name = models.CharField(max_length=100)  # e.g., "slack", "github"
    api_key = models.CharField(max_length=500)  # Encrypted in production
    api_secret = models.CharField(max_length=500, blank=True)
    additional_config = models.JSONField(default=dict)
    
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'plugin_api_key'
        ordering = ['-created_at']  # noqa: RUF012
    
    def __str__(self):
        return f"{self.service_name} - {self.installation.plugin.name}"
