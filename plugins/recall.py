"""
plugins/recall.py — Plugin para buscar información en la memoria histórica
"""

from ai.memory import query_memory

intent_name = "recall"

def execute(params, context=None, memory=None):
    query = params.get("query", "")
    if not query:
        return ("system", "¿Qué es exactamente lo que quieres que busque en mi memoria?", None)
    
    ans = query_memory(query)
    if ans:
        return ("system", ans, None)
    else:
        return ("system", "No he encontrado nada relacionado con eso en mi memoria, Ramiro.", None)
