import importlib
import os
import sys
from typing import Dict, Any

class PluginManager:
    """
    Manages loading and executing plugins dynamically.
    Plugins should be placed in the app/plugins directory.
    """
    def __init__(self, plugin_dir: str = "app/plugins"):
        self.plugin_dir = plugin_dir
        self.plugins: Dict[str, Any] = {}

    def load_plugins(self):
        """
        Dynamically load all plugins from the plugin directory.
        """
        if not os.path.exists(self.plugin_dir):
            os.makedirs(self.plugin_dir)
            
        sys.path.insert(0, os.path.abspath("."))
        
        for filename in os.listdir(self.plugin_dir):
            if filename.endswith(".py") and filename != "__init__.py" and filename != "manager.py":
                module_name = filename[:-3]
                try:
                    module = importlib.import_module(f"app.plugins.{module_name}")
                    if hasattr(module, "register_plugin"):
                        self.plugins[module_name] = module.register_plugin()
                        print(f"Loaded plugin: {module_name}")
                except Exception as e:
                    print(f"Failed to load plugin {module_name}: {e}")

plugin_manager = PluginManager()
