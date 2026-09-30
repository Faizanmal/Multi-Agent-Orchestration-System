# agents/services/performance_tracker.py

import logging
from datetime import datetime, timedelta

from django.db.models import Avg, Q
from django.utils import timezone

from agents import models

from ..models import Agent, TaskExecution

logger = logging.getLogger(__name__)

class PerformanceTracker:
    """
    Tracks and analyzes agent performance metrics including
    success rates, response times, accuracy, and resource utilization.
    """
    
    def track_task_execution(
        self, 
        agent_id: str, 
        task_id: str, 
        task_type: str,
        start_time: datetime,
        end_time: datetime,
        success: bool,
        accuracy: float | None = None,
        error_message: str | None = None,
        resource_usage: dict | None = None
    ):
        """Track a single task execution for performance analysis."""
        
        try:
            execution_time = (end_time - start_time).total_seconds()
            
            # Create task execution record
            TaskExecution.objects.create(
                agent_id=agent_id,
                task_id=task_id,
                execution_identifier=models.CharField(max_length=100, help_text="Task Execution identifier for performance tracking",default=task_id),
                task_type=task_type,
                start_time=start_time,
                end_time=end_time,
                execution_time=execution_time,
                success=success,
                accuracy=accuracy,
                error_message=error_message,
                resource_usage=resource_usage or {}
            )
            
            # Update agent's running performance metrics
            self._update_agent_metrics(agent_id, task_type, execution_time, success, accuracy)
            
            logger.info(f"Tracked execution for agent {agent_id}: {execution_time:.2f}s, success={success}")
            
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error tracking task execution: {e}")
    
    def get_agent_performance(
        self, 
        agent_id: str, 
        task_type: str | None = None, 
        days: int = 30
    ) -> dict:
        """Get comprehensive performance metrics for an agent."""
        
        try:
            # Build query
            query = Q(agent_id=agent_id)
            
            if task_type:
                query &= Q(task_type=task_type)
                
            if days:
                since_date = timezone.now() - timedelta(days=days)
                query &= Q(start_time__gte=since_date)
            
            executions = TaskExecution.objects.filter(query)
            
            if not executions.exists():
                return {}
            
            # Calculate metrics
            total_executions = executions.count()
            successful_executions = executions.filter(success=True).count()
            failed_executions = total_executions - successful_executions
            
            success_rate = successful_executions / total_executions if total_executions > 0 else 0
            
            # Average metrics
            avg_execution_time = executions.aggregate(
                avg_time=Avg('execution_time')
            )['avg_time'] or 0
            
            accuracy_executions = executions.filter(accuracy__isnull=False)
            avg_accuracy = accuracy_executions.aggregate(
                avg_acc=Avg('accuracy')
            )['avg_acc'] or 0
            
            # Error analysis
            error_types = {}
            failed_executions_qs = executions.filter(success=False, error_message__isnull=False)
            for execution in failed_executions_qs:
                error_type = self._categorize_error(execution.error_message)
                error_types[error_type] = error_types.get(error_type, 0) + 1
            
            # Performance trends (last 7 days vs previous 7 days)
            recent_performance = self._get_trend_comparison(agent_id, task_type, 7, 14)
            
            return {
                'agent_id': agent_id,
                'task_type': task_type,
                'period_days': days,
                'total_executions': total_executions,
                'successful_executions': successful_executions,
                'failed_executions': failed_executions,
                'success_rate': success_rate,
                'avg_response_time': avg_execution_time,
                'accuracy': avg_accuracy,
                'error_types': error_types,
                'performance_trend': recent_performance,
                'last_updated': timezone.now().isoformat()
            }
            
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error getting agent performance: {e}")
            return {}
    
    def get_system_performance(self, days: int = 7) -> dict:
        """Get overall system performance metrics."""
        
        try:
            since_date = timezone.now() - timedelta(days=days)
            
            executions = TaskExecution.objects.filter(start_time__gte=since_date)
            
            if not executions.exists():
                return {}
            
            # Overall metrics
            total_executions = executions.count()
            successful_executions = executions.filter(success=True).count()
            overall_success_rate = successful_executions / total_executions
            
            # Agent performance comparison
            agent_performance = []
            for agent in Agent.objects.filter(is_active=True):
                perf = self.get_agent_performance(str(agent.id), days=days)
                if perf:
                    agent_performance.append({
                        'agent_id': str(agent.id),
                        'agent_name': agent.name,
                        'agent_type': agent.type,
                        **perf
                    })
            
            # Task type performance
            task_type_stats = {}
            task_types = executions.values('task_type').distinct()
            
            for task_type_dict in task_types:
                task_type = task_type_dict['task_type']
                type_executions = executions.filter(task_type=task_type)
                type_successful = type_executions.filter(success=True).count()
                type_total = type_executions.count()
                
                task_type_stats[task_type] = {
                    'total_executions': type_total,
                    'success_rate': type_successful / type_total if type_total > 0 else 0,
                    'avg_response_time': type_executions.aggregate(
                        avg_time=Avg('execution_time')
                    )['avg_time'] or 0
                }
            
            # Resource utilization
            resource_usage = self._calculate_resource_usage(executions)
            
            return {
                'period_days': days,
                'total_executions': total_executions,
                'overall_success_rate': overall_success_rate,
                'agent_performance': sorted(
                    agent_performance, 
                    key=lambda x: x.get('success_rate', 0), 
                    reverse=True
                ),
                'task_type_performance': task_type_stats,
                'resource_utilization': resource_usage,
                'generated_at': timezone.now().isoformat()
            }
            
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error getting system performance: {e}")
            return {}
    
    def get_performance_recommendations(self, agent_id: str) -> list[dict]:
        """Get performance improvement recommendations for an agent."""
        
        recommendations = []
        
        try:
            performance = self.get_agent_performance(agent_id, days=30)
            
            if not performance:
                return []
            
            # Check success rate
            if performance['success_rate'] < 0.8:
                recommendations.append({
                    'type': 'success_rate',
                    'priority': 'high',
                    'message': f"Success rate ({performance['success_rate']:.1%}) is below optimal threshold",
                    'suggestions': [
                        "Review error patterns and common failure points",
                        "Consider additional training or capability updates",
                        "Implement better error handling and recovery"
                    ]
                })
            
            # Check response time
            if performance['avg_response_time'] > 10.0:
                recommendations.append({
                    'type': 'response_time',
                    'priority': 'medium',
                    'message': f"Average response time ({performance['avg_response_time']:.1f}s) is slower than optimal",
                    'suggestions': [
                        "Optimize agent processing algorithms",
                        "Consider caching frequently used data",
                        "Review resource allocation and scaling"
                    ]
                })
            
            # Check accuracy
            if performance['accuracy'] > 0 and performance['accuracy'] < 0.7:
                recommendations.append({
                    'type': 'accuracy',
                    'priority': 'high',
                    'message': f"Accuracy ({performance['accuracy']:.1%}) needs improvement",
                    'suggestions': [
                        "Review and improve agent training data",
                        "Implement better validation and quality checks",
                        "Consider ensemble approaches for better accuracy"
                    ]
                })
            
            # Check error patterns
            if performance['error_types']:
                most_common_error = max(performance['error_types'].items(), key=lambda x: x[1])
                if most_common_error[1] > 3:  # More than 3 occurrences
                    recommendations.append({
                        'type': 'error_pattern',
                        'priority': 'medium',
                        'message': f"Frequent {most_common_error[0]} errors ({most_common_error[1]} occurrences)",
                        'suggestions': [
                            f"Investigate root cause of {most_common_error[0]} errors",
                            "Implement specific error handling for this error type",
                            "Consider preventive measures or input validation"
                        ]
                    })
            
            # Performance trend analysis
            trend = performance.get('performance_trend', {})
            if trend.get('success_rate_change', 0) < -0.1:
                recommendations.append({
                    'type': 'declining_performance',
                    'priority': 'high',
                    'message': "Performance has declined significantly in recent period",
                    'suggestions': [
                        "Investigate recent changes that may have affected performance",
                        "Review system logs for anomalies",
                        "Consider rolling back recent updates if necessary"
                    ]
                })
            
            return recommendations
            
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error generating recommendations: {e}")
            return []
    
    def _update_agent_metrics(
        self, 
        agent_id: str, 
        task_type: str, 
        execution_time: float, 
        success: bool, 
        accuracy: float | None = None
    ):
        """Update real-time agent performance metrics."""
        
        try:
            agent = Agent.objects.get(id=agent_id)
            config = agent.configuration or {}
            
            # Update running averages
            metrics = config.get('performance_metrics', {})
            task_metrics = metrics.get(task_type, {
                'total_executions': 0,
                'successful_executions': 0,
                'avg_execution_time': 0.0,
                'avg_accuracy': 0.0
            })
            
            # Update counts
            task_metrics['total_executions'] += 1
            if success:
                task_metrics['successful_executions'] += 1
            
            # Update running average for execution time
            prev_avg_time = task_metrics['avg_execution_time']
            n = task_metrics['total_executions']
            task_metrics['avg_execution_time'] = (prev_avg_time * (n - 1) + execution_time) / n
            
            # Update running average for accuracy if provided
            if accuracy is not None:
                prev_avg_accuracy = task_metrics['avg_accuracy']
                task_metrics['avg_accuracy'] = (prev_avg_accuracy * (n - 1) + accuracy) / n
            
            # Update configuration
            metrics[task_type] = task_metrics
            config['performance_metrics'] = metrics
            agent.configuration = config
            agent.save(update_fields=['configuration'])
            
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error updating agent metrics: {e}")
    
    def _get_trend_comparison(
        self, 
        agent_id: str, 
        task_type: str, 
        recent_days: int, 
        comparison_days: int
    ) -> dict:
        """Compare recent performance with previous period."""
        
        try:
            now = timezone.now()
            recent_start = now - timedelta(days=recent_days)
            comparison_start = now - timedelta(days=comparison_days)
            comparison_end = now - timedelta(days=recent_days)
            
            # Recent performance
            recent_query = Q(
                agent_id=agent_id,
                start_time__gte=recent_start
            )
            if task_type:
                recent_query &= Q(task_type=task_type)
            
            recent_executions = TaskExecution.objects.filter(recent_query)
            recent_success_rate = self._calculate_success_rate(recent_executions)
            
            # Comparison period performance
            comparison_query = Q(
                agent_id=agent_id,
                start_time__gte=comparison_start,
                start_time__lt=comparison_end
            )
            if task_type:
                comparison_query &= Q(task_type=task_type)
            
            comparison_executions = TaskExecution.objects.filter(comparison_query)
            comparison_success_rate = self._calculate_success_rate(comparison_executions)
            
            return {
                'recent_success_rate': recent_success_rate,
                'comparison_success_rate': comparison_success_rate,
                'success_rate_change': recent_success_rate - comparison_success_rate,
                'trend': 'improving' if recent_success_rate > comparison_success_rate else 'declining'
            }
            
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error calculating trend comparison: {e}")
            return {}
    
    def _calculate_success_rate(self, executions) -> float:
        """Calculate success rate for a queryset of executions."""
        total = executions.count()
        if total == 0:
            return 0.0
        successful = executions.filter(success=True).count()
        return successful / total
    
    def _categorize_error(self, error_message: str) -> str:
        """Categorize error messages into types."""
        error_message = error_message.lower()
        
        if 'timeout' in error_message:
            return 'timeout'
        elif 'connection' in error_message:
            return 'connection'
        elif 'authentication' in error_message or 'auth' in error_message:
            return 'authentication'
        elif 'permission' in error_message or 'forbidden' in error_message:
            return 'permission'
        elif 'not found' in error_message or '404' in error_message:
            return 'not_found'
        elif 'server error' in error_message or '500' in error_message:
            return 'server_error'
        elif 'validation' in error_message or 'invalid' in error_message:
            return 'validation'
        else:
            return 'other'
    
    def _calculate_resource_usage(self, executions) -> dict:
        """Calculate resource utilization metrics."""
        
        try:
            total_cpu_time = 0
            total_memory_usage = 0
            execution_count = 0
            
            for execution in executions:
                resource_usage = execution.resource_usage or {}
                total_cpu_time += resource_usage.get('cpu_time', 0)
                total_memory_usage += resource_usage.get('memory_mb', 0)
                execution_count += 1
            
            if execution_count == 0:
                return {}
            
            return {
                'avg_cpu_time': total_cpu_time / execution_count,
                'avg_memory_usage': total_memory_usage / execution_count,
                'total_executions': execution_count
            }
            
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error calculating resource usage: {e}")
            return {}