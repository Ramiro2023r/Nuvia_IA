"""
plugins/window_control.py — Plugin para manipular estados de ventana
"""

from system.window_manager import minimize_window, maximize_window, switch_to_window

intent_name = "window_control"

def execute(params, context=None, memory=None):
    app_name = params.get("app", "")
    action = params.get("action", "")
    
    if action == "minimize":
        minimize_window(app_name)
        return ("system", f"Minimizando {app_name}.", None)
    elif action == "maximize":
        maximize_window(app_name)
        return ("system", f"Maximizando {app_name}.", None)
    elif action == "switch":
        switch_to_window(app_name)
        return ("system", f"Cambiando a la ventana de {app_name}.", None)
        
    return ("system", "No entendí qué quieres hacer con la ventana.", None)
