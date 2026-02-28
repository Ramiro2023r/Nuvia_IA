"""
plugins/system_control.py — Plugin para control de energía (apagado/reinicio)
"""

import os

intent_name = "system_control"

def execute(params, context=None, memory=None):
    """
    Ejecuta acciones de sistema como apagar o reiniciar.
    """
    action = params.get("action")
    
    if action == "shutdown":
        os.system("shutdown /s /t 10")
        return ("system", "Apagando el equipo en 10 segundos.", None)
    elif action == "restart":
        os.system("shutdown /r /t 10")
        return ("system", "Reiniciando el equipo.", None)
    elif action == "cancel_shutdown":
        os.system("shutdown /a")
        return ("system", "Apagado cancelado.", None)
        
    return ("system", "Acción de sistema no reconocida.", None)
