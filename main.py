"""
main.py — Punto de entrada de Nuvia (Versión Tkinter)
Asistente IA de escritorio para Windows.
"""

import sys
import threading
import time
import os
import psutil
import atexit
from core.orchestrator import Orchestrator
from voice.speak import speak
import multiprocessing

LOCK_FILE = "nuvia.lock"

def check_single_instance():
    """Evita múltiples instancias de Nuvia ejecutándose al mismo tiempo."""
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "r") as f:
                pid = int(f.read().strip())
            if psutil.pid_exists(pid):
                proc = psutil.Process(pid)
                if "python" in proc.name().lower() or "nuvia" in proc.name().lower():
                    print(f"[Nuvia] Ya hay una instancia ejecutándose (PID {pid}).")
                    sys.exit(0)
        except psutil.NoSuchProcess:
            pass
        except Exception as e:
            print(f"[Nuvia] Advertencia al verificar instancia previa: {e}")
    
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))

def cleanup_lock():
    """Limpia el archivo de bloqueo al cerrar."""
    if os.path.exists(LOCK_FILE):
        try:
            os.remove(LOCK_FILE)
        except Exception as e:
            print(f"[Nuvia] Error al eliminar lock: {e}")

def main():
    multiprocessing.freeze_support()
    check_single_instance()
    atexit.register(cleanup_lock)
    print("[Nuvia] Iniciando sistema...")
    
    try:
        # 1. Crear el Orquestador
        # El constructor se encarga de inicializar todos los módulos internos
        orchestrator = Orchestrator()

        # 2. Saludo inicial
        orchestrator.say_greeting()
        
        # 3. Iniciar bucle principal
        # NOTA: Este método bloquea el hilo principal porque inicia webview.start()
        orchestrator.start()

    except Exception as e:
        print(f"[Nuvia] Error fatal durante el arranque: {e}")
        sys.exit(1)
    finally:
        print("[Nuvia] Proceso finalizado.")

if __name__ == "__main__":
    main()
