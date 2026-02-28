"""
plugins/remember.py — Plugin para guardar información en memoria explícitamente
"""

from ai.memory import process_memory_storage

intent_name = "remember"

def execute(params, context=None, memory=None):
    info = params.get("info", "")
    if not info:
        return ("system", "No me dijiste qué quieres que recuerde.", None)
    
    # Procesamos el guardado
    process_memory_storage(info)
    return ("system", f"Entendido, Ramiro. He guardado eso en mi memoria: {info}", None)
