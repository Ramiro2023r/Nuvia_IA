"""
system/system_controller.py — Controlador maestro para acciones del sistema operativo (Offline)
"""

import os
import subprocess
import psutil
import pyautogui
import pygetwindow as gw
import shutil
import ctypes
import logging
from datetime import datetime

# Configuración básica de logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler("nuvia_system.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SystemController")

class SystemController:
    """
    Clase principal para gestionar el sistema operativo Windows.
    Diseñada para ser segura, escalable y 100% offline.
    """

    def __init__(self):
        logger.info("SystemController inicializado.")

    # 1. Gestión de Aplicaciones
    def open_app(self, app_path: str) -> bool:
        """Abre una aplicación usando subprocess de forma segura."""
        try:
            logger.info(f"Intentando abrir: {app_path}")
            # Sanitización: solo permitir nombres alfanuméricos, rutas y caracteres seguros
            import re
            if not re.match(r'^[\w\s\-./\\:()]+$', app_path):
                logger.warning(f"Input inseguro rechazado: {app_path}")
                return False
            # Usar shell=False + os.startfile para mayor seguridad
            os.startfile(app_path)
            return True
        except Exception as e:
            logger.error(f"Error al abrir app {app_path}: {e}")
            return False

    def close_app(self, app_name: str) -> bool:
        """Cierra aplicaciones por nombre usando psutil."""
        try:
            logger.info(f"Buscando procesos que coincidan con: {app_name}")
            closed_any = False
            name_lower = app_name.lower()
            
            for proc in psutil.process_iter(['name', 'pid']):
                try:
                    if name_lower in proc.info['name'].lower():
                        logger.info(f"Terminando proceso: {proc.info['name']} (PID: {proc.info['pid']})")
                        proc.terminate()
                        closed_any = True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return closed_any
        except Exception as e:
            logger.error(f"Error al cerrar app {app_name}: {e}")
            return False

    # 2. Control del Sistema
    def shutdown(self):
        """Apagar el sistema después de 1 segundo."""
        logger.warning("Iniciando apagado del sistema.")
        os.system("shutdown /s /t 1")

    def restart(self):
        """Reiniciar el sistema después de 1 segundo."""
        logger.warning("Iniciando reinicio del sistema.")
        os.system("shutdown /r /t 1")

    # 3. Control de Volumen
    def set_volume(self, action: str):
        """
        Controla el volumen usando pyautogui (teclas de hardware virtualizadas).
        action: 'up', 'down', 'mute'
        """
        try:
            if action == 'up':
                pyautogui.press('volumeup')
                logger.info("Volumen aumentado.")
            elif action == 'down':
                pyautogui.press('volumedown')
                logger.info("Volumen disminuido.")
            elif action == 'mute':
                pyautogui.press('volumemute')
                logger.info("Silencio activado/desactivado.")
            return True
        except Exception as e:
            logger.error(f"Error controlando volumen ({action}): {e}")
            return False

    # 4. Gestión de Ventanas
    def manage_window(self, title: str, action: str) -> bool:
        """
        Minimizar, maximizar o enfocar ventanas.
        action: 'minimize', 'maximize', 'focus'
        """
        try:
            windows = gw.getWindowsWithTitle(title)
            if not windows:
                logger.warning(f"No se encontró ninguna ventana con título: {title}")
                return False
            
            win = windows[0]
            if action == 'minimize':
                win.minimize()
            elif action == 'maximize':
                win.maximize()
            elif action == 'focus':
                win.activate()
            
            logger.info(f"Acción '{action}' ejecutada en ventana: {title}")
            return True
        except Exception as e:
            logger.error(f"Error gestionando ventana '{title}' ({action}): {e}")
            return False

    # 5. Gestión de Archivos
    def create_file(self, path: str, content: str = "") -> bool:
        """Crea un archivo con contenido opcional."""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Archivo creado: {path}")
            return True
        except Exception as e:
            logger.error(f"Error creando archivo {path}: {e}")
            return False

    def move_file(self, src: str, dst: str) -> bool:
        """Mueve o renombra un archivo/directorio."""
        try:
            shutil.move(src, dst)
            logger.info(f"Movido de {src} a {dst}")
            return True
        except Exception as e:
            logger.error(f"Error moviendo {src} a {dst}: {e}")
            return False

    def delete_file(self, path: str) -> bool:
        """Elimina un archivo o directorio de forma permanente."""
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            logger.info(f"Eliminado: {path}")
            return True
        except Exception as e:
            logger.error(f"Error eliminando {path}: {e}")
            return False

    # 6. Información del Sistema
    def get_system_stats(self) -> dict:
        """Obtiene información de CPU y RAM."""
        try:
            stats = {
                "cpu_usage": f"{psutil.cpu_percent()}%",
                "ram_usage": f"{psutil.virtual_memory().percent}%",
                "ram_total": f"{round(psutil.virtual_memory().total / (1024**3), 2)} GB",
                "timestamp": datetime.now().isoformat()
            }
            logger.info(f"Stats obtenidas: {stats}")
            return stats
        except Exception as e:
            logger.error(f"Error obteniendo stats del sistema: {e}")
            return {}

if __name__ == "__main__":
    # Prueba básica si se ejecuta directamente
    ctrl = SystemController()
    print("--- Stats del Sistema ---")
    print(ctrl.get_system_stats())
