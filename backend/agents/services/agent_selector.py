# agents/services/agent_selector.py

import logging

from django.db.models import Q

from ..models import Agent, AgentStatus, AgentType
from .performance_tracker import PerformanceTracker

logger = logging.getLogger(__name__)

class SmartAgentSelector:
    """
    Intelligent agent selection system that automatically chooses
    the best agent for a given task based on capabilities, performance,
    availability, and task requirements.
    """
    
    def __init__(self):
        self.performance_tracker = PerformanceTracker()
        
    def select_best_agent(
        self, 
        task_type: str, 
        task_description: str, 
        requirements: dict | None = None,
        exclude_agents: list[str] | None = None
    ) -> Agent | None:
        """
        Select the best available agent for a given task.
        
        Args:
            task_type: Type of task ('text', 'vision', 'reasoning', 'action', etc.)
            task_description: Detailed description of the task
            requirements: Specific requirements (e.g., {'min_accuracy': 0.9})
            exclude_agents: List of agent IDs to exclude from selection
            
        Returns:
            Best matching agent or None if no suitable agent found
        """
        requirements = requirements or {}
        exclude_agents = exclude_agents or []
        
        # Get available agents
        available_agents = self._get_available_agents(task_type, exclude_agents)
        
        if not available_agents:
            logger.warning(f"No available agents found for task type: {task_type}")
            return None
            
        # Score agents based on multiple criteria
        scored_agents = []
        for agent in available_agents:
            score = self._calculate_agent_score(
                agent, task_type, task_description, requirements
            )
            scored_agents.append((agent, score))
            
        # Sort by score (highest first) and return best agent
        scored_agents.sort(key=lambda x: x[1], reverse=True)
        best_agent = scored_agents[0][0]
        
        logger.info(f"Selected agent {best_agent.name} for task type {task_type} (score: {scored_agents[0][1]:.3f})")
        return best_agent
    
    def _get_available_agents(self, task_type: str, exclude_agents: list[str]) -> list[Agent]:
        """Get all available agents that can handle the task type."""
        
        # Map task types to agent types
        task_to_agent_mapping = {
            'text': [AgentType.REASONING, AgentType.ORCHESTRATOR],
            'vision': [AgentType.VISION],
            'image': [AgentType.VISION],
            'reasoning': [AgentType.REASONING],
            'logic': [AgentType.REASONING],
            'action': [AgentType.ACTION],
            'execution': [AgentType.ACTION],
            'memory': [AgentType.MEMORY],
            'storage': [AgentType.MEMORY],
            'orchestration': [AgentType.ORCHESTRATOR],
            'coordination': [AgentType.ORCHESTRATOR],
        }
        
        suitable_agent_types = task_to_agent_mapping.get(task_type.lower(), [])
        
        # Build query
        query = Q(
            type__in=suitable_agent_types,
            status__in=[AgentStatus.IDLE, AgentStatus.ACTIVE],
            is_active=True
        )
        
        if exclude_agents:
            query &= ~Q(id__in=exclude_agents)
            
        return Agent.objects.filter(query)
    
    def _calculate_agent_score(
        self, 
        agent: Agent, 
        task_type: str, 
        task_description: str, 
        requirements: dict
    ) -> float:
        """Calculate a comprehensive score for agent suitability."""
        
        score = 0.0
        
        # 1. Capability match score (40% weight)
        capability_score = self._score_capabilities(agent, task_type, task_description)
        score += capability_score * 0.4
        
        # 2. Performance history score (30% weight)  
        performance_score = self._score_performance(agent, task_type)
        score += performance_score * 0.3
        
        # 3. Availability score (20% weight)
        availability_score = self._score_availability(agent)
        score += availability_score * 0.2
        
        # 4. Requirements match score (10% weight)
        requirements_score = self._score_requirements(agent, requirements)
        score += requirements_score * 0.1
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _score_capabilities(self, agent: Agent, task_type: str, task_description: str) -> float:
        """Score agent based on capabilities match."""
        capabilities = agent.capabilities or []
        
        if not capabilities:
            return 0.0
            
        # Check for exact capability matches
        exact_matches = sum(1 for cap in capabilities if task_type.lower() in cap.lower())
        
        # Check for keyword matches in task description
        keyword_matches = 0
        for cap in capabilities:
            if any(word in task_description.lower() for word in cap.lower().split()):
                keyword_matches += 1
                
        # Calculate capability score
        total_capabilities = len(capabilities)
        exact_score = exact_matches / max(total_capabilities, 1)
        keyword_score = keyword_matches / max(total_capabilities, 1)
        
        return min((exact_score * 0.7 + keyword_score * 0.3), 1.0)
    
    def _score_performance(self, agent: Agent, task_type: str) -> float:
        """Score agent based on historical performance."""
        try:
            performance_data = self.performance_tracker.get_agent_performance(
                agent.id, task_type=task_type, days=30
            )
            
            if not performance_data:
                return 0.5  # Default score for new agents
                
            # Weighted performance score
            success_rate = performance_data.get('success_rate', 0.5)
            avg_response_time = performance_data.get('avg_response_time', 5.0)
            accuracy = performance_data.get('accuracy', 0.5)
            
            # Normalize response time (assume 10s is max acceptable)
            response_time_score = max(0, 1 - (avg_response_time / 10.0))
            
            performance_score = (
                success_rate * 0.4 + 
                response_time_score * 0.3 + 
                accuracy * 0.3
            )
            
            return min(performance_score, 1.0)
            
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Error scoring performance for agent {agent.id}: {e}")
            return 0.5
    
    def _score_availability(self, agent: Agent) -> float:
        """Score agent based on current availability."""
        status_scores = {
            AgentStatus.IDLE: 1.0,
            AgentStatus.ACTIVE: 0.7,
            AgentStatus.PROCESSING: 0.3,
            AgentStatus.ERROR: 0.0,
            AgentStatus.OFFLINE: 0.0,
        }
        
        return status_scores.get(agent.status, 0.0)
    
    def _score_requirements(self, agent: Agent, requirements: dict) -> float:
        """Score agent based on specific requirements."""
        if not requirements:
            return 1.0
            
        score = 1.0
        config = agent.configuration or {}
        
        # Check minimum accuracy requirement
        if 'min_accuracy' in requirements:
            agent_accuracy = config.get('accuracy', 0.5)
            if agent_accuracy < requirements['min_accuracy']:
                score *= 0.5
                
        # Check maximum response time requirement
        if 'max_response_time' in requirements:
            agent_response_time = config.get('avg_response_time', 5.0)
            if agent_response_time > requirements['max_response_time']:
                score *= 0.5
                
        # Check specific feature requirements
        if 'required_features' in requirements:
            agent_features = config.get('features', [])
            required_features = requirements['required_features']
            
            missing_features = set(required_features) - set(agent_features)
            if missing_features:
                score *= (1 - len(missing_features) / len(required_features))
                
        return max(score, 0.0)
    
    def get_agent_recommendations(
        self, 
        task_type: str, 
        task_description: str, 
        count: int = 3
    ) -> list[tuple[Agent, float]]:
        """Get top N agent recommendations with scores."""
        
        available_agents = self._get_available_agents(task_type, [])
        scored_agents = []
        
        for agent in available_agents:
            score = self._calculate_agent_score(
                agent, task_type, task_description, {}
            )
            scored_agents.append((agent, score))
            
        scored_agents.sort(key=lambda x: x[1], reverse=True)
        return scored_agents[:count]
    
    def explain_selection(
        self, 
        agent: Agent, 
        task_type: str, 
        task_description: str, 
        requirements: dict | None = None
    ) -> dict:
        """Provide detailed explanation of why this agent was selected."""
        
        requirements = requirements or {}
        
        explanation = {
            'agent_id': str(agent.id),
            'agent_name': agent.name,
            'agent_type': agent.type,
            'total_score': self._calculate_agent_score(agent, task_type, task_description, requirements),
            'scoring_breakdown': {
                'capabilities': self._score_capabilities(agent, task_type, task_description),
                'performance': self._score_performance(agent, task_type),
                'availability': self._score_availability(agent),
                'requirements': self._score_requirements(agent, requirements),
            },
            'reasoning': [],
        }
        
        # Add reasoning explanations
        if explanation['scoring_breakdown']['capabilities'] > 0.8:
            explanation['reasoning'].append("Agent has excellent capability match for this task type")
            
        if explanation['scoring_breakdown']['performance'] > 0.8:
            explanation['reasoning'].append("Agent has strong historical performance")
            
        if explanation['scoring_breakdown']['availability'] == 1.0:
            explanation['reasoning'].append("Agent is currently idle and immediately available")
            
        if explanation['scoring_breakdown']['requirements'] == 1.0:
            explanation['reasoning'].append("Agent meets all specified requirements")
            
        return explanation