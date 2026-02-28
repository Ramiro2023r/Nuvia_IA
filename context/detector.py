"""
context/detector.py — Detecta la aplicación y ventana activa en Windows
"""

import time
from datetime import datetime
import psutil
import win32gui
import win32process
import logging

logger = logging.getLogger("NuviaContext")

class ActiveWindowDetector:
    """
    Clase para obtener información sobre la ventana y proceso actualmente en foco.
    """

    @staticmethod
    def get_current_context() -> dict:
        """
        Retorna un diccionario con el nombre de la app, el título de la ventana y el proceso.
        """
        try:
            # Obtener el handle de la ventana activa
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return {}

            # Obtener el título de la ventana
            window_title = win32gui.GetWindowText(hwnd)

            # Obtener el PID del proceso
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            # Obtener info del proceso usando psutil
            process = psutil.Process(pid)
            process_name = process.name()
            # A veces el nombre de la app es más amigable si quitamos el .exe
            app_name = process_name.replace(".exe", "").capitalize()

            return {
                "app_name": app_name,
                "window_title": window_title,
                "process_name": process_name,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error detectando contexto: {e}")
            return {
                "app_name": "Desconocido",
                "window_title": "Sin título",
                "process_name": "N/A",
                "timestamp": datetime.now().isoformat()
            }

if __name__ == "__main__":
    # Prueba rápida
    detector = ActiveWindowDetector()
    while True:
        print(detector.get_current_context())
        time.sleep(2)
