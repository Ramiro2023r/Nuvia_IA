"""
ai/ollama_client.py — Cliente para clasificar intenciones usando Mistral-7B local (Ollama)
"""

import requests
import json
import logging
import os

logger = logging.getLogger("OllamaClient")

class OllamaClient:
    """
    Se conecta con Ollama ejecutándose localmente para realizar tareas de clasificación.
    """

    def __init__(self, model="phi3:mini", check_interval=60):
        # Usamos phi3:mini por defecto para equipos de 8GB RAM
        self.model = os.getenv("OLLAMA_MODEL", model)
        # Changed to api/chat as the methods use the messages array format
        self.base_url = "http://localhost:11434/api/chat" 
        self.system_prompt = (
            "Modelo en uso: mistral-7b ejecutándose localmente mediante Ollama.\n"
            "Actúa como un clasificador de intención para NuviaIA.\n\n"
            "Tu tarea es decidir si el usuario pide información en tiempo real.\n"
            "Responde únicamente:\n"
            "GOOGLE -> Si pide precios, clima, noticias de hoy, o datos que cambian cada segundo.\n"
            "LOCAL  -> Para todo lo demás (charla, comandos, preguntas generales).\n"
            "Solo una palabra. Sin explicaciones."
        )
        self._is_online = True
        self._last_check = 0
        self._check_interval = 60 # Reintentar cada 60 segundos si falló
        self.assistant_prompt = (
            "Eres NuviaIA, una asistente inteligente con una personalidad social avanzada. "
            "Eres amigable, perspicaz y tienes opiniones propias basadas en la lógica. "
            "Reglas de respuesta:\n"
            "1. Sé muy breve (máximo 3-4 frases).\n"
            "2. Si es una orden directa, ejecútala o confírmala.\n"
            "3. Si es charla casual, participa de forma natural.\n"
            "4. No interrumpas si no es necesario.\n"
            "5. Usa un tono cercano pero profesional."
        )
        self.intervention_prompt = (
            "Analiza la siguiente conversación entre humanos y decide si NuviaIA (la asistente) debería intervenir.\n"
            "Intervén solo si:\n"
            "- Se menciona a Nuvia o la nube.\n"
            "- Se hace una pregunta que Nuvia puede responder.\n"
            "- Hay un debate donde Nuvia puede aportar un dato objetivo o una opinión valiosa.\n\n"
            "Responde únicamente:\n"
            "SI -> Para intervenir.\n"
            "NO -> Para mantenerse en silencio.\n"
            "Solo una palabra."
        )
        self.search_prompt = (
            "Modelo en uso: mistral-7b ejecutándose localmente mediante Ollama.\n"
            "Eres NuviaIA.\n\n"
            "Debes generar la respuesta utilizando únicamente la información proporcionada abajo.\n\n"
            "Reglas:\n"
            "- No inventes datos.\n"
            "- No agregues información externa.\n"
            "- Resume y estructura claramente.\n"
            "- Sé directa y precisa."
        )
        self.memory_store_prompt = (
            "Analiza si el siguiente mensaje contiene información personal o preferencias del usuario que valga la pena recordar (nombres, gustos, datos biográficos, recordatorios).\n"
            "Responde únicamente:\n"
            "SI -> Si contiene información memorable.\n"
            "NO -> Si es charla trivial o una pregunta general.\n"
            "Solo una palabra."
        )

    def classify(self, user_input: str) -> str:
        """
        Envía el input a Ollama y retorna 'LOCAL' o 'GOOGLE'.
        """
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_input}
                ],
                "stream": False,
                "options": {
                    "temperature": 0.0,
                    "num_predict": 10
                }
            }
            decision = self._post_to_ollama(payload, "LOCAL")
            return "GOOGLE" if "GOOGLE" in decision.upper() else "LOCAL"
        except Exception:
            return "LOCAL"

    def should_intervene(self, conversation_text: str) -> bool:
        """
        Decide si Nuvia debe participar en una conversación de fondo.
        """
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": self.intervention_prompt},
                    {"role": "user", "content": conversation_text}
                ],
                "stream": False,
                "options": {
                    "temperature": 0.0,
                    "num_predict": 5
                }
            }
            decision = self._post_to_ollama(payload, "NO")
            return "SI" in decision.upper()
        except Exception:
            return False

    def should_remember(self, text: str) -> bool:
        """
        Decide si un texto contiene información importante para guardar.
        """
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": self.memory_store_prompt},
                    {"role": "user", "content": text}
                ],
                "stream": False,
                "options": {
                    "temperature": 0.0,
                    "num_predict": 5
                }
            }
            decision = self._post_to_ollama(payload, "NO")
            return "SI" in decision.upper()
        except Exception:
            return False

    def chat_response(self, user_input: str, context: str = "", history: list = None) -> str:
        """Genera una respuesta conversacional completa (bloqueante)."""
        messages = self._prepare_messages(user_input, context, history)
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.7, "num_predict": 150}
        }
        return self._post_to_ollama(payload, "No pude generar una respuesta.")

    def stream_chat_response(self, user_input: str, context: str = "", history: list = None):
        """Genera una respuesta conversacional en streaming (yield por frase)."""
        messages = self._prepare_messages(user_input, context, history)
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {"temperature": 0.7, "num_predict": 200}
        }
        
        sentence = ""
        try:
            # 60s de timeout para el primer chunk (carga de modelo)
            response = requests.post(self.base_url, json=payload, stream=True, timeout=60)
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    content = chunk.get("message", {}).get("content", "")
                    sentence += content
                    
                    if any(p in content for p in ['.', '!', '?', '\n']):
                        yield sentence.strip()
                        sentence = ""
            
            if sentence.strip():
                yield sentence.strip()
                
        except Exception as e:
            logger.error(f"Error en streaming Ollama: {e}")
            # No enviar mensaje de error por voz si falla el stream para no molestar
            yield ""

    def _prepare_messages(self, user_input: str, context: str = "", history: list = None):
        messages = [{"role": "system", "content": self.assistant_prompt}]
        if context: messages.append({"role": "system", "content": f"Contexto: {context}"})
        if history: messages.extend(history)
        # Siempre añadir el mensaje actual del usuario al final
        messages.append({"role": "user", "content": user_input})
        return messages

    def summarize_search(self, user_input: str, search_results: str) -> str:
        """
        Genera una respuesta basada en resultados de búsqueda.
        """
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.search_prompt},
                {"role": "user", "content": f"Pregunta: {user_input}\nResultados:\n{search_results}"}
            ],
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 300
            }
        }
        return self._post_to_ollama(payload, "No pude procesar los resultados de la búsqueda.")

    def _post_to_ollama(self, payload: dict, fallback: str) -> str:
        import time
        now = time.time()

        # Circuit Breaker: Si está offline, no intentamos hasta que pase el intervalo
        if not self._is_online:
            if now - self._last_check < self._check_interval:
                return fallback
            logger.info("Reintentando conexión con Ollama...")

        try:
            # 30s de timeout para clasificación también, Ollama puede ser lento cargando
            response = requests.post(self.base_url, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            message = result.get("message", {})
            content = message.get("content", "").strip()
            
            if not self._is_online:
                logger.info("Conexión con Ollama restaurada.")
                self._is_online = True
            
            return content or fallback
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if self._is_online:
                logger.warning(f"Ollama fuera de línea o lento (timeout 30s).")
                self._is_online = False
                self._last_check = now
            return fallback
        except Exception as e:
            logger.error(f"Error inesperado al conectar con Ollama: {e}")
            return fallback

if __name__ == "__main__":
    # Prueba básica
    client = OllamaClient()
    test_input = "¿Cuál es el precio del Bitcoin hoy?"
    print(f"Clasificación: {test_input} -> {client.classify(test_input)}")
    
    test_input2 = "Hola Nuvia, ¿quién eres?"
    print(f"Chat: {test_input2} -> {client.chat_response(test_input2)}")
