"""
plugins/open_app.py — Plugin para abrir aplicaciones
"""

import os
import subprocess
from system.commands import _find_app_path, _open

intent_name = "open_app"

def execute(params, context=None, memory=None):
    """
    Abre una aplicación basada en el parámetro 'app'.
    """
    app_name = params.get("app", "").lower()
    if not app_name:
        return ("system", "No me dijiste qué aplicación abrir.", None)

    path = _find_app_path(app_name)
    
    if path:
        _open(f'start "" "{path}"', shell=True)
        return ("system", f"Abriendo {app_name}, Ramiro.", None)
    else:
        # Fallback a comando directo si no hay acceso directo
        _open(f"start {app_name}", shell=True)
        return ("system", f"Intentando abrir {app_name} de forma directa.", None)
