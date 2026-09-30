"""
Plugin Architecture Models
Supports custom agent plugins and marketplace functionality
"""
import uuid
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import URLValidator
from django.db import models

User = get_user_model()


class PluginCategory(models.TextChoices):
    AGENT = 'agent', 'Agent Plugin'
    TOOL = 'tool', 'Tool Integration'
    DATA_SOURCE = 'data_source', 'Data Source'
    WORKFLOW = 'workflow', 'Workflow Template'
    ANALYTICS = 'analytics', 'Analytics Extension'
    VISUALIZATION = 'visualization', 'Visualization'
    INTEGRATION = 'integration', 'External Integration'


class PluginStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    PENDING_REVIEW = 'pending_review', 'Pending Review'
    APPROVED = 'approved', 'Approved'
    REJECTED = 'rejected', 'Rejected'
    DEPRECATED = 'deprecated', 'Deprecated'
    ARCHIVED = 'archived', 'Archived'


class AgentPlugin(models.Model):
    """Registry for custom agent plugins"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic info
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    display_name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=30, choices=PluginCategory.choices, default=PluginCategory.AGENT)
    
    # Version info
    version = models.CharField(max_length=50, default='1.0.0')
    min_system_version = models.CharField(max_length=50, blank=True, help_text="Minimum compatible system version")
    
    # Author info
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='plugins_authored')
    author_name = models.CharField(max_length=200)
    author_email = models.EmailField(blank=True)
    author_website = models.URLField(blank=True, validators=[URLValidator()])
    
    # Plugin content
    plugin_code = models.TextField(help_text="Python code for the plugin")
    configuration_schema = models.JSONField(default=dict, help_text="JSON schema for plugin configuration")
    default_configuration = models.JSONField(default=dict)
    
    # Capabilities
    capabilities = models.JSONField(default=list, help_text="List of capabilities this plugin provides")
    required_dependencies = models.JSONField(default=list, help_text="Python packages required")
    api_requirements = models.JSONField(default=dict, help_text="External APIs required (e.g., API keys)")
    
    # Marketplace info
    status = models.CharField(max_length=20, choices=PluginStatus.choices, default=PluginStatus.DRAFT)
    is_public = models.BooleanField(default=False, help_text="Available in public marketplace")
    is_featured = models.BooleanField(default=False)
    is_official = models.BooleanField(default=False, help_text="Official plugin by system team")
    
    # Pricing
    is_free = models.BooleanField(default=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    license_type = models.CharField(max_length=50, default='MIT')
    
    # Statistics
    downloads_count = models.IntegerField(default=0)
    active_installations = models.IntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('0.00'))
    total_reviews = models.IntegerField(default=0)
    
    # Media
    icon_url = models.URLField(blank=True)
    banner_url = models.URLField(blank=True)
    screenshots = models.JSONField(default=list, help_text="List of screenshot URLs")
    video_url = models.URLField(blank=True)
    
    # Documentation
    documentation = models.TextField(blank=True, help_text="Markdown documentation")
    readme = models.TextField(blank=True)
    changelog = models.TextField(blank=True)
    
    # Repository
    repository_url = models.URLField(blank=True, validators=[URLValidator()])
    homepage_url = models.URLField(blank=True, validators=[URLValidator()])
    support_url = models.URLField(blank=True, validators=[URLValidator()])
    
    # SEO
    tags = models.JSONField(default=list, help_text="Search tags")
    keywords = models.CharField(max_length=500, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    last_reviewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-is_featured', '-average_rating', '-downloads_count']  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=['slug']),
            models.Index(fields=['category', '-downloads_count']),
            models.Index(fields=['status', 'is_public']),
            models.Index(fields=['-average_rating', '-downloads_count']),
        ]
    
    def __str__(self):
        return f"{self.display_name} v{self.version}"
    
    def increment_downloads(self):
        """Increment download counter"""
        self.downloads_count += 1
        self.save(update_fields=['downloads_count'])
    
    def update_rating(self, new_rating: float):
        """Update average rating with new review"""
        current_total = float(self.average_rating) * self.total_reviews
        new_total = current_total + new_rating
        self.total_reviews += 1
        self.average_rating = Decimal(str(new_total / self.total_reviews))
        self.save(update_fields=['average_rating', 'total_reviews'])


class PluginInstallation(models.Model):
    """Track plugin installations by users"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plugin = models.ForeignKey(AgentPlugin, on_delete=models.CASCADE, related_name='installations')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='plugin_installations')
    
    # Installation details
    installed_version = models.CharField(max_length=50)
    configuration = models.JSONField(default=dict, help_text="User-specific configuration")
    is_enabled = models.BooleanField(default=True)
    
    # Usage tracking
    last_used_at = models.DateTimeField(null=True, blank=True)
    usage_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    
    # Performance
    average_execution_time_ms = models.IntegerField(null=True, blank=True)
    success_rate = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal('1.0000'))
    
    # Metadata
    installed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['plugin', 'user']  # noqa: RUF012
        ordering = ['-installed_at']  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=['user', '-last_used_at']),
            models.Index(fields=['plugin', 'is_enabled']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.plugin.name} v{self.installed_version}"
    
    def record_usage(self, execution_time_ms: int | None = None, success: bool = True):
        """Record plugin usage"""
        from django.utils import timezone
        
        self.usage_count += 1
        self.last_used_at = timezone.now()
        
        if not success:
            self.error_count += 1
        
        # Update success rate
        self.success_rate = Decimal(str((self.usage_count - self.error_count) / self.usage_count))
        
        # Update average execution time
        if execution_time_ms:
            if self.average_execution_time_ms:
                # Exponential moving average
                alpha = 0.2
                new_avg = alpha * execution_time_ms + (1 - alpha) * self.average_execution_time_ms
                self.average_execution_time_ms = int(new_avg)
            else:
                self.average_execution_time_ms = execution_time_ms
        
        self.save()


class PluginReview(models.Model):
    """User reviews for plugins"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plugin = models.ForeignKey(AgentPlugin, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='plugin_reviews')
    installation = models.ForeignKey(PluginInstallation, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Review content
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    title = models.CharField(max_length=200)
    review_text = models.TextField()
    
    # Additional feedback
    pros = models.JSONField(default=list, help_text="List of positive points")
    cons = models.JSONField(default=list, help_text="List of negative points")
    
    # Verification
    is_verified_purchase = models.BooleanField(default=False)
    
    # Helpful votes
    helpful_count = models.IntegerField(default=0)
    not_helpful_count = models.IntegerField(default=0)
    
    # Response
    author_response = models.TextField(blank=True)
    author_response_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['plugin', 'user']  # noqa: RUF012
        ordering = ['-created_at']  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=['plugin', '-rating']),
            models.Index(fields=['-helpful_count']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.plugin.name} ({self.rating}★)"


class PluginDependency(models.Model):
    """Track dependencies between plugins"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plugin = models.ForeignKey(AgentPlugin, on_delete=models.CASCADE, related_name='dependencies')
    required_plugin = models.ForeignKey(AgentPlugin, on_delete=models.CASCADE, related_name='dependent_plugins')
    
    # Version constraints
    min_version = models.CharField(max_length=50, blank=True)
    max_version = models.CharField(max_length=50, blank=True)
    is_optional = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['plugin', 'required_plugin']  # noqa: RUF012
        verbose_name_plural = 'Plugin dependencies'
    
    def __str__(self):
        return f"{self.plugin.name} requires {self.required_plugin.name}"


class PluginExecutionLog(models.Model):
    """Log plugin executions for debugging and monitoring"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    installation = models.ForeignKey(PluginInstallation, on_delete=models.CASCADE, related_name='execution_logs')
    
    # Execution details
    execution_context = models.JSONField(default=dict)
    input_data = models.JSONField(default=dict)
    output_data = models.JSONField(default=dict, null=True, blank=True)
    
    # Performance
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    execution_time_ms = models.IntegerField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('running', 'Running'),
        ('success', 'Success'),
        ('error', 'Error'),
        ('timeout', 'Timeout')
    ], default='running')
    error_message = models.TextField(blank=True)
    error_trace = models.TextField(blank=True)
    
    # Resource usage
    memory_usage_mb = models.IntegerField(null=True, blank=True)
    cpu_usage_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    class Meta:
        ordering = ['-started_at']  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=['installation', '-started_at']),
            models.Index(fields=['status', '-started_at']),
        ]
    
    def __str__(self):
        return f"{self.installation.plugin.name} - {self.status}"


class PluginMarketplaceMetrics(models.Model):
    """Aggregate metrics for marketplace analytics"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plugin = models.ForeignKey(AgentPlugin, on_delete=models.CASCADE, related_name='metrics')
    
    # Time period
    date = models.DateField()
    
    # Metrics
    views_count = models.IntegerField(default=0)
    downloads_count = models.IntegerField(default=0)
    new_installations = models.IntegerField(default=0)
    uninstallations = models.IntegerField(default=0)
    active_users = models.IntegerField(default=0)
    total_executions = models.IntegerField(default=0)
    
    # Revenue (if paid plugin)
    revenue = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Engagement
    average_session_duration_seconds = models.IntegerField(null=True, blank=True)
    average_executions_per_user = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['plugin', 'date']  # noqa: RUF012
        ordering = ['-date']  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=['plugin', '-date']),
            models.Index(fields=['-downloads_count']),
        ]
    
    def __str__(self):
        return f"{self.plugin.name} - {self.date}"


class PluginCollection(models.Model):
    """Curated collections of plugins"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    
    curator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='plugin_collections')
    plugins = models.ManyToManyField(AgentPlugin, related_name='collections')
    
    is_official = models.BooleanField(default=False)
    is_public = models.BooleanField(default=True)
    
    banner_url = models.URLField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_official', '-created_at']  # noqa: RUF012
    
    def __str__(self):
        return self.name
