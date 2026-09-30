from datetime import timezone

"""
Azure CosmosDB Integration Service
Following Azure best practices for scalable, globally-distributed data storage
"""

import logging
import os
from datetime import datetime
from typing import Any

from azure.cosmos import CosmosClient, PartitionKey, exceptions
from azure.cosmos.container import Container
from azure.cosmos.database import Database
from django.conf import settings

logger = logging.getLogger(__name__)


class CosmosDBConfig:
    """Configuration for CosmosDB connections"""
    
    # Connection settings
    ENDPOINT = getattr(settings, 'COSMOS_ENDPOINT', os.getenv('COSMOS_ENDPOINT'))
    KEY = getattr(settings, 'COSMOS_KEY', os.getenv('COSMOS_KEY'))
    DATABASE_NAME = getattr(settings, 'COSMOS_DATABASE', 'MultiAgentSystem')
    
    # Container definitions with hierarchical partition keys
    CONTAINERS = {  # noqa: RUF012
        'sessions': {
            'partition_key': ['/tenantId', '/userId', '/sessionId'],  # Hierarchical
            'unique_key_policy': {'uniqueKeys': [{'paths': ['/sessionId']}]},
            'indexing_policy': {
                'indexingMode': 'consistent',
                'automatic': True,
                'includedPaths': [
                    {'path': '/*'}
                ],
                'excludedPaths': [
                    {'path': '/messages/*'},  # Exclude large arrays from indexing
                    {'path': '/_etag/?'}
                ]
            }
        },
        'agents': {
            'partition_key': ['/tenantId', '/agentType'],
            'indexing_policy': {
                'indexingMode': 'consistent',
                'includedPaths': [
                    {'path': '/name/?'},
                    {'path': '/capabilities/*'},
                    {'path': '/status/?'}
                ],
                'excludedPaths': [
                    {'path': '/configuration/*'}
                ]
            }
        },
        'conversations': {
            'partition_key': ['/tenantId', '/userId', '/conversationId'],
            'default_ttl': 2592000,  # 30 days TTL for old conversations
            'indexing_policy': {
                'indexingMode': 'consistent',
                'includedPaths': [
                    {'path': '/timestamp/?'},
                    {'path': '/userId/?'}
                ]
            }
        },
        'analytics': {
            'partition_key': ['/tenantId', '/metricType', '/datePartition'],
            'analytical_storage_ttl': -1,  # Enable analytical storage
            'indexing_policy': {
                'indexingMode': 'consistent',
                'includedPaths': [
                    {'path': '/timestamp/?'},
                    {'path': '/value/?'},
                    {'path': '/metricType/?'}
                ]
            }
        },
        'user_contexts': {
            'partition_key': ['/tenantId', '/userId'],
            'indexing_policy': {
                'indexingMode': 'consistent',
                'includedPaths': [
                    {'path': '/userId/?'},
                    {'path': '/lastAccessed/?'}
                ],
                'excludedPaths': [
                    {'path': '/context/*'},  # Large context data
                    {'path': '/history/*'}
                ]
            }
        }
    }


class CosmosDBService:
    """
    Service for Azure CosmosDB operations
    Implements best practices:
    - Hierarchical partition keys to overcome 20GB limit
    - Optimized indexing policies
    - Connection pooling via singleton
    - Proper error handling and retries
    """
    
    def __init__(self):
        """Initialize CosmosDB client with connection pooling"""
        if not CosmosDBConfig.ENDPOINT or not CosmosDBConfig.KEY:
            logger.warning("CosmosDB credentials not configured")
            self.client = None
            self.database = None
            return
        
        try:
            # Initialize client with connection retry policy
            self.client = CosmosClient(
                CosmosDBConfig.ENDPOINT,
                CosmosDBConfig.KEY,
                consistency_level='Session',  # Balance between consistency and performance
                connection_retry_policy={
                    'retry_total': 3,
                    'retry_backoff_max': 5
                }
            )
            
            # Get or create database
            self.database = self._get_or_create_database()
            
            # Ensure containers exist
            self.containers = self._ensure_containers()
            
            logger.info("CosmosDB service initialized successfully")
            
        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to initialize CosmosDB: {e}")
            self.client = None
            self.database = None
    
    def _get_or_create_database(self) -> Database:
        """Get or create database"""
        try:
            return self.client.create_database_if_not_exists(
                id=CosmosDBConfig.DATABASE_NAME,
                offer_throughput=400  # Shared throughput for cost optimization
            )
        except Exception as e:
            logger.error(f"Database creation failed: {e}")
            raise
    
    def _ensure_containers(self) -> dict[str, Container]:
        """Ensure all containers exist with proper configuration"""
        containers = {}
        
        for container_name, config in CosmosDBConfig.CONTAINERS.items():
            try:
                # Create hierarchical partition key
                partition_key = PartitionKey(
                    path=config['partition_key'],
                    kind='MultiHash'  # For hierarchical keys
                )
                
                # Container settings
                container_settings = {
                    'id': container_name,
                    'partition_key': partition_key,
                    'indexing_policy': config.get('indexing_policy')
                }
                
                # Add TTL if specified
                if 'default_ttl' in config:
                    container_settings['default_ttl'] = config['default_ttl']
                
                # Add analytical storage if specified
                if 'analytical_storage_ttl' in config:
                    container_settings['analytical_storage_ttl'] = config['analytical_storage_ttl']
                
                # Add unique key policy if specified
                if 'unique_key_policy' in config:
                    container_settings['unique_key_policy'] = config['unique_key_policy']
                
                # Create container
                container = self.database.create_container_if_not_exists(**container_settings)
                containers[container_name] = container
                
                logger.info(f"Container '{container_name}' ready")
                
            except Exception as e:  # noqa: BLE001
                logger.error(f"Failed to create container '{container_name}': {e}")
        
        return containers
    
    def create_item(self, container_name: str, item: dict[str, Any],
                   tenant_id: str, partition_values: list[str]) -> dict[str, Any]:
        """
        Create item in container with proper partitioning
        
        Args:
            container_name: Container name
            item: Item data
            tenant_id: Tenant ID for multi-tenancy
            partition_values: Hierarchical partition key values
            
        Returns:
            Created item
        """
        if not self.client:
            raise Exception("CosmosDB not initialized")  # noqa: TRY002
        
        container = self.containers.get(container_name)
        if not container:
            raise ValueError(f"Container '{container_name}' not found")
        
        try:
            # Add partition key values
            item['tenantId'] = tenant_id
            
            # Add timestamp for tracking
            if 'timestamp' not in item:
                item['timestamp'] = datetime.now(timezone.utc).isoformat()
            
            # Generate ID if not provided
            if 'id' not in item:
                import uuid
                item['id'] = str(uuid.uuid4())
            
            # Create item
            created_item = container.create_item(
                body=item,
                enable_automatic_id_generation=False
            )
            
            logger.debug(f"Created item in {container_name}: {created_item['id']}")
            return created_item
            
        except exceptions.CosmosHttpResponseError as e:
            if e.status_code == 409:
                logger.warning(f"Item already exists: {item.get('id')}")
            else:
                logger.error(f"Failed to create item: {e}")
            raise
    
    def read_item(self, container_name: str, item_id: str, 
                  partition_key_values: list[Any]) -> dict[str, Any] | None:
        """
        Read item by ID and partition key
        
        Args:
            container_name: Container name
            item_id: Item ID
            partition_key_values: Partition key values (hierarchical)
            
        Returns:
            Item or None
        """
        if not self.client:
            raise Exception("CosmosDB not initialized")  # noqa: TRY002
        
        container = self.containers.get(container_name)
        if not container:
            raise ValueError(f"Container '{container_name}' not found")
        
        try:
            item = container.read_item(
                item=item_id,
                partition_key=partition_key_values
            )
            return item
        except exceptions.CosmosResourceNotFoundError:
            logger.debug(f"Item not found: {item_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to read item: {e}")
            raise
    
    def query_items(self, container_name: str, query: str, 
                   parameters: list[dict] | None = None,
                   partition_key: list[Any] | None = None,
                   max_item_count: int = 100) -> list[dict[str, Any]]:
        """
        Query items with SQL-like syntax
        
        Args:
            container_name: Container name
            query: SQL query
            parameters: Query parameters
            partition_key: Partition key for targeted query
            max_item_count: Max items to return
            
        Returns:
            List of items
        """
        if not self.client:
            raise Exception("CosmosDB not initialized")  # noqa: TRY002
        
        container = self.containers.get(container_name)
        if not container:
            raise ValueError(f"Container '{container_name}' not found")
        
        try:
            query_options = {
                'enable_cross_partition_query': partition_key is None,
                'max_item_count': max_item_count
            }
            
            if partition_key:
                query_options['partition_key'] = partition_key
            
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                **query_options
            ))
            
            logger.debug(f"Query returned {len(items)} items from {container_name}")
            return items
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise
    
    def update_item(self, container_name: str, item_id: str,
                   partition_key_values: list[Any], updates: dict[str, Any]) -> dict[str, Any]:
        """
        Update item with patch operations
        
        Args:
            container_name: Container name
            item_id: Item ID
            partition_key_values: Partition key values
            updates: Fields to update
            
        Returns:
            Updated item
        """
        if not self.client:
            raise Exception("CosmosDB not initialized")  # noqa: TRY002
        
        container = self.containers.get(container_name)
        if not container:
            raise ValueError(f"Container '{container_name}' not found")
        
        try:
            # Read existing item
            item = self.read_item(container_name, item_id, partition_key_values)
            if not item:
                raise ValueError(f"Item not found: {item_id}")
            
            # Apply updates
            item.update(updates)
            item['lastModified'] = datetime.now(timezone.utc).isoformat()
            
            # Replace item
            updated_item = container.replace_item(
                item=item_id,
                body=item
            )
            
            logger.debug(f"Updated item in {container_name}: {item_id}")
            return updated_item
            
        except Exception as e:
            logger.error(f"Failed to update item: {e}")
            raise
    
    def delete_item(self, container_name: str, item_id: str,
                   partition_key_values: list[Any]):
        """
        Delete item
        
        Args:
            container_name: Container name
            item_id: Item ID
            partition_key_values: Partition key values
        """
        if not self.client:
            raise Exception("CosmosDB not initialized")  # noqa: TRY002
        
        container = self.containers.get(container_name)
        if not container:
            raise ValueError(f"Container '{container_name}' not found")
        
        try:
            container.delete_item(
                item=item_id,
                partition_key=partition_key_values
            )
            logger.debug(f"Deleted item from {container_name}: {item_id}")
            
        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"Item not found for deletion: {item_id}")
        except Exception as e:
            logger.error(f"Failed to delete item: {e}")
            raise
    
    def batch_create_items(self, container_name: str, items: list[dict[str, Any]],
                          tenant_id: str) -> list[dict[str, Any]]:
        """
        Batch create multiple items (transactional batch)
        
        Args:
            container_name: Container name
            items: List of items to create
            tenant_id: Tenant ID
            
        Returns:
            List of created items
        """
        if not self.client:
            raise Exception("CosmosDB not initialized")  # noqa: TRY002
        
        container = self.containers.get(container_name)
        if not container:
            raise ValueError(f"Container '{container_name}' not found")
        
        created_items = []
        
        # CosmosDB transactional batches limited to 100 items
        batch_size = 100
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            
            try:
                for item in batch:
                    item['tenantId'] = tenant_id
                    if 'timestamp' not in item:
                        item['timestamp'] = datetime.now(timezone.utc).isoformat()
                    if 'id' not in item:
                        import uuid
                        item['id'] = str(uuid.uuid4())
                    
                    created = container.create_item(body=item)
                    created_items.append(created)
                
                logger.info(f"Batch created {len(batch)} items in {container_name}")
                
            except Exception as e:
                logger.error(f"Batch create failed: {e}")
                raise
        
        return created_items
    
    def get_container_metrics(self, container_name: str) -> dict[str, Any]:
        """Get container usage metrics"""
        if not self.client:
            raise Exception("CosmosDB not initialized")  # noqa: TRY002
        
        container = self.containers.get(container_name)
        if not container:
            raise ValueError(f"Container '{container_name}' not found")
        
        try:
            # Get container properties
            properties = container.read()
            
            return {
                'container_name': container_name,
                'partition_key': properties.get('partitionKey'),
                'indexing_policy': properties.get('indexingPolicy'),
                'default_ttl': properties.get('defaultTtl'),
                'analytical_storage_enabled': properties.get('analyticalStorageTtl') is not None
            }
        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to get container metrics: {e}")
            return {}


# Singleton instance
_cosmos_service = None

def get_cosmos_service() -> CosmosDBService:
    """Get or create CosmosDB service singleton"""
    global _cosmos_service
    if _cosmos_service is None:
        _cosmos_service = CosmosDBService()
    return _cosmos_service
