"""
plugins/hello_nuevi.py — Plugin de prueba para verificar la escalabilidad
"""

intent_name = "hello_nuevi"

def execute(params, context=None, memory=None):
    """
    Plugin de prueba que responde a un saludo especial.
    """
    return ("system", "¡Hola Ramiro! El sistema de plugins dinámicos está funcionando a la perfección. Soy una extensión de tu asistente.", None)
