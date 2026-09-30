import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

class CoordinationStrategy(models.TextChoices):
    """Strategies for multi-agent coordination"""
    SEQUENTIAL = 'sequential', 'Sequential'
    PARALLEL = 'parallel', 'Parallel'
    HIERARCHICAL = 'hierarchical', 'Hierarchical'
    COLLABORATIVE = 'collaborative', 'Collaborative'
    COMPETITIVE = 'competitive', 'Competitive'

class AgentCoordinationSession(models.Model):
    """Coordination session for multi-agent workflows"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    strategy = models.CharField(
        max_length=20, 
        choices=CoordinationStrategy.choices, 
        default=CoordinationStrategy.SEQUENTIAL
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='coordination_sessions')
    
    # Session configuration
    config = models.JSONField(default=dict, help_text="Coordination configuration")
    context = models.JSONField(default=dict, help_text="Shared context between agents")
    
    # Status tracking
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['strategy', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.strategy})"

class AgentInteraction(models.Model):
    """Tracks interactions between agents in coordination"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    coordination_session = models.ForeignKey(
        AgentCoordinationSession, 
        on_delete=models.CASCADE, 
        related_name='interactions'
    )
    
    # Agent references (from main agents app)
    source_agent_id = models.UUIDField(help_text="ID of the agent initiating interaction")
    target_agent_id = models.UUIDField(help_text="ID of the agent receiving interaction")
    
    # Interaction details
    interaction_type = models.CharField(max_length=50)  # request, response, broadcast, handoff
    content = models.JSONField(default=dict)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['created_at']  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=['coordination_session', 'created_at']),
            models.Index(fields=['source_agent_id', 'target_agent_id']),
        ]
    
    def __str__(self):
        return f"{self.interaction_type}: {self.source_agent_id} → {self.target_agent_id}"

class CoordinationMetric(models.Model):
    """Performance metrics for agent coordination"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    coordination_session = models.ForeignKey(
        AgentCoordinationSession, 
        on_delete=models.CASCADE, 
        related_name='metrics'
    )
    
    metric_name = models.CharField(max_length=100)
    metric_value = models.FloatField()
    metadata = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=['coordination_session', 'metric_name']),
        ]
    
    def __str__(self):
        return f"{self.metric_name}: {self.metric_value}"
