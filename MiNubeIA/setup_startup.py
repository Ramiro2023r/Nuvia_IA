"""
setup_startup.py — Agrega Nuvia al inicio de Windows
Ejecuta este script UNA SOLA VEZ con: python setup_startup.py
"""

import os
import pathlib
import sys

def setup():
    startup_folder = pathlib.Path(os.environ["APPDATA"]) / \
        "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"

    project_dir = pathlib.Path(__file__).parent.resolve()
    python_exe  = pathlib.Path(sys.executable)
    # Usar pythonw.exe para no mostrar ventana de consola
    pythonw = python_exe.parent / "pythonw.exe"
    if not pythonw.exists():
        pythonw = python_exe  # fallback

    bat_content = f'@echo off\n"{pythonw}" "{project_dir / "main.py"}"\n'
    bat_path = startup_folder / "Nuvia.bat"

    try:
        bat_path.write_text(bat_content, encoding="utf-8")
        print(f"✅ Nuvia agregada al inicio de Windows.")
        print(f"   Archivo: {bat_path}")
        print(f"   Nuvia se iniciará automáticamente en el siguiente arranque.")
    except Exception as e:
        print(f"❌ Error al crear el acceso directo: {e}")
        print("   Intenta ejecutar este script como Administrador.")

def remove():
    startup_folder = pathlib.Path(os.environ["APPDATA"]) / \
        "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    bat_path = startup_folder / "Nuvia.bat"
    if bat_path.exists():
        bat_path.unlink()
        print("✅ Nuvia eliminada del inicio de Windows.")
    else:
        print("ℹ️  Nuvia no estaba en el inicio de Windows.")

if __name__ == "__main__":
    if "--remove" in sys.argv:
        remove()
    else:
        setup()
