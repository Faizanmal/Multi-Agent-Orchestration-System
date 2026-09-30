# agents/services/analytics_dashboard.py

import logging
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, F, Q
from django.utils import timezone

from ..models import Agent, AgentStatus, Message, Session, Task, TaskStatus
from .performance_tracker import PerformanceTracker

# Get the custom user model
User = get_user_model()

logger = logging.getLogger(__name__)

class AnalyticsDashboard:
    """
    Comprehensive analytics dashboard that provides real-time insights,
    performance metrics, and intelligent recommendations for the multi-agent system.
    """
    
    def __init__(self):
        self.performance_tracker = PerformanceTracker()
    
    async def get_dashboard_data(
        self, 
        user_id: str | None = None, 
        time_range: str = '7d',
        include_predictions: bool = True
    ) -> dict:
        """
        Get comprehensive dashboard data including metrics, trends, and insights.
        
        Args:
            user_id: Optional user ID to filter data
            time_range: Time range for data (1d, 7d, 30d, 90d)
            include_predictions: Whether to include predictive analytics
            
        Returns:
            Complete dashboard data structure
        """
        
        # Parse time range
        days = self._parse_time_range(time_range)
        since_date = timezone.now() - timedelta(days=days)
        
        try:
            dashboard_data = {
                'metadata': {
                    'generated_at': timezone.now().isoformat(),
                    'time_range': time_range,
                    'days_included': days,
                    'user_id': user_id
                },
                'overview': await self._get_system_overview(user_id, since_date),
                'agent_metrics': await self._get_agent_metrics(user_id, since_date),
                'task_analytics': await self._get_task_analytics(user_id, since_date),
                'performance_trends': await self._get_performance_trends(user_id, since_date, days),
                'user_activity': await self._get_user_activity(user_id, since_date),
                'system_health': await self._get_system_health(),
                'insights': await self._generate_insights(user_id, since_date),
                'recommendations': await self._get_recommendations(user_id, since_date)
            }
            
            # Add predictions if requested
            if include_predictions:
                dashboard_data['predictions'] = await self._get_predictive_analytics(user_id, since_date)
            
            return dashboard_data
            
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error generating dashboard data: {e}")
            return {
                'error': str(e),
                'metadata': {
                    'generated_at': timezone.now().isoformat(),
                    'time_range': time_range
                }
            }
    
    async def _get_system_overview(self, user_id: str, since_date: datetime) -> dict:
        """Get high-level system overview metrics."""
        
        # Base queries
        agent_query = Q(is_active=True)
        task_query = Q(created_at__gte=since_date)
        session_query = Q(created_at__gte=since_date)
        message_query = Q(created_at__gte=since_date)
        
        if user_id:
            task_query &= Q(created_by_id=user_id)
            session_query &= Q(user_id=user_id)
            message_query &= Q(sender_id=user_id)
        
        # Active agents by status
        agent_counts = Agent.objects.filter(agent_query).aggregate(
            total=Count('id'),
            idle=Count('id', filter=Q(status=AgentStatus.IDLE)),
            active=Count('id', filter=Q(status=AgentStatus.ACTIVE)),
            processing=Count('id', filter=Q(status=AgentStatus.PROCESSING)),
            error=Count('id', filter=Q(status=AgentStatus.ERROR))
        )
        
        # Task statistics
        task_stats = Task.objects.filter(task_query).aggregate(
            total=Count('id'),
            completed=Count('id', filter=Q(status=TaskStatus.COMPLETED)),
            pending=Count('id', filter=Q(status=TaskStatus.PENDING)),
            in_progress=Count('id', filter=Q(status=TaskStatus.IN_PROGRESS)),
            failed=Count('id', filter=Q(status=TaskStatus.FAILED))
        )
        
        # Session statistics
        session_stats = Session.objects.filter(session_query).aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(is_active=True))
        )
        
        # Message statistics
        message_stats = Message.objects.filter(message_query).aggregate(
            total=Count('id'),
            user_messages=Count('id', filter=Q(sender__isnull=False)),
            agent_messages=Count('id', filter=Q(sender_agent__isnull=False))
        )
        
        # Calculate success rates
        success_rate = (
            task_stats['completed'] / max(task_stats['total'], 1)
        ) if task_stats['total'] > 0 else 0
        
        agent_utilization = (
            (agent_counts['active'] + agent_counts['processing']) / max(agent_counts['total'], 1)
        ) if agent_counts['total'] > 0 else 0
        
        return {
            'agents': {
                'total': agent_counts['total'],
                'by_status': {
                    'idle': agent_counts['idle'],
                    'active': agent_counts['active'],
                    'processing': agent_counts['processing'],
                    'error': agent_counts['error']
                },
                'utilization_rate': agent_utilization
            },
            'tasks': {
                'total': task_stats['total'],
                'by_status': {
                    'completed': task_stats['completed'],
                    'pending': task_stats['pending'],
                    'in_progress': task_stats['in_progress'],
                    'failed': task_stats['failed']
                },
                'success_rate': success_rate,
                'completion_rate': task_stats['completed'] / max(task_stats['total'], 1)
            },
            'sessions': {
                'total': session_stats['total'],
                'active': session_stats['active']
            },
            'messages': {
                'total': message_stats['total'],
                'user_messages': message_stats['user_messages'],
                'agent_messages': message_stats['agent_messages']
            }
        }
    
    async def _get_agent_metrics(self, user_id: str, since_date: datetime) -> dict:
        """Get detailed agent performance metrics."""
        
        agent_metrics = {}
        
        # Get all active agents
        agents = Agent.objects.filter(is_active=True)
        
        for agent in agents:
            # Get agent performance data
            performance_data = self.performance_tracker.get_agent_performance(
                str(agent.id), 
                days=(timezone.now() - since_date).days
            )
            
            # Get task counts for this agent
            task_query = Q(assigned_agent=agent, created_at__gte=since_date)
            if user_id:
                task_query &= Q(created_by_id=user_id)
            
            task_counts = Task.objects.filter(task_query).aggregate(
                total=Count('id'),
                completed=Count('id', filter=Q(status=TaskStatus.COMPLETED)),
                failed=Count('id', filter=Q(status=TaskStatus.FAILED))
            )
            
            # Calculate agent-specific metrics
            agent_metrics[str(agent.id)] = {
                'agent_info': {
                    'id': str(agent.id),
                    'name': agent.name,
                    'type': agent.type,
                    'status': agent.status,
                    'capabilities': agent.capabilities
                },
                'tasks': task_counts,
                'performance': performance_data or {},
                'efficiency_score': await self._calculate_agent_efficiency(agent, performance_data),
                'last_active': await self._get_agent_last_activity(agent)
            }
        
        # Calculate top performers
        sorted_agents = sorted(
            agent_metrics.items(), 
            key=lambda x: x[1].get('efficiency_score', 0), 
            reverse=True
        )
        
        return {
            'individual_metrics': agent_metrics,
            'top_performers': [agent_id for agent_id, _ in sorted_agents[:5]],
            'total_agents': len(agents),
            'agents_summary': {
                'highest_efficiency': max([m['efficiency_score'] for m in agent_metrics.values()]) if agent_metrics else 0,
                'average_efficiency': sum([m['efficiency_score'] for m in agent_metrics.values()]) / len(agent_metrics) if agent_metrics else 0,
                'lowest_efficiency': min([m['efficiency_score'] for m in agent_metrics.values()]) if agent_metrics else 0
            }
        }
    
    async def _get_task_analytics(self, user_id: str, since_date: datetime) -> dict:
        """Get detailed task analytics and patterns."""
        
        # Base task query
        task_query = Q(created_at__gte=since_date)
        if user_id:
            task_query &= Q(created_by_id=user_id)
        
        tasks = Task.objects.filter(task_query)
        
        # Task type distribution
        task_type_stats = tasks.values('task_type').annotate(
            count=Count('id'),
            avg_duration=Avg('actual_duration'),
            success_rate=Count('id', filter=Q(status=TaskStatus.COMPLETED)) / Count('id')
        ).order_by('-count')
        
        # Priority distribution
        priority_stats = tasks.values('priority').annotate(
            count=Count('id'),
            avg_completion_time=Avg(
                F('completed_at') - F('created_at'),
                filter=Q(status=TaskStatus.COMPLETED)
            )
        )
        
        # Time-based patterns (hourly distribution)
        hourly_stats = {}
        for hour in range(24):
            hour_tasks = tasks.filter(created_at__hour=hour)
            hourly_stats[hour] = {
                'count': hour_tasks.count(),
                'completion_rate': (
                    hour_tasks.filter(status=TaskStatus.COMPLETED).count() / 
                    max(hour_tasks.count(), 1)
                )
            }
        
        # Complexity analysis
        complexity_analysis = await self._analyze_task_complexity(tasks)
        
        # Failure analysis
        failed_tasks = tasks.filter(status=TaskStatus.FAILED)
        failure_patterns = await self._analyze_failure_patterns(failed_tasks)
        
        return {
            'task_types': list(task_type_stats),
            'priority_distribution': list(priority_stats),
            'hourly_patterns': hourly_stats,
            'complexity_analysis': complexity_analysis,
            'failure_analysis': failure_patterns,
            'trends': {
                'total_tasks': tasks.count(),
                'avg_completion_time': tasks.filter(
                    status=TaskStatus.COMPLETED
                ).aggregate(
                    avg_time=Avg(F('completed_at') - F('created_at'))
                )['avg_time'],
                'most_common_type': task_type_stats[0]['task_type'] if task_type_stats else None
            }
        }
    
    async def _get_performance_trends(self, user_id: str, since_date: datetime, days: int) -> dict:
        """Get performance trends over time."""
        
        # Calculate time intervals for trend analysis
        intervals = []
        interval_days = max(days // 10, 1)  # Divide into ~10 intervals
        
        for i in range(0, days, interval_days):
            start_date = since_date + timedelta(days=i)
            end_date = min(start_date + timedelta(days=interval_days), timezone.now())
            intervals.append((start_date, end_date))
        
        trends = {
            'task_completion_rate': [],
            'agent_efficiency': [],
            'response_times': [],
            'error_rates': [],
            'user_activity': []
        }
        
        for start_date, end_date in intervals:
            # Task completion rate for this interval
            interval_tasks = Task.objects.filter(
                created_at__gte=start_date, 
                created_at__lt=end_date
            )
            
            if user_id:
                interval_tasks = interval_tasks.filter(created_by_id=user_id)
            
            completion_rate = (
                interval_tasks.filter(status=TaskStatus.COMPLETED).count() /
                max(interval_tasks.count(), 1)
            )
            
            trends['task_completion_rate'].append({
                'date': start_date.isoformat(),
                'value': completion_rate
            })

            # Agent efficiency: (completed / total) weighted by avg speed relative to period length
            completed_tasks = interval_tasks.filter(status=TaskStatus.COMPLETED)
            avg_duration = completed_tasks.aggregate(
                avg_time=Avg('actual_duration')
            )['avg_time'] or 0
            # Normalise duration: efficiency = completion_rate penalised by how slow tasks were
            # A task completing within 10 % of the interval window is considered "fast" (score 1.0)
            interval_seconds = (end_date - start_date).total_seconds()
            speed_score = max(0.0, 1.0 - (avg_duration / max(interval_seconds * 0.1, 1)))
            agent_efficiency = (completion_rate * 0.6) + (speed_score * 0.4)
            trends['agent_efficiency'].append({
                'date': start_date.isoformat(),
                'value': min(agent_efficiency, 1.0),
            })
            
            # Response times
            avg_response_time = interval_tasks.filter(
                status=TaskStatus.COMPLETED
            ).aggregate(
                avg_time=Avg('actual_duration')
            )['avg_time'] or 0
            
            trends['response_times'].append({
                'date': start_date.isoformat(),
                'value': avg_response_time
            })
            
            # Error rates
            error_rate = (
                interval_tasks.filter(status=TaskStatus.FAILED).count() /
                max(interval_tasks.count(), 1)
            )
            
            trends['error_rates'].append({
                'date': start_date.isoformat(),
                'value': error_rate
            })
            
            # User activity (messages sent)
            if user_id:
                activity_count = Message.objects.filter(
                    sender_id=user_id,
                    created_at__gte=start_date,
                    created_at__lt=end_date
                ).count()
            else:
                activity_count = Message.objects.filter(
                    created_at__gte=start_date,
                    created_at__lt=end_date
                ).count()
            
            trends['user_activity'].append({
                'date': start_date.isoformat(),
                'value': activity_count
            })
        
        return trends
    
    async def _get_user_activity(self, user_id: str, since_date: datetime) -> dict:
        """Get user activity patterns and statistics."""
        
        if not user_id:
            return {}
        
        user_query = Q(created_at__gte=since_date)
        
        # User sessions
        sessions = Session.objects.filter(user_id=user_id, **user_query.children[0])
        
        # User messages
        messages = Message.objects.filter(sender_id=user_id, **user_query.children[0])
        
        # User tasks
        tasks = Task.objects.filter(created_by_id=user_id, **user_query.children[0])
        
        # Activity patterns
        daily_activity = {}
        for day in range((timezone.now() - since_date).days + 1):
            date = since_date + timedelta(days=day)
            date_str = date.strftime('%Y-%m-%d')
            
            daily_activity[date_str] = {
                'sessions': sessions.filter(created_at__date=date.date()).count(),
                'messages': messages.filter(created_at__date=date.date()).count(),
                'tasks': tasks.filter(created_at__date=date.date()).count()
            }
        
        # Most active hours
        hourly_activity = {}
        for hour in range(24):
            hourly_activity[hour] = {
                'messages': messages.filter(created_at__hour=hour).count(),
                'tasks': tasks.filter(created_at__hour=hour).count()
            }
        
        return {
            'summary': {
                'total_sessions': sessions.count(),
                'total_messages': messages.count(),
                'total_tasks': tasks.count(),
                'active_days': len([d for d in daily_activity.values() if d['sessions'] > 0])
            },
            'daily_activity': daily_activity,
            'hourly_patterns': hourly_activity,
            'engagement_score': await self._calculate_user_engagement_score(user_id, since_date)
        }
    
    async def _get_system_health(self) -> dict:
        """Get overall system health metrics."""
        
        # Agent health
        agent_health = {}
        total_agents = Agent.objects.filter(is_active=True).count()
        
        if total_agents > 0:
            healthy_agents = Agent.objects.filter(
                is_active=True,
                status__in=[AgentStatus.IDLE, AgentStatus.ACTIVE, AgentStatus.PROCESSING]
            ).count()
            
            agent_health = {
                'total_agents': total_agents,
                'healthy_agents': healthy_agents,
                'health_percentage': (healthy_agents / total_agents) * 100
            }
        
        # Database health (simplified)
        db_health = {
            'status': 'healthy',  # Would include actual DB health checks
            'total_records': {
                'agents': Agent.objects.count(),
                'tasks': Task.objects.count(),
                'sessions': Session.objects.count(),
                'messages': Message.objects.count()
            }
        }
        
        # Recent error tracking
        recent_errors = Task.objects.filter(
            status=TaskStatus.FAILED,
            created_at__gte=timezone.now() - timedelta(hours=24)
        ).count()
        
        return {
            'overall_status': 'healthy' if recent_errors < 10 else 'degraded',
            'agent_health': agent_health,
            'database_health': db_health,
            'recent_errors': recent_errors,
            'uptime_percentage': 99.5,  # Would calculate actual uptime
            'last_updated': timezone.now().isoformat()
        }
    
    async def _generate_insights(self, user_id: str, since_date: datetime) -> list[dict]:
        """Generate intelligent insights from the analytics data."""
        
        insights = []
        
        try:
            # Task completion insights
            if user_id:
                user_tasks = Task.objects.filter(created_by_id=user_id, created_at__gte=since_date)
                completion_rate = (
                    user_tasks.filter(status=TaskStatus.COMPLETED).count() / 
                    max(user_tasks.count(), 1)
                )
                
                if completion_rate > 0.9:
                    insights.append({
                        'type': 'positive',
                        'category': 'productivity',
                        'title': 'Excellent Task Completion Rate',
                        'description': f'You have a {completion_rate:.1%} task completion rate - outstanding performance!',
                        'impact': 'high',
                        'actionable': False
                    })
                elif completion_rate < 0.7:
                    insights.append({
                        'type': 'warning',
                        'category': 'productivity',
                        'title': 'Task Completion Rate Needs Attention',
                        'description': f'Your task completion rate is {completion_rate:.1%}. Consider reviewing failed tasks.',
                        'impact': 'medium',
                        'actionable': True,
                        'suggested_action': 'Review failed tasks and identify common failure patterns'
                    })
            
            # Agent utilization insights
            agents = Agent.objects.filter(is_active=True)
            if agents.exists():
                idle_agents = agents.filter(status=AgentStatus.IDLE).count()
                total_agents = agents.count()
                
                if idle_agents > total_agents * 0.5:
                    insights.append({
                        'type': 'info',
                        'category': 'resource_utilization',
                        'title': 'High Agent Availability',
                        'description': f'{idle_agents} out of {total_agents} agents are idle and ready for tasks.',
                        'impact': 'low',
                        'actionable': True,
                        'suggested_action': 'Consider scaling down idle agents or increasing task volume'
                    })
            
            # Performance trend insights
            recent_tasks = Task.objects.filter(created_at__gte=timezone.now() - timedelta(days=7))
            older_tasks = Task.objects.filter(
                created_at__gte=timezone.now() - timedelta(days=14),
                created_at__lt=timezone.now() - timedelta(days=7)
            )
            
            if recent_tasks.exists() and older_tasks.exists():
                recent_success = recent_tasks.filter(status=TaskStatus.COMPLETED).count() / recent_tasks.count()
                older_success = older_tasks.filter(status=TaskStatus.COMPLETED).count() / older_tasks.count()
                
                if recent_success > older_success + 0.1:
                    insights.append({
                        'type': 'positive',
                        'category': 'performance_trend',
                        'title': 'Improving Performance Trend',
                        'description': f'Task success rate improved by {(recent_success - older_success):.1%} this week.',
                        'impact': 'medium',
                        'actionable': False
                    })
            
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error generating insights: {e}")
        
        return insights
    
    async def _get_recommendations(self, user_id: str, since_date: datetime) -> list[dict]:
        """Get intelligent recommendations for system optimization."""
        
        recommendations = []
        
        try:
            # Agent optimization recommendations
            agent_performance = {}
            for agent in Agent.objects.filter(is_active=True):
                perf = self.performance_tracker.get_agent_performance(str(agent.id), days=30)
                if perf:
                    agent_performance[str(agent.id)] = perf['success_rate']
            
            if agent_performance:
                avg_success_rate = sum(agent_performance.values()) / len(agent_performance)
                underperforming_agents = [
                    agent_id for agent_id, success_rate in agent_performance.items() 
                    if success_rate < avg_success_rate - 0.2
                ]
                
                if underperforming_agents:
                    recommendations.append({
                        'type': 'optimization',
                        'category': 'agent_performance',
                        'title': 'Agent Performance Optimization',
                        'description': f'{len(underperforming_agents)} agents are underperforming compared to average.',
                        'priority': 'high',
                        'estimated_impact': 'medium',
                        'actions': [
                            'Review agent configurations',
                            'Update agent capabilities',
                            'Provide additional training data'
                        ]
                    })
            
            # Task optimization recommendations
            if user_id:
                failed_tasks = Task.objects.filter(
                    created_by_id=user_id,
                    status=TaskStatus.FAILED,
                    created_at__gte=since_date
                )
                
                if failed_tasks.count() > 5:
                    recommendations.append({
                        'type': 'process_improvement',
                        'category': 'task_management',
                        'title': 'Task Failure Reduction',
                        'description': f'You have {failed_tasks.count()} failed tasks. Consider optimizing task definitions.',
                        'priority': 'medium',
                        'estimated_impact': 'high',
                        'actions': [
                            'Review failed task patterns',
                            'Simplify complex task requirements',
                            'Add input validation'
                        ]
                    })
            
            # Resource utilization recommendations
            total_agents = Agent.objects.filter(is_active=True).count()
            busy_agents = Agent.objects.filter(
                is_active=True,
                status=AgentStatus.PROCESSING
            ).count()
            
            if total_agents > 0:
                utilization_rate = busy_agents / total_agents
                
                if utilization_rate > 0.8:
                    recommendations.append({
                        'type': 'scaling',
                        'category': 'resource_management',
                        'title': 'Consider Agent Scaling',
                        'description': f'Agent utilization is {utilization_rate:.1%}. Consider adding more agents.',
                        'priority': 'medium',
                        'estimated_impact': 'high',
                        'actions': [
                            'Deploy additional agent instances',
                            'Optimize task distribution',
                            'Implement load balancing'
                        ]
                    })
        
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error generating recommendations: {e}")
        
        return recommendations
    
    async def _get_predictive_analytics(self, user_id: str, since_date: datetime) -> dict:
        """Generate predictive analytics and forecasts."""
        
        predictions = {
            'task_volume_forecast': [],
            'resource_requirements': {},
            'potential_bottlenecks': [],
            'success_rate_prediction': 0.0
        }
        
        try:
            # Simple task volume prediction (linear trend)
            tasks_per_day = {}
            current_date = since_date
            
            while current_date <= timezone.now():
                day_key = current_date.strftime('%Y-%m-%d')
                day_tasks = Task.objects.filter(
                    created_at__date=current_date.date()
                )
                
                if user_id:
                    day_tasks = day_tasks.filter(created_by_id=user_id)
                
                tasks_per_day[day_key] = day_tasks.count()
                current_date += timedelta(days=1)
            
            # Calculate trend and predict next 7 days
            if len(tasks_per_day) > 3:
                values = list(tasks_per_day.values())
                trend = (values[-1] - values[0]) / len(values)
                
                for i in range(7):
                    future_date = timezone.now() + timedelta(days=i+1)
                    predicted_tasks = max(0, values[-1] + trend * (i + 1))
                    
                    predictions['task_volume_forecast'].append({
                        'date': future_date.strftime('%Y-%m-%d'),
                        'predicted_tasks': int(predicted_tasks),
                        'confidence': max(0.3, 0.9 - i * 0.1)  # Decreasing confidence
                    })
            
            # Resource requirements prediction
            if predictions['task_volume_forecast']:
                avg_predicted_tasks = sum(
                    p['predicted_tasks'] for p in predictions['task_volume_forecast']
                ) / len(predictions['task_volume_forecast'])
                
                # Estimate required agents (assuming each agent handles ~10 tasks/day)
                required_agents = max(1, int(avg_predicted_tasks / 10))
                current_agents = Agent.objects.filter(is_active=True).count()
                
                predictions['resource_requirements'] = {
                    'recommended_agents': required_agents,
                    'current_agents': current_agents,
                    'scaling_needed': required_agents > current_agents,
                    'scaling_factor': required_agents / max(current_agents, 1)
                }
            
            # Success rate prediction based on recent trends
            recent_tasks = Task.objects.filter(created_at__gte=timezone.now() - timedelta(days=7))
            if user_id:
                recent_tasks = recent_tasks.filter(created_by_id=user_id)
            
            if recent_tasks.exists():
                current_success_rate = (
                    recent_tasks.filter(status=TaskStatus.COMPLETED).count() / 
                    recent_tasks.count()
                )
                predictions['success_rate_prediction'] = current_success_rate
        
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error generating predictive analytics: {e}")
        
        return predictions
    
    # Helper methods
    
    def _parse_time_range(self, time_range: str) -> int:
        """Parse time range string to number of days."""
        range_mapping = {
            '1d': 1, '1day': 1, '1 day': 1,
            '7d': 7, '1w': 7, '1week': 7, '1 week': 7,
            '30d': 30, '1m': 30, '1month': 30, '1 month': 30,
            '90d': 90, '3m': 90, '3months': 90, '3 months': 90
        }
        
        return range_mapping.get(time_range.lower(), 7)
    
    async def _calculate_agent_efficiency(self, agent: Agent, performance_data: dict) -> float:
        """Calculate agent efficiency score."""
        if not performance_data:
            return 0.5
        
        success_rate = performance_data.get('success_rate', 0.5)
        avg_response_time = performance_data.get('avg_response_time', 5.0)
        accuracy = performance_data.get('accuracy', 0.5)
        
        # Normalize response time (assume 10s is acceptable)
        response_time_score = max(0, 1 - (avg_response_time / 10.0))
        
        # Weighted efficiency score
        efficiency = (
            success_rate * 0.4 + 
            response_time_score * 0.3 + 
            accuracy * 0.3
        )
        
        return min(efficiency, 1.0)
    
    async def _get_agent_last_activity(self, agent: Agent) -> str | None:
        """Get agent's last activity timestamp."""
        try:
            last_task = Task.objects.filter(assigned_agent=agent).order_by('-created_at').first()
            if last_task:
                return last_task.created_at.isoformat()
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Error fetching last task: {e}")
        
        return None
    
    async def _analyze_task_complexity(self, tasks) -> dict:
        """Analyze task complexity patterns."""
        # Simplified complexity analysis
        complexity_scores = []
        
        for task in tasks:
            # Simple complexity heuristic based on description length and requirements
            desc_complexity = len(task.description) / 100.0  # Normalize by 100 chars
            req_complexity = len(task.requirements) / 10.0   # Normalize by 10 requirements
            
            complexity = min(desc_complexity + req_complexity, 5.0)  # Cap at 5.0
            complexity_scores.append(complexity)
        
        if complexity_scores:
            return {
                'average_complexity': sum(complexity_scores) / len(complexity_scores),
                'max_complexity': max(complexity_scores),
                'min_complexity': min(complexity_scores),
                'high_complexity_count': len([c for c in complexity_scores if c > 3.0])
            }
        
        return {}
    
    async def _analyze_failure_patterns(self, failed_tasks) -> dict:
        """Analyze patterns in failed tasks."""
        patterns = {
            'by_type': {},
            'by_agent': {},
            'by_time': {},
            'common_factors': []
        }
        
        # Group by task type
        for task in failed_tasks:
            patterns['by_type'][task.task_type] = patterns['by_type'].get(task.task_type, 0) + 1
            
            if task.assigned_agent:
                agent_name = task.assigned_agent.name
                patterns['by_agent'][agent_name] = patterns['by_agent'].get(agent_name, 0) + 1
            
            # Group by hour of day
            hour = task.created_at.hour
            patterns['by_time'][hour] = patterns['by_time'].get(hour, 0) + 1
        
        # Identify common factors
        if patterns['by_type']:
            most_failed_type = max(patterns['by_type'].items(), key=lambda x: x[1])
            patterns['common_factors'].append(f"Most failed task type: {most_failed_type[0]} ({most_failed_type[1]} failures)")
        
        return patterns
    
    async def _calculate_user_engagement_score(self, user_id: str, since_date: datetime) -> float:
        """Calculate user engagement score."""
        try:
            # Get user activity metrics
            sessions = Session.objects.filter(user_id=user_id, created_at__gte=since_date).count()
            messages = Message.objects.filter(sender_id=user_id, created_at__gte=since_date).count()
            tasks = Task.objects.filter(created_by_id=user_id, created_at__gte=since_date).count()
            
            # Simple engagement calculation
            days = (timezone.now() - since_date).days + 1
            
            session_score = min(sessions / days, 5) / 5  # Cap at 5 sessions per day
            message_score = min(messages / days, 20) / 20  # Cap at 20 messages per day
            task_score = min(tasks / days, 10) / 10  # Cap at 10 tasks per day
            
            engagement_score = (session_score * 0.3 + message_score * 0.4 + task_score * 0.3)
            
            return min(engagement_score, 1.0)
            
        except Exception:  # noqa: BLE001
            return 0.0