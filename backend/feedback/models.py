"""
User Feedback Models
Collect and analyze user feedback for continuous improvement
"""

import uuid

from django.db import models


class UserFeedback(models.Model):
    """User feedback on agent responses"""
    
    FEEDBACK_TYPE_CHOICES = [  # noqa: RUF012
        ('rating', 'Rating'),
        ('thumbs', 'Thumbs Up/Down'),
        ('text', 'Text Feedback'),
        ('bug_report', 'Bug Report'),
        ('feature_request', 'Feature Request')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('authentication.CustomUser', on_delete=models.CASCADE, related_name='feedback')
    
    # Feedback details
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPE_CHOICES)
    rating = models.IntegerField(null=True, blank=True)  # 1-5 stars
    thumbs_up = models.BooleanField(null=True, blank=True)  # True=up, False=down
    comment = models.TextField(blank=True)
    
    # Context
    message = models.ForeignKey('agents.Message', on_delete=models.SET_NULL, null=True, blank=True, related_name='feedback')
    session = models.ForeignKey('agents.Session', on_delete=models.SET_NULL, null=True, blank=True, related_name='feedback')
    agent = models.ForeignKey('agents.Agent', on_delete=models.SET_NULL, null=True, blank=True, related_name='feedback')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Analysis
    sentiment = models.CharField(max_length=20, blank=True)  # positive, negative, neutral
    processed = models.BooleanField(default=False)
    action_taken = models.TextField(blank=True)
    
    class Meta:
        db_table = 'user_feedback'
        ordering = ['-created_at']  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['agent', '-created_at']),
            models.Index(fields=['feedback_type']),
            models.Index(fields=['processed'])
        ]
    
    def __str__(self):
        return f"Feedback from {self.user.email} - {self.feedback_type}"


class AgentRating(models.Model):
    """Aggregate agent ratings"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.OneToOneField('agents.Agent', on_delete=models.CASCADE, related_name='rating')
    
    # Rating metrics
    total_ratings = models.IntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    thumbs_up_count = models.IntegerField(default=0)
    thumbs_down_count = models.IntegerField(default=0)
    
    # Quality metrics
    response_quality_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    accuracy_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    helpfulness_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    
    # Performance
    average_response_time = models.IntegerField(default=0)  # milliseconds
    total_interactions = models.IntegerField(default=0)
    
    # Timestamps
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'agent_ratings'
    
    def __str__(self):
        return f"Rating for {self.agent.name}: {self.average_rating}"
    
    def update_rating(self, new_rating):
        """Update average rating with new rating"""
        total_score = self.average_rating * self.total_ratings + new_rating
        self.total_ratings += 1
        self.average_rating = total_score / self.total_ratings
        self.save()
    
    def update_thumbs(self, is_up):
        """Update thumbs count"""
        if is_up:
            self.thumbs_up_count += 1
        else:
            self.thumbs_down_count += 1
        self.save()


class FeedbackAnalysis(models.Model):
    """Analyzed feedback insights"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    feedback = models.OneToOneField(UserFeedback, on_delete=models.CASCADE, related_name='analysis')
    
    # Sentiment analysis
    sentiment_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)  # -1 to 1
    sentiment_label = models.CharField(max_length=20, blank=True)
    
    # Topic extraction
    topics = models.JSONField(default=list)  # List of topics
    keywords = models.JSONField(default=list)  # List of keywords
    
    # Classification
    category = models.CharField(max_length=50, blank=True)
    priority = models.CharField(max_length=20, default='medium')  # low, medium, high, critical
    
    # Recommendations
    recommended_actions = models.JSONField(default=list)
    assigned_to = models.ForeignKey('authentication.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Metadata
    analyzed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'feedback_analysis'
    
    def __str__(self):
        return f"Analysis for feedback {self.feedback.id}"


class FeedbackTrend(models.Model):
    """Aggregated feedback trends over time"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Time period
    period = models.CharField(max_length=20)  # daily, weekly, monthly
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Agent (optional - can be system-wide)
    agent = models.ForeignKey('agents.Agent', on_delete=models.CASCADE, null=True, blank=True, related_name='trends')
    
    # Metrics
    total_feedback = models.IntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    satisfaction_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    
    # Sentiment breakdown
    positive_count = models.IntegerField(default=0)
    neutral_count = models.IntegerField(default=0)
    negative_count = models.IntegerField(default=0)
    
    # Common issues
    top_issues = models.JSONField(default=list)
    top_requests = models.JSONField(default=list)
    
    # Metadata
    generated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'feedback_trends'
        ordering = ['-start_date']  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(fields=['period', '-start_date']),
            models.Index(fields=['agent', '-start_date'])
        ]
    
    def __str__(self):
        agent_name = self.agent.name if self.agent else "System-wide"
        return f"{agent_name} - {self.period} - {self.start_date}"
