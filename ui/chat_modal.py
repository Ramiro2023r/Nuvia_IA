"""
ui/chat_modal.py — Modal de chat glassmorphism para Nuvia.

Aparece con animación slide-up + fade desde la boca de Nuvia.
Diseño: burbuja de diálogo oscura con cola triangular apuntando a Nuvia.
Thread-safe: usa after() para actualizaciones desde otros hilos.
"""

import tkinter as tk
import time
import math
import threading
from datetime import datetime
from ai.model_manager import ModelManager
from ui.model_panel import ModelPanel, _LILA_LIGHT

# ── Colores ──
_BG           = "#1a1a2e"
_HEADER_BG    = "#12122a"
_BORDER_COLOR = "#7c3aed"
_USER_BG      = "#2d2d44"
_NUVIA_BG     = "#4c1d95"
_TEXT_COLOR    = "#f0f0ff"
_TIMESTAMP_CL = "#6b7280"
_BUTTON_COLOR = "#7c3aed"
_PLACEHOLDER  = "#4b5563"
_ENTRY_BG     = "#2d2d44"
_CLOSE_HOVER  = "#ef4444"

# ── Dimensiones ──
_WIDTH  = 360
_HEIGHT = 460
_TAIL_W = 16
_TAIL_H = 10
_RADIUS = 18
_ANIM_DURATION_IN  = 250   # ms
_ANIM_DURATION_OUT = 200   # ms
_ANIM_STEP_MS      = 16    # ~60fps
_SLIDE_OFFSET      = 30    # px de desplazamiento vertical


class ChatModal:
    """Modal de chat que flota junto a la nube de Nuvia."""

    def __init__(self, parent_window):
        """
        parent_window: instancia de CloudWindow (ui/nube.py).
        Usa parent_window.root como ventana padre de Tkinter.
        """
        self._parent = parent_window
        self._root = None   # Toplevel window
        self._visible = False
        self._animating = False
        self._messages = []
        self._on_send_callback = None  # callback(text) cuando el usuario escribe

        # Widgets internos
        self._canvas_bg = None
        self._msg_frame = None
        self._msg_canvas = None
        self._msg_container = None
        self._msg_inner = None
        self._entry = None
        self._placeholder_active = True
        self._scroll_id = None

        # Gestión de Modelos
        self.model_manager = ModelManager.instance()
        self._model_panel = None
        self._model_status_label = None

    # ══════════════════════════════════════════════════════════════════════
    # CREACIÓN DE LA VENTANA
    # ══════════════════════════════════════════════════════════════════════

    def _create_window(self):
        """Crea el Toplevel con todos los widgets."""
        if self._root is not None:
            return

        parent_tk = self._parent.root
        self._root = tk.Toplevel(parent_tk)
        self._root.overrideredirect(True)
        self._root.wm_attributes("-topmost", True)
        self._root.configure(bg=_BG)

        # En Windows, hacer la ventana semi-opaca
        try:
            self._root.wm_attributes("-alpha", 0.0)
        except Exception:
            pass

        self._root.geometry(f"{_WIDTH}x{_HEIGHT + _TAIL_H}")

        # ── Frame principal con borde ──
        main_frame = tk.Frame(self._root, bg=_BG, highlightbackground=_BORDER_COLOR,
                              highlightthickness=2)
        main_frame.pack(fill="both", expand=True, padx=0, pady=(_TAIL_H, 0))

        # ── Cola triangular (Canvas en la parte superior) ──
        tail_canvas = tk.Canvas(self._root, width=_WIDTH, height=_TAIL_H,
                                bg=_BG, highlightthickness=0)
        tail_canvas.place(x=0, y=0)
        # Triángulo apuntando hacia arriba
        cx = _WIDTH // 2
        tail_canvas.create_polygon(
            cx - _TAIL_W // 2, _TAIL_H,
            cx, 0,
            cx + _TAIL_W // 2, _TAIL_H,
            fill=_BORDER_COLOR, outline=_BORDER_COLOR
        )

        # ── Header ──
        header = tk.Frame(main_frame, bg=_HEADER_BG, height=36)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        title_label = tk.Label(header, text="  Nuvia ✨", bg=_HEADER_BG,
                               fg=_TEXT_COLOR, font=("Segoe UI", 11, "bold"),
                               anchor="w")
        title_label.pack(side="left", fill="x", expand=True)

        close_btn = tk.Label(header, text=" ✕ ", bg=_HEADER_BG, fg="#9ca3af",
                             font=("Segoe UI", 11), cursor="hand2")
        close_btn.pack(side="right", padx=4, pady=4)
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg=_CLOSE_HOVER))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg="#9ca3af"))
        close_btn.bind("<Button-1>", lambda e: self.hide())

        # Hacer header draggable
        header.bind("<ButtonPress-1>", self._on_header_press)
        header.bind("<B1-Motion>", self._on_header_drag)
        title_label.bind("<ButtonPress-1>", self._on_header_press)
        title_label.bind("<B1-Motion>", self._on_header_drag)

        # ── Barra de Modelo Activo ──
        model_bar = tk.Frame(main_frame, bg=_HEADER_BG, height=30)
        model_bar.pack(fill="x")
        model_bar.pack_propagate(False)

        self._model_status_label = tk.Label(model_bar, text="🤖 Modelo: [Ninguno ▼]", 
                                            bg=_HEADER_BG, fg=_LILA_LIGHT,
                                            font=("Segoe UI", 9), cursor="hand2")
        self._model_status_label.pack(side="left", padx=10)
        self._model_status_label.bind("<Button-1>", lambda e: self.toggle_model_panel())

        config_icon = tk.Label(model_bar, text="⚙", bg=_HEADER_BG, fg=_LILA_LIGHT,
                               font=("Segoe UI", 12), cursor="hand2")
        config_icon.pack(side="right", padx=10)
        config_icon.bind("<Button-1>", lambda e: self.toggle_model_panel())

        # Separador
        tk.Frame(main_frame, bg=_BORDER_COLOR, height=1).pack(fill="x")

        # ── Panel de Configuración (Inicialmente OCULTO) ──
        self._model_panel = ModelPanel(main_frame, on_connected_callback=self._on_ai_connected)
        # No se empaqueta todavía

        # ── Área de mensajes (Canvas con scroll) ──
        self._msg_container = tk.Frame(main_frame, bg=_BG)
        self._msg_container.pack(fill="both", expand=True, padx=0, pady=0)

        self._msg_canvas = tk.Canvas(self._msg_container, bg=_BG, highlightthickness=0,
                                     bd=0)
        self._msg_canvas.pack(fill="both", expand=True, side="left")

        self._msg_inner = tk.Frame(self._msg_canvas, bg=_BG)
        self._msg_canvas_window = self._msg_canvas.create_window(
            (0, 0), window=self._msg_inner, anchor="nw", width=_WIDTH - 8
        )

        self._msg_inner.bind("<Configure>", self._on_msg_configure)
        self._msg_canvas.bind("<Configure>", self._on_canvas_configure)

        # Scroll con rueda del ratón
        self._msg_canvas.bind("<MouseWheel>", self._on_mousewheel)
        self._msg_inner.bind("<MouseWheel>", self._on_mousewheel)

        # ── Separador inferior ──
        sep2 = tk.Frame(main_frame, bg=_BORDER_COLOR, height=1)
        sep2.pack(fill="x")

        # ── Barra de entrada ──
        input_bar = tk.Frame(main_frame, bg=_HEADER_BG, height=46)
        input_bar.pack(fill="x", side="bottom")
        input_bar.pack_propagate(False)

        entry_frame = tk.Frame(input_bar, bg=_ENTRY_BG, highlightbackground="#3d3d5c",
                               highlightthickness=1)
        entry_frame.pack(side="left", fill="both", expand=True, padx=(8, 4), pady=8)

        self._entry = tk.Entry(entry_frame, bg=_ENTRY_BG, fg=_PLACEHOLDER,
                               font=("Segoe UI", 11), insertbackground=_TEXT_COLOR,
                               relief="flat", border=0)
        self._entry.pack(fill="both", expand=True, padx=6, pady=2)
        self._entry.insert(0, "Escríbeme algo...")
        self._placeholder_active = True

        self._entry.bind("<FocusIn>", self._on_entry_focus_in)
        self._entry.bind("<FocusOut>", self._on_entry_focus_out)
        self._entry.bind("<Return>", self._on_send)
        self._entry.bind("<MouseWheel>", lambda e: None)  # No propagar scroll

        send_btn = tk.Label(input_bar, text=" ➤ ", bg=_BUTTON_COLOR, fg="white",
                            font=("Segoe UI", 13, "bold"), cursor="hand2",
                            padx=6, pady=2)
        send_btn.pack(side="right", padx=(4, 8), pady=8)
        send_btn.bind("<Button-1>", self._on_send)
        send_btn.bind("<Enter>", lambda e: send_btn.config(bg="#6d28d9"))
        send_btn.bind("<Leave>", lambda e: send_btn.config(bg=_BUTTON_COLOR))

        # Reposicionar en la primera muestra
        self.reposition()

    # ══════════════════════════════════════════════════════════════════════
    # POSICIONAMIENTO
    # ══════════════════════════════════════════════════════════════════════

    def reposition(self):
        """Posiciona el modal debajo de la nube, centrado."""
        if not self._root or not self._parent.root:
            return
        try:
            px = self._parent.root.winfo_x()
            py = self._parent.root.winfo_y()
            pw = self._parent.root.winfo_width()
            ph = self._parent.root.winfo_height()
        except Exception:
            return

        # Centrar horizontalmente bajo la nube
        x = px + (pw // 2) - (_WIDTH // 2)
        y = py + ph - 10  # Justo debajo de la nube

        # Clamp a pantalla
        try:
            sw = self._root.winfo_screenwidth()
            sh = self._root.winfo_screenheight()
            x = max(10, min(x, sw - _WIDTH - 10))
            y = max(10, min(y, sh - _HEIGHT - _TAIL_H - 10))
        except Exception:
            pass

        self._target_x = x
        self._target_y = y
        
        # Si ya está visible y NO está animando, mover instantáneamente
        if self._visible and not self._animating:
            self._root.geometry(f"+{x}+{y}")

    # ══════════════════════════════════════════════════════════════════════
    # DRAG
    # ══════════════════════════════════════════════════════════════════════

    def _on_header_press(self, e):
        self._drag_x = e.x_root - self._root.winfo_x()
        self._drag_y = e.y_root - self._root.winfo_y()

    def _on_header_drag(self, e):
        x = e.x_root - self._drag_x
        y = e.y_root - self._drag_y
        self._root.geometry(f"+{x}+{y}")

    # ══════════════════════════════════════════════════════════════════════
    # SCROLL
    # ══════════════════════════════════════════════════════════════════════

    def _on_msg_configure(self, e=None):
        self._msg_canvas.configure(scrollregion=self._msg_canvas.bbox("all"))

    def _on_canvas_configure(self, e=None):
        self._msg_canvas.itemconfig(self._msg_canvas_window, width=e.width - 4)

    def _on_mousewheel(self, e):
        self._msg_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

    def _scroll_to_bottom(self):
        """Auto-scroll al último mensaje."""
        self._msg_canvas.update_idletasks()
        self._msg_canvas.yview_moveto(1.0)

    # ══════════════════════════════════════════════════════════════════════
    # ENTRY / PLACEHOLDER
    # ══════════════════════════════════════════════════════════════════════

    def _on_entry_focus_in(self, e=None):
        if self._placeholder_active:
            self._entry.delete(0, "end")
            self._entry.config(fg=_TEXT_COLOR)
            self._placeholder_active = False

    def _on_entry_focus_out(self, e=None):
        if not self._entry.get().strip():
            self._entry.delete(0, "end")
            self._entry.insert(0, "Escríbeme algo...")
            self._entry.config(fg=_PLACEHOLDER)
            self._placeholder_active = True

    def _on_send(self, e=None):
        """Envía el texto del usuario."""
        if self._placeholder_active:
            return
        text = self._entry.get().strip()
        if not text:
            return

        self._entry.delete(0, "end")
        self.append_user_message(text)

        if self._on_send_callback:
            self._on_send_callback(text)

    # ══════════════════════════════════════════════════════════════════════
    # MENSAJES
    # ══════════════════════════════════════════════════════════════════════

    def append_user_message(self, text: str):
        """Agrega un mensaje del usuario (alineado a la derecha)."""
        def _do():
            self._add_bubble(text, is_user=True)
        if self._root:
            self._root.after(0, _do)

    def append_nuvia_message(self, text: str):
        """Agrega un mensaje de Nuvia (alineado a la izquierda). Thread-safe."""
        def _do():
            self._add_bubble(text, is_user=False)
        if self._root:
            self._root.after(0, _do)

    def _add_bubble(self, text: str, is_user: bool):
        """Crea una burbuja de mensaje con timestamp."""
        if not self._msg_inner:
            return

        now = datetime.now().strftime("%I:%M %p")
        anchor = "e" if is_user else "w"
        bg = _USER_BG if is_user else _NUVIA_BG
        name = "Tú" if is_user else "Nuvia"
        padx_l = (60, 10) if is_user else (10, 60)

        # Container del mensaje
        msg_row = tk.Frame(self._msg_inner, bg=_BG)
        msg_row.pack(fill="x", padx=padx_l, pady=(4, 0), anchor=anchor)

        # Burbuja
        bubble = tk.Frame(msg_row, bg=bg, padx=10, pady=6)
        bubble.pack(anchor=anchor)

        # Nombre
        name_label = tk.Label(bubble, text=name, bg=bg, fg=_BORDER_COLOR,
                              font=("Segoe UI", 8, "bold"), anchor="w")
        name_label.pack(anchor="w")

        # Texto del mensaje
        msg_label = tk.Label(bubble, text=text, bg=bg, fg=_TEXT_COLOR,
                             font=("Segoe UI", 11), wraplength=240,
                             justify="left", anchor="w")
        msg_label.pack(anchor="w")

        # Bind mousewheel en cada widget nuevo
        for w in (msg_row, bubble, name_label, msg_label):
            w.bind("<MouseWheel>", self._on_mousewheel)

        # Timestamp
        ts_frame = tk.Frame(self._msg_inner, bg=_BG)
        ts_frame.pack(fill="x", padx=padx_l, pady=(0, 4), anchor=anchor)
        ts_label = tk.Label(ts_frame, text=now, bg=_BG, fg=_TIMESTAMP_CL,
                            font=("Segoe UI", 8))
        ts_label.pack(anchor=anchor)
        ts_label.bind("<MouseWheel>", self._on_mousewheel)

        self._messages.append({"text": text, "is_user": is_user, "time": now})

        # Auto-scroll
        self._root.after(50, self._scroll_to_bottom)

    # ══════════════════════════════════════════════════════════════════════
    # SHOW / HIDE CON ANIMACIÓN
    # ══════════════════════════════════════════════════════════════════════

    def show(self):
        """Muestra el modal con animación slide-up + fade-in."""
        if self._visible or self._animating:
            return

        self._create_window()
        self.reposition()
        self._animating = True

        # Posición inicial: desplazada hacia abajo
        start_y = self._target_y + _SLIDE_OFFSET
        self._root.geometry(f"{_WIDTH}x{_HEIGHT + _TAIL_H}+{self._target_x}+{start_y}")
        self._root.deiconify()

        steps = max(1, _ANIM_DURATION_IN // _ANIM_STEP_MS)
        self._animate_show(0, steps, start_y, self._target_y)

    def _animate_show(self, step, total_steps, start_y, end_y):
        """Ejecuta un frame de la animación de entrada."""
        if not self._root:
            self._animating = False
            return

        progress = min(1.0, step / total_steps)
        # Easing: ease-out cubic
        t = 1.0 - (1.0 - progress) ** 3

        alpha = t
        current_y = int(start_y + (end_y - start_y) * t)

        try:
            self._root.wm_attributes("-alpha", min(0.95, alpha))
            self._root.geometry(f"+{self._target_x}+{current_y}")
        except Exception:
            pass

        if step < total_steps:
            self._root.after(_ANIM_STEP_MS,
                             lambda: self._animate_show(step + 1, total_steps, start_y, end_y))
        else:
            self._animating = False
            self._visible = True
            # Focus al campo de texto
            try:
                self._entry.focus_set()
                self._on_entry_focus_in()
            except Exception:
                pass

    def hide(self):
        """Oculta el modal con animación slide-down + fade-out."""
        if not self._visible or self._animating:
            return

        self._animating = True
        try:
            start_y = self._root.winfo_y()
        except Exception:
            start_y = self._target_y

        end_y = start_y + _SLIDE_OFFSET
        steps = max(1, _ANIM_DURATION_OUT // _ANIM_STEP_MS)
        self._animate_hide(0, steps, start_y, end_y)

    def _animate_hide(self, step, total_steps, start_y, end_y):
        """Ejecuta un frame de la animación de salida."""
        if not self._root:
            self._animating = False
            self._visible = False
            return

        progress = min(1.0, step / total_steps)
        t = progress ** 2  # ease-in

        alpha = max(0.0, 0.95 * (1.0 - t))
        current_y = int(start_y + (end_y - start_y) * t)

        try:
            self._root.wm_attributes("-alpha", alpha)
            self._root.geometry(f"+{self._root.winfo_x()}+{current_y}")
        except Exception:
            pass

        if step < total_steps:
            self._root.after(_ANIM_STEP_MS,
                             lambda: self._animate_hide(step + 1, total_steps, start_y, end_y))
        else:
            self._animating = False
            self._visible = False
            try:
                self._root.withdraw()
            except Exception:
                pass

    def toggle(self):
        """Muestra u oculta el modal."""
        if self._visible:
            self.hide()
        else:
            self.show()

    @property
    def is_visible(self):
        return self._visible

    # ══════════════════════════════════════════════════════════════════════
    # MODEL PANEL INTEGRATION
    # ══════════════════════════════════════════════════════════════════════

    def toggle_model_panel(self, preselect=None):
        """Muestra u oculta el panel de modelos."""
        if not self._model_panel: return
        
        if self._model_panel.winfo_ismapped():
            self._model_panel.hide()
        else:
            if preselect:
                self._model_panel.select_model(preselect)
            self._model_panel.show()
            self._msg_container.pack_forget() # Ocultar el contenedor entero
        
        # Si cerramos, restauramos mensajes
        if not self._model_panel.winfo_ismapped():
            self._msg_container.pack(fill="both", expand=True, padx=0, pady=0)
            self._update_model_status_text()

    def _on_ai_connected(self, model_name):
        """Callback cuando se conecta un modelo."""
        self._model_panel.hide()
        if self._msg_container:
            self._msg_container.pack(fill="both", expand=True, padx=0, pady=0)
        self._update_model_status_text()
        self.append_nuvia_message(f"✅ Conectado a {model_name.capitalize()}. ¡Listo para ayudarte!")

    def _update_model_status_text(self):
        active = self.model_manager.active_model_name
        if active == "none":
            text = "🤖 Modelo: [Ninguno ▼]"
        else:
            text = f"🤖 Activo: {active.capitalize()} ▼"
        
        if self._model_status_label:
            self._model_status_label.config(text=text)

    def set_on_send(self, callback):
        """Registra callback para cuando el usuario envía texto. callback(text: str)"""
        self._on_send_callback = callback
