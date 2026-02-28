"""
ai/search_engine.py — Motor de búsqueda basado en Google Custom Search
"""

import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()

# Configuración de Logging
logger = logging.getLogger("SearchEngine")

class SearchEngine:
    """
    Gestiona búsquedas online usando Google Custom Search API.
    Diseñado para ser independiente y no bloqueante.
    """

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
        self.cx = os.getenv("GOOGLE_SEARCH_CX")
        self.enabled = bool(self.api_key and self.cx)
        
        if not self.enabled:
            logger.warning("SearchEngine desactivado: Faltan GOOGLE_SEARCH_API_KEY o GOOGLE_SEARCH_CX en .env")

    def search(self, query: str, num_results: int = 3) -> list:
        """
        Realiza una búsqueda y devuelve una lista de resultados.
        """
        if not self.enabled:
            return []

        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": self.api_key,
            "cx": self.cx,
            "q": query,
            "num": num_results
        }

        try:
            logger.info(f"Buscando en Google: {query}")
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = data.get("items", [])
            return results
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión en SearchEngine: {e}")
            return []
        except Exception as e:
            logger.error(f"Error inesperado en SearchEngine: {e}")
            return []

    def summarize_results(self, results: list) -> str:
        """
        Procesa los resultados para devolver un texto legible.
        """
        if not results:
            return "No encontré resultados relevantes en internet."

        summary = "He encontrado esto en internet:\n"
        for i, item in enumerate(results, 1):
            title = item.get("title")
            snippet = item.get("snippet")
            summary += f"{i}. {title}: {snippet}\n"
            
        return summary

if __name__ == "__main__":
    # Prueba rápida
    engine = SearchEngine()
    if engine.enabled:
        res = engine.search("clima en Lima hoy")
        print(engine.summarize_results(res))
    else:
        print("SearchEngine no configurado.")
