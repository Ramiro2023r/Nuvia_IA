"""
ui/model_panel.py — Panel de configuración de IA.
Maneja la selección de modelos y la entrada de API keys.
"""

import tkinter as tk
from tkinter import ttk
import threading
import logging
from ai.model_manager import ModelManager

logger = logging.getLogger("ModelPanel")

# ── Colores (Sincronizados con chat_modal.py) ──
_BG           = "#12122a"
_TEXT_COLOR    = "#f0f0ff"
_LILA_LIGHT    = "#a78bfa"
_BORDER_LILA   = "#7c3aed"
_ENTRY_BG      = "#2d2d44"
_BTN_OK        = "#7c3aed"
_BTN_CANCEL    = "#2d2d44"
_COLOR_SUCCESS = "#10b981"
_COLOR_ERROR   = "#ef4444"
_COLOR_WARN    = "#f59e0b"

class ModelPanel(tk.Frame):
    def __init__(self, parent, on_connected_callback=None):
        super().__init__(parent, bg=_BG, highlightbackground=_BORDER_LILA, highlightthickness=1)
        self.on_connected = on_connected_callback
        self.manager = ModelManager.instance()
        
        self._setup_ui()
        self.load_current_state()

    def _setup_ui(self):
        # Título
        tk.Label(self, text="Conectar modelo de IA", bg=_BG, fg=_LILA_LIGHT,
                 font=("Segoe UI", 11, "bold")).pack(pady=(10, 5))

        # Selección de Modelo 
        tk.Label(self, text="Proveedor:", bg=_BG, fg=_TEXT_COLOR,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20)

        self.model_var = tk.StringVar(value="gemini")
        models_frame = tk.Frame(self, bg=_BG)
        models_frame.pack(fill="x", padx=20, pady=2)

        opciones = [
            ("Gemini (Google)", "gemini"),
            ("GPT (OpenAI)", "openai"),
            ("Grok (xAI)", "grok"),
            ("Groq (Llama)", "groq"),
            ("Ollama (Local)", "ollama")
        ]

        # Usar Grid para ahorrar espacio vertical (2 columnas)
        for i, (text, val) in enumerate(opciones):
            rb = tk.Radiobutton(models_frame, text=text, variable=self.model_var, 
                                value=val, bg=_BG, fg=_TEXT_COLOR, 
                                selectcolor=_BORDER_LILA, activebackground=_BG,
                                font=("Segoe UI", 8), command=self._on_model_change)
            rb.grid(row=i//2, column=i%2, sticky="w", padx=2, pady=1)

        # API Key
        self.key_label = tk.Label(self, text="API Key:", bg=_BG, fg=_TEXT_COLOR, font=("Segoe UI", 9, "bold"))
        self.key_label.pack(anchor="w", padx=20, pady=(8, 0))

        key_frame = tk.Frame(self, bg=_BG)
        key_frame.pack(fill="x", padx=20, pady=2)

        self.show_key = tk.BooleanVar(value=False)
        self.key_entry = tk.Entry(key_frame, bg=_ENTRY_BG, fg=_TEXT_COLOR, 
                                  insertbackground=_TEXT_COLOR, border=0, 
                                  show="*", font=("Segoe UI", 10))
        self.key_entry.pack(side="left", fill="x", expand=True, ipady=3)
        self.key_entry.bind("<Return>", lambda e: self._start_connection())

        self.eye_btn = tk.Button(key_frame, text="👁", bg=_ENTRY_BG, fg=_TEXT_COLOR,
                                 command=self._toggle_key_visibility, relief="flat",
                                 font=("Segoe UI", 10), width=3)
        self.eye_btn.pack(side="right", padx=2)

        # Estado (Reducido wraplength para que no empuje todo)
        self.status_label = tk.Label(self, text="", bg=_BG, fg=_TEXT_COLOR, 
                                     font=("Segoe UI", 9), wraplength=280)
        self.status_label.pack(pady=5)

        # Botones de Acción (Más arriba para evitar recortes)
        btns_frame = tk.Frame(self, bg=_BG)
        btns_frame.pack(fill="x", padx=20, pady=5)

        self.connect_btn = tk.Button(btns_frame, text="Conectar", bg=_BTN_OK, fg="white",
                                     command=self._start_connection, font=("Segoe UI", 9, "bold"),
                                     width=10, relief="flat", cursor="hand2")
        self.connect_btn.pack(side="left")

        self.delete_btn = tk.Button(btns_frame, text="Eliminar Llave", bg=_COLOR_ERROR, fg="white",
                                     command=self._on_delete_key, font=("Segoe UI", 8),
                                     width=12, relief="flat", cursor="hand2")
        self.delete_btn.pack(side="right")

        # Botón Cancelar (Cerrar) al final
        tk.Button(self, text="Volver al chat", bg=_BG, fg=_LILA_LIGHT,
                  command=self.hide, font=("Segoe UI", 9, "underline"),
                  relief="flat", cursor="hand2").pack(pady=5)

    def _on_model_change(self):
        model = self.model_var.get()
        if model == "ollama":
            self.key_entry.delete(0, tk.END)
            self.key_entry.insert(0, "http://localhost:11434")
            self.key_label.config(text="Ollama URL:")
            self.key_entry.config(show="")
        else:
            self.key_label.config(text="API Key:")
            key = self.manager.get_key_from_env(model)
            self.key_entry.delete(0, tk.END)
            self.key_entry.insert(0, key)
            if not self.show_key.get():
                self.key_entry.config(show="*")

    def _toggle_key_visibility(self):
        is_visible = self.show_key.get()
        self.show_key.set(not is_visible)
        
        if self.show_key.get():
            self.key_entry.config(show="")
            self.eye_btn.config(fg=_LILA_LIGHT)
        else:
            if self.model_var.get() != "ollama":
                self.key_entry.config(show="*")
                self.eye_btn.config(fg=_TEXT_COLOR)

    def load_current_state(self):
        active = self.manager.active_model_name
        if active != "none":
            self.model_var.set(active)
            self._on_model_change()

    def _on_delete_key(self):
        model = self.model_var.get()
        if model == "none" or model == "ollama": return
        
        self.manager.delete_key(model)
        self.key_entry.delete(0, tk.END)
        self.status_label.config(text=f"Llave de {model} borrada.", fg=_COLOR_ERROR)
        
        # Si era el modelo activo, desconectar
        if self.manager.active_model_name == model:
            self.manager.set_model("none")
            if self.on_connected:
                self.on_connected("none", "none")
        
        self.after(3000, lambda: self.status_label.config(text=""))

    def _start_connection(self):
        model = self.model_var.get()
        key = self.key_entry.get().strip()
        
        self.status_label.config(text="⌛ Probando conexión...", fg=_COLOR_WARN)
        self.connect_btn.config(state="disabled")
        
        # Ejecutar en hilo para no colgar la UI
        threading.Thread(target=self._test_proc, args=(model, key), daemon=True).start()

    def _test_proc(self, model, key):
        success, msg = self.manager.set_model(model, api_key=key)
        
        def finish():
            self.connect_btn.config(state="normal")
            if success:
                self.status_label.config(text=f"✅ {msg}", fg=_COLOR_SUCCESS)
                if self.on_connected:
                    self.master.after(1500, lambda: self.on_connected(model))
            else:
                self.status_label.config(text=f"❌ {msg}", fg=_COLOR_ERROR)
        
        self.master.after(0, finish)

    def show(self):
        self.pack(fill="both", expand=True, padx=10, pady=10)
        self.tkraise()

    def hide(self):
        self.pack_forget()

    def select_model(self, model_name):
        """Método público para llamar desde voz."""
        self.model_var.set(model_name)
        self._on_model_change()
        self.show()
