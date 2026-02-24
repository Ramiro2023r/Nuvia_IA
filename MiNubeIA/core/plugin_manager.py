"""
core/plugin_manager.py — Gestor dinámico de plugins para intenciones
"""

import os
import importlib
import pkgutil
import logging

logger = logging.getLogger("NuviaPlugins")

class PluginManager:
    """
    Carga y administra plugins dinámicamente desde la carpeta /plugins.
    Cada plugin debe definir 'intent_name' y una función 'execute'.
    """

    def __init__(self, plugins_folder="plugins"):
        self.plugins_folder = plugins_folder
        self.plugins = {}
        # load_plugins() se debe llamar explícitamente después de la inicialización para evitar importaciones circulares

    def load_plugins(self):
        """Busca y carga todos los módulos en la carpeta de plugins."""
        # Asegurar que la carpeta existe
        if not os.path.exists(self.plugins_folder):
            os.makedirs(self.plugins_folder)
            with open(os.path.join(self.plugins_folder, "__init__.py"), "w") as f:
                pass

        logger.info(f"Cargando plugins desde '{self.plugins_folder}'...")
        
        # Iterar sobre los módulos en la carpeta
        for loader, module_name, is_pkg in pkgutil.iter_modules([self.plugins_folder]):
            try:
                # Importar el módulo dinámicamente
                full_module_name = f"{self.plugins_folder}.{module_name}"
                module = importlib.import_module(full_module_name)
                
                # Recargar si ya existe para permitir actualizaciones en caliente
                importlib.reload(module)

                # Verificar si tiene los atributos necesarios
                if hasattr(module, "intent_name") and hasattr(module, "execute"):
                    intent = module.intent_name
                    self.plugins[intent] = module.execute
                    logger.info(f"Plugin registrado: [{intent}] desde {module_name}")
                else:
                    logger.warning(f"Módulo {module_name} ignorado: falta intent_name o execute")
            except Exception as e:
                logger.error(f"Error cargando plugin {module_name}: {e}")

    def execute_plugin(self, intent_name, params, context=None, memory=None):
        """
        Ejecuta el plugin correspondiente a la intención.
        Retorna (accion, respuesta, extra) o None si no hay plugin.
        """
        plugin_func = self.plugins.get(intent_name)
        if plugin_func:
            try:
                return plugin_func(params, context, memory)
            except Exception as e:
                logger.error(f"Error ejecutando plugin {intent_name}: {e}")
                return ("error", f"Error en el plugin {intent_name}", str(e))
        return None

# Instancia única (Singleton) para ser usada en todo el sistema
plugin_manager = PluginManager()
