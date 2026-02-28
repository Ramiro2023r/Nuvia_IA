"""
ai/providers/gemini_provider.py — Implementación de Google Gemini.
"""

import logging
from typing import List, Dict, Generator
from google import genai
from .base_provider import BaseProvider

logger = logging.getLogger("GeminiProvider")

class GeminiProvider(BaseProvider):
    def __init__(self, api_key: str, variant: str = "gemini-flash-latest"):
        self.api_key = api_key
        self.variant = variant
        self.client = genai.Client(api_key=api_key)
        self.system_instruction = (
            "Eres Nuevi, la asistente IA personal de Ramiro. "
            "Responde de forma concisa, amigable y siempre en español. "
            "Máximo 3 oraciones si no te piden más detalle."
        )

    def _prepare_contents(self, prompt: str, history: List[Dict[str, str]]):
        # Convertir historial al formato de GenAI si es necesario
        # Por ahora simplificamos a prompt directo + instrucción de sistema
        return [prompt]

    def ask(self, prompt: str, history: List[Dict[str, str]] = None) -> str:
        try:
            response = self.client.models.generate_content(
                model=self.variant,
                contents=self._prepare_contents(prompt, history),
                config={'system_instruction': self.system_instruction}
            )
            return response.text
        except Exception as e:
            logger.error(f"Error en Gemini ask: {e}")
            return f"Error de conexión con Gemini: {str(e)}"

    def stream_ask(self, prompt: str, history: List[Dict[str, str]] = None) -> Generator[str, None, None]:
        try:
            response = self.client.models.generate_content_stream(
                model=self.variant,
                contents=self._prepare_contents(prompt, history),
                config={'system_instruction': self.system_instruction}
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
            logger.error(f"Error en Gemini stream: {e}")
            yield "No pude conectar con Gemini en este momento."

    def test_connection(self) -> (bool, str):
        try:
            # Una prueba mínima
            self.client.models.generate_content(
                model=self.variant,
                contents=["Hola"],
                config={'max_output_tokens': 5}
            )
            return True, "Conexión exitosa con Gemini."
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                return False, "Cuota de Gemini agotada (429). Prueba más tarde o usa otro modelo."
            if "404" in error_msg:
                return False, f"Modelo '{self.variant}' no encontrado (404). Contacta a soporte."
            return False, f"Fallo de Gemini: {error_msg}"
