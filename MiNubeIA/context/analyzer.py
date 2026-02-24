"""
context/analyzer.py — Analiza el contexto activo y toma capturas si es necesario
"""

import os
import pathlib
import logging
from mss import mss
from datetime import datetime

logger = logging.getLogger("NuviaContext")

# Carpeta para capturas efímeras
CONTEXT_ASSETS = pathlib.Path(__file__).parent.parent / "assets" / "context"

class ContextAnalyzer:
    """
    Recibe el contexto del detector y realiza acciones adicionales como screenshots.
    """

    def __init__(self):
        # Aplicaciones que disparan una captura de pantalla para dar más contexto visual
        self.creative_apps = [
            "Code", "Photoshop", "Premiere", "AfterFX", "Illustrator", 
            "Figma", "Blender", "Unity", "Unrealeditor", "Cursor",
            "Chrome", "Edge" # Añadimos navegadores por utilidad
        ]
        
        CONTEXT_ASSETS.mkdir(parents=True, exist_ok=True)

    def analyze(self, context_data: dict) -> dict:
        """
        Analiza los datos del detector y añade captura de pantalla si la app es relevante.
        """
        if not context_data:
            return {"summary": "No hay una ventana activa detectada."}

        app_name = context_data.get("app_name", "")
        window_title = context_data.get("window_title", "")
        
        result = {
            "app_name": app_name,
            "window_title": window_title,
            "has_screenshot": False,
            "screenshot_path": None,
            "summary": f"El usuario está usando {app_name} en la ventana '{window_title}'."
        }

        # Comprobar si debemos tomar captura
        if any(creative in app_name for creative in self.creative_apps):
            screenshot_path = self._take_screenshot()
            if screenshot_path:
                result["has_screenshot"] = True
                result["screenshot_path"] = screenshot_path
                result["summary"] += " He tomado una captura de pantalla para analizar el contenido visualmente."

        return result

    def _take_screenshot(self) -> str | None:
        """Toma captura de la pantalla principal."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = CONTEXT_ASSETS / f"ctx_{timestamp}.png"
            
            with mss() as sct:
                # Captura la pantalla 1
                sct.shot(output=str(filename))
                
            logger.info(f"Captura de contexto guardada: {filename}")
            return str(filename)
        except Exception as e:
            logger.error(f"Error al tomar captura: {e}")
            return None

    def clean_old_screenshots(self, max_files=10):
        """Mantiene la carpeta limpia eliminando capturas viejas."""
        files = sorted(CONTEXT_ASSETS.glob("ctx_*.png"), key=os.path.getmtime)
        while len(files) > max_files:
            try:
                os.remove(files.pop(0))
            except:
                pass

    def generate_context_suggestions(self, context_data: dict, screenshot_path: str = None) -> dict:
        """
        Genera sugerencias inteligentes basadas en la app activa usando Gemini.
        """
        import json
        from ai.gemini import ask

        app_name = context_data.get("app_name", "")
        window_title = context_data.get("window_title", "")
        
        # Determinar el rol del experto
        role = "Asistente experto"
        if "Code" in app_name or "Cursor" in app_name:
            role = "Senior Software Developer"
        elif "Premiere" in app_name or "AfterFX" in app_name:
            role = "Editor de Video Profesional"
        elif any(x in app_name for x in ["Photoshop", "Illustrator", "Figma"]):
            role = "Diseñador Gráfico y de UI/UX experto"

        prompt = f"""
        Actúa como un {role}.
        Estás observando el espacio de trabajo del usuario en la aplicación: {app_name}.
        Título de la ventana: {window_title}.
        
        Si hay una imagen adjunta, analízala para dar sugerencias específicas sobre el contenido o código.
        
        Responde exclusivamente en formato JSON con la siguiente estructura:
        {{
          "mode": "{role}",
          "suggestions": "Un párrafo breve con 2-3 sugerencias útiles para lo que está haciendo el usuario.",
          "priority_actions": ["Acción 1", "Acción 2"]
        }}
        """

        try:
            # Llamada multimodal a Gemini
            raw_response = ask(prompt, image_path=screenshot_path)
            
            # Limpieza básica de JSON si Gemini incluye markdown
            clean_json = raw_response.strip()
            if "```json" in clean_json:
                clean_json = clean_json.split("```json")[1].split("```")[0].strip()
            
            return json.loads(clean_json)
        except Exception as e:
            logger.error(f"Error generando sugerencias contextuales: {e}")
            return {
                "mode": role,
                "suggestions": "No pude analizar tu pantalla en este momento, pero parece que estás concentrado en tu trabajo.",
                "priority_actions": []
            }

if __name__ == "__main__":
    # Prueba rápida
    analyzer = ContextAnalyzer()
    print(analyzer.analyze({"app_name": "Code", "window_title": "analyzer.py - MiNubeIA"}))
