"""
Plugin Manager for dynamic plugin loading and execution
"""

import importlib
import inspect
import logging
from pathlib import Path
from typing import Any

from app.plugins.base import PluginResult, RemediatorPlugin, ValidatorPlugin

logger = logging.getLogger(__name__)


class PluginConfig:
    """Plugin configuration"""

    def __init__(
        self,
        name: str,
        enabled: bool = True,
        priority: int = 0,
        config: dict[str, Any] | None = None,
    ):
        self.name = name
        self.enabled = enabled
        self.priority = priority
        self.config = config or {}


class PluginManager:
    """Manages loading and execution of plugins"""

    def __init__(self):
        self.validators: dict[str, ValidatorPlugin] = {}
        self.remediators: dict[str, RemediatorPlugin] = {}
        self.plugin_configs: dict[str, PluginConfig] = {}
        self._loaded = False

    def load_plugins(self, plugin_dir: Path | None = None) -> None:
        """Load all plugins from the plugins directory"""
        if self._loaded:
            return

        if plugin_dir is None:
            plugin_dir = Path(__file__).parent

        # Get all Python files in the plugins directory
        plugin_files = [
            f for f in plugin_dir.glob("*.py")
            if not f.name.startswith("_") and f.name not in ["base.py", "plugin_manager.py"]
        ]

        for plugin_file in plugin_files:
            try:
                # Import the module
                module_name = f"app.plugins.{plugin_file.stem}"
                module = importlib.import_module(module_name)

                # Find all classes in the module
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # Check if it's a validator plugin
                    if (
                        issubclass(obj, ValidatorPlugin)
                        and obj is not ValidatorPlugin
                        and not inspect.isabstract(obj)
                    ):
                        instance = obj()
                        self.validators[instance.name] = instance
                        logger.info(f"Loaded validator plugin: {instance.name}")

                    # Check if it's a remediator plugin
                    elif (
                        issubclass(obj, RemediatorPlugin)
                        and obj is not RemediatorPlugin
                        and not inspect.isabstract(obj)
                    ):
                        instance = obj()
                        self.remediators[instance.name] = instance
                        logger.info(f"Loaded remediator plugin: {instance.name}")

            except Exception as e:
                logger.error(f"Failed to load plugin from {plugin_file}: {e}")

        self._loaded = True
        logger.info(
            f"Loaded {len(self.validators)} validators and {len(self.remediators)} remediators"
        )

    def register_validator(self, validator: ValidatorPlugin) -> None:
        """Register a validator plugin"""
        self.validators[validator.name] = validator
        logger.info(f"Registered validator: {validator.name}")

    def register_remediator(self, remediator: RemediatorPlugin) -> None:
        """Register a remediator plugin"""
        self.remediators[remediator.name] = remediator
        logger.info(f"Registered remediator: {remediator.name}")

    def configure_plugin(self, config: PluginConfig) -> None:
        """Configure a plugin"""
        self.plugin_configs[config.name] = config

    def is_plugin_enabled(self, plugin_name: str) -> bool:
        """Check if a plugin is enabled"""
        if plugin_name in self.plugin_configs:
            return self.plugin_configs[plugin_name].enabled
        return True  # Default to enabled

    def get_plugin_config(self, plugin_name: str) -> dict[str, Any]:
        """Get configuration for a plugin"""
        if plugin_name in self.plugin_configs:
            return self.plugin_configs[plugin_name].config
        return {}

    async def validate_content(
        self,
        content: str,
        metadata: dict[str, Any] | None = None,
        validators: list[str] | None = None,
    ) -> dict[str, PluginResult]:
        """
        Run validation plugins on content
        
        Args:
            content: The content to validate
            metadata: Additional metadata for validation
            validators: List of validator names to run (None = run all enabled)
        
        Returns:
            Dictionary of validator name to result
        """
        if not self._loaded:
            self.load_plugins()

        results = {}
        metadata = metadata or {}

        # Determine which validators to run
        validators_to_run = []
        if validators:
            # Run specific validators
            for name in validators:
                if name in self.validators and self.is_plugin_enabled(name):
                    validators_to_run.append((name, self.validators[name]))
        else:
            # Run all enabled validators
            for name, validator in self.validators.items():
                if self.is_plugin_enabled(name):
                    validators_to_run.append((name, validator))

        # Sort by priority
        def get_priority(item: tuple[str, ValidatorPlugin]) -> int:
            name = item[0]
            return self.plugin_configs.get(name, PluginConfig(name)).priority
        
        validators_to_run.sort(key=get_priority, reverse=True)

        # Run validators
        for name, validator in validators_to_run:
            try:
                # Add plugin config to metadata
                plugin_metadata = {**metadata, "config": self.get_plugin_config(name)}
                result = await validator.validate(content, plugin_metadata)
                results[name] = result
            except Exception as e:
                logger.error(f"Error running validator {name}: {e}")
                results[name] = PluginResult(
                    success=False,
                    message=f"Validator error: {e!s}",
                )

        return results

    async def remediate_content(
        self,
        content: str,
        issues: list[dict[str, Any]],
        remediators: list[str] | None = None,
    ) -> dict[str, PluginResult]:
        """
        Run remediation plugins on content
        
        Args:
            content: The content to remediate
            issues: List of issues to remediate
            remediators: List of remediator names to run (None = run all enabled)
        
        Returns:
            Dictionary of remediator name to result
        """
        if not self._loaded:
            self.load_plugins()

        results = {}

        # Determine which remediators to run
        remediators_to_run = []
        if remediators:
            # Run specific remediators
            for name in remediators:
                if name in self.remediators and self.is_plugin_enabled(name):
                    remediators_to_run.append((name, self.remediators[name]))
        else:
            # Run all enabled remediators
            for name, remediator in self.remediators.items():
                if self.is_plugin_enabled(name):
                    remediators_to_run.append((name, remediator))

        # Sort by priority
        def get_priority(item: tuple[str, RemediatorPlugin]) -> int:
            name = item[0]
            return self.plugin_configs.get(name, PluginConfig(name)).priority
        
        remediators_to_run.sort(key=get_priority, reverse=True)

        # Run remediators
        current_content = content
        for name, remediator in remediators_to_run:
            try:
                result = await remediator.remediate(current_content, issues)
                results[name] = result

                # If remediation was successful and returned new content, use it
                if result.success and result.data and "content" in result.data:
                    current_content = result.data["content"]
            except Exception as e:
                logger.error(f"Error running remediator {name}: {e}")
                results[name] = PluginResult(
                    success=False,
                    message=f"Remediator error: {e!s}",
                )

        return results

    def get_available_validators(self) -> list[dict[str, Any]]:
        """Get list of available validators"""
        if not self._loaded:
            self.load_plugins()

        return [
            {
                "name": validator.name,
                "description": validator.description,
                "enabled": self.is_plugin_enabled(validator.name),
                "priority": self.plugin_configs.get(
                    validator.name, PluginConfig(validator.name)
                ).priority,
            }
            for validator in self.validators.values()
        ]

    def get_available_remediators(self) -> list[dict[str, Any]]:
        """Get list of available remediators"""
        if not self._loaded:
            self.load_plugins()

        return [
            {
                "name": remediator.name,
                "description": remediator.description,
                "enabled": self.is_plugin_enabled(remediator.name),
                "priority": self.plugin_configs.get(
                    remediator.name, PluginConfig(remediator.name)
                ).priority,
            }
            for remediator in self.remediators.values()
        ]


# Global plugin manager instance
plugin_manager = PluginManager()
