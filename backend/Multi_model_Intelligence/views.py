import json
import logging

from agents.services.groq_service import GroqService
from agents.services.multimodal_processor import MultiModalProcessor
from asgiref.sync import async_to_sync
from django.conf import settings
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .catalog import seed_default_ai_models
from .coordination import get_coordination_service
from .models import (
    AIModelConfig,
    CrossModalInsight,
    ModalityResult,
    ModelCoordinationRun,
    MultiModalSession,
)

logger = logging.getLogger(__name__)

class AIModelConfigViewSet(viewsets.ViewSet):
    """Manage AI model configurations"""
    permission_classes = [AllowAny] if settings.DEBUG else [IsAuthenticated]

    def list(self, request):
        """List AI model configurations (user's + global defaults)."""
        try:
            model_type = request.query_params.get('model_type')
            is_active = request.query_params.get('is_active')

            queryset = AIModelConfig.objects.all()
            if request.user.is_authenticated:
                from django.db.models import Q
                queryset = queryset.filter(
                    Q(created_by=request.user) | Q(created_by__isnull=True)
                )

            if model_type:
                queryset = queryset.filter(model_type=model_type)
            if is_active is not None:
                queryset = queryset.filter(is_active=is_active.lower() == 'true')

            data = [self._serialize(config) for config in queryset[:100]]
            return Response({'models': data, 'count': len(data)})
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error listing AI models: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request):
        """Create a new AI model configuration"""
        try:
            name = request.data.get('name')
            model_type = request.data.get('model_type')
            provider = request.data.get('provider')
            model_id = request.data.get('model_id')

            if not all([name, model_type, provider, model_id]):
                return Response(
                    {'error': 'name, model_type, provider, and model_id are required'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Normalize UI aliases
            type_aliases = {'image': 'vision', 'llm': 'text'}
            model_type = type_aliases.get(str(model_type).lower(), model_type)

            config_payload = dict(request.data.get('config') or {})
            api_key = request.data.get('api_key')
            if api_key:
                config_payload['api_key'] = api_key

            config = AIModelConfig.objects.create(
                name=name,
                model_type=model_type,
                provider=str(provider).lower(),
                model_id=model_id,
                config=config_payload,
                capabilities=request.data.get('capabilities') or [],
                is_default=bool(request.data.get('is_default', False)),
                created_by=request.user if request.user.is_authenticated else None,
            )

            return Response(
                {**self._serialize(config), 'message': 'AI model configuration created successfully'},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error creating AI model config: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, pk=None):
        try:
            config = AIModelConfig.objects.get(pk=pk)
            return Response(self._serialize(config))
        except AIModelConfig.DoesNotExist:
            return Response({'error': 'Model not found'}, status=status.HTTP_404_NOT_FOUND)

    def partial_update(self, request, pk=None):
        try:
            config = AIModelConfig.objects.get(pk=pk)
            for field in ('name', 'model_type', 'provider', 'model_id', 'capabilities', 'is_active', 'is_default'):
                if field in request.data:
                    setattr(config, field, request.data[field])
            if 'config' in request.data and isinstance(request.data['config'], dict):
                merged = dict(config.config or {})
                merged.update(request.data['config'])
                config.config = merged
            if request.data.get('api_key'):
                merged = dict(config.config or {})
                merged['api_key'] = request.data['api_key']
                config.config = merged
            config.save()
            return Response(self._serialize(config))
        except AIModelConfig.DoesNotExist:
            return Response({'error': 'Model not found'}, status=status.HTTP_404_NOT_FOUND)

    def destroy(self, request, pk=None):
        try:
            config = AIModelConfig.objects.get(pk=pk)
            config.delete()
            return Response({'success': True, 'message': 'Model deleted'})
        except AIModelConfig.DoesNotExist:
            return Response({'error': 'Model not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def seed_defaults(self, request):
        """Seed built-in provider models if the catalog is empty."""
        created = seed_default_ai_models(
            user=request.user if request.user.is_authenticated else None
        )
        return Response({'created': created, 'count': len(created)})

    @staticmethod
    def _serialize(config: AIModelConfig) -> dict:
        safe_config = dict(config.config or {})
        if safe_config.get('api_key'):
            safe_config['api_key'] = '••••••••'
        return {
            'id': str(config.id),
            'name': config.name,
            'model_type': config.model_type,
            'provider': config.provider,
            'model_id': config.model_id,
            'capabilities': config.capabilities or [],
            'is_active': config.is_active,
            'is_default': config.is_default,
            'config': safe_config,
            'created_at': config.created_at.isoformat() if config.created_at else None,
            'updated_at': config.updated_at.isoformat() if config.updated_at else None,
        }


class MultiModalIntelligenceViewSet(viewsets.ViewSet):
    """Multi-modal intelligence processing"""
    permission_classes = [AllowAny] if settings.DEBUG else [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]  # noqa: RUF012
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.processor = MultiModalProcessor()
        self.groq_service = GroqService()
    
    @action(detail=False, methods=['post'])
    def process_multimodal(self, request):
        """Process multi-modal input with intelligence"""
        try:
            # Create session
            user = request.user if request.user.is_authenticated else None
            if not user:
                return Response(
                    {'error': 'Authentication required'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            session_name = request.data.get('session_name', 'Multi-Modal Processing')
            session = MultiModalSession.objects.create(
                name=session_name,
                user=user,
                status='processing'
            )
            
            # Collect input data
            input_data = {}
            input_modalities = []
            
            if 'text' in request.data:
                input_data['text'] = request.data['text']
                input_modalities.append('text')
            
            for field_name in ['image', 'audio', 'video', 'document']:
                if field_name in request.FILES:
                    input_data[field_name] = request.FILES[field_name]
                    input_modalities.append(field_name)
            
            if not input_data:
                session.status = 'failed'
                session.save()
                return Response(
                    {'error': 'No input data provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            session.input_modalities = input_modalities
            session.save()
            
            # Process multi-modal input
            processing_options = request.data.get('processing_options', {})
            if isinstance(processing_options, str):
                processing_options = json.loads(processing_options)
            
            result = async_to_sync(self.processor.process_multimodal_input)(
                input_data=input_data,
                processing_options=processing_options
            )
            
            # Store results for each modality
            for modality_type, modality_result in result.get('results', {}).items():
                ModalityResult.objects.create(
                    session=session,
                    modality_type=modality_type,
                    output_data=modality_result,
                    confidence_score=modality_result.get('confidence', 0.0),
                    processing_time=result.get('processing_time', 0.0) / len(result.get('results', {}))
                )
            
            # Generate cross-modal insights
            if len(input_modalities) > 1:
                insights = self._generate_cross_modal_insights(
                    session, 
                    result.get('results', {}), 
                    input_modalities
                )
                result['cross_modal_insights'] = insights
            
            # Update session
            session.results = result
            session.status = 'completed'
            session.completed_at = timezone.now()
            session.save()
            
            return Response({
                'session_id': str(session.id),
                'results': result,
                'input_modalities': input_modalities,
                'status': 'completed'
            })
            
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error in multi-modal processing: {e}")
            if 'session' in locals():
                session.status = 'failed'
                session.save()
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def cross_modal_analysis(self, request):
        """Perform cross-modal analysis"""
        try:
            modality_results = request.data.get('modality_results', {})
            
            if len(modality_results) < 2:
                return Response(
                    {'error': 'At least 2 modalities required for cross-modal analysis'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Analyze correlations
            insights = []
            modalities = list(modality_results.keys())
            
            for i, mod1 in enumerate(modalities):
                for mod2 in modalities[i+1:]:
                    insight = self._analyze_modality_pair(
                        mod1, 
                        modality_results[mod1],
                        mod2, 
                        modality_results[mod2]
                    )
                    insights.append(insight)
            
            return Response({
                'insights': insights,
                'analyzed_modalities': modalities,
                'insight_count': len(insights)
            })
            
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error in cross-modal analysis: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def sessions(self, request):
        """List multi-modal sessions"""
        try:
            user = request.user if request.user.is_authenticated else None
            if not user:
                return Response(
                    {'error': 'Authentication required'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            sessions = MultiModalSession.objects.filter(user=user)[:20]
            
            data = [{
                'id': str(session.id),
                'name': session.name,
                'status': session.status,
                'input_modalities': session.input_modalities,
                'created_at': session.created_at.isoformat(),
                'completed_at': session.completed_at.isoformat() if session.completed_at else None,
                'modality_count': session.modality_results.count(),
                'insights_count': session.cross_modal_insights.count(),
            } for session in sessions]
            
            return Response({'sessions': data, 'count': len(data)})
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error listing sessions: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def session_detail(self, request, pk=None):
        """Get detailed information about a session"""
        try:
            session = MultiModalSession.objects.get(id=pk)
            
            if not request.user.is_authenticated or session.user != request.user:  # noqa: SIM102
                if not settings.DEBUG:
                    return Response(
                        {'error': 'Unauthorized'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            modality_results = [{
                'id': str(result.id),
                'modality_type': result.modality_type,
                'confidence_score': result.confidence_score,
                'processing_time': result.processing_time,
                'output_data': result.output_data,
            } for result in session.modality_results.all()]
            
            insights = [{
                'id': str(insight.id),
                'insight_type': insight.insight_type,
                'involved_modalities': insight.involved_modalities,
                'description': insight.description,
                'confidence': insight.confidence,
            } for insight in session.cross_modal_insights.all()]
            
            return Response({
                'id': str(session.id),
                'name': session.name,
                'status': session.status,
                'input_modalities': session.input_modalities,
                'results': session.results,
                'modality_results': modality_results,
                'cross_modal_insights': insights,
                'created_at': session.created_at.isoformat(),
            })
        except MultiModalSession.DoesNotExist:
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error fetching session detail: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _generate_cross_modal_insights(self, session, results, modalities):
        """Generate insights from cross-modal analysis"""
        insights = []
        
        try:
            # Use AI to analyze relationships
            analysis_prompt = f"""
            Analyze the following multi-modal results and identify key insights:
            
            Modalities: {modalities}
            Results: {json.dumps(results, indent=2)}
            
            Identify:
            1. Correlations between different modalities
            2. Contradictions or inconsistencies
            3. Reinforcing evidence across modalities
            4. Unique insights from each modality
            
            Provide insights in a structured format.
            """
            
            ai_insights = self.groq_service.chat_completion([
                {"role": "user", "content": analysis_prompt}
            ])
            
            # Create insight record
            CrossModalInsight.objects.create(
                session=session,
                insight_type='ai_analysis',
                involved_modalities=modalities,
                description=ai_insights.get('content', 'AI analysis completed'),
                confidence=0.85,
                evidence=results
            )
            
            insights.append({
                'type': 'ai_analysis',
                'modalities': modalities,
                'description': ai_insights.get('content', ''),
                'confidence': 0.85
            })
            
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error generating cross-modal insights: {e}")
        
        return insights
    
    def _analyze_modality_pair(self, mod1, result1, mod2, result2):
        """Analyze a pair of modalities for correlations"""
        return {
            'modalities': [mod1, mod2],
            'correlation_type': 'reinforcement',
            'confidence': 0.75,
            'description': f"Analysis of {mod1} and {mod2} modalities"
        }


# ===== MULTI-MODEL ORCHESTRATION VIEWSET =====

class MultiModelViewSet(viewsets.ViewSet):
    """ViewSet for multi-model orchestration operations"""
    permission_classes = [AllowAny] if settings.DEBUG else [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def chat(self, request):
        """
        Execute chat completion with automatic model selection
        
        POST /api/multimodel/chat/
        {
            "messages": [...],
            "complexity": "moderate",  # optional
            "priority": "balanced",  # speed, cost, quality, balanced
            "stream": false
        }
        """
        try:
            from .services import TaskComplexity, get_orchestrator
            orchestrator = get_orchestrator()
            
            messages = request.data.get('messages', [])
            if not messages:
                return Response(
                    {'error': 'Messages are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get parameters
            complexity_str = request.data.get('complexity')
            complexity = TaskComplexity[complexity_str.upper()] if complexity_str else None
            
            priority = request.data.get('priority', 'balanced')
            stream = request.data.get('stream', False)
            
            # Get user preferences
            user_prefs = self._get_user_preferences(request.user)
            
            # Execute
            result = orchestrator.chat_completion(
                messages=messages,
                complexity=complexity,
                priority=user_prefs.get('priority', priority),
                stream=stream,
                constraints=user_prefs.get('constraints', {})
            )
            
            if 'error' not in result:
                # Log execution
                self._log_execution(request.user, messages, result)
            
            return Response(result)
            
        except Exception as e:  # noqa: BLE001
            logger.error(f"Chat completion error: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def models(self, request):
        """Get available models and their capabilities"""
        from .services import ModelConfig
        
        models_data = {}
        for provider, models in ModelConfig.MODELS.items():
            models_data[provider.value] = {
                model_name: {
                    'complexity': [c.value for c in config['complexity']],
                    'speed': config['speed'],
                    'cost': config['cost'],
                    'context_window': config['context_window'],
                    'strengths': config['strengths']
                }
                for model_name, config in models.items()
            }
        
        return Response(models_data)
    
    @action(detail=False, methods=['get'])
    def performance(self, request):
        """Get performance insights"""
        from .models import ModelExecution
        from .services import get_orchestrator
        
        orchestrator = get_orchestrator()
        insights = orchestrator.get_performance_insights()
        
        # Add user-specific metrics
        user_executions = ModelExecution.objects.filter(user=request.user).order_by('-created_at')[:100]
        
        user_stats = {
            'total_executions': user_executions.count(),
            'success_rate': sum(1 for e in user_executions if e.success) / max(user_executions.count(), 1),
            'avg_duration': sum(e.duration_ms for e in user_executions) / max(user_executions.count(), 1) if user_executions.count() > 0 else 0,
            'total_tokens': sum(e.tokens_used for e in user_executions),
            'estimated_cost': sum(float(e.estimated_cost) for e in user_executions)
        }
        
        return Response({
            'global_insights': insights,
            'user_stats': user_stats
        })
    
    @action(detail=False, methods=['get', 'put'])
    def preferences(self, request):
        """Get or update user model preferences"""
        from .models import ModelPreference
        
        if request.method == 'GET':
            try:
                pref = ModelPreference.objects.get(user=request.user)
                return Response({
                    'default_priority': pref.default_priority,
                    'max_cost_per_request': str(pref.max_cost_per_request) if pref.max_cost_per_request else None,
                    'monthly_budget': str(pref.monthly_budget) if pref.monthly_budget else None,
                    'preferred_providers': pref.preferred_providers,
                    'disabled_providers': pref.disabled_providers,
                    'complexity_overrides': pref.complexity_overrides
                })
            except ModelPreference.DoesNotExist:
                return Response({
                    'default_priority': 'balanced',
                    'preferred_providers': [],
                    'disabled_providers': [],
                    'complexity_overrides': {}
                })
        
        elif request.method == 'PUT':
            pref, created = ModelPreference.objects.get_or_create(user=request.user)  # noqa: RUF059
            
            # Update fields
            if 'default_priority' in request.data:
                pref.default_priority = request.data['default_priority']
            if 'max_cost_per_request' in request.data:
                pref.max_cost_per_request = request.data['max_cost_per_request']
            if 'monthly_budget' in request.data:
                pref.monthly_budget = request.data['monthly_budget']
            if 'preferred_providers' in request.data:
                pref.preferred_providers = request.data['preferred_providers']
            if 'disabled_providers' in request.data:
                pref.disabled_providers = request.data['disabled_providers']
            if 'complexity_overrides' in request.data:
                pref.complexity_overrides = request.data['complexity_overrides']
            
            pref.save()
            
            return Response({'message': 'Preferences updated successfully'})
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get user's model execution history"""
        from .models import ModelExecution
        
        limit = int(request.query_params.get('limit', 50))
        provider = request.query_params.get('provider')
        complexity = request.query_params.get('complexity')
        
        queryset = ModelExecution.objects.filter(user=request.user)
        
        if provider:
            queryset = queryset.filter(provider=provider)
        if complexity:
            queryset = queryset.filter(complexity=complexity)
        
        executions = queryset[:limit]
        
        data = [{
            'id': str(e.id),
            'provider': e.provider,
            'model_name': e.model_name,
            'complexity': e.complexity,
            'duration_ms': e.duration_ms,
            'tokens_used': e.tokens_used,
            'estimated_cost': str(e.estimated_cost),
            'success': e.success,
            'created_at': e.created_at.isoformat()
        } for e in executions]
        
        return Response(data)
    
    @action(detail=False, methods=['post'])
    def analyze_complexity(self, request):
        """Analyze task complexity for given messages"""
        from .services import get_orchestrator
        
        messages = request.data.get('messages', [])
        if not messages:
            return Response(
                {'error': 'Messages are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        orchestrator = get_orchestrator()
        complexity = orchestrator.analyze_task_complexity(messages)
        
        # Get recommended model
        provider, model = orchestrator.select_optimal_model(
            complexity,
            request.data.get('priority', 'balanced')
        )
        
        return Response({
            'complexity': complexity.value,
            'recommended_provider': provider.value,
            'recommended_model': model
        })
    
    def _get_user_preferences(self, user):
        """Get user preferences"""
        from .models import ModelPreference
        
        try:
            pref = ModelPreference.objects.get(user=user)
            return {
                'priority': pref.default_priority,
                'constraints': {
                    'max_cost': 'low' if pref.max_cost_per_request and float(pref.max_cost_per_request) < 0.01 else None
                }
            }
        except ModelPreference.DoesNotExist:
            return {'priority': 'balanced', 'constraints': {}}
    
    def _log_execution(self, user, messages, result):
        """Log model execution"""
        from .models import ModelExecution
        
        try:
            metadata = result.get('metadata', {})
            usage = result.get('usage', {})
            
            ModelExecution.objects.create(
                user=user,
                provider=metadata.get('provider', 'unknown'),
                model_name=metadata.get('model', 'unknown'),
                complexity=metadata.get('complexity', 'simple'),
                prompt=str(messages[-1].get('content', ''))[:1000] if messages else '',
                response=result.get('content', '')[:1000] if result.get('content') else '',
                duration_ms=int(metadata.get('duration', 0) * 1000),
                tokens_used=usage.get('total_tokens', 0),
                prompt_tokens=usage.get('prompt_tokens', 0),
                completion_tokens=usage.get('completion_tokens', 0),
                estimated_cost=0.0,  # Calculate based on provider pricing
                success='error' not in result,
                error_message=result.get('error'),
                priority=metadata.get('priority', 'balanced')
            )
        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to log execution: {e}")


class ModelCoordinationViewSet(viewsets.ViewSet):
    """Coordinate registered AI models with each other."""
    permission_classes = [AllowAny] if settings.DEBUG else [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def run(self, request):
        """
        POST /intelligence/api/coordinate/run/
        {
          "prompt": "...",
          "mode": "route|collaborative|debate|pipeline",
          "model_ids": ["uuid", ...],  // optional
          "options": { "rounds": 2, "priority": "balanced", "judge_model_id": "..." }
        }
        """
        prompt = (request.data.get('prompt') or request.data.get('task') or '').strip()
        mode = (request.data.get('mode') or 'route').lower()
        model_ids = request.data.get('model_ids') or []
        options = request.data.get('options') or {}

        if not prompt:
            return Response({'error': 'prompt is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            service = get_coordination_service()
            result = service.run(
                mode=mode,
                prompt=prompt,
                model_ids=[str(i) for i in model_ids] if model_ids else None,
                options=options,
                user=request.user if request.user.is_authenticated else None,
            )
            return Response(result)
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.exception('Model coordination failed')
            return Response({'error': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def history(self, request):
        qs = ModelCoordinationRun.objects.all()
        if request.user.is_authenticated:
            qs = qs.filter(user=request.user)
        qs = qs[:30]
        data = [{
            'id': str(r.id),
            'mode': r.mode,
            'prompt': r.prompt[:200],
            'status': r.status,
            'final_answer': (r.final_answer or '')[:500],
            'duration_ms': r.duration_ms,
            'model_ids': r.model_ids,
            'created_at': r.created_at.isoformat(),
        } for r in qs]
        return Response({'results': data, 'count': len(data)})

    @action(detail=False, methods=['get'])
    def modes(self, request):
        return Response({
            'modes': [
                {
                    'id': 'route',
                    'name': 'Smart Route',
                    'description': 'Pick the best model and failover across the others',
                },
                {
                    'id': 'collaborative',
                    'name': 'Collaborative',
                    'description': 'Models propose together, refine a shared draft, then synthesize',
                },
                {
                    'id': 'debate',
                    'name': 'Debate / Consensus',
                    'description': 'Independent answers, peer critique, then a judge picks the winner',
                },
                {
                    'id': 'pipeline',
                    'name': 'Sequential Pipeline',
                    'description': 'Each model processes the previous stage output in order',
                },
            ]
        })

