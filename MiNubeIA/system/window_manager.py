"""
system/window_manager.py — Gestión de ventanas del sistema operativo
"""

import pygetwindow as gw
import logging

logger = logging.getLogger("NuviaSystem")

def get_active_window_title() -> str:
    """Retorna el título de la ventana activa."""
    try:
        active = gw.getActiveWindow()
        return active.title if active else "Escritorio"
    except Exception as e:
        logger.error(f"Error obteniendo ventana activa: {e}")
        return "Desconocido"

def minimize_window(app_name: str) -> bool:
    """Minimiza la primera ventana que coincida con app_name."""
    try:
        windows = gw.getWindowsWithTitle(app_name)
        if windows:
            windows[0].minimize()
            logger.info(f"Ventana '{app_name}' minimizada.")
            return True
        return False
    except Exception as e:
        logger.error(f"Error minimizando ventana: {e}")
        return False

def maximize_window(app_name: str) -> bool:
    """Maximiza la primera ventana que coincida con app_name."""
    try:
        windows = gw.getWindowsWithTitle(app_name)
        if windows:
            windows[0].maximize()
            logger.info(f"Ventana '{app_name}' maximizada.")
            return True
        return False
    except Exception as e:
        logger.error(f"Error maximizando ventana: {e}")
        return False

def switch_to_window(app_name: str) -> bool:
    """Cambia el foco a la primera ventana que coincida con app_name."""
    try:
        windows = gw.getWindowsWithTitle(app_name)
        if windows:
            windows[0].activate()
            logger.info(f"Cambiado foco a ventana: '{app_name}'")
            return True
        return False
    except Exception as e:
        logger.error(f"Error cambiando a ventana: {e}")
        return False

if __name__ == "__main__":
    # Prueba rápida
    print(f"Activa: {get_active_window_title()}")
