"""
ai/memory.py — Sistema de memoria persistente para Nuvia
"""

import os
import json
import pathlib
from google import genai
from dotenv import load_dotenv

load_dotenv()

_API_KEY = os.getenv("GEMINI_API_KEY", "")
_MEMORY_FILE = pathlib.Path(__file__).parent.parent / "memory.json"

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
    memory = load_memory()
    if not memory:
        return None
        
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
        print(f"[Nuvia Memory Retrieval Error] {e}")
        return None
