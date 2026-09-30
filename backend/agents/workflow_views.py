from datetime import timezone

# backend/agents/workflow_views.py
"""
API Views for Workflow Management
Provides endpoints for creating, executing, and monitoring workflows
"""

import asyncio
import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Agent
from .services.workflow_orchestrator import WorkflowOrchestrator
from .services.workflow_templates import (
    WorkflowCategory,
    WorkflowTemplates,
    get_template,
)

logger = logging.getLogger(__name__)


class WorkflowViewSet(viewsets.ViewSet):
    """
    ViewSet for managing and executing workflows
    """
    permission_classes = [AllowAny] if settings.DEBUG else [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orchestrator = WorkflowOrchestrator()
    
    @action(detail=False, methods=['get'])
    def templates(self, request):
        """
        List all available workflow templates
        
        GET /api/workflows/templates/
        Query params:
        - category: Filter by workflow category
        """
        try:
            templates = WorkflowTemplates.get_all_templates()
            
            # Filter by category if provided
            category = request.query_params.get('category')
            if category:
                templates = {
                    k: v for k, v in templates.items()
                    if v.get('category') == category
                }
            
            # Format for API response
            template_list = [
                {
                    'id': template['id'],
                    'name': template['name'],
                    'description': template['description'],
                    'category': template['category'],
                    'step_count': len(template['steps']),
                    'input_schema': template.get('input_schema', {}),
                }
                for template in templates.values()
            ]
            
            return Response({
                'count': len(template_list),
                'templates': template_list
            })
            
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error fetching templates: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """
        List all workflow categories
        
        GET /api/workflows/categories/
        """
        try:
            categories = [
                {
                    'value': cat.value,
                    'name': cat.name.replace('_', ' ').title()
                }
                for cat in WorkflowCategory
            ]
            
            return Response({'categories': categories})
            
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error fetching categories: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def template_detail(self, request, pk=None):
        """
        Get detailed information about a specific workflow template
        
        GET /api/workflows/{template_id}/template_detail/
        """
        try:
            template = get_template(pk)
            
            if not template:
                return Response(
                    {'error': f'Template {pk} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(template)
            
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error fetching template detail: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def execute(self, request):
        """
        Execute a workflow
        
        POST /api/workflows/execute/
        Body:
        {
            "workflow_id": "data_analysis_pipeline",
            "input_data": {
                "data_source": "file.csv",
                "analysis_type": "descriptive"
            },
            "session_id": "optional-session-id"
        }
        """
        try:
            workflow_id = request.data.get('workflow_id')
            input_data = request.data.get('input_data', {})
            session_id = request.data.get('session_id')
            
            if not workflow_id:
                return Response(
                    {'error': 'workflow_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate template exists
            template = get_template(workflow_id)
            if not template:
                return Response(
                    {'error': f'Workflow template {workflow_id} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get user ID
            user_id = request.user.id if request.user.is_authenticated else 1
            
            # Execute workflow asynchronously
            result = asyncio.run(
                self.orchestrator.execute_workflow(
                    workflow_id=workflow_id,
                    input_data=input_data,
                    user_id=user_id,
                    session_id=session_id,
                    callback=self._create_progress_callback(session_id)
                )
            )
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.exception("Error executing workflow")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def execute_async(self, request):
        """
        Execute a workflow asynchronously (non-blocking)
        
        POST /api/workflows/execute_async/
        Body:
        {
            "workflow_id": "data_analysis_pipeline",
            "input_data": {...},
            "session_id": "optional-session-id"
        }
        
        Returns immediately with execution_id for status checking
        """
        try:
            workflow_id = request.data.get('workflow_id')
            input_data = request.data.get('input_data', {})
            session_id = request.data.get('session_id')
            
            if not workflow_id:
                return Response(
                    {'error': 'workflow_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate template exists
            template = get_template(workflow_id)
            if not template:
                return Response(
                    {'error': f'Workflow template {workflow_id} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get user ID
            user_id = request.user.id if request.user.is_authenticated else 1
            
            # Generate execution ID
            from datetime import datetime
            execution_id = f"{workflow_id}_{int(datetime.now(timezone.utc).timestamp())}"
            
            # Start workflow in background
            # In production, you'd use Celery or similar
            import threading
            
            def run_workflow():
                try:
                    asyncio.run(
                        self.orchestrator.execute_workflow(
                            workflow_id=workflow_id,
                            input_data=input_data,
                            user_id=user_id,
                            session_id=session_id,
                            callback=self._create_progress_callback(session_id)
                        )
                    )
                except Exception as e:  # noqa: BLE001
                    logger.error(f"Background workflow execution failed: {e}")
            
            thread = threading.Thread(target=run_workflow)
            thread.daemon = True
            thread.start()
            
            return Response({
                'execution_id': execution_id,
                'status': 'started',
                'message': 'Workflow execution started in background'
            }, status=status.HTTP_202_ACCEPTED)
            
        except Exception as e:
            logger.exception("Error starting async workflow")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """
        Get status of a workflow execution
        
        GET /api/workflows/{execution_id}/status/
        """
        try:
            status_info = self.orchestrator.get_workflow_status(pk)
            
            if not status_info:
                return Response(
                    {'error': 'Workflow execution not found or completed'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(status_info)
            
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error fetching workflow status: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def quick_start(self, request):
        """
        Quick start workflows with common use cases
        
        POST /api/workflows/quick_start/
        Body:
        {
            "use_case": "analyze_data" | "support_ticket" | "code_review" | "research",
            "input": "User's input text or data"
        }
        """
        try:
            use_case = request.data.get('use_case')
            user_input = request.data.get('input')
            
            if not use_case or not user_input:
                return Response(
                    {'error': 'use_case and input are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Map use cases to workflows
            workflow_mapping = {
                'analyze_data': {
                    'workflow_id': 'data_analysis_pipeline',
                    'input_transform': lambda x: {
                        'data_source': x,
                        'analysis_type': 'descriptive',
                        'output_format': 'report'
                    }
                },
                'support_ticket': {
                    'workflow_id': 'customer_support_ticket',
                    'input_transform': lambda x: {
                        'customer_message': x,
                        'priority': 'medium'
                    }
                },
                'code_review': {
                    'workflow_id': 'code_review_process',
                    'input_transform': lambda x: {
                        'repository': x,
                        'branch': 'main'
                    }
                },
                'research': {
                    'workflow_id': 'research_and_summarize',
                    'input_transform': lambda x: {
                        'research_query': x,
                        'depth': 'moderate',
                        'output_format': 'summary'
                    }
                },
                'create_content': {
                    'workflow_id': 'content_creation_workflow',
                    'input_transform': lambda x: {
                        'topic': x,
                        'content_type': 'article',
                        'length': 'medium',
                        'tone': 'professional'
                    }
                },
                'fix_bug': {
                    'workflow_id': 'bug_investigation',
                    'input_transform': lambda x: {
                        'bug_description': x,
                        'steps_to_reproduce': []
                    }
                },
            }
            
            if use_case not in workflow_mapping:
                return Response(
                    {
                        'error': f'Unknown use case: {use_case}',
                        'available_use_cases': list(workflow_mapping.keys())
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            workflow_config = workflow_mapping[use_case]
            workflow_id = workflow_config['workflow_id']
            input_data = workflow_config['input_transform'](user_input)
            
            # Get user ID
            user_id = request.user.id if request.user.is_authenticated else 1
            
            # Execute workflow
            result = asyncio.run(
                self.orchestrator.execute_workflow(
                    workflow_id=workflow_id,
                    input_data=input_data,
                    user_id=user_id,
                    session_id=None
                )
            )
            
            return Response({
                'use_case': use_case,
                'workflow_id': workflow_id,
                'result': result
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.exception("Error in quick start")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def agent_capabilities(self, request):
        """
        Get available agent capabilities for workflow planning
        
        GET /api/workflows/agent_capabilities/
        """
        try:
            # Get user ID
            user_id = request.user.id if request.user.is_authenticated else 1
            
            # Get all agents for user
            agents = Agent.objects.filter(owner_id=user_id, is_active=True)
            
            # Group by type and aggregate capabilities
            capabilities_by_type = {}
            for agent in agents:
                agent_type = agent.type
                if agent_type not in capabilities_by_type:
                    capabilities_by_type[agent_type] = {
                        'type': agent_type,
                        'count': 0,
                        'capabilities': set(),
                        'agents': []
                    }
                
                capabilities_by_type[agent_type]['count'] += 1
                capabilities_by_type[agent_type]['capabilities'].update(agent.capabilities)
                capabilities_by_type[agent_type]['agents'].append({
                    'id': str(agent.id),
                    'name': agent.name,
                    'status': agent.status
                })
            
            # Convert sets to lists for JSON serialization
            for agent_type, value in capabilities_by_type.items():
                value['capabilities'] = list(
                    value['capabilities']
                )
            
            return Response({
                'agent_types': list(capabilities_by_type.values())
            })
            
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error fetching agent capabilities: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _create_progress_callback(self, session_id):
        """Create a callback function for sending progress updates"""
        
        def callback(progress):
            """Send progress update via WebSocket"""
            if session_id:
                try:
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        f"session_{session_id}",
                        {
                            'type': 'workflow_progress',
                            'progress': progress
                        }
                    )
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"Could not send progress update: {e}")
        
        return callback
