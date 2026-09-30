import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class DataSource(models.Model):
    """Data source configurations"""
    SOURCE_TYPES = [  # noqa: RUF012
        ('database', 'Database'),
        ('api', 'API'),
        ('file', 'File System'),
        ('cloud_storage', 'Cloud Storage'),
        ('stream', 'Data Stream'),
        ('webhook', 'Webhook'),
        ('ftp', 'FTP/SFTP'),
        ('email', 'Email'),
    ]
    
    DATABASE_TYPES = [  # noqa: RUF012
        ('postgresql', 'PostgreSQL'),
        ('mysql', 'MySQL'),
        ('mongodb', 'MongoDB'),
        ('redis', 'Redis'),
        ('sqlite', 'SQLite'),
        ('oracle', 'Oracle'),
        ('mssql', 'SQL Server'),
    ]
    
    STATUS_CHOICES = [  # noqa: RUF012
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Error'),
        ('testing', 'Testing'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='data_sources')
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES)
    database_type = models.CharField(max_length=20, choices=DATABASE_TYPES, blank=True)
    
    # Connection details (encrypted in production)
    connection_config = models.JSONField(default=dict)
    
    # Metadata
    schema_info = models.JSONField(default=dict, blank=True)
    last_sync = models.DateTimeField(blank=True, null=True)
    
    # Monitoring
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='inactive')
    last_test_at = models.DateTimeField(blank=True, null=True)
    last_test_success = models.BooleanField(default=False)
    connection_time = models.FloatField(blank=True, null=True)  # milliseconds
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'data_pipeline_sources'
        ordering = ['-created_at']  # noqa: RUF012
    
    def __str__(self):
        return f"{self.name} ({self.source_type})"


class DataPipeline(models.Model):
    """Data processing pipelines"""
    STATUS_CHOICES = [  # noqa: RUF012
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('error', 'Error'),
        ('archived', 'Archived'),
    ]
    
    TRIGGER_TYPES = [  # noqa: RUF012
        ('manual', 'Manual'),
        ('scheduled', 'Scheduled'),
        ('event', 'Event-driven'),
        ('stream', 'Continuous Stream'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pipelines')
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Configuration
    pipeline_config = models.JSONField(default=dict)
    steps = models.JSONField(default=list)  # Ordered list of processing steps
    
    # Sources and destinations
    source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='source_pipelines')
    destination = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='destination_pipelines')
    
    # Execution settings
    trigger_type = models.CharField(max_length=20, choices=TRIGGER_TYPES, default='manual')
    schedule_config = models.JSONField(default=dict, blank=True)
    
    # Status and monitoring
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    last_run_at = models.DateTimeField(blank=True, null=True)
    next_run_at = models.DateTimeField(blank=True, null=True)
    
    # Performance metrics
    total_executions = models.PositiveIntegerField(default=0)
    successful_executions = models.PositiveIntegerField(default=0)
    failed_executions = models.PositiveIntegerField(default=0)
    average_duration = models.FloatField(default=0.0)  # seconds
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'data_pipelines'
        ordering = ['-created_at']  # noqa: RUF012
    
    def __str__(self):
        return f"{self.name} ({self.status})"
    
    def success_rate(self):
        if self.total_executions == 0:
            return 0
        return (self.successful_executions / self.total_executions) * 100


class PipelineExecution(models.Model):
    """Track pipeline executions"""
    STATUS_CHOICES = [  # noqa: RUF012
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pipeline = models.ForeignKey(DataPipeline, on_delete=models.CASCADE, related_name='executions')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Execution details
    trigger_type = models.CharField(max_length=20)
    input_parameters = models.JSONField(default=dict, blank=True)
    
    # Progress tracking
    current_step = models.CharField(max_length=255, blank=True)
    progress_percentage = models.PositiveIntegerField(default=0)
    steps_completed = models.PositiveIntegerField(default=0)
    total_steps = models.PositiveIntegerField(default=0)
    
    # Results
    output_data = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    error_step = models.CharField(max_length=255, blank=True)
    
    # Performance
    duration = models.FloatField(blank=True, null=True)  # seconds
    records_processed = models.PositiveIntegerField(default=0)
    records_failed = models.PositiveIntegerField(default=0)
    
    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'data_pipeline_executions'
        ordering = ['-started_at']  # noqa: RUF012
    
    def __str__(self):
        return f"{self.pipeline.name} execution ({self.status})"


class DataQualityRule(models.Model):
    """Data quality validation rules"""
    RULE_TYPES = [  # noqa: RUF012
        ('completeness', 'Completeness'),
        ('accuracy', 'Accuracy'),
        ('consistency', 'Consistency'),
        ('validity', 'Validity'),
        ('uniqueness', 'Uniqueness'),
        ('timeliness', 'Timeliness'),
        ('custom', 'Custom'),
    ]
    
    SEVERITY_LEVELS = [  # noqa: RUF012
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quality_rules')
    pipeline = models.ForeignKey(DataPipeline, on_delete=models.CASCADE, related_name='quality_rules')
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    rule_type = models.CharField(max_length=20, choices=RULE_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='medium')
    
    # Rule configuration
    rule_config = models.JSONField(default=dict)
    threshold = models.FloatField(default=100.0)  # Percentage threshold for pass/fail
    
    # Settings
    is_active = models.BooleanField(default=True)
    stop_on_failure = models.BooleanField(default=False)
    
    # Monitoring
    last_check_at = models.DateTimeField(blank=True, null=True)
    last_result = models.JSONField(default=dict, blank=True)
    pass_count = models.PositiveIntegerField(default=0)
    fail_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'data_quality_rules'
    
    def __str__(self):
        return f"{self.name} ({self.rule_type})"
    
    def success_rate(self):
        total = self.pass_count + self.fail_count
        if total == 0:
            return 0
        return (self.pass_count / total) * 100


class DataQualityCheck(models.Model):
    """Individual quality check results"""
    STATUS_CHOICES = [  # noqa: RUF012
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('warning', 'Warning'),
        ('skipped', 'Skipped'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rule = models.ForeignKey(DataQualityRule, on_delete=models.CASCADE, related_name='checks')
    execution = models.ForeignKey(PipelineExecution, on_delete=models.CASCADE, related_name='quality_checks')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    score = models.FloatField()  # Quality score (0-100)
    
    # Results
    result_data = models.JSONField(default=dict)
    issues_found = models.JSONField(default=list, blank=True)
    
    # Details
    records_checked = models.PositiveIntegerField(default=0)
    records_passed = models.PositiveIntegerField(default=0)
    records_failed = models.PositiveIntegerField(default=0)
    
    check_duration = models.FloatField(default=0.0)  # milliseconds
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'data_quality_checks'
        ordering = ['-created_at']  # noqa: RUF012
    
    def __str__(self):
        return f"{self.rule.name} check ({self.status})"


class PipelineSchedule(models.Model):
    """Pipeline scheduling configuration"""
    FREQUENCY_CHOICES = [  # noqa: RUF012
        ('once', 'Once'),
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('cron', 'Custom Cron'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pipeline = models.ForeignKey(DataPipeline, on_delete=models.CASCADE, related_name='schedules')
    
    name = models.CharField(max_length=255)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    cron_expression = models.CharField(max_length=100, blank=True)
    
    # Schedule settings
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(blank=True, null=True)
    schedule_timezone = models.CharField(max_length=50, default='UTC')
    
    # Execution parameters
    parameters = models.JSONField(default=dict, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    last_run_at = models.DateTimeField(blank=True, null=True)
    next_run_at = models.DateTimeField(blank=True, null=True)
    
    # Statistics
    total_runs = models.PositiveIntegerField(default=0)
    successful_runs = models.PositiveIntegerField(default=0)
    failed_runs = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'data_pipeline_schedules'
    
    def __str__(self):
        return f"Schedule: {self.name} ({self.frequency})"


class DataTransformation(models.Model):
    """Data transformation definitions"""
    TRANSFORMATION_TYPES = [  # noqa: RUF012
        ('filter', 'Filter'),
        ('map', 'Map/Transform'),
        ('aggregate', 'Aggregate'),
        ('join', 'Join'),
        ('sort', 'Sort'),
        ('validate', 'Validate'),
        ('clean', 'Clean'),
        ('enrich', 'Enrich'),
        ('custom', 'Custom Script'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pipeline = models.ForeignKey(DataPipeline, on_delete=models.CASCADE, related_name='transformations')
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    transformation_type = models.CharField(max_length=20, choices=TRANSFORMATION_TYPES)
    
    # Configuration
    config = models.JSONField(default=dict)
    script = models.TextField(blank=True)  # For custom transformations
    
    # Ordering
    order = models.PositiveIntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'data_transformations'
        ordering = ['order']  # noqa: RUF012
    
    def __str__(self):
        return f"{self.name} ({self.transformation_type})"
