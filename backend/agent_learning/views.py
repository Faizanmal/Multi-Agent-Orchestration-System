import logging

from django.db.models import Avg, Count, Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (
    AdaptiveStrategy,
    AgentLearningProfile,
    LearningEvent,
    ReinforcementState,
    SkillMatrix,
)
from .serializers import (
    AdaptiveStrategySerializer,
    AgentLearningProfileSerializer,
    LearningEventSerializer,
    ReinforcementStateSerializer,
    SkillMatrixSerializer,
)
from .services import RLEngine, StrategyOptimizer

logger = logging.getLogger(__name__)


class AgentLearningViewSet(viewsets.ModelViewSet):
    """Manage agent learning profiles and training"""
    queryset = AgentLearningProfile.objects.all()
    serializer_class = AgentLearningProfileSerializer
    
    @action(detail=True, methods=['post'])
    def record_experience(self, request, pk=None):
        """Record a new experience for reinforcement learning"""
        profile = self.get_object()
        
        try:
            state = request.data.get('state', {})
            action = request.data.get('action', {})
            reward = request.data.get('reward', 0.0)
            next_state = request.data.get('next_state', {})
            task_type = request.data.get('task_type', 'general')
            success = request.data.get('success', False)
            execution_time = request.data.get('execution_time', 0.0)
            
            # Create reinforcement state
            rl_state = ReinforcementState.objects.create(
                learning_profile=profile,
                state_representation=state,
                action_taken=action,
                reward=reward,
                next_state=next_state,
                task_type=task_type,
                success=success,
                execution_time=execution_time
            )
            
            # Update Q-values using RL engine
            engine = RLEngine(profile)
            engine.update_q_values(rl_state)
            
            # Update profile metrics
            profile.total_tasks_completed += 1
            profile.save()
            
            return Response({
                'message': 'Experience recorded successfully',
                'state_id': str(rl_state.id),
                'q_value': rl_state.q_value
            })
            
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error recording experience: {e!s}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def get_recommendations(self, request, pk=None):
        """Get recommended actions based on current state"""
        profile = self.get_object()
        current_state = request.query_params.get('state', '{}')
        
        try:
            import json
            state_dict = json.loads(current_state)
            
            engine = RLEngine(profile)
            recommendations = engine.get_best_action(state_dict)
            
            return Response({
                'recommended_action': recommendations['action'],
                'expected_reward': recommendations['q_value'],
                'confidence': recommendations['confidence']
            })
            
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error getting recommendations: {e!s}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def update_skill(self, request, pk=None):
        """Update a specific skill for the agent"""
        profile = self.get_object()
        
        try:
            skill_name = request.data.get('skill_name')
            skill_category = request.data.get('skill_category')
            success = request.data.get('success', False)
            execution_time = request.data.get('execution_time', 0.0)
            
            # Get or create skill
            skill, _ = SkillMatrix.objects.get_or_create(
                learning_profile=profile,
                skill_name=skill_name,
                defaults={'skill_category': skill_category}
            )
            
            # Update skill metrics
            skill.attempts_count += 1
            if success:
                skill.success_count += 1
            else:
                skill.failure_count += 1
            
            # Update average execution time
            if skill.avg_execution_time == 0:
                skill.avg_execution_time = execution_time
            else:
                skill.avg_execution_time = (skill.avg_execution_time * (skill.attempts_count - 1) + execution_time) / skill.attempts_count
            
            # Calculate expertise level (success rate weighted by attempts)
            success_rate = skill.success_count / skill.attempts_count
            # Expertise improves with both success rate and experience
            skill.expertise_level = min(1.0, (success_rate * 0.7) + (min(skill.attempts_count / 100, 1.0) * 0.3))
            
            skill.last_used = timezone.now()
            skill.save()
            
            # Check for skill improvement events
            if skill.expertise_level > 0.8 and skill.attempts_count == 10:
                LearningEvent.objects.create(
                    learning_profile=profile,
                    event_type='skill_mastered',
                    description=f"Agent mastered skill: {skill_name}",
                    metrics_before={'expertise': 0.0},
                    metrics_after={'expertise': skill.expertise_level},
                    improvement=skill.expertise_level * 100
                )
            
            return Response({
                'message': 'Skill updated successfully',
                'skill': SkillMatrixSerializer(skill).data
            })
            
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error updating skill: {e!s}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def top_performers(self, request):
        """Get top performing agents"""
        top_agents = self.queryset.order_by('-success_rate')[:10]
        serializer = self.get_serializer(top_agents, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def learning_history(self, request, pk=None):
        """Get learning history and events"""
        profile = self.get_object()
        events = profile.events.all()[:50]
        serializer = LearningEventSerializer(events, many=True)
        return Response(serializer.data)


class AdaptiveStrategyViewSet(viewsets.ModelViewSet):
    """Manage adaptive coordination strategies"""
    queryset = AdaptiveStrategy.objects.filter(is_active=True)
    serializer_class = AdaptiveStrategySerializer
    
    @action(detail=False, methods=['post'])
    def recommend_strategy(self, request):
        """Recommend best strategy for given task"""
        try:
            task_description = request.data.get('task_description', '')
            task_complexity = request.data.get('complexity', 'medium')
            available_agents = request.data.get('agents', [])
            
            optimizer = StrategyOptimizer()
            recommended = optimizer.recommend_strategy(
                task_description=task_description,
                complexity=task_complexity,
                agents=available_agents
            )
            
            return Response(recommended)
            
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error recommending strategy: {e!s}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def record_usage(self, request, pk=None):
        """Record strategy usage and outcome"""
        strategy = self.get_object()
        
        try:
            success = request.data.get('success', False)
            completion_time = request.data.get('completion_time', 0.0)
            
            # Update usage stats
            strategy.times_used += 1
            
            # Update success rate (moving average)
            old_rate = strategy.success_rate
            strategy.success_rate = (old_rate * (strategy.times_used - 1) + (1.0 if success else 0.0)) / strategy.times_used
            
            # Update completion time (moving average)
            old_time = strategy.avg_completion_time
            strategy.avg_completion_time = (old_time * (strategy.times_used - 1) + completion_time) / strategy.times_used
            
            # Update confidence based on success rate and usage count
            usage_confidence = min(1.0, strategy.times_used / 50)  # Confidence increases with usage
            success_confidence = strategy.success_rate
            strategy.confidence_score = (usage_confidence * 0.3) + (success_confidence * 0.7)
            
            strategy.last_used = timezone.now()
            strategy.save()
            
            return Response({
                'message': 'Strategy usage recorded',
                'strategy': self.get_serializer(strategy).data
            })
            
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error recording strategy usage: {e!s}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def top_strategies(self, request):
        """Get top performing strategies"""
        strategies = self.queryset.order_by('-confidence_score', '-success_rate')[:10]
        serializer = self.get_serializer(strategies, many=True)
        return Response(serializer.data)


class ReinforcementStateViewSet(viewsets.ReadOnlyModelViewSet):
    """View reinforcement learning states (read-only)"""
    queryset = ReinforcementState.objects.all()
    serializer_class = ReinforcementStateSerializer
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Get analytics on RL states"""
        agent_id = request.query_params.get('agent_id')
        task_type = request.query_params.get('task_type')
        
        queryset = self.queryset
        if agent_id:
            queryset = queryset.filter(learning_profile__agent_id=agent_id)
        if task_type:
            queryset = queryset.filter(task_type=task_type)
        
        analytics = {
            'total_states': queryset.count(),
            'success_rate': queryset.filter(success=True).count() / max(queryset.count(), 1),
            'avg_reward': queryset.aggregate(Avg('reward'))['reward__avg'] or 0,
            'avg_execution_time': queryset.aggregate(Avg('execution_time'))['execution_time__avg'] or 0,
            'by_task_type': {}
        }
        
        # Task type breakdown
        task_types = queryset.values('task_type').annotate(
            count=Count('id'),
            avg_reward=Avg('reward'),
            success_rate=Count('id', filter=Q(success=True))
        )
        
        for tt in task_types:
            analytics['by_task_type'][tt['task_type']] = {
                'count': tt['count'],
                'avg_reward': tt['avg_reward'],
                'success_rate': tt['success_rate'] / tt['count'] if tt['count'] > 0 else 0
            }
        
        return Response(analytics)
