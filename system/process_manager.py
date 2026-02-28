"""
system/process_manager.py — Gestión de procesos del sistema operativo
"""

import psutil
import logging

logger = logging.getLogger("NuviaSystem")

def close_app(app_name: str) -> bool:
    """
    Busca procesos que coincidan con app_name (parcial) y los cierra.
    Retorna True si encontró y cerró al menos uno, False de lo contrario.
    """
    if not app_name:
        return False

    name_lower = app_name.lower()
    closed_any = False

    logger.info(f"Intentando cerrar procesos que coincidan con: {app_name}")

    for proc in psutil.process_iter(['name', 'pid']):
        try:
            # Comprobar si el nombre del proceso coincide
            p_name = proc.info['name'].lower()
            if name_lower in p_name:
                logger.info(f"Cerrando proceso: {p_name} (PID: {proc.info['pid']})")
                proc.terminate() # Intento de cierre suave
                closed_any = True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            logger.error(f"Error al cerrar proceso {proc.info.get('name')}: {e}")
            continue

    return closed_any

if __name__ == "__main__":
    # Prueba rápida: Cierra el bloc de notas si está abierto
    res = close_app("notepad")
    print(f"Resultado: {res}")
