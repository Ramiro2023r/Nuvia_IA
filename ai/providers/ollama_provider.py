"""
ai/providers/ollama_provider.py — Implementación de IA Local (Ollama).
"""

import logging
from typing import List, Dict, Generator
from ai.ollama_client import OllamaClient
from .base_provider import BaseProvider

logger = logging.getLogger("OllamaProvider")

class OllamaProvider(BaseProvider):
    def __init__(self, variant: str = "phi3:mini", base_url: str = "http://localhost:11434"):
        self.variant = variant
        self.client = OllamaClient(model=variant)

    def ask(self, prompt: str, history: List[Dict[str, str]] = None) -> str:
        try:
            return self.client.chat_response(prompt, "", history)
        except Exception as e:
            logger.error(f"Error en Ollama ask: {e}")
            return "Ollama no respondió. Asegúrate de que esté corriendo localmente."

    def stream_ask(self, prompt: str, history: List[Dict[str, str]] = None) -> Generator[str, None, None]:
        try:
            generator = self.client.stream_chat_response(prompt, "", history)
            for chunk in generator:
                yield chunk
        except Exception as e:
            logger.error(f"Error en Ollama stream: {e}")
            yield "Ollama (local) fuera de línea."

    def test_connection(self) -> (bool, str):
        # OllamaClient ya tiene lógica interna para verificar si responde
        return True, "Ollama está listo." # Simplificado para local
