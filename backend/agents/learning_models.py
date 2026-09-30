from datetime import timezone

"""
Agent Learning & Adaptation Models
Implements reinforcement learning and adaptive coordination for agents
"""
import uuid
from datetime import datetime
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

from .models import Agent, Session

User = get_user_model()


class LearningStrategy(models.TextChoices):
    Q_LEARNING = 'q_learning', 'Q-Learning'
    SARSA = 'sarsa', 'SARSA'
    POLICY_GRADIENT = 'policy_gradient', 'Policy Gradient'
    ACTOR_CRITIC = 'actor_critic', 'Actor-Critic'
    CUSTOM = 'custom', 'Custom'


class AgentLearningProfile(models.Model):
    """Tracks learning progress and capabilities of an agent"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.OneToOneField(Agent, on_delete=models.CASCADE, related_name='learning_profile')
    strategy = models.CharField(max_length=30, choices=LearningStrategy.choices, default=LearningStrategy.Q_LEARNING)
    
    # Learning parameters
    learning_rate = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal('0.1000'))
    discount_factor = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal('0.9500'))
    exploration_rate = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal('0.3000'))
    
    # Experience tracking
    total_experiences = models.IntegerField(default=0)
    successful_experiences = models.IntegerField(default=0)
    failed_experiences = models.IntegerField(default=0)
    
    # Performance metrics
    average_reward = models.DecimalField(max_digits=8, decimal_places=4, default=Decimal('0.0000'))
    best_reward = models.DecimalField(max_digits=8, decimal_places=4, default=Decimal('0.0000'))
    current_performance_score = models.DecimalField(max_digits=8, decimal_places=4, default=Decimal('0.5000'))
    
    # Specialization tracking
    specialized_tasks = models.JSONField(default=list, help_text="List of task types agent excels at")
    skill_matrix = models.JSONField(default=dict, help_text="Skill name to proficiency mapping")
    
    # Learning state
    q_table = models.JSONField(default=dict, help_text="State-action Q-values")
    policy = models.JSONField(default=dict, help_text="Current policy mapping")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_training_at = models.DateTimeField(null=True, blank=True)
    is_learning_enabled = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-current_performance_score']  # noqa: RUF012
    
    def __str__(self):
        return f"{self.agent.name} Learning Profile ({self.strategy})"
    
    def update_exploration_rate(self, decay_factor=0.995):
        """Decay exploration rate over time (epsilon-greedy)"""
        current = float(self.exploration_rate)
        self.exploration_rate = Decimal(str(max(0.01, current * decay_factor)))
        self.save()
    
    def calculate_success_rate(self):
        """Calculate success rate from experiences"""
        if self.total_experiences == 0:
            return 0.0
        return self.successful_experiences / self.total_experiences


class AgentExperience(models.Model):
    """Records individual learning experiences for agents"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='experiences')
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='experiences', null=True, blank=True)
    
    # Reinforcement learning tuple (S, A, R, S', done)
    state = models.JSONField(help_text="Current state representation")
    action = models.JSONField(help_text="Action taken")
    reward = models.DecimalField(max_digits=8, decimal_places=4)
    next_state = models.JSONField(help_text="Resulting state")
    done = models.BooleanField(default=False, help_text="Episode completed")
    
    # Context
    task_type = models.CharField(max_length=100)
    coordination_strategy = models.CharField(max_length=50, blank=True)
    execution_time_ms = models.IntegerField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=['agent', '-created_at']),
            models.Index(fields=['task_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.agent.name} - {self.task_type} (R: {self.reward})"


class AdaptiveCoordinationRule(models.Model):
    """Rules for adapting coordination strategies based on learned patterns"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField()
    
    # Conditions
    task_complexity_min = models.IntegerField(default=0, help_text="Minimum complexity score")
    task_complexity_max = models.IntegerField(default=100, help_text="Maximum complexity score")
    agent_count_min = models.IntegerField(default=1)
    agent_count_max = models.IntegerField(default=10)
    task_types = models.JSONField(default=list, help_text="Applicable task types")
    
    # Recommended strategy
    recommended_strategy = models.CharField(max_length=50)
    strategy_parameters = models.JSONField(default=dict)
    
    # Performance tracking
    times_applied = models.IntegerField(default=0)
    success_rate = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal('0.0000'))
    average_improvement = models.DecimalField(max_digits=8, decimal_places=4, default=Decimal('0.0000'))
    
    # Metadata
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='coordination_rules')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_auto_generated = models.BooleanField(default=False, help_text="Generated by learning system")
    
    class Meta:
        ordering = ['-success_rate', '-times_applied']  # noqa: RUF012
    
    def __str__(self):
        return f"{self.name} -> {self.recommended_strategy}"
    
    def update_performance(self, success: bool, improvement: float):
        """Update rule performance after application"""
        self.times_applied += 1
        
        # Update success rate (running average)
        current_success = float(self.success_rate)
        new_success = (current_success * (self.times_applied - 1) + (1.0 if success else 0.0)) / self.times_applied
        self.success_rate = Decimal(str(new_success))
        
        # Update average improvement
        current_improvement = float(self.average_improvement)
        new_improvement = (current_improvement * (self.times_applied - 1) + improvement) / self.times_applied
        self.average_improvement = Decimal(str(new_improvement))
        
        self.save()


class AgentSkillEvolution(models.Model):
    """Tracks evolution of agent skills over time"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='skill_evolutions')
    skill_name = models.CharField(max_length=100)
    
    # Skill metrics
    proficiency_level = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal('0.5000'))
    confidence_score = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal('0.5000'))
    usage_count = models.IntegerField(default=0)
    
    # Performance history
    performance_history = models.JSONField(default=list, help_text="Time-series performance data")
    recent_successes = models.IntegerField(default=0)
    recent_failures = models.IntegerField(default=0)
    
    # Learning insights
    learned_patterns = models.JSONField(default=list, help_text="Patterns discovered during learning")
    common_mistakes = models.JSONField(default=list, help_text="Frequent errors to avoid")
    best_practices = models.JSONField(default=list, help_text="Successful strategies")
    
    # Metadata
    first_used_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['agent', 'skill_name']  # noqa: RUF012
        ordering = ['-proficiency_level', '-usage_count']  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=['agent', '-proficiency_level']),
            models.Index(fields=['skill_name', '-proficiency_level']),
        ]
    
    def __str__(self):
        return f"{self.agent.name} - {self.skill_name} (L{self.proficiency_level})"
    
    def record_usage(self, success: bool, performance_score: float):
        """Record skill usage and update metrics"""
        self.usage_count += 1
        
        if success:
            self.recent_successes += 1
        else:
            self.recent_failures += 1
        
        # Update proficiency with exponential moving average
        alpha = 0.1  # Learning rate for skill update
        current_proficiency = float(self.proficiency_level)
        new_proficiency = current_proficiency + alpha * (performance_score - current_proficiency)
        self.proficiency_level = Decimal(str(max(0.0, min(1.0, new_proficiency))))
        
        # Update confidence based on consistency
        total_recent = self.recent_successes + self.recent_failures
        if total_recent > 0:
            consistency = self.recent_successes / total_recent
            self.confidence_score = Decimal(str(consistency))
        
        # Add to performance history
        history = self.performance_history or []
        history.append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'performance': performance_score,
            'success': success,
            'proficiency': float(self.proficiency_level)
        })
        # Keep last 100 records
        self.performance_history = history[-100:]
        
        self.save()


class LearningSession(models.Model):
    """Tracks training/learning sessions for agents"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='learning_sessions')
    
    # Session details
    session_type = models.CharField(max_length=50, choices=[
        ('online', 'Online Learning'),
        ('batch', 'Batch Training'),
        ('transfer', 'Transfer Learning'),
        ('fine_tune', 'Fine-tuning')
    ])
    
    # Training data
    experiences_processed = models.IntegerField(default=0)
    episodes_completed = models.IntegerField(default=0)
    training_data_size = models.IntegerField(default=0)
    
    # Results
    initial_performance = models.DecimalField(max_digits=8, decimal_places=4)
    final_performance = models.DecimalField(max_digits=8, decimal_places=4)
    improvement_percentage = models.DecimalField(max_digits=8, decimal_places=4, default=Decimal('0.0000'))
    
    # Configuration
    hyperparameters = models.JSONField(default=dict)
    training_config = models.JSONField(default=dict)
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('paused', 'Paused')
    ], default='running')
    
    # Metadata
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['-started_at']  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=['agent', '-started_at']),
            models.Index(fields=['status', '-started_at']),
        ]
    
    def __str__(self):
        return f"{self.agent.name} - {self.session_type} ({self.status})"
    
    def complete(self):
        """Mark session as completed and calculate metrics"""
        self.status = 'completed'
        self.completed_at = datetime.now(timezone.utc)
        
        if self.started_at:
            duration = self.completed_at - self.started_at
            self.duration_seconds = int(duration.total_seconds())
        
        # Calculate improvement
        if self.initial_performance > 0:
            improvement = ((float(self.final_performance) - float(self.initial_performance)) / 
                         float(self.initial_performance)) * 100
            self.improvement_percentage = Decimal(str(improvement))
        
        self.save()
