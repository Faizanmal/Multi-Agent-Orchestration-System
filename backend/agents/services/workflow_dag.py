"""
Advanced Workflow Orchestration with DAG Support
Directed Acyclic Graph based workflow execution with:
- Conditional branching
- Parallel execution
- Error handling and retry logic
- Workflow templates
- State management
"""
import asyncio
import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class NodeStatus(Enum):
    """Workflow node execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


class NodeType(Enum):
    """Types of workflow nodes"""
    TASK = "task"
    CONDITION = "condition"
    PARALLEL = "parallel"
    AGENT = "agent"
    API_CALL = "api_call"
    TRANSFORM = "transform"
    HUMAN_INPUT = "human_input"


@dataclass
class WorkflowNode:
    """
    Represents a node in the workflow DAG
    """
    id: str
    name: str
    type: NodeType
    action: Callable | None = None
    condition: Callable | None = None
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    status: NodeStatus = NodeStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    timeout: int = 300  # seconds
    metadata: dict[str, Any] = field(default_factory=dict)
    start_time: datetime | None = None
    end_time: datetime | None = None
    error: str | None = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
    
    def can_execute(self, completed_nodes: set) -> bool:
        """Check if node can be executed based on dependencies"""
        return all(dep in completed_nodes for dep in self.dependencies)
    
    def is_terminal(self) -> bool:
        """Check if node is in terminal state"""
        return self.status in [NodeStatus.SUCCESS, NodeStatus.FAILED, NodeStatus.SKIPPED]
    
    def to_dict(self) -> dict:
        """Convert node to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type.value,
            'status': self.status.value,
            'inputs': self.inputs,
            'outputs': self.outputs,
            'dependencies': self.dependencies,
            'retry_count': self.retry_count,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'error': self.error,
            'metadata': self.metadata,
        }


class WorkflowDAG:
    """
    Directed Acyclic Graph for workflow representation
    """
    
    def __init__(self, workflow_id: str, name: str):
        self.workflow_id = workflow_id
        self.name = name
        self.nodes: dict[str, WorkflowNode] = {}
        self.edges: dict[str, list[str]] = {}  # node_id -> [dependent_node_ids]
        self.created_at = datetime.now(timezone.utc)
        self.context: dict[str, Any] = {}
    
    def add_node(self, node: WorkflowNode) -> str:
        """Add node to DAG"""
        if node.id in self.nodes:
            raise ValueError(f"Node {node.id} already exists")
        
        self.nodes[node.id] = node
        self.edges[node.id] = []
        
        logger.info(f"Added node {node.id} ({node.name}) to workflow {self.workflow_id}")
        return node.id
    
    def add_edge(self, from_node_id: str, to_node_id: str):
        """Add edge between nodes (dependency)"""
        if from_node_id not in self.nodes:
            raise ValueError(f"Node {from_node_id} not found")
        if to_node_id not in self.nodes:
            raise ValueError(f"Node {to_node_id} not found")
        
        # Check for cycles
        if self._creates_cycle(from_node_id, to_node_id):
            raise ValueError("Adding this edge would create a cycle")
        
        self.edges[from_node_id].append(to_node_id)
        self.nodes[to_node_id].dependencies.append(from_node_id)
        
        logger.info(f"Added edge: {from_node_id} -> {to_node_id}")
    
    def _creates_cycle(self, from_node: str, to_node: str) -> bool:
        """Check if adding edge would create cycle"""
        visited = set()
        
        def dfs(node_id: str) -> bool:
            if node_id == from_node:
                return True
            if node_id in visited:
                return False
            
            visited.add(node_id)
            for next_node in self.edges.get(node_id, []):
                if dfs(next_node):
                    return True
            return False
        
        return dfs(to_node)
    
    def get_executable_nodes(self, completed_nodes: set) -> list[WorkflowNode]:
        """Get nodes that can be executed based on completed dependencies"""
        executable = []
        
        for node in self.nodes.values():
            if node.status == NodeStatus.PENDING and node.can_execute(completed_nodes):
                executable.append(node)
        
        return executable
    
    def get_start_nodes(self) -> list[WorkflowNode]:
        """Get nodes with no dependencies (entry points)"""
        return [node for node in self.nodes.values() if not node.dependencies]
    
    def to_dict(self) -> dict:
        """Convert DAG to dictionary"""
        return {
            'workflow_id': self.workflow_id,
            'name': self.name,
            'created_at': self.created_at.isoformat(),
            'nodes': {node_id: node.to_dict() for node_id, node in self.nodes.items()},
            'edges': self.edges,
            'context': self.context,
        }


class WorkflowEngine:
    """
    Workflow execution engine with DAG support
    """
    
    def __init__(self):
        self.active_workflows: dict[str, WorkflowDAG] = {}
        self.execution_history: dict[str, list[dict]] = {}
    
    async def execute_workflow(self, dag: WorkflowDAG) -> dict:
        """
        Execute workflow DAG
        
        Returns:
            Workflow execution result
        """
        self.active_workflows[dag.workflow_id] = dag
        
        logger.info(f"Starting workflow execution: {dag.workflow_id} ({dag.name})")
        
        completed_nodes = set()
        failed_nodes = set()
        
        try:
            # Get initial executable nodes
            executable_nodes = dag.get_start_nodes()
            
            while executable_nodes:
                # Execute nodes in parallel
                tasks = [
                    self._execute_node(dag, node)
                    for node in executable_nodes
                ]
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for node, result in zip(executable_nodes, results):
                    if isinstance(result, Exception):
                        logger.error(f"Node {node.id} failed: {result!s}")
                        failed_nodes.add(node.id)
                        node.status = NodeStatus.FAILED
                        node.error = str(result)
                    elif result:
                        completed_nodes.add(node.id)
                        node.status = NodeStatus.SUCCESS
                    else:
                        node.status = NodeStatus.SKIPPED
                
                # Get next executable nodes
                executable_nodes = dag.get_executable_nodes(completed_nodes)
                
                # Remove nodes that depend on failed nodes
                if failed_nodes:
                    executable_nodes = [
                        node for node in executable_nodes
                        if not any(dep in failed_nodes for dep in node.dependencies)
                    ]
            
            # Determine overall status
            all_nodes = set(dag.nodes.keys())
            if completed_nodes == all_nodes:
                status = "completed"
            elif failed_nodes:
                status = "failed"
            else:
                status = "partial"
            
            result = {
                'workflow_id': dag.workflow_id,
                'status': status,
                'completed_nodes': len(completed_nodes),
                'failed_nodes': len(failed_nodes),
                'total_nodes': len(all_nodes),
                'context': dag.context,
                'execution_summary': self._generate_summary(dag),
            }
            
            # Store in history
            self._store_execution_history(dag.workflow_id, result)
            
            logger.info(f"Workflow {dag.workflow_id} completed: {status}")
            
            return result
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e!s}")
            raise
        finally:
            # Cleanup
            if dag.workflow_id in self.active_workflows:
                del self.active_workflows[dag.workflow_id]
    
    async def _execute_node(self, dag: WorkflowDAG, node: WorkflowNode) -> bool:
        """
        Execute a single workflow node
        
        Returns:
            True if successful, False if skipped
        """
        node.status = NodeStatus.RUNNING
        node.start_time = datetime.now(timezone.utc)
        
        logger.info(f"Executing node {node.id} ({node.name})")
        
        try:
            # Handle different node types
            if node.type == NodeType.CONDITION:
                result = await self._execute_condition_node(dag, node)
            elif node.type == NodeType.PARALLEL:
                result = await self._execute_parallel_node(dag, node)
            elif node.type == NodeType.TASK:
                result = await self._execute_task_node(dag, node)
            elif node.type == NodeType.AGENT:
                result = await self._execute_agent_node(dag, node)
            else:
                result = await self._execute_generic_node(dag, node)
            
            node.end_time = datetime.now(timezone.utc)
            
            # Update context with outputs
            if node.outputs:
                dag.context.update(node.outputs)
            
            return result
            
        except Exception as e:
            logger.error(f"Node {node.id} execution failed: {e!s}")
            node.error = str(e)
            node.end_time = datetime.now(timezone.utc)
            
            # Retry logic
            if node.retry_count < node.max_retries:
                node.retry_count += 1
                node.status = NodeStatus.RETRYING
                logger.info(f"Retrying node {node.id} (attempt {node.retry_count})")
                await asyncio.sleep(2 ** node.retry_count)  # Exponential backoff
                return await self._execute_node(dag, node)
            else:
                raise
    
    async def _execute_task_node(self, dag: WorkflowDAG, node: WorkflowNode) -> bool:
        """Execute task node"""
        if node.action:
            # Prepare inputs with context
            inputs = {**dag.context, **node.inputs}
            
            # Execute action
            if asyncio.iscoroutinefunction(node.action):
                result = await node.action(inputs)
            else:
                result = node.action(inputs)
            
            # Store outputs
            node.outputs = result if isinstance(result, dict) else {'result': result}
            return True
        
        return False
    
    async def _execute_condition_node(self, dag: WorkflowDAG, node: WorkflowNode) -> bool:
        """Execute conditional node"""
        if node.condition:
            inputs = {**dag.context, **node.inputs}
            
            if asyncio.iscoroutinefunction(node.condition):
                result = await node.condition(inputs)
            else:
                result = node.condition(inputs)
            
            node.outputs = {'condition_result': result}
            return bool(result)
        
        return True
    
    async def _execute_parallel_node(self, dag: WorkflowDAG, node: WorkflowNode) -> bool:
        """Execute parallel node — fan-out to sub-tasks defined in node.inputs['subtasks']."""
        subtasks = node.inputs.get('subtasks', [])
        if not subtasks:
            # Nothing to fan out; treat as a no-op success
            return True

        async def _run_subtask(subtask_config: dict) -> Any:
            action = subtask_config.get('action')
            if action is None:
                return None
            inputs = {**dag.context, **subtask_config.get('inputs', {})}
            if asyncio.iscoroutinefunction(action):
                return await action(inputs)
            return action(inputs)

        results = await asyncio.gather(
            *[_run_subtask(st) for st in subtasks],
            return_exceptions=True,
        )

        outputs: dict[str, Any] = {}
        all_ok = True
        for i, result in enumerate(results):
            key = subtasks[i].get('output_key', f'subtask_{i}')
            if isinstance(result, Exception):
                logger.error(f"Parallel subtask {i} of node {node.id} failed: {result}")
                outputs[key] = {'error': str(result)}
                all_ok = False
            else:
                outputs[key] = result

        node.outputs = outputs
        dag.context.update(outputs)
        return all_ok

    async def _execute_agent_node(self, dag: WorkflowDAG, node: WorkflowNode) -> bool:
        """Execute agent node — invokes a Groq-backed agent and stores its response."""
        from django.conf import settings as django_settings
        from groq import Groq

        agent_type = node.metadata.get('agent_type', 'orchestrator')
        task_content = node.inputs.get('content') or str(dag.context)[:2000]

        _agent_prompts: dict[str, str] = {
            'orchestrator': (
                'You are an Orchestrator Agent. Analyse the request, decompose it into subtasks, '
                'and synthesise a coherent answer. Think step-by-step.'
            ),
            'reasoning': (
                'You are a Reasoning Agent. Apply rigorous logical analysis, break problems into '
                'clear steps, and justify every conclusion.'
            ),
            'vision': (
                'You are a Vision Agent. Analyse visual content, extract text, detect objects, '
                'and reason about visual patterns.'
            ),
            'action': (
                'You are an Action Agent. Execute concrete tasks and report results precisely.'
            ),
            'memory': (
                'You are a Memory Agent. Retrieve and organise contextual information, '
                'summarise what you know, and flag knowledge gaps.'
            ),
        }
        system_prompt = _agent_prompts.get(
            agent_type, 'You are a specialised AI assistant. Be helpful and precise.'
        )

        client = Groq(api_key=django_settings.GROQ_API_KEY)
        model = django_settings.GROQ_CONFIG.get('MODEL', 'llama-3.3-70b-versatile')
        response = client.chat.completions.create(
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': task_content},
            ],
            model=model,
            temperature=0.7,
            max_tokens=1024,
        )

        output = response.choices[0].message.content
        node.outputs = {'agent_type': agent_type, 'response': output}
        output_key = node.metadata.get('output_key', f'{agent_type}_response')
        dag.context[output_key] = output
        logger.info(f"Agent node {node.id} ({agent_type}) completed successfully")
        return True
    
    async def _execute_generic_node(self, dag: WorkflowDAG, node: WorkflowNode) -> bool:
        """Execute generic node"""
        if node.action:
            return await self._execute_task_node(dag, node)
        return True
    
    def _generate_summary(self, dag: WorkflowDAG) -> dict:
        """Generate execution summary"""
        summary = {
            'total_nodes': len(dag.nodes),
            'node_statuses': {},
            'total_duration': 0,
        }
        
        for status in NodeStatus:
            count = sum(1 for node in dag.nodes.values() if node.status == status)
            summary['node_statuses'][status.value] = count
        
        # Calculate total duration
        durations = []
        for node in dag.nodes.values():
            if node.start_time and node.end_time:
                duration = (node.end_time - node.start_time).total_seconds()
                durations.append(duration)
        
        if durations:
            summary['total_duration'] = sum(durations)
            summary['avg_node_duration'] = sum(durations) / len(durations)
        
        return summary
    
    def _store_execution_history(self, workflow_id: str, result: dict):
        """Store workflow execution history"""
        if workflow_id not in self.execution_history:
            self.execution_history[workflow_id] = []
        
        result['executed_at'] = datetime.now(timezone.utc).isoformat()
        self.execution_history[workflow_id].append(result)
        
        # Keep only last 100 executions
        if len(self.execution_history[workflow_id]) > 100:
            self.execution_history[workflow_id] = self.execution_history[workflow_id][-100:]


# Global workflow engine instance
workflow_engine = WorkflowEngine()
