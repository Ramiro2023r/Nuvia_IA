"""
plugins/close_app.py — Plugin para cerrar aplicaciones
"""

from system.process_manager import close_app

intent_name = "close_app"

def execute(params, context=None, memory=None):
    """
    Cierra una aplicación basada en el parámetro 'app'.
    """
    app_name = params.get("app", "")
    if not app_name:
        return ("system", "No especificaste qué aplicación cerrar.", None)

    success = close_app(app_name)
    if success:
        return ("system", f"He cerrado {app_name}, Ramiro.", None)
    else:
        return ("system", f"No encontré el proceso {app_name} activo.", None)
