import uuid

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class ModelExecution(models.Model):
    """Track model execution history and performance"""
    PROVIDER_CHOICES = [  # noqa: RUF012
        ('nvidia', 'NVIDIA'),
        ('groq', 'Groq'),
        ('google', 'Google'),
        ('anthropic', 'Anthropic'),
        ('openai', 'OpenAI'),
    ]
    
    COMPLEXITY_CHOICES = [  # noqa: RUF012
        ('simple', 'Simple'),
        ('moderate', 'Moderate'),
        ('complex', 'Complex'),
        ('creative', 'Creative'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='model_executions')
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    model_name = models.CharField(max_length=100)
    complexity = models.CharField(max_length=20, choices=COMPLEXITY_CHOICES)
    
    # Request details
    prompt = models.TextField()
    response = models.TextField()
    
    # Performance metrics
    duration_ms = models.IntegerField(help_text="Execution duration in milliseconds")
    tokens_used = models.IntegerField()
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    
    # Cost tracking
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    
    # Status
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, null=True)
    
    # Metadata
    priority = models.CharField(max_length=20, default='balanced')
    context = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'multimodel_executions'
        indexes = [  # noqa: RUF012
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['provider', 'model_name']),
            models.Index(fields=['complexity', 'created_at']),
        ]
        ordering = ['-created_at']  # noqa: RUF012
    
    def __str__(self):
        return f"{self.provider}/{self.model_name} - {self.complexity}"


class ModelPreference(models.Model):
    """User preferences for model selection"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='model_preferences')
    
    # Default preferences
    default_priority = models.CharField(
        max_length=20,
        choices=[
            ('speed', 'Speed'),
            ('cost', 'Cost'),
            ('quality', 'Quality'),
            ('balanced', 'Balanced'),
        ],
        default='balanced'
    )
    
    # Budget constraints
    max_cost_per_request = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    monthly_budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Provider preferences
    preferred_providers = models.JSONField(
        default=list,
        help_text="Ordered list of preferred providers"
    )
    disabled_providers = models.JSONField(
        default=list,
        help_text="List of disabled providers"
    )
    
    # Complexity overrides
    complexity_overrides = models.JSONField(
        default=dict,
        help_text="Custom model selection per complexity level"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'multimodel_preferences'
    
    def __str__(self):
        return f"{self.user.username}'s preferences"


class ModelPerformanceMetrics(models.Model):
    """Aggregate performance metrics per model"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.CharField(max_length=20)
    model_name = models.CharField(max_length=100)
    
    # Aggregate metrics
    total_requests = models.IntegerField(default=0)
    successful_requests = models.IntegerField(default=0)
    failed_requests = models.IntegerField(default=0)
    
    # Performance
    avg_duration_ms = models.FloatField(default=0)
    avg_tokens = models.FloatField(default=0)
    total_cost = models.DecimalField(max_digits=12, decimal_places=6, default=0)
    
    # Time period
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    # Metadata
    metadata = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'multimodel_performance_metrics'
        unique_together = ['provider', 'model_name', 'period_start']  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=['provider', 'model_name', 'period_start']),
        ]
    
    def __str__(self):
        return f"{self.provider}/{self.model_name} - {self.period_start.date()}"


class ModelFallbackLog(models.Model):
    """Log fallback events when primary model fails"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    execution = models.ForeignKey(
        ModelExecution, 
        on_delete=models.CASCADE, 
        related_name='fallback_logs'
    )
    
    # Original attempt
    original_provider = models.CharField(max_length=20)
    original_model = models.CharField(max_length=100)
    failure_reason = models.TextField()
    
    # Fallback details
    fallback_provider = models.CharField(max_length=20)
    fallback_model = models.CharField(max_length=100)
    fallback_success = models.BooleanField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'multimodel_fallback_logs'
        ordering = ['-created_at']  # noqa: RUF012
    
    def __str__(self):
        return f"Fallback: {self.original_provider} -> {self.fallback_provider}"


class AIModelConfig(models.Model):
    """Configuration for AI models"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    
    model_type = models.CharField(
        max_length=20,
        choices=[
            ('text', 'Text Model'),
            ('vision', 'Vision Model'),
            ('audio', 'Audio Model'),
            ('video', 'Video Model'),
            ('multimodal', 'Multi-Modal Model'),
        ]
    )
    
    provider = models.CharField(max_length=100)
    model_id = models.CharField(max_length=200)
    config = models.JSONField(default=dict, help_text="Model configuration parameters")
    capabilities = models.JSONField(default=list, help_text="List of model capabilities")
    
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='ai_model_configs'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'multimodel_ai_configs'
        ordering = ['-created_at']  # noqa: RUF012
    
    def __str__(self):
        return f"{self.name} ({self.provider}/{self.model_id})"


class MultiModalSession(models.Model):
    """Session for multimodal interactions"""
    
    STATUS_CHOICES = [  # noqa: RUF012
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='multimodal_sessions')
    
    name = models.CharField(max_length=200)
    input_modalities = models.JSONField(default=list, help_text="List of input modalities")
    output_modalities = models.JSONField(default=list, help_text="List of output modalities")
    processing_config = models.JSONField(default=dict)
    results = models.JSONField(default=dict)
    context = models.JSONField(default=dict, help_text="Shared context across modalities")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'multimodal_sessions'
        ordering = ['-created_at']  # noqa: RUF012
    
    def __str__(self):
        return f"{self.name} - {self.status}"


class ModalityResult(models.Model):
    """Results from individual modality processing"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(MultiModalSession, on_delete=models.CASCADE, related_name='modality_results')
    
    modality_type = models.CharField(max_length=50)
    input_data = models.JSONField(default=dict)
    output_data = models.JSONField(default=dict)
    
    confidence_score = models.FloatField(default=0.0)
    processing_time = models.FloatField(default=0.0, help_text="Processing time in seconds")
    tokens_used = models.IntegerField(default=0)
    
    model_used = models.ForeignKey(
        AIModelConfig,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'multimodal_modality_results'
        ordering = ['created_at']  # noqa: RUF012
    
    def __str__(self):
        return f"{self.session.name} - {self.modality_type}"


class CrossModalInsight(models.Model):
    """Insights generated from cross-modal analysis"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(MultiModalSession, on_delete=models.CASCADE, related_name='cross_modal_insights')
    
    insight_type = models.CharField(max_length=100)
    involved_modalities = models.JSONField(default=list)
    description = models.TextField()
    confidence = models.FloatField(default=0.0)
    evidence = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'multimodal_cross_insights'
        ordering = ['-confidence', '-created_at']  # noqa: RUF012

    def __str__(self):
        return f"{self.insight_type} ({self.confidence:.2f})"


class ModelCoordinationRun(models.Model):
    """Audit log for multi-model coordination runs (route/collaborate/debate/pipeline)."""

    MODE_CHOICES = [  # noqa: RUF012
        ('route', 'Smart Route'),
        ('collaborative', 'Collaborative'),
        ('debate', 'Debate / Consensus'),
        ('pipeline', 'Sequential Pipeline'),
    ]
    STATUS_CHOICES = [  # noqa: RUF012
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='model_coordination_runs',
    )
    mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    prompt = models.TextField()
    model_ids = models.JSONField(default=list)
    options = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    result = models.JSONField(default=dict, blank=True)
    final_answer = models.TextField(blank=True)
    duration_ms = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'multimodel_coordination_runs'
        ordering = ['-created_at']  # noqa: RUF012

    def __str__(self):
        return f"{self.mode} ({self.status})"
