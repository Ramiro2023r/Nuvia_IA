"""
ai/gemini.py — Integración con Google Gemini + generación de imágenes (pollinations.ai)
"""

import os
import pathlib
import requests
import urllib.parse
from datetime import datetime
import json
import logging
import time

from google import genai
from dotenv import load_dotenv

load_dotenv()

# ── Configuración Gemini ──────────────────────────────────────────────────────
_API_KEY = os.getenv("GEMINI_API_KEY", "")
_LAST_QUOTA_ERROR = 0
_QUOTA_COOLDOWN = 300 # 5 min

_SYSTEM_PROMPT = (
    "Eres Nuevi, la asistente IA personal de Ramiro. "
    "Responde de forma concisa, amigable y siempre en español. "
    "Máximo 3 oraciones si no te piden más detalle."
)

_client = None

def _get_client():
    global _client
    if _client is None:
        if not _API_KEY:
            raise ValueError("GEMINI_API_KEY no está configurada en el archivo .env")
        # El nuevo cliente de Google GenAI
        _client = genai.Client(api_key=_API_KEY)
    return _client


def ask(prompt: str, image_path: str = None) -> str:
    """Envía una pregunta a Gemini y retorna la respuesta completa. Soporta imágenes."""
    try:
        client = _get_client()
        contents = [prompt]
        
        # Soporte multimodal: enviar imagen si existe
        if image_path:
            img_path = pathlib.Path(image_path)
            if img_path.exists():
                try:
                    img_data = img_path.read_bytes()
                    # Determinar mime type
                    suffix = img_path.suffix.lower()
                    mime_map = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp'}
                    mime_type = mime_map.get(suffix, 'image/png')
                    contents = [
                        prompt,
                        {"mime_type": mime_type, "data": img_data}
                    ]
                except Exception as img_err:
                    logging.getLogger("Gemini").warning(f"No se pudo cargar la imagen: {img_err}")
        
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=contents,
            config={'system_instruction': _SYSTEM_PROMPT}
        )
        return response.text
    except Exception as e:
        return _handle_gemini_error(e)

def stream_ask(prompt: str):
    """Streaming de Gemini por frases."""
    try:
        client = _get_client()
        response = client.models.generate_content_stream(
            model="gemini-1.5-flash",
            contents=[prompt],
            config={'system_instruction': _SYSTEM_PROMPT}
        )
        
        sentence = ""
        for chunk in response:
            text = chunk.text
            sentence += text
            if any(p in text for p in ['.', '!', '?', '\n']):
                yield sentence.strip()
                sentence = ""
        if sentence.strip():
            yield sentence.strip()
            
    except Exception as e:
        yield _handle_gemini_error(e)

def _handle_gemini_error(e):
    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
        return "He agotado mi cuota de Google, pero puedo seguir por local."
    return "No pude conectar con la nube."



# ── Generación de imágenes (pollinations.ai — gratuito, sin key) ──────────────
_IMAGES_DIR = pathlib.Path(__file__).parent.parent / "assets" / "generated"

def generate_image(prompt: str) -> pathlib.Path | None:
    """
    Genera una imagen usando pollinations.ai.
    Retorna el path local del archivo guardado, o None si falla.
    """
    _IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=512&height=512&nologo=true"

    try:
        print(f"[Nuvia IMG] Generando imagen: {prompt}")
        response = requests.get(url, timeout=60)
        response.raise_for_status()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = _IMAGES_DIR / f"nuvia_{timestamp}.jpg"
        filename.write_bytes(response.content)
        print(f"[Nuvia IMG] Imagen guardada en {filename}")
        return filename

    except Exception as e:
        print(f"[Nuvia IMG] Error generando imagen: {e}")
        return None
