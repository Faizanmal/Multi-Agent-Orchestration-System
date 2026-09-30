# Model Context Protocol (MCP) Integration Views

from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import MCPSession, MCPTool, MCPToolExecution
from .serializers import MCPToolSerializer
from .services import MCPService, MCPToolRegistry


class MCPToolViewSet(viewsets.ModelViewSet):
    """MCP Tool management and execution."""
    
    serializer_class = MCPToolSerializer
    permission_classes = [AllowAny] if settings.DEBUG else [IsAuthenticated]
    
    def get_queryset(self):
        if settings.DEBUG:
            return MCPTool.objects.all()
        return MCPTool.objects.filter(is_public=True)
    
    @action(detail=False, methods=['get'])
    def available_tools(self, request):
        """Get all available MCP tools."""
        try:
            registry = MCPToolRegistry()
            available_tools = registry.get_available_tools()
            
            return Response({
                'tools': available_tools,
                'count': len(available_tools)
            })
            
        except Exception as e:  # noqa: BLE001
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def execute_tool(self, request, pk=None):
        """Execute an MCP tool with given parameters."""
        tool = self.get_object()
        parameters = request.data.get('parameters', {})
        session_id = request.data.get('session_id')
        
        try:
            mcp_service = MCPService()
            
            # Execute tool
            execution_result = mcp_service.execute_tool(
                tool_name=tool.name,
                parameters=parameters,
                session_id=session_id
            )
            
            # Record execution
            execution = MCPToolExecution.objects.create(
                tool=tool,
                session_id=session_id,
                parameters=parameters,
                result=execution_result,
                success=execution_result.get('success', False),
                execution_time=execution_result.get('execution_time', 0)
            )
            
            return Response({
                'execution_id': str(execution.id),
                'result': execution_result,
                'success': execution.success
            })
            
        except Exception as e:  # noqa: BLE001
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def batch_execute(self, request):
        """Execute multiple MCP tools in sequence or parallel."""
        tools_config = request.data.get('tools', [])
        execution_mode = request.data.get('mode', 'sequential')  # sequential or parallel
        session_id = request.data.get('session_id')
        
        if not tools_config:
            return Response(
                {'error': 'tools configuration is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            mcp_service = MCPService()
            
            if execution_mode == 'parallel':
                results = mcp_service.execute_tools_parallel(tools_config, session_id)
            else:
                results = mcp_service.execute_tools_sequential(tools_config, session_id)
            
            return Response({
                'results': results,
                'execution_mode': execution_mode,
                'total_tools': len(tools_config)
            })
            
        except Exception as e:  # noqa: BLE001
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MCPSessionViewSet(viewsets.ViewSet):
    """MCP Session management for context persistence."""
    
    permission_classes = [AllowAny] if settings.DEBUG else [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def create_session(self, request):
        """Create a new MCP session with tools and context."""
        session_name = request.data.get('name', 'MCP Session')
        enabled_tools = request.data.get('enabled_tools', [])
        context_data = request.data.get('context', {})
        
        try:
            session = MCPSession.objects.create(
                name=session_name,
                enabled_tools=enabled_tools,
                context_data=context_data,
                created_by=request.user if request.user.is_authenticated else None
            )
            
            return Response({
                'session_id': str(session.id),
                'name': session.name,
                'enabled_tools': session.enabled_tools,
                'created_at': session.created_at.isoformat()
            })
            
        except Exception as e:  # noqa: BLE001
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def get_session_context(self, request, pk=None):
        """Get session context and execution history."""
        try:
            session = MCPSession.objects.get(id=pk)
            
            # Get recent executions
            executions = MCPToolExecution.objects.filter(
                session_id=str(session.id)
            ).order_by('-created_at')[:20]
            
            return Response({
                'session': {
                    'id': str(session.id),
                    'name': session.name,
                    'enabled_tools': session.enabled_tools,
                    'context_data': session.context_data,
                    'created_at': session.created_at.isoformat()
                },
                'executions': [
                    {
                        'id': str(exec.id),
                        'tool_name': exec.tool.name,
                        'success': exec.success,
                        'execution_time': exec.execution_time,
                        'created_at': exec.created_at.isoformat()
                    }
                    for exec in executions
                ]
            })
            
        except MCPSession.DoesNotExist:
            return Response(
                {'error': 'Session not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:  # noqa: BLE001
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MCPAgentIntegrationViewSet(viewsets.ViewSet):
    """Integration between MCP tools and agents."""
    
    permission_classes = [AllowAny] if settings.DEBUG else [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def agent_tool_selection(self, request):
        """Smart tool selection for agents based on task type."""
        agent_id = request.data.get('agent_id')
        task_description = request.data.get('task_description', '')
        task_type = request.data.get('task_type', '')
        
        if not agent_id:
            return Response(
                {'error': 'agent_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            mcp_service = MCPService()
            
            # Get recommended tools for the task
            recommended_tools = mcp_service.recommend_tools_for_task(
                task_description=task_description,
                task_type=task_type,
                agent_capabilities=[]  # Could be enhanced with agent capabilities
            )
            
            return Response({
                'agent_id': agent_id,
                'recommended_tools': recommended_tools,
                'task_type': task_type
            })
            
        except Exception as e:  # noqa: BLE001
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def execute_with_agent_context(self, request):
        """Execute MCP tools with agent context and memory."""
        agent_id = request.data.get('agent_id')
        tool_name = request.data.get('tool_name')
        parameters = request.data.get('parameters', {})
        use_agent_memory = request.data.get('use_agent_memory', True)
        
        try:
            mcp_service = MCPService()
            
            # Get agent context if requested
            agent_context = {}
            if use_agent_memory and agent_id:
                # This would integrate with agent memory system
                agent_context = {
                    'agent_id': agent_id,
                    'previous_executions': [],
                    'agent_memory': {}
                }
            
            # Execute tool with context
            result = mcp_service.execute_tool_with_context(
                tool_name=tool_name,
                parameters=parameters,
                context=agent_context
            )
            
            return Response({
                'result': result,
                'agent_id': agent_id,
                'context_used': bool(agent_context)
            })
            
        except Exception as e:  # noqa: BLE001
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
