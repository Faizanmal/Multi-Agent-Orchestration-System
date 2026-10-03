from rest_framework import serializers

from .models import (
    AdaptiveStrategy,
    AgentLearningPolicy,
    AgentLearningProfile,
    LearningEvent,
    ReinforcementState,
    SkillMatrix,
)


class SkillMatrixSerializer(serializers.ModelSerializer):
    success_rate = serializers.SerializerMethodField()

    class Meta:
        model = SkillMatrix
        fields = "__all__"

    def get_success_rate(self, obj):
        if obj.attempts_count == 0:
            return 0.0
        return obj.success_count / obj.attempts_count


class LearningEventSerializer(serializers.ModelSerializer):
    agent_name = serializers.CharField(
        source="learning_profile.agent.name", read_only=True
    )

    class Meta:
        model = LearningEvent
        fields = "__all__"


class AgentLearningProfileSerializer(serializers.ModelSerializer):
    agent_name = serializers.CharField(source="agent.name", read_only=True)
    agent_type = serializers.CharField(source="agent.agent_type", read_only=True)
    recent_events = LearningEventSerializer(source="events", many=True, read_only=True)
    skills = SkillMatrixSerializer(many=True, read_only=True)

    class Meta:
        model = AgentLearningProfile
        fields = "__all__"


class ReinforcementStateSerializer(serializers.ModelSerializer):
    agent_name = serializers.CharField(
        source="learning_profile.agent.name", read_only=True
    )

    class Meta:
        model = ReinforcementState
        fields = "__all__"


class AdaptiveStrategySerializer(serializers.ModelSerializer):
    sessions_count = serializers.SerializerMethodField()

    class Meta:
        model = AdaptiveStrategy
        fields = "__all__"

    def get_sessions_count(self, obj):
        return obj.learned_from_sessions.count()


class AgentLearningPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentLearningPolicy
        fields = "__all__"
