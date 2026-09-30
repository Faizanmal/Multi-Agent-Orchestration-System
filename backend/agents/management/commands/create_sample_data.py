"""
Django management command to create sample agents and sessions
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from agents.models import Agent, AgentStatus, Session

# Get the custom user model
User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample agents and sessions for development'

    def handle(self, *args, **options):
        # Create or get default user
        # Note: CustomUser uses email as USERNAME_FIELD
        default_user, created = User.objects.get_or_create(
            email='default@example.com',
            defaults={
                'username': 'default_user',
                'first_name': 'Default',
                'last_name': 'User'
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Created default user'))

        # Create sample agents
        agents_data = [
            {
                'name': 'Master Orchestrator',
                'type': 'orchestrator',
                'capabilities': ['task_coordination', 'agent_management', 'workflow_optimization', 'real_time_sync'],
                'description': 'Coordinates all agent activities and manages workflow optimization'
            },
            {
                'name': 'Vision Analyst',
                'type': 'vision',
                'capabilities': ['image_analysis', 'object_detection', 'ocr', 'visual_reasoning', 'video_processing'],
                'description': 'Specializes in visual content analysis and computer vision tasks'
            },
            {
                'name': 'Logic Engine',
                'type': 'reasoning',
                'capabilities': ['logical_analysis', 'problem_solving', 'decision_making', 'pattern_recognition', 'inference'],
                'description': 'Handles complex reasoning and logical analysis tasks'
            },
            {
                'name': 'Action Executor',
                'type': 'action',
                'capabilities': ['api_integration', 'task_execution', 'external_tools', 'automation', 'mcp_tools'],
                'description': 'Executes actions and integrates with external systems'
            },
            {
                'name': 'Memory Keeper',
                'type': 'memory',
                'capabilities': ['context_storage', 'knowledge_retrieval', 'learning', 'history_management', 'semantic_search'],
                'description': 'Manages context, memory, and knowledge retrieval'
            }
        ]

        created_agents = []
        for agent_data in agents_data:
            agent, created = Agent.objects.get_or_create(
                name=agent_data['name'],
                owner=default_user,
                defaults={
                    'type': agent_data['type'],
                    'capabilities': agent_data['capabilities'],
                    'description': agent_data['description'],
                    'status': AgentStatus.IDLE
                }
            )
            created_agents.append(agent)
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created agent: {agent.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Agent already exists: {agent.name}')
                )

        # Create sample sessions
        sessions_data = [
            {
                'name': 'Multi-Agent Intelligence Hub',
                'description': 'Main collaborative session for all agents',
                'agent_count': 5
            },
            {
                'name': 'Vision Analysis Session',
                'description': 'Specialized session for visual content analysis',
                'agent_count': 2
            },
            {
                'name': 'Problem Solving Workshop',
                'description': 'Session focused on complex reasoning tasks',
                'agent_count': 3
            }
        ]

        for session_data in sessions_data:
            session, created = Session.objects.get_or_create(
                name=session_data['name'],
                user=default_user,
                defaults={
                    'description': session_data.get('description', ''),
                    'is_active': True
                }
            )
            
            if created:
                # Add agents to session
                agents_to_add = created_agents[:session_data.get('agent_count', len(created_agents))]
                session.agents.set(agents_to_add)
                
                self.stdout.write(
                    self.style.SUCCESS(f'Created session: {session.name} with {len(agents_to_add)} agents')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Session already exists: {session.name}')
                )

        self.stdout.write(
            self.style.SUCCESS('Sample data creation completed!')
        )