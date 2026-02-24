"""
plugins/general_chat.py — Plugin para conversaciones generales y preguntas de IA
"""

from ai.gemini import ask

intent_name = "general_chat"

def execute(params, context=None, memory=None):
    message = params.get("message", "")
    if not message:
        return None # Dejar que el orquestador maneje el vacío

    # Inyectar contexto si existe
    prompt = message
    if context and context.get("summary"):
        prompt = f"[Contexto: {context['summary']}]\n{message}"
        
    ans = ask(prompt)
    return ("ai", ans, None)
