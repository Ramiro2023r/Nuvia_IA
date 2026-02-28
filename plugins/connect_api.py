"""
plugins/connect_api.py — Plugin para abrir el panel de configuración de modelos.
"""

import logging

logger = logging.getLogger("PluginConnectAPI")

intent_name = "connect_api"

def execute(params, context=None, memory=None):
    """
    Señala al orquestador que debe abrir el ModelPanel en el ChatModal.
    """
    model = params.get("model")
    
    # Este plugin no hace nada por sí mismo en el sistema,
    # el Orchestrator detectará este intent y llamará a la UI.
    
    if model:
        msg = f"¡Perfecto! Abriendo el chat para configurar {model.capitalize()}. Ingresa tu API Key en el panel."
    else:
        msg = "¿Qué modelo quieres conectar? Tengo Gemini, GPT, Grok, Groq y Ollama local."
        
    return ("ui", msg, {"action": "open_model_panel", "preselect": model})
