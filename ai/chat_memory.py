import json
import os
import logging

logger = logging.getLogger("ChatMemory")

class ChatMemory:
    """
    Gestiona la memoria a corto plazo de la conversación.
    Mantiene una ventana deslizante de los últimos N intercambios.
    """
    def __init__(self, max_messages=10):
        self.max_messages = max_messages
        self.history = [] # Lista de diccionarios: {"role": "user/assistant", "content": "..."}

    def add_message(self, role, content):
        """Añade un mensaje al historial y mantiene el límite."""
        self.history.append({"role": role, "content": content})
        if len(self.history) > self.max_messages * 2: # 10 intercambios = 20 mensajes
            # En lugar de solo borrar, intentamos resumir los primeros mensajes para no perder contexto
            self._condense_history()

    def _condense_history(self):
        """Resume la primera mitad del historial para liberar espacio."""
        try:
            from ai.ollama_client import OllamaClient
            ollama = OllamaClient()
            
            # Tomamos los primeros 10 mensajes para resumir
            to_summarize = self.history[:10]
            conv_text = "\n".join([f"{m['role']}: {m['content']}" for m in to_summarize])
            
            summary = ollama.chat_response(
                f"Resume brevemente esta conversación en una sola frase para recordar el contexto: \n{conv_text}"
            )
            
            # Nuevo historial: El resumen + los mensajes restantes
            remaining = self.history[10:]
            self.history = [{"role": "system", "content": f"Contexto previo: {summary}"}] + remaining
            logger.info("Historial de chat resumido automáticamente.")
        except Exception as e:
            logger.error(f"Error resumiendo historial: {e}")
            # Fallback: borrar los más viejos
            self.history = self.history[-(self.max_messages * 2):]

    def get_history(self):
        """Retorna el historial completo."""
        return self.history

    def clear(self):
        """Limpia el historial."""
        self.history = []

    def get_last_user_message(self):
        """Retorna el último mensaje del usuario."""
        for msg in reversed(self.history):
            if msg["role"] == "user":
                return msg["content"]
        return None
