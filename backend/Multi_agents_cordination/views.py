import logging

from agents.models import Agent
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import AgentCoordinationSession, CoordinationStrategy
from .services import CoordinationService

logger = logging.getLogger(__name__)
User = get_user_model()


def _default_user():
    user, _ = User.objects.get_or_create(
        email='default@example.com',
        defaults={'username': 'default_user', 'first_name': 'Default', 'last_name': 'User'},
    )
    return user


class CoordinationSessionViewSet(viewsets.ViewSet):
    """Manage multi-agent coordination sessions"""
    permission_classes = [AllowAny] if settings.DEBUG else [IsAuthenticated]

    def list(self, request):
        try:
            if request.user.is_authenticated:
                sessions = AgentCoordinationSession.objects.filter(user=request.user)
            elif settings.DEBUG:
                sessions = AgentCoordinationSession.objects.all()[:50]
            else:
                return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

            data = [{
                'id': str(session.id),
                'name': session.name,
                'strategy': session.strategy,
                'is_active': session.is_active,
                'created_at': session.created_at.isoformat(),
                'interaction_count': session.interactions.count(),
                'metrics_count': session.metrics.count(),
                'final_answer': (session.context or {}).get('final_answer', '')[:300],
                'task': (session.context or {}).get('task', '')[:200],
            } for session in sessions]
            return Response({'sessions': data, 'count': len(data)})
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error listing coordination sessions: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request):
        try:
            name = request.data.get('name', 'New Coordination Session')
            strategy = request.data.get('strategy', 'sequential')
            config = request.data.get('config', {})

            valid = {c.value for c in CoordinationStrategy}
            if strategy not in valid:
                return Response(
                    {'error': f'Invalid strategy. Use one of: {", ".join(sorted(valid))}'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user = request.user if request.user.is_authenticated else None
            if not user:
                if settings.DEBUG:
                    user = _default_user()
                else:
                    return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

            session = AgentCoordinationSession.objects.create(
                name=name,
                strategy=strategy,
                config=config or {},
                user=user,
            )
            return Response({
                'id': str(session.id),
                'name': session.name,
                'strategy': session.strategy,
                'created_at': session.created_at.isoformat(),
                'message': 'Coordination session created successfully',
            }, status=status.HTTP_201_CREATED)
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error creating coordination session: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, pk=None):
        try:
            session = AgentCoordinationSession.objects.get(id=pk)
            return Response({
                'id': str(session.id),
                'name': session.name,
                'strategy': session.strategy,
                'is_active': session.is_active,
                'config': session.config,
                'context': session.context,
                'created_at': session.created_at.isoformat(),
                'completed_at': session.completed_at.isoformat() if session.completed_at else None,
            })
        except AgentCoordinationSession.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    def destroy(self, request, pk=None):
        try:
            session = AgentCoordinationSession.objects.get(id=pk)
            session.delete()
            return Response({'success': True})
        except AgentCoordinationSession.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def coordinate_agents(self, request, pk=None):
        """Coordinate multiple agents for a task using real LLM strategies."""
        try:
            coordination_session = AgentCoordinationSession.objects.get(id=pk)

            agent_ids = request.data.get('agent_ids', [])
            task_description = (request.data.get('task') or '').strip()
            strategy = request.data.get('strategy', coordination_session.strategy)
            use_model_coord = bool(request.data.get('use_model_coordination', False))

            if not agent_ids or not task_description:
                return Response(
                    {'error': 'agent_ids and task are required'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            agents = list(Agent.objects.filter(id__in=agent_ids, is_active=True))
            if len(agents) != len(agent_ids):  # noqa: SIM102
                # Allow partial match in DEBUG if some IDs invalid
                if not agents:
                    return Response(
                        {'error': 'No active agents found for the given IDs'},
                        status=status.HTTP_404_NOT_FOUND,
                    )

            service = CoordinationService()
            result = service.execute_on_coordination_session(
                coord_session=coordination_session,
                strategy=strategy,
                agents=agents,
                task=task_description,
                context=request.data.get('context') or {},
            )

            # Optional: refine final answer via multi-model coordination
            if use_model_coord and result.get('final_answer'):
                try:
                    from Multi_model_Intelligence.coordination import (
                        get_coordination_service,
                    )
                    model_result = get_coordination_service().run(
                        mode='collaborative',
                        prompt=(
                            f"Improve and synthesize this multi-agent result for the task.\n\n"
                            f"Task: {task_description}\n\n"
                            f"Agent output:\n{result['final_answer']}"
                        ),
                        model_ids=request.data.get('model_ids'),
                        options={'rounds': 1},
                        user=request.user if request.user.is_authenticated else None,
                    )
                    result['model_coordination'] = {
                        'run_id': model_result.get('run_id'),
                        'mode': model_result.get('mode'),
                        'models_used': model_result.get('models_used'),
                    }
                    result['final_answer'] = model_result.get('final_answer') or result['final_answer']
                except Exception as exc:  # noqa: BLE001
                    logger.warning('Model coordination bridge skipped: %s', exc)
                    result['model_coordination_error'] = str(exc)

            return Response(result)
        except AgentCoordinationSession.DoesNotExist:
            return Response({'error': 'Coordination session not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception('Error coordinating agents')
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def quick_run(self, request):
        """
        Create a session and run coordination in one call.
        POST /coordination/api/sessions/quick_run/
        { name?, strategy, agent_ids, task, use_model_coordination? }
        """
        create_resp = self.create(request)
        if create_resp.status_code >= 400:
            return create_resp
        return self.coordinate_agents(request, pk=create_resp.data['id'])

    @action(detail=False, methods=['get'])
    def strategies(self, request):
        return Response({
            'strategies': [
                {'id': 'sequential', 'name': 'Sequential', 'description': 'Agents run in order; each builds on the previous output'},
                {'id': 'parallel', 'name': 'Parallel', 'description': 'All agents work at once; results are merged'},
                {'id': 'hierarchical', 'name': 'Hierarchical', 'description': 'Orchestrator delegates sub-tasks to specialists'},
                {'id': 'collaborative', 'name': 'Collaborative', 'description': 'Agents critique and refine a shared answer'},
                {'id': 'competitive', 'name': 'Competitive', 'description': 'Independent answers; a judge picks the best'},
            ]
        })

    @action(detail=True, methods=['get'])
    def interactions(self, request, pk=None):
        try:
            coordination_session = AgentCoordinationSession.objects.get(id=pk)
            interactions = coordination_session.interactions.all()[:100]
            data = [{
                'id': str(interaction.id),
                'source_agent_id': str(interaction.source_agent_id),
                'target_agent_id': str(interaction.target_agent_id),
                'interaction_type': interaction.interaction_type,
                'content': interaction.content,
                'created_at': interaction.created_at.isoformat(),
                'processed': interaction.processed,
            } for interaction in interactions]
            return Response({'interactions': data, 'count': len(data)})
        except AgentCoordinationSession.DoesNotExist:
            return Response({'error': 'Coordination session not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'])
    def metrics(self, request, pk=None):
        try:
            coordination_session = AgentCoordinationSession.objects.get(id=pk)
            metrics = list(coordination_session.metrics.all()[:50])
            data = [{
                'metric_name': metric.metric_name,
                'metric_value': metric.metric_value,
                'metadata': metric.metadata,
                'timestamp': metric.timestamp.isoformat(),
            } for metric in metrics]
            aggregated = {}
            for metric in metrics:
                aggregated.setdefault(metric.metric_name, []).append(metric.metric_value)
            summary = {
                name: {
                    'avg': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values),
                    'count': len(values),
                }
                for name, values in aggregated.items()
            }
            return Response({'metrics': data, 'summary': summary, 'count': len(data)})
        except AgentCoordinationSession.DoesNotExist:
            return Response({'error': 'Coordination session not found'}, status=status.HTTP_404_NOT_FOUND)
