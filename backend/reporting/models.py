import uuid

from django.conf import settings
from django.db import models


class Report(models.Model):
    """Model for storing reports"""
    REPORT_TYPES = [  # noqa: RUF012
        ('agent_performance', 'Agent Performance'),
        ('system_metrics', 'System Metrics'),
        ('usage_analytics', 'Usage Analytics'),
        ('financial', 'Financial Report'),
        ('custom', 'Custom Report'),
    ]
    
    STATUS_CHOICES = [  # noqa: RUF012
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports')
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    report_type = models.CharField(max_length=30, choices=REPORT_TYPES)
    
    # Configuration
    config = models.JSONField(default=dict)
    filters = models.JSONField(default=dict)
    date_range = models.JSONField(default=dict)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Generation
    last_generated = models.DateTimeField(blank=True, null=True)
    generation_time = models.FloatField(blank=True, null=True)  # seconds
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'reporting_reports'
        ordering = ['-created_at']  # noqa: RUF012
    
    def __str__(self):
        return f"{self.name} ({self.report_type})"


class ReportTemplate(models.Model):
    """Pre-built report templates"""
    CATEGORIES = [  # noqa: RUF012
        ('performance', 'Performance'),
        ('analytics', 'Analytics'),
        ('financial', 'Financial'),
        ('operational', 'Operational'),
        ('custom', 'Custom'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORIES)
    
    # Template configuration
    config = models.JSONField()
    default_filters = models.JSONField(default=dict)
    required_params = models.JSONField(default=list)
    
    # Metadata
    thumbnail_url = models.URLField(blank=True)
    tags = models.JSONField(default=list)
    
    # Usage tracking
    usage_count = models.PositiveIntegerField(default=0)
    rating = models.FloatField(default=0.0)
    
    is_official = models.BooleanField(default=False)
    is_public = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'reporting_templates'
    
    def __str__(self):
        return f"{self.name} Template"


class Dashboard(models.Model):
    """Custom dashboards"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dashboards')
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Layout configuration
    layout = models.JSONField(default=dict)
    widgets = models.JSONField(default=list)
    
    # Settings
    is_public = models.BooleanField(default=False)
    is_default = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'reporting_dashboards'
    
    def __str__(self):
        return self.name


class Widget(models.Model):
    """Dashboard widgets"""
    WIDGET_TYPES = [  # noqa: RUF012
        ('chart', 'Chart'),
        ('metric', 'Metric'),
        ('table', 'Table'),
        ('text', 'Text'),
        ('gauge', 'Gauge'),
        ('progress', 'Progress'),
        ('map', 'Map'),
    ]
    
    CHART_TYPES = [  # noqa: RUF012
        ('line', 'Line Chart'),
        ('bar', 'Bar Chart'),
        ('pie', 'Pie Chart'),
        ('area', 'Area Chart'),
        ('scatter', 'Scatter Plot'),
        ('donut', 'Donut Chart'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE, related_name='widget_set')
    
    name = models.CharField(max_length=255)
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES)
    chart_type = models.CharField(max_length=20, choices=CHART_TYPES, blank=True)
    
    # Configuration
    config = models.JSONField(default=dict)
    data_source = models.JSONField(default=dict)
    filters = models.JSONField(default=dict)
    
    # Layout
    position = models.JSONField(default=dict)  # x, y, width, height
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'reporting_widgets'
    
    def __str__(self):
        return f"{self.name} ({self.widget_type})"


class ReportSchedule(models.Model):
    """Scheduled report generation"""
    FREQUENCY_CHOICES = [  # noqa: RUF012
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='schedules')
    
    name = models.CharField(max_length=255)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    
    # Recipients
    email_recipients = models.JSONField(default=list)
    notification_settings = models.JSONField(default=dict)
    
    # Schedule settings
    next_run = models.DateTimeField()
    last_run = models.DateTimeField(blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'reporting_schedules'
    
    def __str__(self):
        return f"{self.name} ({self.frequency})"


class ReportExport(models.Model):
    """Track report exports"""
    EXPORT_FORMATS = [  # noqa: RUF012
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
        ('json', 'JSON'),
    ]
    
    STATUS_CHOICES = [  # noqa: RUF012
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='exports')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    format = models.CharField(max_length=10, choices=EXPORT_FORMATS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # File details
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.PositiveIntegerField(blank=True, null=True)  # bytes
    download_url = models.URLField(blank=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    
    # Processing details
    processing_time = models.FloatField(blank=True, null=True)  # seconds
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'reporting_exports'
        ordering = ['-created_at']  # noqa: RUF012
    
    def __str__(self):
        return f"{self.report.name} export ({self.format})"
