"""
system/commands.py — Puente entre el orquestador y el sistema de plugins
"""

import os
import subprocess
from datetime import datetime
def execute_intent(intent_data: dict, context=None, memory=None):
    """
    Coordina la ejecución de la intención. 
    Primero intenta usar el sistema de plugins dinámicos.
    """
    from core.plugin_manager import plugin_manager
    intent = intent_data.get("intent")
    
    # 1. Intentar ejecutar vía Plugin
    # Pasamos params, contexto y memoria al plugin
    plugin_result = plugin_manager.execute_plugin(intent, intent_data, context, memory)
    
    if plugin_result:
        return plugin_result

    # 2. Fallbacks predeterminados (lógica que no vale la pena separar todavía)
    if intent == "get_time":
        now = datetime.now()
        text = f"Son las {now.strftime('%I:%M %p')} de hoy {now.strftime('%A %d de %B')}"
        return ("time", text, None)

    # Default: Tratar como pregunta general para Gemini
    question = intent_data.get("question", intent_data.get("message", ""))
    return ("ai", None, question)


# ── Utilidades compartidas (usadas por plugins) ──────────────────────

def _find_app_path(name: str) -> str | None:
    """Busca el ejecutable de una app en el Menú Inicio."""
    search_paths = [
        os.path.join(os.environ.get("ProgramData", "C:\\ProgramData"), "Microsoft\\Windows\\Start Menu\\Programs"),
        os.path.join(os.environ.get("AppData", ""), "Microsoft\\Windows\\Start Menu\\Programs"),
        "C:\\Program Files",
        "C:\\Program Files (x86)"
    ]

    for base_path in search_paths:
        if not os.path.exists(base_path): continue
        for root, dirs, files in os.walk(base_path):
            for file in files:
                if file.lower().endswith((".lnk", ".exe")) and name in file.lower():
                    return os.path.join(root, file)
    return None

def _open(*args, shell=False):
    """Abre un proceso sin bloquear."""
    try:
        subprocess.Popen(
            args[0] if shell else list(args),
            shell=shell,
            creationflags=subprocess.CREATE_NO_WINDOW if not shell else 0,
        )
    except Exception as e:
        print(f"[Nuvia CMD] Error: {e}")
