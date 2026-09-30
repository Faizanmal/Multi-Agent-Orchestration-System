"""
Plugin Service
Manages plugin lifecycle, execution, and marketplace operations
"""
import traceback
from typing import Any

from django.core.exceptions import ValidationError
from django.db.models import Avg, Q, Sum
from django.utils import timezone

from ..models import Agent
from ..plugin_models import (
    AgentPlugin,
    PluginDependency,
    PluginExecutionLog,
    PluginInstallation,
    PluginMarketplaceMetrics,
    PluginReview,
    PluginStatus,
)


class PluginService:
    """Service for managing plugin operations"""
    
    @staticmethod
    def install_plugin(plugin: AgentPlugin, user, configuration: dict | None = None) -> PluginInstallation:
        """Install a plugin for a user"""
        
        # Check if already installed
        existing = PluginInstallation.objects.filter(plugin=plugin, user=user).first()
        if existing:
            existing.is_enabled = True
            existing.configuration = configuration or existing.configuration
            existing.save()
            return existing
        
        # Check dependencies
        dependencies = PluginDependency.objects.filter(plugin=plugin, is_optional=False)
        for dep in dependencies:
            dep_installed = PluginInstallation.objects.filter(
                plugin=dep.required_plugin,
                user=user,
                is_enabled=True
            ).exists()
            
            if not dep_installed:
                raise ValidationError(
                    f"Missing required dependency: {dep.required_plugin.name}"
                )
        
        # Create installation
        installation = PluginInstallation.objects.create(
            plugin=plugin,
            user=user,
            installed_version=plugin.version,
            configuration=configuration or plugin.default_configuration
        )
        
        # Update plugin stats
        plugin.active_installations += 1
        plugin.increment_downloads()
        
        return installation
    
    @staticmethod
    def uninstall_plugin(installation: PluginInstallation):
        """Uninstall a plugin"""
        plugin = installation.plugin
        installation.delete()
        
        # Update stats
        plugin.active_installations = max(0, plugin.active_installations - 1)
        plugin.save()
    
    @staticmethod
    def execute_plugin(installation: PluginInstallation, 
                      input_data: dict,
                      execution_context: dict | None = None) -> tuple[bool, Any, str]:
        """
        Execute a plugin safely
        Returns: (success, result, error_message)
        """
        
        if not installation.is_enabled:
            return False, None, "Plugin is disabled"
        
        # Create execution log
        log = PluginExecutionLog.objects.create(
            installation=installation,
            input_data=input_data,
            execution_context=execution_context or {},
            status='running'
        )
        
        try:
            # Load plugin code
            plugin_code = installation.plugin.plugin_code
            
            # Create a safe namespace
            namespace = {
                '__builtins__': __builtins__,
                'input_data': input_data,
                'context': execution_context or {},
                'config': installation.configuration
            }
            
            # Execute plugin code
            start_time = timezone.now()
            exec(plugin_code, namespace)  # noqa: S102
            end_time = timezone.now()
            
            # Get result (plugin should set 'result' variable)
            result = namespace.get('result')
            
            # Calculate execution time
            execution_time = int((end_time - start_time).total_seconds() * 1000)
            
            # Update log
            log.status = 'success'
            log.output_data = {'result': result}
            log.completed_at = end_time
            log.execution_time_ms = execution_time
            log.save()
            
            # Update installation stats
            installation.record_usage(execution_time, success=True)
            
            return True, result, ""
            
        except Exception as e:  # noqa: BLE001
            error_message = str(e)
            error_trace = traceback.format_exc()
            
            # Update log
            log.status = 'error'
            log.error_message = error_message
            log.error_trace = error_trace
            log.completed_at = timezone.now()
            log.save()
            
            # Update installation stats
            installation.record_usage(success=False)
            
            return False, None, error_message
    
    @staticmethod
    def validate_plugin_code(code: str) -> tuple[bool, str]:
        """
        Validate plugin code for security and correctness
        Returns: (is_valid, error_message)
        """
        
        # Check for forbidden imports
        forbidden_modules = ['os', 'subprocess', 'sys', 'importlib', '__import__']
        for module in forbidden_modules:
            if f"import {module}" in code:
                return False, f"Forbidden module: {module}"
        
        # Check for dangerous functions
        dangerous_patterns = ['eval(', 'exec(', 'compile(', '__import__']
        for pattern in dangerous_patterns:
            if pattern in code:
                return False, f"Dangerous pattern detected: {pattern}"
        
        # Try to compile code
        try:
            compile(code, '<plugin>', 'exec')
        except SyntaxError as e:
            return False, f"Syntax error: {e!s}"
        
        return True, ""
    
    @staticmethod
    def search_plugins(query: str = "",
                      category: str | None = None,
                      tags: list[str] | None = None,
                      min_rating: float = 0.0,
                      is_free: bool | None = None,
                      sort_by: str = 'downloads') -> list[AgentPlugin]:
        """Search plugins in marketplace"""
        
        plugins = AgentPlugin.objects.filter(
            status=PluginStatus.APPROVED,
            is_public=True
        )
        
        # Text search
        if query:
            plugins = plugins.filter(
                Q(name__icontains=query) |
                Q(display_name__icontains=query) |
                Q(description__icontains=query) |
                Q(keywords__icontains=query)
            )
        
        # Category filter
        if category:
            plugins = plugins.filter(category=category)
        
        # Tags filter
        if tags:
            for tag in tags:
                plugins = plugins.filter(tags__contains=[tag])
        
        # Rating filter
        if min_rating > 0:
            plugins = plugins.filter(average_rating__gte=min_rating)
        
        # Price filter
        if is_free is not None:
            plugins = plugins.filter(is_free=is_free)
        
        # Sorting
        if sort_by == 'downloads':
            plugins = plugins.order_by('-downloads_count')
        elif sort_by == 'rating':
            plugins = plugins.order_by('-average_rating')
        elif sort_by == 'recent':
            plugins = plugins.order_by('-published_at')
        elif sort_by == 'name':
            plugins = plugins.order_by('display_name')
        
        return plugins
    
    @staticmethod
    def get_plugin_recommendations(user, limit: int = 10) -> list[AgentPlugin]:
        """Get personalized plugin recommendations"""
        
        # Get user's installed plugins
        installed_plugins = PluginInstallation.objects.filter(user=user).values_list('plugin_id', flat=True)
        
        # Get categories user is interested in
        user_categories = AgentPlugin.objects.filter(
            id__in=installed_plugins
        ).values_list('category', flat=True).distinct()
        
        # Find popular plugins in same categories
        recommendations = AgentPlugin.objects.filter(
            status=PluginStatus.APPROVED,
            is_public=True,
            category__in=user_categories
        ).exclude(
            id__in=installed_plugins
        ).order_by('-average_rating', '-downloads_count')[:limit]
        
        return recommendations
    
    @staticmethod
    def submit_review(plugin: AgentPlugin, user, rating: int, 
                     title: str, review_text: str,
                     pros: list[str] | None = None, cons: list[str] | None = None) -> PluginReview:
        """Submit a plugin review"""
        
        # Check if user has installed the plugin
        installation = PluginInstallation.objects.filter(plugin=plugin, user=user).first()
        is_verified = installation is not None
        
        # Create or update review
        review, created = PluginReview.objects.update_or_create(
            plugin=plugin,
            user=user,
            defaults={
                'rating': rating,
                'title': title,
                'review_text': review_text,
                'pros': pros or [],
                'cons': cons or [],
                'is_verified_purchase': is_verified,
                'installation': installation
            }
        )
        
        if created:
            # Update plugin rating
            plugin.update_rating(rating)
        
        return review
    
    @staticmethod
    def get_plugin_analytics(plugin: AgentPlugin, days: int = 30) -> dict:
        """Get analytics for a plugin"""
        from datetime import timedelta
        
        start_date = timezone.now().date() - timedelta(days=days)
        
        metrics = PluginMarketplaceMetrics.objects.filter(
            plugin=plugin,
            date__gte=start_date
        ).order_by('date')
        
        total_downloads = metrics.aggregate(Sum('downloads_count'))['downloads_count__sum'] or 0
        total_views = metrics.aggregate(Sum('views_count'))['views_count__sum'] or 0
        avg_active_users = metrics.aggregate(Avg('active_users'))['active_users__avg'] or 0
        total_revenue = metrics.aggregate(Sum('revenue'))['revenue__sum'] or 0
        
        return {
            'plugin_id': str(plugin.id),
            'plugin_name': plugin.name,
            'period_days': days,
            'total_downloads': total_downloads,
            'total_views': total_views,
            'average_active_users': round(avg_active_users, 2),
            'total_revenue': float(total_revenue),
            'conversion_rate': (total_downloads / total_views * 100) if total_views > 0 else 0,
            'daily_metrics': [
                {
                    'date': str(m.date),
                    'downloads': m.downloads_count,
                    'views': m.views_count,
                    'active_users': m.active_users,
                    'executions': m.total_executions,
                    'revenue': float(m.revenue)
                }
                for m in metrics
            ]
        }
    
    @staticmethod
    def create_agent_from_plugin(plugin: AgentPlugin, user, agent_name: str) -> Agent:
        """Create an agent instance from a plugin"""
        
        # Ensure user has installed the plugin
        installation = PluginInstallation.objects.filter(
            plugin=plugin,
            user=user,
            is_enabled=True
        ).first()
        
        if not installation:
            raise ValidationError("Plugin must be installed first")
        
        # Create agent with plugin configuration
        agent = Agent.objects.create(
            name=agent_name,
            type='custom',
            owner=user,
            capabilities=plugin.capabilities,
            configuration={
                'plugin_id': str(plugin.id),
                'plugin_name': plugin.name,
                'plugin_version': plugin.version,
                **installation.configuration
            }
        )
        
        return agent


class PluginMarketplaceService:
    """Service for marketplace operations"""
    
    @staticmethod
    def submit_plugin(plugin_data: dict, author) -> AgentPlugin:
        """Submit a new plugin to marketplace"""
        
        # Validate plugin code
        is_valid, error = PluginService.validate_plugin_code(plugin_data.get('plugin_code', ''))
        if not is_valid:
            raise ValidationError(f"Invalid plugin code: {error}")
        
        # Create plugin
        plugin = AgentPlugin.objects.create(
            author=author,
            author_name=author.get_full_name() or author.username,
            status=PluginStatus.PENDING_REVIEW,
            **plugin_data
        )
        
        return plugin
    
    @staticmethod
    def approve_plugin(plugin: AgentPlugin):
        """Approve a plugin for marketplace"""
        plugin.status = PluginStatus.APPROVED
        plugin.published_at = timezone.now()
        plugin.last_reviewed_at = timezone.now()
        plugin.save()
    
    @staticmethod
    def reject_plugin(plugin: AgentPlugin, reason: str):
        """Reject a plugin"""
        plugin.status = PluginStatus.REJECTED
        plugin.last_reviewed_at = timezone.now()
        plugin.save()
        
        # Notify author (implementation depends on notification system)
        # send_notification(plugin.author, f"Plugin rejected: {reason}")
    
    @staticmethod
    def get_trending_plugins(limit: int = 10) -> list[AgentPlugin]:
        """Get trending plugins based on recent activity"""
        from datetime import timedelta
        
        # Get plugins with high recent download/usage activity
        recent_date = timezone.now().date() - timedelta(days=7)
        
        trending_plugin_ids = PluginMarketplaceMetrics.objects.filter(
            date__gte=recent_date
        ).values('plugin').annotate(
            total_activity=Sum('downloads_count') + Sum('total_executions')
        ).order_by('-total_activity')[:limit].values_list('plugin_id', flat=True)
        
        # Get plugin objects maintaining order
        plugins = AgentPlugin.objects.filter(
            id__in=trending_plugin_ids,
            status=PluginStatus.APPROVED,
            is_public=True
        )
        
        # Preserve ordering
        plugin_dict = {str(p.id): p for p in plugins}
        return [plugin_dict[str(pid)] for pid in trending_plugin_ids if str(pid) in plugin_dict]
    
    @staticmethod
    def get_featured_plugins() -> list[AgentPlugin]:
        """Get featured plugins"""
        return AgentPlugin.objects.filter(
            is_featured=True,
            status=PluginStatus.APPROVED,
            is_public=True
        ).order_by('-average_rating')
    
    @staticmethod
    def record_plugin_view(plugin: AgentPlugin):
        """Record a plugin page view"""
        today = timezone.now().date()
        
        metric, _ = PluginMarketplaceMetrics.objects.get_or_create(
            plugin=plugin,
            date=today
        )
        metric.views_count += 1
        metric.save()
