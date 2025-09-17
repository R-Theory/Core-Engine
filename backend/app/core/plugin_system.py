"""
Plugin System - Core plugin management and registry

This module provides the main plugin system functionality including plugin
discovery, loading, management, and coordination.
"""

import os
import importlib
import inspect
from typing import Dict, List, Any, Optional, Type, Union
import asyncio
from pathlib import Path
import logging

from .plugin_interface import (
    Plugin, PluginType, PluginStatus, PluginConfig, PluginResult,
    PluginMetadata, StoragePlugin, ParserPlugin, ProcessorPlugin,
    PluginException, PluginInitializationError
)

logger = logging.getLogger(__name__)

class PluginRegistry:
    """
    Central registry for managing all plugins in the system
    
    Handles plugin discovery, loading, configuration, and lifecycle management.
    """
    
    def __init__(self):
        self._plugins: Dict[str, Plugin] = {}
        self._plugin_classes: Dict[str, Type[Plugin]] = {}
        self._plugin_configs: Dict[str, PluginConfig] = {}
        self.logger = logging.getLogger(__name__)

    async def discover_plugins(self, plugin_dir: str = None) -> List[str]:
        """
        Discover available plugin classes
        
        Args:
            plugin_dir: Directory to search for plugins (defaults to app/plugins)
            
        Returns:
            List[str]: List of discovered plugin names
        """
        if not plugin_dir:
            # Default to the plugins directory
            current_dir = Path(__file__).parent.parent
            plugin_dir = current_dir / "plugins"
        
        discovered = []
        
        try:
            # Walk through plugin directory
            for root, dirs, files in os.walk(plugin_dir):
                for file in files:
                    if file.endswith('.py') and not file.startswith('__'):
                        module_path = Path(root) / file
                        
                        # Convert file path to module name
                        relative_path = module_path.relative_to(current_dir)
                        module_name = str(relative_path).replace('/', '.').replace('\\', '.')[:-3]
                        
                        try:
                            # Import the module
                            module = importlib.import_module(f"app.{module_name}")
                            
                            # Find plugin classes
                            for name, obj in inspect.getmembers(module, inspect.isclass):
                                if (issubclass(obj, Plugin) and 
                                    obj != Plugin and 
                                    not obj.__name__.startswith('Base')):
                                    
                                    plugin_name = obj.__name__.lower().replace('plugin', '')
                                    self._plugin_classes[plugin_name] = obj
                                    discovered.append(plugin_name)
                                    
                                    self.logger.info(f"Discovered plugin: {plugin_name}")
                        
                        except Exception as e:
                            self.logger.warning(f"Failed to load module {module_name}: {str(e)}")
            
            return discovered
            
        except Exception as e:
            self.logger.error(f"Plugin discovery failed: {str(e)}")
            return []

    def register_plugin_class(self, name: str, plugin_class: Type[Plugin]):
        """
        Manually register a plugin class
        
        Args:
            name: Plugin name
            plugin_class: Plugin class to register
        """
        if not issubclass(plugin_class, Plugin):
            raise ValueError(f"Plugin class must inherit from Plugin: {plugin_class}")
        
        self._plugin_classes[name] = plugin_class
        self.logger.info(f"Registered plugin class: {name}")

    async def load_plugin(self, name: str, config: PluginConfig) -> bool:
        """
        Load and initialize a plugin
        
        Args:
            name: Plugin name
            config: Plugin configuration
            
        Returns:
            bool: True if loaded successfully
        """
        try:
            if name not in self._plugin_classes:
                raise PluginInitializationError(f"Plugin class not found: {name}")
            
            plugin_class = self._plugin_classes[name]
            plugin_instance = plugin_class(config)
            
            # Store configuration
            self._plugin_configs[name] = config
            
            # Initialize plugin if enabled
            if config.enabled:
                plugin_instance.status = PluginStatus.INITIALIZING
                success = await plugin_instance.initialize()
                
                if success:
                    plugin_instance.status = PluginStatus.ACTIVE
                    self._plugins[name] = plugin_instance
                    self.logger.info(f"Plugin loaded and initialized: {name}")
                    return True
                else:
                    plugin_instance.status = PluginStatus.ERROR
                    self.logger.error(f"Plugin initialization failed: {name}")
                    return False
            else:
                plugin_instance.status = PluginStatus.DISABLED
                self._plugins[name] = plugin_instance
                self.logger.info(f"Plugin loaded but disabled: {name}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to load plugin {name}: {str(e)}")
            return False

    async def unload_plugin(self, name: str) -> bool:
        """
        Unload a plugin and cleanup its resources
        
        Args:
            name: Plugin name
            
        Returns:
            bool: True if unloaded successfully
        """
        try:
            if name in self._plugins:
                plugin = self._plugins[name]
                await plugin.cleanup()
                del self._plugins[name]
                self.logger.info(f"Plugin unloaded: {name}")
            
            if name in self._plugin_configs:
                del self._plugin_configs[name]
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unload plugin {name}: {str(e)}")
            return False

    async def enable_plugin(self, name: str) -> bool:
        """
        Enable a plugin
        
        Args:
            name: Plugin name
            
        Returns:
            bool: True if enabled successfully
        """
        try:
            if name not in self._plugins:
                self.logger.error(f"Plugin not loaded: {name}")
                return False
            
            plugin = self._plugins[name]
            config = self._plugin_configs[name]
            
            if not config.enabled:
                config.enabled = True
                plugin.config = config
                
                plugin.status = PluginStatus.INITIALIZING
                success = await plugin.initialize()
                
                if success:
                    plugin.status = PluginStatus.ACTIVE
                    self.logger.info(f"Plugin enabled: {name}")
                    return True
                else:
                    plugin.status = PluginStatus.ERROR
                    config.enabled = False
                    self.logger.error(f"Failed to enable plugin: {name}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error enabling plugin {name}: {str(e)}")
            return False

    async def disable_plugin(self, name: str) -> bool:
        """
        Disable a plugin
        
        Args:
            name: Plugin name
            
        Returns:
            bool: True if disabled successfully
        """
        try:
            if name not in self._plugins:
                return True
            
            plugin = self._plugins[name]
            config = self._plugin_configs[name]
            
            if config.enabled:
                config.enabled = False
                plugin.config = config
                
                await plugin.cleanup()
                plugin.status = PluginStatus.DISABLED
                
                self.logger.info(f"Plugin disabled: {name}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error disabling plugin {name}: {str(e)}")
            return False

    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get a plugin instance by name"""
        return self._plugins.get(name)

    def get_enabled_plugins(self, plugin_type: PluginType = None) -> List[Plugin]:
        """
        Get all enabled plugins, optionally filtered by type
        
        Args:
            plugin_type: Optional plugin type filter
            
        Returns:
            List[Plugin]: List of enabled plugins
        """
        plugins = [
            plugin for plugin in self._plugins.values()
            if plugin.is_enabled()
        ]
        
        if plugin_type:
            plugins = [
                plugin for plugin in plugins
                if plugin.metadata.plugin_type == plugin_type
            ]
        
        # Sort by priority (lower number = higher priority)
        plugins.sort(key=lambda p: p.config.priority)
        
        return plugins

    def get_storage_plugins(self) -> List[StoragePlugin]:
        """Get all enabled storage plugins"""
        return [
            plugin for plugin in self.get_enabled_plugins(PluginType.STORAGE)
            if isinstance(plugin, StoragePlugin)
        ]

    def get_parser_plugins(self) -> List[ParserPlugin]:
        """Get all enabled parser plugins"""
        return [
            plugin for plugin in self.get_enabled_plugins(PluginType.PARSER)
            if isinstance(plugin, ParserPlugin)
        ]

    def get_processor_plugins(self) -> List[ProcessorPlugin]:
        """Get all enabled processor plugins"""
        return [
            plugin for plugin in self.get_enabled_plugins(PluginType.PROCESSOR)
            if isinstance(plugin, ProcessorPlugin)
        ]

    async def get_parser_for_file(self, file_path: str, mime_type: str = None) -> Optional[ParserPlugin]:
        """
        Find the best parser for a given file
        
        Args:
            file_path: Path to the file
            mime_type: Optional MIME type
            
        Returns:
            Optional[ParserPlugin]: Best parser for the file, or None
        """
        parsers = self.get_parser_plugins()
        
        for parser in parsers:
            try:
                if await parser.can_parse(file_path, mime_type):
                    return parser
            except Exception as e:
                self.logger.warning(f"Parser {parser.metadata.name} failed can_parse check: {str(e)}")
        
        return None

    def get_plugin_metadata(self, name: str) -> Optional[PluginMetadata]:
        """Get metadata for a plugin"""
        plugin = self._plugins.get(name)
        return plugin.metadata if plugin else None

    def get_all_plugin_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all plugins (loaded and available)
        
        Returns:
            Dict with plugin info including status, metadata, and config
        """
        info = {}
        
        # Add loaded plugins
        for name, plugin in self._plugins.items():
            config = self._plugin_configs.get(name, PluginConfig())
            info[name] = {
                "loaded": True,
                "enabled": config.enabled,
                "status": plugin.status,
                "metadata": plugin.metadata.dict(),
                "config": config.dict()
            }
        
        # Add available but not loaded plugins
        for name, plugin_class in self._plugin_classes.items():
            if name not in info:
                try:
                    # Create temporary instance to get metadata
                    temp_config = PluginConfig()
                    temp_instance = plugin_class(temp_config)
                    info[name] = {
                        "loaded": False,
                        "enabled": False,
                        "status": PluginStatus.INACTIVE,
                        "metadata": temp_instance.metadata.dict(),
                        "config": temp_config.dict()
                    }
                except Exception as e:
                    self.logger.warning(f"Failed to get metadata for {name}: {str(e)}")
        
        return info

    async def health_check(self) -> Dict[str, bool]:
        """
        Check health of all enabled plugins
        
        Returns:
            Dict[str, bool]: Plugin name -> health status
        """
        health = {}
        
        for name, plugin in self._plugins.items():
            if plugin.is_enabled():
                try:
                    health[name] = await plugin.health_check()
                except Exception as e:
                    self.logger.error(f"Health check failed for {name}: {str(e)}")
                    health[name] = False
        
        return health

# Global plugin registry instance
plugin_registry = PluginRegistry()