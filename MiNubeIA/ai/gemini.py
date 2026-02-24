"""
ai/gemini.py — Integración con Google Gemini + generación de imágenes (pollinations.ai)
"""

import os
import pathlib
import requests
import urllib.parse
from datetime import datetime

from google import genai
from dotenv import load_dotenv

load_dotenv()

# ── Configuración Gemini ──────────────────────────────────────────────────────
_API_KEY = os.getenv("GEMINI_API_KEY", "")

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
    """
    Envía una pregunta a Gemini (opcionalmente con una imagen) y retorna la respuesta.
    """
    try:
        client = _get_client()
        contents = [prompt]
        
        if image_path and os.path.exists(image_path):
            with open(image_path, "rb") as f:
                image_data = f.read()
                # El SDK espera un objeto Part o bytes estructurados para imagenes
                from google.genai import types
                contents.append(types.Part.from_bytes(data=image_data, mime_type="image/png"))

        response = client.models.generate_content(
            model="models/gemini-flash-latest",
            contents=contents,
            config={'system_instruction': _SYSTEM_PROMPT}
        )
        return response.text.strip()
    except Exception as e:
        print(f"[Nuvia Gemini ERROR]: {e}")
        return "Lo siento Ramiro, hubo un problema al procesar esa información visual."



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
