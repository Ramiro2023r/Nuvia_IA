"""
ai/providers/base_provider.py — Interfaz base para todos los proveedores de IA.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Generator, Optional

class BaseProvider(ABC):
    """
    Clase abstracta que define el contrato para cualquier motor de IA en Nuvia.
    """
    
    @abstractmethod
    def ask(self, prompt: str, history: List[Dict[str, str]] = None) -> str:
        """Respuesta completa (síncrona/esperada)."""
        pass

    @abstractmethod
    def stream_ask(self, prompt: str, history: List[Dict[str, str]] = None) -> Generator[str, None, None]:
        """Respuesta en streaming por frases."""
        pass

    @abstractmethod
    def test_connection(self) -> (bool, str):
        """Prueba si las credenciales son válidas."""
        pass
