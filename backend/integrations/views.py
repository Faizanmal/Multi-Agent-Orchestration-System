from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Integration, IntegrationExecution, IntegrationType
from .serializers import IntegrationSerializer


class IntegrationViewSet(viewsets.ModelViewSet):
    """Manage integrations"""
    serializer_class = IntegrationSerializer
    permission_classes = [IsAuthenticated]  # noqa: RUF012
    
    def get_queryset(self):
        return Integration.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Test integration connection"""
        integration = self.get_object()
        
        try:
            # Test based on integration type
            if integration.integration_type == IntegrationType.AZURE_COSMOSDB:
                from Multi_model_Intelligence.services.azure_cosmos_service import (
                    AzureCosmosService,
                )
                service = AzureCosmosService()
                # Test connection
                result = service.test_connection()
            elif integration.integration_type == IntegrationType.AZURE_FUNCTIONS:
                from Multi_model_Intelligence.services.azure_functions_service import (
                    AzureFunctionsService,
                )
                service = AzureFunctionsService()
                result = service.test_connection()
            else:
                return Response({
                    'status': 'error',
                    'message': f'Test not implemented for {integration.integration_type}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'status': 'success',
                'message': 'Connection successful',
                'details': result
            })
        except Exception as e:  # noqa: BLE001
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class AzureCosmosDBViewSet(viewsets.ViewSet):
    """Azure CosmosDB operations"""
    permission_classes = [IsAuthenticated]  # noqa: RUF012
    
    def list(self, request):
        """List all containers"""
        try:
            from Multi_model_Intelligence.services.azure_cosmos_service import (
                AzureCosmosService,
            )
            service = AzureCosmosService()
            containers = service.list_containers()
            return Response(containers)
        except Exception as e:  # noqa: BLE001
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def query(self, request):
        """Execute CosmosDB query"""
        try:
            from Multi_model_Intelligence.services.azure_cosmos_service import (
                AzureCosmosService,
            )
            service = AzureCosmosService()
            
            container_name = request.data.get('container')
            query = request.data.get('query')
            
            if not container_name or not query:
                return Response({
                    'error': 'container and query are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            results = service.query_items(container_name, query)
            return Response({
                'results': results
            })
        except Exception as e:  # noqa: BLE001
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AzureFunctionsViewSet(viewsets.ViewSet):
    """Azure Functions operations"""
    permission_classes = [IsAuthenticated]  # noqa: RUF012
    
    @action(detail=False, methods=['post'])
    def trigger(self, request):
        """Trigger an Azure Function"""
        try:
            from Multi_model_Intelligence.services.azure_functions_service import (
                AzureFunctionsService,
            )
            service = AzureFunctionsService()
            
            function_name = request.data.get('function_name')
            payload = request.data.get('payload', {})
            
            if not function_name:
                return Response({
                    'error': 'function_name is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            result = service.trigger_function(function_name, payload)
            return Response({
                'status': 'success',
                'result': result
            })
        except Exception as e:  # noqa: BLE001
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def logs(self, request):
        """Get Azure Function logs"""
        try:
            from Multi_model_Intelligence.services.azure_functions_service import (
                AzureFunctionsService,
            )
            service = AzureFunctionsService()
            
            function_name = request.query_params.get('function_name')
            if not function_name:
                return Response({
                    'error': 'function_name is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            logs = service.get_logs(function_name)
            return Response({
                'logs': logs
            })
        except Exception as e:  # noqa: BLE001
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_cosmos_containers(request):
    """List Azure CosmosDB containers"""
    try:
        from Multi_model_Intelligence.services.azure_cosmos_service import (
            AzureCosmosService,
        )
        service = AzureCosmosService()
        containers = service.list_containers()
        return Response({
            'containers': containers
        })
    except Exception as e:  # noqa: BLE001
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def query_cosmos_db(request):
    """Query Azure CosmosDB"""
    try:
        from Multi_model_Intelligence.services.azure_cosmos_service import (
            AzureCosmosService,
        )
        service = AzureCosmosService()
        
        container = request.data.get('container')
        query = request.data.get('query')
        
        if not container or not query:
            return Response({
                'error': 'container and query are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        results = service.query_items(container, query)
        return Response({
            'results': results
        })
    except Exception as e:  # noqa: BLE001
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_azure_function(request):
    """Trigger an Azure Function"""
    try:
        from Multi_model_Intelligence.services.azure_functions_service import (
            AzureFunctionsService,
        )
        service = AzureFunctionsService()
        
        function_name = request.data.get('function_name')
        payload = request.data.get('payload', {})
        
        if not function_name:
            return Response({
                'error': 'function_name is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        result = service.trigger_function(function_name, payload)
        return Response({
            'status': 'success',
            'result': result
        })
    except Exception as e:  # noqa: BLE001
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_function_logs(request):
    """Get Azure Function logs"""
    try:
        from Multi_model_Intelligence.services.azure_functions_service import (
            AzureFunctionsService,
        )
        service = AzureFunctionsService()
        
        function_name = request.query_params.get('function_name')
        if not function_name:
            return Response({
                'error': 'function_name is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logs = service.get_logs(function_name)
        return Response({
            'logs': logs
        })
    except Exception as e:  # noqa: BLE001
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def zapier_webhook(request):
    """Handle Zapier webhook"""
    try:
        # Process Zapier webhook
        data = request.data
        
        # Create execution record
        integration = Integration.objects.filter(
            user=request.user,
            integration_type=IntegrationType.ZAPIER,
            is_active=True
        ).first()
        
        if not integration:
            return Response({
                'error': 'No active Zapier integration found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        execution = IntegrationExecution.objects.create(
            integration=integration,
            status='success',
            request_data=data,
            response_data={'message': 'Webhook received'}
        )
        
        return Response({
            'status': 'success',
            'execution_id': str(execution.id)
        })
    except Exception as e:  # noqa: BLE001
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def make_webhook(request):
    """Handle Make.com webhook"""
    try:
        # Process Make webhook
        data = request.data
        
        # Create execution record
        integration = Integration.objects.filter(
            user=request.user,
            integration_type=IntegrationType.MAKE,
            is_active=True
        ).first()
        
        if not integration:
            return Response({
                'error': 'No active Make integration found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        execution = IntegrationExecution.objects.create(
            integration=integration,
            status='success',
            request_data=data,
            response_data={'message': 'Webhook received'}
        )
        
        return Response({
            'status': 'success',
            'execution_id': str(execution.id)
        })
    except Exception as e:  # noqa: BLE001
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

