import uuid

from agents.models import Agent, Session
from django.db import models


class LearningAlgorithm(models.TextChoices):
    """Types of learning algorithms"""

    Q_LEARNING = "q_learning", "Q-Learning"
    SARSA = "sarsa", "SARSA"
    DEEP_Q = "deep_q", "Deep Q-Network"
    PPO = "ppo", "Proximal Policy Optimization"
    A3C = "a3c", "Asynchronous Advantage Actor-Critic"


class AgentLearningProfile(models.Model):
    """Tracks learning progress and adaptations for each agent"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.OneToOneField(
        Agent, on_delete=models.CASCADE, related_name="learning_profile"
    )
    algorithm = models.CharField(
        max_length=50,
        choices=LearningAlgorithm.choices,
        default=LearningAlgorithm.Q_LEARNING,
    )

    # Learning metrics
    total_tasks_completed = models.IntegerField(default=0)
    success_rate = models.FloatField(default=0.0)  # 0-1
    average_response_time = models.FloatField(default=0.0)  # seconds
    learning_rate = models.FloatField(default=0.1)
    discount_factor = models.FloatField(default=0.95)

    # Skill specialization
    specialized_capabilities = models.JSONField(
        default=dict
    )  # {"vision": 0.9, "reasoning": 0.7}
    task_type_performance = models.JSONField(default=dict)  # {"image_analysis": 0.85}

    # Adaptation history
    adaptations_count = models.IntegerField(default=0)
    last_adaptation = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "agent_learning_profile"
        ordering = ("-success_rate",)

    def __str__(self):
        return f"Learning Profile: {self.agent.name} ({self.success_rate:.2%})"


class ReinforcementState(models.Model):
    """Stores state-action-reward tuples for reinforcement learning"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    learning_profile = models.ForeignKey(
        AgentLearningProfile, on_delete=models.CASCADE, related_name="states"
    )
    session = models.ForeignKey(
        Session, on_delete=models.CASCADE, null=True, blank=True
    )

    # RL components
    state_representation = models.JSONField()  # Current state features
    action_taken = models.JSONField()  # Action performed
    reward = models.FloatField()  # Reward received
    next_state = models.JSONField(null=True, blank=True)  # Resulting state

    # Q-value tracking
    q_value = models.FloatField(default=0.0)
    expected_q_value = models.FloatField(default=0.0)

    # Context
    task_type = models.CharField(max_length=100)
    success = models.BooleanField(default=False)
    execution_time = models.FloatField(default=0.0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "reinforcement_state"
        ordering = ("-created_at",)
        indexes = (
            models.Index(fields=["learning_profile", "-created_at"]),
            models.Index(fields=["task_type", "success"]),
        )


class AdaptiveStrategy(models.Model):
    """Stores learned strategies for coordination"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField()

    # Strategy configuration
    strategy_type = models.CharField(
        max_length=50
    )  # sequential, parallel, hierarchical
    agent_roles = (
        models.JSONField()
    )  # {"orchestrator": "agent_1", "workers": ["agent_2"]}
    conditions = models.JSONField()  # When to apply this strategy

    # Performance metrics
    times_used = models.IntegerField(default=0)
    success_rate = models.FloatField(default=0.0)
    avg_completion_time = models.FloatField(default=0.0)
    confidence_score = models.FloatField(
        default=0.5
    )  # How confident we are in this strategy

    # Learning data
    learned_from_sessions = models.ManyToManyField(
        Session, related_name="learned_strategies"
    )
    last_used = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "adaptive_strategy"
        ordering = ("-confidence_score", "-success_rate")

    def __str__(self):
        return f"{self.name} ({self.success_rate:.2%})"


class LearningEvent(models.Model):
    """Logs significant learning events and adaptations"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    learning_profile = models.ForeignKey(
        AgentLearningProfile, on_delete=models.CASCADE, related_name="events"
    )

    event_type = models.CharField(
        max_length=50
    )  # skill_improved, strategy_learned, adaptation_applied
    description = models.TextField()
    metrics_before = models.JSONField()
    metrics_after = models.JSONField()
    improvement = models.FloatField(default=0.0)  # Percentage improvement

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "learning_event"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.event_type} - {self.learning_profile.agent.name}"


class SkillMatrix(models.Model):
    """Tracks skills and expertise levels for agents"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    learning_profile = models.ForeignKey(
        AgentLearningProfile, on_delete=models.CASCADE, related_name="skills"
    )

    skill_name = models.CharField(
        max_length=100
    )  # e.g., "image_classification", "sentiment_analysis"
    skill_category = models.CharField(
        max_length=50
    )  # vision, reasoning, action, memory
    expertise_level = models.FloatField(default=0.0)  # 0-1

    # Performance tracking
    attempts_count = models.IntegerField(default=0)
    success_count = models.IntegerField(default=0)
    failure_count = models.IntegerField(default=0)
    avg_execution_time = models.FloatField(default=0.0)

    last_used = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "skill_matrix"
        unique_together = ("learning_profile", "skill_name")
        ordering = ("-expertise_level",)

    def __str__(self):
        return f"{self.skill_name}: {self.expertise_level:.2f}"


class AgentLearningPolicy(models.Model):
    """Stores learned policies for agents (Q-tables, neural networks, etc.)"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(
        Agent, on_delete=models.CASCADE, related_name="learning_policies"
    )
    agent_identifier = models.CharField(max_length=255, db_index=True)

    # Policy data
    policy_data = models.JSONField(
        help_text="Serialized policy (Q-table, weights, etc.)"
    )
    algorithm_type = models.CharField(max_length=50, default="q_learning")

    # Metadata
    total_episodes = models.IntegerField(default=0)
    average_reward = models.FloatField(default=0.0)
    is_active = models.BooleanField(default=True)

    # Version control
    version = models.IntegerField(default=1)
    parent_policy = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "agent_learning_policies"
        ordering = ("-updated_at",)
        indexes = (models.Index(fields=["agent_identifier", "is_active"]),)

    def __str__(self):
        return f"Policy for {self.agent_identifier} (v{self.version})"
