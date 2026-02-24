"""
main.py — Punto de entrada de Nuvia (Versión Tkinter)
Asistente IA de escritorio para Windows.
"""

import sys
import threading
import time
from core.orchestrator import Orchestrator
from voice.speak import speak

def main():
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
