"""
plugins/show_chat.py — Plugin para abrir y cerrar el chat modal de Nuvia.

Intents manejados:
  - show_chat: Abre el modal de chat
  - hide_chat: Cierra el modal de chat
"""

intent_name = "show_chat"


def execute(params, context=None, memory=None):
    """
    Abre el chat modal de Nuvia.
    El modal se abre a través de la referencia global del orchestrator.
    """
    action = params.get("action", "show")

    if action == "hide":
        return ("system", "__HIDE_CHAT__", None)
    else:
        return ("system", "__SHOW_CHAT__", None)
