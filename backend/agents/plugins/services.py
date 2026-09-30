import logging
from typing import Any

from . import models
from .registry import plugin_registry

logger = logging.getLogger(__name__)

# Import the models directly to avoid typing issues
Plugin = models.Plugin
PluginInstallation = models.PluginInstallation
PluginRating = models.PluginRating


class PluginService:
    """Service for managing plugin operations"""

    def __init__(self):
        self.registry = plugin_registry

    def initialize_plugins(self) -> None:
        """Initialize and load all active plugins"""
        try:
            logger.info("Initializing plugin system...")
            self.registry.load_installed_plugins()
            logger.info(f"Loaded {len(self.registry.get_installed_plugins())} plugins")
        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to initialize plugins: {e}")

    def install_plugin(
        self, plugin_id: str, user_id: str, configuration: dict[str, Any] | None = None
    ) -> bool:
        """Install a plugin for a user"""
        try:
            plugin = Plugin.objects.get(id=plugin_id)

            # Create or update installation record
            installation, created = PluginInstallation.objects.get_or_create(
                plugin=plugin,
                user_id=user_id,
                defaults={"configuration": configuration or {}, "is_active": True},
            )

            if not created:
                installation.configuration = configuration or installation.configuration
                installation.is_active = True
                installation.save()

            # Load the plugin
            plugin_instance = self.registry._load_plugin(plugin)
            if plugin_instance:
                self.registry._plugins[str(plugin.id)] = plugin_instance
                self.registry._installed_plugins[str(plugin.id)] = installation
                logger.info(f"Installed plugin: {plugin.name} for user {user_id}")
                return True
            else:
                logger.error(f"Failed to load plugin: {plugin.name}")
                return False

        except Plugin.DoesNotExist:
            logger.error(f"Plugin with ID {plugin_id} not found")
            return False
        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to install plugin {plugin_id}: {e}")
            return False

    def uninstall_plugin(self, plugin_id: str, user_id: str) -> bool:
        """Uninstall a plugin for a user"""
        try:
            installation = PluginInstallation.objects.get(
                plugin_id=plugin_id, user_id=user_id
            )
            installation.is_active = False
            installation.save()

            # Remove from registry
            if str(plugin_id) in self.registry._plugins:
                del self.registry._plugins[str(plugin_id)]
            if str(plugin_id) in self.registry._installed_plugins:
                del self.registry._installed_plugins[str(plugin_id)]

            logger.info(
                f"Uninstalled plugin: {installation.plugin.name} for user {user_id}"
            )
            return True
        except PluginInstallation.DoesNotExist:
            logger.error(
                f"Plugin installation {plugin_id} not found for user {user_id}"
            )
            return False
        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to uninstall plugin {plugin_id}: {e}")
            return False

    def execute_plugin(
        self, plugin_id: str, user_id: str, **kwargs
    ) -> dict[str, Any] | None:
        """Execute a plugin with given parameters"""
        try:
            # Check if plugin is installed by user
            installation = PluginInstallation.objects.get(
                plugin_id=plugin_id, user_id=user_id, is_active=True
            )

            # Get plugin instance
            plugin_instance = self.registry.get_plugin(str(plugin_id))
            if not plugin_instance:
                logger.error(f"Plugin {plugin_id} not loaded")
                return None

            # Apply configuration
            if installation.configuration:
                plugin_instance.configure(installation.configuration)

            # Execute plugin
            result = plugin_instance.execute(**kwargs)
            logger.info(f"Executed plugin: {plugin_instance.name}")
            return result

        except PluginInstallation.DoesNotExist:
            logger.error(f"Plugin {plugin_id} not installed for user {user_id}")
            return None
        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to execute plugin {plugin_id}: {e}")
            return None

    def get_user_plugins(self, user_id: str) -> dict[str, Any]:
        """Get all plugins installed by a user"""
        try:
            installations = PluginInstallation.objects.filter(
                user_id=user_id, is_active=True
            ).select_related("plugin")

            plugins_info = {}
            for installation in installations:
                plugin_instance = self.registry.get_plugin(str(installation.plugin.id))
                if plugin_instance:
                    plugins_info[str(installation.plugin.id)] = (
                        plugin_instance.get_info()
                    )

            return plugins_info
        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to get user plugins: {e}")
            return {}


# Global plugin service instance
plugin_service = PluginService()
