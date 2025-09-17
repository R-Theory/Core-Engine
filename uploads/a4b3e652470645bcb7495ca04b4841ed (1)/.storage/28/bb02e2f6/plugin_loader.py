import os
import yaml
import json
import importlib.util
from typing import Dict, Any, List, Optional
from pathlib import Path
from pydantic import BaseModel, ValidationError
import logging

logger = logging.getLogger(__name__)

class PluginManifest(BaseModel):
    name: str
    version: str
    description: str
    author: str
    category: str
    capabilities: List[str]
    config_schema: Dict[str, Any]
    oauth: Optional[Dict[str, Any]] = None
    permissions: List[str]
    health_check: Optional[Dict[str, Any]] = None

class PluginLoader:
    def __init__(self, plugins_dir: str = "/app/plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.loaded_plugins: Dict[str, Any] = {}
        self.plugin_manifests: Dict[str, PluginManifest] = {}
    
    async def load_plugins(self):
        """Load all plugins from the plugins directory"""
        if not self.plugins_dir.exists():
            logger.warning(f"Plugins directory {self.plugins_dir} does not exist")
            return
        
        for plugin_dir in self.plugins_dir.iterdir():
            if plugin_dir.is_dir():
                await self._load_plugin(plugin_dir)
    
    async def _load_plugin(self, plugin_dir: Path):
        """Load a single plugin from directory"""
        manifest_path = plugin_dir / "manifest.yaml"
        
        if not manifest_path.exists():
            logger.warning(f"No manifest.yaml found in {plugin_dir}")
            return
        
        try:
            # Load and validate manifest
            with open(manifest_path, 'r') as f:
                manifest_data = yaml.safe_load(f)
            
            manifest = PluginManifest(**manifest_data)
            
            # Load plugin module
            plugin_module = await self._load_plugin_module(plugin_dir, manifest.name)
            
            if plugin_module:
                self.loaded_plugins[manifest.name] = plugin_module
                self.plugin_manifests[manifest.name] = manifest
                logger.info(f"Successfully loaded plugin: {manifest.name}")
            
        except (ValidationError, yaml.YAMLError, Exception) as e:
            logger.error(f"Failed to load plugin from {plugin_dir}: {e}")
    
    async def _load_plugin_module(self, plugin_dir: Path, plugin_name: str):
        """Load the Python module for a plugin"""
        main_file = plugin_dir / "main.py"
        
        if not main_file.exists():
            logger.warning(f"No main.py found for plugin {plugin_name}")
            return None
        
        try:
            spec = importlib.util.spec_from_file_location(plugin_name, main_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Validate plugin has required interface
            if not hasattr(module, 'PluginClass'):
                logger.error(f"Plugin {plugin_name} missing PluginClass")
                return None
            
            return module.PluginClass()
            
        except Exception as e:
            logger.error(f"Failed to load module for plugin {plugin_name}: {e}")
            return None
    
    def get_plugin(self, plugin_name: str):
        """Get a loaded plugin by name"""
        return self.loaded_plugins.get(plugin_name)
    
    def get_manifest(self, plugin_name: str) -> Optional[PluginManifest]:
        """Get plugin manifest by name"""
        return self.plugin_manifests.get(plugin_name)
    
    def list_plugins(self) -> List[str]:
        """List all loaded plugin names"""
        return list(self.loaded_plugins.keys())
    
    async def execute_plugin_action(self, plugin_name: str, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an action on a plugin"""
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            raise ValueError(f"Plugin {plugin_name} not found")
        
        if not hasattr(plugin, action):
            raise ValueError(f"Action {action} not supported by plugin {plugin_name}")
        
        try:
            result = await getattr(plugin, action)(**params)
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Plugin action failed: {plugin_name}.{action} - {e}")
            return {"success": False, "error": str(e)}