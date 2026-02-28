"""
ui/window.py — Ventana de Nuvia con transparencia nativa de pywebview.

Análisis del código fuente de pywebview 6.1 revela que transparent=True:
  1. Establece WebView2.DefaultBackgroundColor = Color.Transparent (edgechromium.py:108)
  2. Establece WinForms SupportsTransparentBackColor (winforms.py:271)
  3. Ejecuta un hack Show()/Hide() necesario para que funcione (winforms.py:736-741)
  4. La ventana se re-muestra automáticamente en on_navigation_start (edgechromium.py:340-343)

Por lo tanto, DEBEMOS usar transparent=True y confiar en el mecanismo interno.
El CSS debe tener background: transparent (NO un color sólido).
"""
import webview
import os
import logging
import threading
import time

logger = logging.getLogger("NuviaUI")


class WebViewWindow:
    def __init__(self):
        self.window = None
        self._html_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "web_ui", "index.html")
        )

    def create(self):
        """Crea la ventana con transparent=True para activar la cadena interna de pywebview."""
        self.window = webview.create_window(
            "Nuvia",
            url=f"file:///{self._html_path}",
            width=260,
            height=220,
            frameless=True,
            transparent=True,  # CRÍTICO: activa DefaultBackgroundColor=Transparent + hack Show/Hide
            on_top=True,
            easy_drag=True,
            # NO pasar background_color — pywebview lo ignora cuando transparent=True
        )

    def start(self):
        """Inicia la GUI. No forzar gui= para dejar que pywebview elija edgechromium automáticamente."""
        webview.start(debug=False)

    def set_state(self, state):
        if self.window:
            try:
                self.window.evaluate_js(f"window.setCloudState('{state}')")
            except:
                pass

    def start_mouth(self):
        if self.window:
            try:
                self.window.evaluate_js("window.startTalking()")
            except:
                pass

    def stop_mouth(self):
        if self.window:
            try:
                self.window.evaluate_js("window.stopTalking()")
            except:
                pass

    def close(self):
        if self.window:
            self.window.destroy()
