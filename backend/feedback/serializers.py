"""
User Feedback Serializers
"""

from rest_framework import serializers

from .models import AgentRating, FeedbackAnalysis, FeedbackTrend, UserFeedback


class UserFeedbackSerializer(serializers.ModelSerializer):
    """Serializer for user feedback"""
    
    class Meta:
        model = UserFeedback
        fields = [  # noqa: RUF012
            'id', 'feedback_type', 'rating', 'thumbs_up', 'comment',
            'message', 'session', 'agent', 'sentiment', 'processed',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'sentiment', 'processed', 'created_at', 'updated_at']  # noqa: RUF012


class AgentRatingSerializer(serializers.ModelSerializer):
    """Serializer for agent ratings"""
    
    class Meta:
        model = AgentRating
        fields = [  # noqa: RUF012
            'id', 'agent', 'total_ratings', 'average_rating',
            'thumbs_up_count', 'thumbs_down_count',
            'response_quality_score', 'accuracy_score', 'helpfulness_score',
            'average_response_time', 'total_interactions', 'last_updated'
        ]
        read_only_fields = ['id', 'last_updated']  # noqa: RUF012


class FeedbackAnalysisSerializer(serializers.ModelSerializer):
    """Serializer for feedback analysis"""
    
    class Meta:
        model = FeedbackAnalysis
        fields = [  # noqa: RUF012
            'id', 'feedback', 'sentiment_score', 'sentiment_label',
            'topics', 'keywords', 'category', 'priority',
            'recommended_actions', 'assigned_to', 'analyzed_at'
        ]
        read_only_fields = ['id', 'analyzed_at']  # noqa: RUF012


class FeedbackTrendSerializer(serializers.ModelSerializer):
    """Serializer for feedback trends"""
    
    class Meta:
        model = FeedbackTrend
        fields = [  # noqa: RUF012
            'id', 'period', 'start_date', 'end_date', 'agent',
            'total_feedback', 'average_rating', 'satisfaction_score',
            'positive_count', 'neutral_count', 'negative_count',
            'top_issues', 'top_requests', 'generated_at'
        ]
        read_only_fields = ['id', 'generated_at']  # noqa: RUF012
