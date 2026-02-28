"""
ai/providers/grok_provider.py — Implementación de Grok (xAI).
Usa la interfaz compatible con OpenAI.
"""

import logging
from typing import List, Dict, Generator
from openai import OpenAI
from .base_provider import BaseProvider

logger = logging.getLogger("GrokProvider")

class GrokProvider(BaseProvider):
    def __init__(self, api_key: str, variant: str = "grok-2"):
        self.api_key = api_key
        self.variant = variant
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.x.ai/v1"
        )
        self.system_prompt = "Eres Nuevi, la asistente IA personal de Ramiro. Responde de forma concisa y en español."

    def _build_messages(self, prompt: str, history: List[Dict[str, str]]):
        messages = [{"role": "system", "content": self.system_prompt}]
        if history:
            for msg in history:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": prompt})
        return messages

    def ask(self, prompt: str, history: List[Dict[str, str]] = None) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.variant,
                messages=self._build_messages(prompt, history)
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error en Grok ask: {e}")
            return f"Error con Grok (xAI): {str(e)}"

    def stream_ask(self, prompt: str, history: List[Dict[str, str]] = None) -> Generator[str, None, None]:
        try:
            stream = self.client.chat.completions.create(
                model=self.variant,
                messages=self._build_messages(prompt, history),
                stream=True
            )
            sentence = ""
            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    sentence += content
                    if any(p in content for p in ['.', '!', '?', '\n']):
                        yield sentence.strip()
                        sentence = ""
            if sentence.strip():
                yield sentence.strip()
        except Exception as e:
            yield "Conexión fallida con Grok."

    def test_connection(self) -> (bool, str):
        try:
            self.client.models.list()
            return True, "Conexión exitosa con Grok (xAI)."
        except Exception as e:
            return False, f"Fallo de Grok: {str(e)}"
