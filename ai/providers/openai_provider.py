"""
ai/providers/openai_provider.py — Implementación de OpenAI (GPT).
"""

import logging
from typing import List, Dict, Generator
from openai import OpenAI
from .base_provider import BaseProvider

logger = logging.getLogger("OpenAIProvider")

class OpenAIProvider(BaseProvider):
    def __init__(self, api_key: str, variant: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.variant = variant
        self.client = OpenAI(api_key=api_key)
        self.system_prompt = {
            "role": "system",
            "content": "Eres Nuevi, la asistente IA personal de Ramiro. Responde de forma concisa, amigable y siempre en español. Máximo 3 oraciones si no te piden más detalle."
        }

    def _build_messages(self, prompt: str, history: List[Dict[str, str]]):
        messages = [self.system_prompt]
        if history:
            # OpenAI usa role: user/assistant
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
            logger.error(f"Error en OpenAI ask: {e}")
            return f"Error con OpenAI: {str(e)}"

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
            logger.error(f"Error en OpenAI stream: {e}")
            yield "Error en la conexión con OpenAI."

    def test_connection(self) -> (bool, str):
        try:
            self.client.models.list() # Prueba mínima de API key
            return True, "Conexión exitosa con OpenAI."
        except Exception as e:
            return False, f"Fallo de OpenAI: {str(e)}"
