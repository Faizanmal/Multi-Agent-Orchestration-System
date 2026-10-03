"""
User Feedback Service
Process and analyze user feedback for continuous improvement
"""

import logging
from datetime import timedelta

from django.db.models import Avg, Count
from django.utils import timezone

logger = logging.getLogger(__name__)


class FeedbackService:
    """Service for managing user feedback"""

    @staticmethod
    def submit_feedback(user, feedback_type, **kwargs):
        """Submit user feedback"""
        from .models import AgentRating, UserFeedback

        try:
            # Create feedback
            feedback = UserFeedback.objects.create(
                user=user, feedback_type=feedback_type, **kwargs
            )

            # Update agent rating if agent feedback
            if feedback.agent:
                rating, _created = AgentRating.objects.get_or_create(
                    agent=feedback.agent
                )

                if feedback_type == "rating" and feedback.rating:
                    rating.update_rating(feedback.rating)
                elif feedback_type == "thumbs" and feedback.thumbs_up is not None:
                    rating.update_thumbs(feedback.thumbs_up)

                rating.total_interactions += 1
                rating.save()

            # Analyze feedback asynchronously
            FeedbackService._analyze_feedback(feedback)

            logger.info(f"Feedback submitted: {feedback.id}")
            return feedback

        except Exception as e:  # noqa: BLE001
            logger.error(f"Error submitting feedback: {e}")
            return None

    @staticmethod
    def _analyze_feedback(feedback):
        """Analyze feedback sentiment and extract insights"""
        from .models import FeedbackAnalysis

        try:
            # Simple sentiment analysis based on rating and comment
            sentiment_score = 0.0
            sentiment_label = "neutral"

            if feedback.rating:
                # Map rating (1-5) to sentiment (-1 to 1)
                sentiment_score = (feedback.rating - 3) / 2.0
                if sentiment_score > 0.3:
                    sentiment_label = "positive"
                elif sentiment_score < -0.3:
                    sentiment_label = "negative"

            elif feedback.thumbs_up is not None:
                sentiment_score = 1.0 if feedback.thumbs_up else -1.0
                sentiment_label = "positive" if feedback.thumbs_up else "negative"

            # Extract keywords from comment
            keywords = []
            topics = []
            if feedback.comment:
                # Simple keyword extraction (in production, use NLP)
                words = feedback.comment.lower().split()
                keywords = [w for w in words if len(w) > 4][:10]

                # Topic detection based on keywords
                if any(
                    word in feedback.comment.lower() for word in ["slow", "lag", "wait"]
                ):
                    topics.append("performance")
                if any(
                    word in feedback.comment.lower()
                    for word in ["wrong", "incorrect", "error"]
                ):
                    topics.append("accuracy")
                if any(
                    word in feedback.comment.lower()
                    for word in ["confusing", "unclear", "understand"]
                ):
                    topics.append("clarity")

            # Determine priority
            priority = "medium"
            if sentiment_score < -0.5 or feedback.feedback_type == "bug_report":
                priority = "high"
            elif sentiment_score < -0.8:
                priority = "critical"
            elif feedback.feedback_type == "feature_request":
                priority = "low"

            # Generate recommendations
            recommendations = []
            if "performance" in topics:
                recommendations.append("optimize_response_time")
            if "accuracy" in topics:
                recommendations.append("review_model_training")
            if "clarity" in topics:
                recommendations.append("improve_response_formatting")

            # Create analysis
            analysis = FeedbackAnalysis.objects.create(
                feedback=feedback,
                sentiment_score=sentiment_score,
                sentiment_label=sentiment_label,
                topics=topics,
                keywords=keywords,
                priority=priority,
                recommended_actions=recommendations,
            )

            # Update feedback
            feedback.sentiment = sentiment_label
            feedback.processed = True
            feedback.save()

            # Integrate with learning service if negative feedback
            if sentiment_score < 0 and feedback.message:
                FeedbackService._integrate_with_learning(feedback, sentiment_score)

            logger.info(f"Feedback analyzed: {feedback.id}")
            return analysis

        except Exception as e:  # noqa: BLE001
            logger.error(f"Error analyzing feedback: {e}")
            return None

    @staticmethod
    def _integrate_with_learning(feedback, sentiment_score):
        """Integrate feedback with agent learning service"""
        try:
            from agents.services.learning_service_enhanced import get_learning_service

            learning_service = get_learning_service()

            # Provide negative reward for poor feedback
            reward = sentiment_score  # -1 to 0

            if feedback.message and feedback.agent:
                # Create state representation
                state = {
                    "agent_id": str(feedback.agent.id),
                    "message_id": str(feedback.message.id),
                    "user_satisfaction": sentiment_score,
                }

                # Provide feedback to learning system
                learning_service.provide_feedback(
                    agent_id=str(feedback.agent.id),
                    state=state,
                    action="generate_response",
                    reward=reward,
                )

                logger.info(f"Integrated feedback with learning service: {feedback.id}")

        except Exception as e:  # noqa: BLE001
            logger.error(f"Error integrating with learning service: {e}")

    @staticmethod
    def get_agent_insights(agent_id, days=30):
        """Get insights for an agent"""
        from .models import AgentRating, UserFeedback

        start_date = timezone.now() - timedelta(days=days)

        # Get feedback
        feedbacks = UserFeedback.objects.filter(
            agent_id=agent_id, created_at__gte=start_date
        )

        # Calculate metrics
        total_feedback = feedbacks.count()

        sentiment_counts = feedbacks.values("sentiment").annotate(count=Count("id"))
        sentiment_breakdown = {
            item["sentiment"]: item["count"] for item in sentiment_counts
        }

        avg_rating = (
            feedbacks.filter(rating__isnull=False).aggregate(avg=Avg("rating"))["avg"]
            or 0
        )

        # Get agent rating
        try:
            agent_rating = AgentRating.objects.get(agent_id=agent_id)
            rating_data = {
                "average_rating": float(agent_rating.average_rating),
                "total_ratings": agent_rating.total_ratings,
                "thumbs_up": agent_rating.thumbs_up_count,
                "thumbs_down": agent_rating.thumbs_down_count,
                "response_quality": float(agent_rating.response_quality_score),
            }
        except AgentRating.DoesNotExist:
            rating_data = {}

        # Common issues
        issues = feedbacks.filter(sentiment="negative").values_list(
            "comment", flat=True
        )[:10]

        return {
            "period_days": days,
            "total_feedback": total_feedback,
            "average_rating": round(avg_rating, 2),
            "sentiment_breakdown": sentiment_breakdown,
            "rating_data": rating_data,
            "recent_issues": list(issues),
        }

    @staticmethod
    def generate_trend_report(period="weekly", agent_id=None):
        """Generate feedback trend report"""
        from .models import FeedbackTrend, UserFeedback

        # Determine date range
        now = timezone.now()
        if period == "daily":
            start_date = now.date()
            end_date = start_date
        elif period == "weekly":
            start_date = (now - timedelta(days=7)).date()
            end_date = now.date()
        else:  # monthly
            start_date = (now - timedelta(days=30)).date()
            end_date = now.date()

        # Get feedback
        feedbacks = UserFeedback.objects.filter(
            created_at__date__range=[start_date, end_date]
        )

        if agent_id:
            feedbacks = feedbacks.filter(agent_id=agent_id)

        # Calculate metrics
        total_feedback = feedbacks.count()
        avg_rating = (
            feedbacks.filter(rating__isnull=False).aggregate(avg=Avg("rating"))["avg"]
            or 0
        )

        sentiment_counts = feedbacks.values("sentiment").annotate(count=Count("id"))
        positive = negative = neutral = 0
        for item in sentiment_counts:
            if item["sentiment"] == "positive":
                positive = item["count"]
            elif item["sentiment"] == "negative":
                negative = item["count"]
            else:
                neutral = item["count"]

        # Satisfaction score (0-100)
        satisfaction = (positive / total_feedback * 100) if total_feedback > 0 else 0

        # Common issues and requests
        top_issues = list(
            feedbacks.filter(feedback_type="bug_report").values("comment")[:5]
        )

        top_requests = list(
            feedbacks.filter(feedback_type="feature_request").values("comment")[:5]
        )

        # Create or update trend
        trend, created = FeedbackTrend.objects.update_or_create(  # noqa: RUF059
            period=period,
            start_date=start_date,
            end_date=end_date,
            agent_id=agent_id,
            defaults={
                "total_feedback": total_feedback,
                "average_rating": avg_rating,
                "satisfaction_score": satisfaction,
                "positive_count": positive,
                "neutral_count": neutral,
                "negative_count": negative,
                "top_issues": top_issues,
                "top_requests": top_requests,
            },
        )

        return trend


# Singleton instance
_feedback_service = None


def get_feedback_service():
    """Get FeedbackService singleton"""
    global _feedback_service
    if _feedback_service is None:
        _feedback_service = FeedbackService()
    return _feedback_service
