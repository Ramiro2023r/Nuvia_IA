"""
ai/classifier.py — Clasificador de intenciones usando Google Gemini
"""

import os
import json
import time
from google import genai
from dotenv import load_dotenv

load_dotenv()

_API_KEY = os.getenv("GEMINI_API_KEY", "")
_LAST_QUOTA_ERROR = 0
_QUOTA_COOLDOWN = 300 # 5 minutos

_SYSTEM_INSTRUCTIONS = """
Eres el motor de clasificación de intención de Nuevi.
Analiza el mensaje y devuelve EXCLUSIVAMENTE un JSON válido con esta estructura:
{
  "intent": "nombre_intencion",
  "parameters": { "param1": "valor1", ... }
}

Intenciones y sus parámetros:
1. open_app: { "app": "nombre" }
2. close_app: { "app": "nombre" }
3. send_whatsapp: { "number": "ej: 34600112233", "message": "texto" }
4. generate_image: { "prompt": "descripción visual" }
5. remember: { "info": "información a guardar" }
6. recall: { "query": "búsqueda en memoria" }
7. suggest_context: { "action": "analyze" }
8. system_control: { "action": "shutdown/restart/cancel_shutdown" }
9. change_voice: { "voice_request": "descripción de la voz deseada" }
10. show_chat: { "action": "show" }
11. hide_chat: { "action": "hide" }
12. general_chat: { "message": "texto del usuario" }

Reglas:
- No incluyas texto extra ni markdown.
- Si no estás seguro, usa 'general_chat'.
- Para WhatsApp, extrae el número si se menciona.
- Usa 'change_voice' cuando el usuario pida cambiar voz, acento o idioma.
  Frases comunes: "habla como", "habla en", "cambia tu voz", "pon voz de",
  "habla con acento", "cambia idioma", "habla diferente".
  En voice_request pon la parte descriptiva (ej: "argentino", "japonés").
- Usa 'show_chat' cuando pidan abrir/mostrar el chat o teclado.
  Frases: "muestra el chat", "abre el chat", "quiero escribirte",
  "muéstrame el chat", "abre el teclado".
- Usa 'hide_chat' cuando pidan cerrar/ocultar el chat.
  Frases: "cierra el chat", "oculta el chat", "esconde el chat".
"""

_client = None

def _get_client():
    global _client
    if _client is None:
        if not _API_KEY:
            raise ValueError("GEMINI_API_KEY no detectada")
        _client = genai.Client(api_key=_API_KEY)
    return _client

def classify_intent(text: str) -> dict:
    """
    Envía el texto a Gemini para clasificar la intención.
    Retorna un diccionario con la estructura JSON definida.
    """
    global _LAST_QUOTA_ERROR
    
    # 1. Circuit Breaker
    if time.time() - _LAST_QUOTA_ERROR < _QUOTA_COOLDOWN:
        return {"intent": "general_chat", "parameters": {"message": text}}

    try:
        client = _get_client()
        response = client.models.generate_content(
            model="models/gemini-flash-latest",
            contents=text,
            config={'system_instruction': _SYSTEM_INSTRUCTIONS}
        )
        
        # Limpiar posible basura o markdown si Gemini lo ignora
        raw_text = response.text.strip()
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[-1].split("```")[0].strip()
        elif raw_text.startswith("```"):
             raw_text = raw_text.replace("```", "").strip()
        
        return json.loads(raw_text)
    except Exception as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            print("[Nuvia Classifier] Cuota agotada. Activando cooldown.")
            _LAST_QUOTA_ERROR = time.time()
        else:
            print(f"[Nuvia Classifier] Error: {e}")
        # Fallback seguro con nueva estructura
        return {
            "intent": "general_chat",
            "parameters": { "message": text }
        }
