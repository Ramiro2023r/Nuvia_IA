import os
import pathlib
import json
import time
from ai.ollama_client import OllamaClient
from google import genai
from dotenv import load_dotenv

load_dotenv()

_API_KEY = os.getenv("GEMINI_API_KEY", "")
_MEMORY_FILE = pathlib.Path(__file__).parent.parent / "memory.json"
_LAST_QUOTA_ERROR = 0
_QUOTA_COOLDOWN = 300 # 5 minutos de espera si hay 429
_ollama = None

def _get_ollama():
    global _ollama
    if _ollama is None:
        _ollama = OllamaClient()
    return _ollama

_STORE_PROMPT = """
Eres el módulo de memoria persistente del asistente Nuvia.
Tu tarea es analizar el mensaje del usuario y determinar si contiene información importante que deba guardarse en memoria a largo plazo.
Debes responder EXCLUSIVAMENTE con un JSON válido. No agregues texto, explicación ni markdown.

Tipos de memoria permitidos:
1. preference → gustos o preferencias del usuario.
2. personal_info → información personal relevante.
3. project_info → información sobre proyectos.
4. reminder_info → datos que podrían servir como recordatorio futuro.
5. none → si el mensaje no contiene información que deba guardarse.

Formato de salida obligatorio:
{
  "store": true o false,
  "type": "preference | personal_info | project_info | reminder_info | none",
  "key": "clave_corta_en_snake_case",
  "value": "información limpia y resumida"
}
"""

_RETRIEVE_PROMPT = """
Eres el módulo de recuperación de memoria de Nuvia.
Tienes acceso a la siguiente memoria almacenada en formato JSON:
{memory_context}

El usuario pregunta: "{user_question}"
Responde de forma natural y breve basándote en la memoria.
Si no existe información relevante, responde exactamente: "NO_DATA".
"""

_client = None

def _get_client():
    global _client
    if _client is None:
        if not _API_KEY:
            raise ValueError("GEMINI_API_KEY no detectada")
        _client = genai.Client(api_key=_API_KEY)
    return _client

def load_memory() -> dict:
    if not _MEMORY_FILE.exists():
        return {}
    try:
        return json.loads(_MEMORY_FILE.read_text(encoding="utf-8"))
    except:
        return {}

def save_memory(memory_data: dict):
    _MEMORY_FILE.write_text(json.dumps(memory_data, indent=2, ensure_ascii=False), encoding="utf-8")

def process_memory_storage(text: str):
    """Analiza si el texto contiene algo que recordar y lo guarda."""
    global _LAST_QUOTA_ERROR
    
    # 1. Filtro local ultra-rápido: solo procesar si contiene palabras clave de "memoria"
    keywords = ["recuerda", "guarda", "anota", "mi nombre es", "vivo en", "me gusta", "no olvides"]
    if not any(k in text.lower() for k in keywords):
        return

    # 2. Refinamiento en Fase 3: Delegar a Ollama local la decisión final
    # Solo molestamos a Gemini si Ollama cree que es algo importante.
    ollama = _get_ollama()
    if not ollama.should_remember(text):
        return

    # 3. Circuit Breaker para Cuota de Google
    if time.time() - _LAST_QUOTA_ERROR < _QUOTA_COOLDOWN:
        return

    try:
        client = _get_client()
        response = client.models.generate_content(
            model="models/gemini-flash-latest",
            contents=f"{_STORE_PROMPT}\n\nEntrada: '{text}'"
        )
        
        raw_text = response.text.strip()
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[-1].split("```")[0].strip()
            
        data = json.loads(raw_text)
        
        if data.get("store"):
            memory = load_memory()
            m_type = data.get("type", "general")
            if m_type not in memory:
                memory[m_type] = {}
            
            memory[m_type][data["key"]] = data["value"]
            save_memory(memory)
            print(f"[Nuvia Memory] Guardado: {data['key']} = {data['value']}")
            
    except Exception as e:
        print(f"[Nuvia Memory Storage Error] {e}")

def query_memory(question: str) -> str | None:
    """Busca en la memoria local si hay respuesta para la pregunta."""
    global _LAST_QUOTA_ERROR
    
    # 1. Filtro local estructural: Si la pregunta no parece informativa, no molestar a Gemini
    q_low = question.lower()
    retrieval_triggers = ["quién", "quien", "qué", "que", "cuál", "cuanto", "cuánto", 
                          "dónde", "donde", "sabes", "conoces", "recuerdas", "cuéntame", 
                          "cuentame", "dime", "info"]
    if not any(t in q_low for t in retrieval_triggers):
        return None

    # 2. Circuit Breaker
    if time.time() - _LAST_QUOTA_ERROR < _QUOTA_COOLDOWN:
        return None

    memory = load_memory()
    if not memory:
        return None
        
    # 3. Hit local por keywords (Fase 3: Búsqueda ultra-rápida)
    for m_type, content in memory.items():
        for key, value in content.items():
            clean_key = key.replace("_", " ")
            if clean_key in q_low:
                print(f"[Nuvia Memory] Hit local por keyword: {key}")
                return value

    # 3. Si no hay hit exacto, intentamos con Gemini (si no está bloqueado)
    try:
        client = _get_client()
        context = json.dumps(memory, ensure_ascii=False)
        prompt = _RETRIEVE_PROMPT.format(memory_context=context, user_question=question)
        
        response = client.models.generate_content(
            model="models/gemini-flash-latest",
            contents=prompt
        )


        answer = response.text.strip()
        
        if "NO_DATA" in answer:
            return None
        
        return answer
    except Exception as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            print("[Nuvia Memory] Cuota de Gemini agotada. Entrando en cooldown.")
            _LAST_QUOTA_ERROR = time.time()
        else:
            print(f"[Nuvia Memory Retrieval Error] {e}")
        return None
