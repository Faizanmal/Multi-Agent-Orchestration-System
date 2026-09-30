from django.contrib import admin

from .models import (
    AdaptiveStrategy,
    AgentLearningProfile,
    LearningEvent,
    ReinforcementState,
    SkillMatrix,
)


@admin.register(AgentLearningProfile)
class AgentLearningProfileAdmin(admin.ModelAdmin):
    list_display = ('agent', 'algorithm', 'success_rate', 'total_tasks_completed', 'updated_at')
    list_filter = ('algorithm', 'created_at')
    search_fields = ('agent__name',)
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(ReinforcementState)
class ReinforcementStateAdmin(admin.ModelAdmin):
    list_display = ('learning_profile', 'task_type', 'success', 'reward', 'q_value', 'created_at')
    list_filter = ('success', 'task_type', 'created_at')
    search_fields = ('learning_profile__agent__name',)
    readonly_fields = ('id', 'created_at')


@admin.register(AdaptiveStrategy)
class AdaptiveStrategyAdmin(admin.ModelAdmin):
    list_display = ('name', 'strategy_type', 'success_rate', 'confidence_score', 'times_used', 'is_active')
    list_filter = ('strategy_type', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(LearningEvent)
class LearningEventAdmin(admin.ModelAdmin):
    list_display = ('learning_profile', 'event_type', 'improvement', 'created_at')
    list_filter = ('event_type', 'created_at')
    search_fields = ('learning_profile__agent__name', 'description')
    readonly_fields = ('id', 'created_at')


@admin.register(SkillMatrix)
class SkillMatrixAdmin(admin.ModelAdmin):
    list_display = ('learning_profile', 'skill_name', 'skill_category', 'expertise_level', 'attempts_count', 'success_count')
    list_filter = ('skill_category', 'created_at')
    search_fields = ('skill_name', 'learning_profile__agent__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
