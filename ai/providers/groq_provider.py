"""
ai/providers/groq_provider.py — Implementación de Groq (Llama/Mixtral).
"""

import logging
from typing import List, Dict, Generator
from groq import Groq
from .base_provider import BaseProvider

logger = logging.getLogger("GroqProvider")

class GroqProvider(BaseProvider):
    def __init__(self, api_key: str, variant: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key
        self.variant = variant
        self.client = Groq(api_key=api_key)
        self.system_prompt = "Eres Nuevi, la asistente IA personal de Ramiro. Responde de forma concisa y en español."

    def _build_messages(self, prompt: str, history: List[Dict[str, str]]):
        messages = [{"role": "system", "content": self.system_prompt}]
        # ... lógica de mensajes similar a OpenAI
        messages.append({"role": "user", "content": prompt})
        return messages

    def ask(self, prompt: str, history: List[Dict[str, str]] = None) -> str:
        try:
            completion = self.client.chat.completions.create(
                model=self.variant,
                messages=self._build_messages(prompt, history)
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Error en Groq ask: {e}")
            return f"Error con Groq: {str(e)}"

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
            yield "Conexión fallida con Groq."

    def test_connection(self) -> (bool, str):
        try:
            self.client.models.list()
            return True, "Conexión exitosa con Groq."
        except Exception as e:
            return False, str(e)
