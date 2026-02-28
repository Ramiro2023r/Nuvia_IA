"""
ui/image_viewer.py — Popup para mostrar imágenes generadas por Nuvia
"""

import tkinter as tk
from tkinter import filedialog
import pathlib
from PIL import Image, ImageTk


class ImageViewer(tk.Toplevel):
    """Ventana emergente que muestra una imagen generada."""

    def __init__(self, parent, image_path: pathlib.Path):
        super().__init__(parent)
        self.title("Nuvia – Imagen Generada ✨")
        self.resizable(False, False)
        self.configure(bg="#1a1a2e")
        self._image_path = image_path

        # ── Cargar imagen ─────────────────────────────────────────────────
        img = Image.open(image_path)
        img.thumbnail((512, 512), Image.LANCZOS)
        self._photo = ImageTk.PhotoImage(img)

        # ── Layout ────────────────────────────────────────────────────────
        title_lbl = tk.Label(
            self,
            text="🎨 Imagen creada por Nuvia",
            bg="#1a1a2e",
            fg="#a29bfe",
            font=("Segoe UI", 12, "bold"),
            pady=8,
        )
        title_lbl.pack()

        img_lbl = tk.Label(self, image=self._photo, bg="#1a1a2e", padx=10)
        img_lbl.pack()

        btn_frame = tk.Frame(self, bg="#1a1a2e", pady=10)
        btn_frame.pack()

        save_btn = tk.Button(
            btn_frame,
            text="💾  Guardar como...",
            command=self._save,
            bg="#6c5ce7",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
        )
        save_btn.pack(side="left", padx=4)

        close_btn = tk.Button(
            btn_frame,
            text="✕  Cerrar",
            command=self.destroy,
            bg="#2d3436",
            fg="#dfe6e9",
            font=("Segoe UI", 10),
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
        )
        close_btn.pack(side="left", padx=4)

        # Centrar ventana
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")

        self.lift()
        self.focus_force()

    def _save(self):
        dest = filedialog.asksaveasfilename(
            defaultextension=".jpg",
            filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png"), ("Todos", "*.*")],
            initialfile=self._image_path.name,
        )
        if dest:
            import shutil
            shutil.copy2(self._image_path, dest)
