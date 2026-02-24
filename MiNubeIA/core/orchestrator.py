"""
core/orchestrator.py — El cerebro central de Nuevi
Coordina voz, contexto, clasificación, plugins, memoria e IA.
Sincronizado con la interfaz tkinter (CloudWindow).
"""

import logging
import threading
import time
from voice.listen import VoiceListener
from voice.speak import speak, set_voice_callbacks
from ai.classifier import classify_intent
from ai.gemini import ask
from ai.memory import process_memory_storage, query_memory
from context.detector import ActiveWindowDetector
from context.analyzer import ContextAnalyzer
from core.plugin_manager import plugin_manager
from ui.nube import CloudWindow

# Configuración de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger("NuviaOrchestrator")

class Orchestrator:
    """
    Orquestador central que implementa la arquitectura de 7 pasos:
    Voz -> Clasificar -> Contexto -> [Plugin / Gemini / Memoria] -> Respuesta -> Web UI.
    """

    def __init__(self):
        logger.info("Inicializando Orquestador de Nuevi...")
        
        # 1. Componentes de UI (Web)
        self.ui = CloudWindow()
        
        # 2. Componentes de Contexto
        self.detector = ActiveWindowDetector()
        self.analyzer = ContextAnalyzer()
        
        # 3. Gestor de Plugins
        # LLamamos a load_plugins aquí para evitar que el import circular en plugins/
        # bloquee la inicialización del singleton en core/plugin_manager
        self.plugin_manager = plugin_manager
        self.plugin_manager.load_plugins()
        
        # 4. Listener de Voz
        self.listener = VoiceListener(
            on_command=self.process_command,
            on_listening=self._update_ui_listening,
            on_processing=self._update_ui_thinking
        )

        # Conectar callbacks de voz para la animación de la boca en la UI
        set_voice_callbacks(
            on_start=self._update_ui_speaking_start,
            on_stop=self._update_ui_idle
        )

    def start(self):
        """Inicia todos los hilos y la UI central."""
        logger.info("Nuvia lista para la acción.")
        
        # Iniciar listener en hilo separado (no bloqueante)
        self.listener.start()
        
        # Iniciar la interfaz web
        # NOTA: webview.start() bloquea el hilo principal.
        self.ui.create()
        
        # Hilo para inicializar estado visual una vez cargue
        def _init_ui():
            time.sleep(1.0)
            self._update_ui_idle()
            
        threading.Thread(target=_init_ui, daemon=True).start()
        
        self.ui.start()

    def say_greeting(self):
        """Dice el saludo inicial con el timing correcto."""
        def _delayed_greeting():
            # Esperar a que la ventana se cree y el fade-in comience
            time.sleep(1.5)
            saludo = "Hola Ramiro soy nuvia aqui estoy para lo que me necesites"
            speak(saludo)
            
        threading.Thread(target=_delayed_greeting, daemon=True).start()

    # --- Callbacks de Sincronización UI ---

    def _update_ui_listening(self):
        """Notifica a la UI que estamos escuchando."""
        try:
            self.ui.set_state("listening")
        except: pass

    def _update_ui_thinking(self):
        """Notifica a la UI que estamos procesando."""
        try:
            self.ui.set_state("thinking")
        except: pass

    def _update_ui_speaking_start(self):
        """Notifica a la UI que empezamos a hablar (boca on)."""
        try:
            self.ui.set_state("speaking")
            self.ui.start_mouth()
        except: pass

    def _update_ui_idle(self):
        """Vuelve al estado de espera y detiene la animación."""
        try:
            self.ui.set_state("idle")
            self.ui.stop_mouth()
        except: pass

    def process_command(self, text: str):
        """
        Punto de entrada para el texto transcrito.
        Coordina el análisis y la ejecución.
        """
        if not text: return
        
        logger.info(f"Entrada recibida: '{text}'")
        self._update_ui_thinking()

        # Ejecutar el flujo pesado en un hilo para no congelar la UI si hay red lenta
        threading.Thread(target=self._orchestrate_flow, args=(text,), daemon=True).start()

    def _orchestrate_flow(self, text: str):
        """Flujo de decisión lógica (Paso 2 al 7)."""
        try:
            # 1. Obtener contexto actual (Windows Apps/Ventanas)
            raw_context = self.detector.get_current_context()
            context = self.analyzer.analyze(raw_context)

            # 2. Clasificar intención usando el Classifier (Gemini)
            intent_data = classify_intent(text)
            intent = intent_data.get("intent", "general_chat")
            params = intent_data.get("parameters", {})
            logger.info(f"Intención detectada: {intent}")

            # 3. Almacenamiento proactivo en memoria (Background)
            threading.Thread(target=process_memory_storage, args=(text,), daemon=True).start()

            # 4. DECISIÓN DE EJECUCIÓN
            
            # A. ¿Es un intent local soportado por un plugin?
            response_data = plugin_manager.execute_plugin(intent, params, context)
            
            if response_data:
                # El plugin devolvió (fuente, texto, extra)
                _, response_text, _ = response_data
            else:
                # B. Si no hay plugin, intentamos memoria o Gemini directo
                memory_ans = query_memory(text)
                if memory_ans:
                    response_text = memory_ans
                else:
                    # Fallback a Gemini con el contexto de la aplicación abierta
                    prompt = text
                    if context.get("summary"):
                        prompt = f"[CONTEXTO ACTUAL: {context['summary']}]\n{text}"
                    response_text = ask(prompt)

            # 5. ENTREGA DE RESPUESTA (Voz)
            # El speak activará automáticamente la boca vía los callbacks configurados
            logger.info(f"Nuevi responde: {response_text}")
            speak(response_text)

        except Exception as e:
            logger.error(f"Error crítico en el orquestador: {e}")
            speak("Lo siento Ramiro, tuve un problema interno al procesar eso.")
            self._update_ui_idle()

    def stop(self):
        """Detiene todos los servicios."""
        if hasattr(self, 'listener'):
            self.listener.stop()
        self.ui.close()
        logger.info("Orquestador detenido.")
