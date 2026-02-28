"""
core/orchestrator.py — El cerebro central de Nuevi
Coordina voz, contexto, clasificación, plugins, memoria e IA en modo Asíncrono.
"""

import logging
import threading
import time
import os
import numpy as np
import asyncio
import concurrent.futures
from voice import VoiceEngine
from voice.speak import speak, stop_speak, set_voice_callbacks, is_speaking
from ai.classifier import classify_intent
from ai.model_manager import ModelManager
from ai.memory import process_memory_storage, query_memory
from ai.chat_memory import ChatMemory
from ai.search_engine import SearchEngine
from ai.ollama_client import OllamaClient
from system.system_controller import SystemController
from core.security_layer import SecurityManager
from context.detector import ActiveWindowDetector
from context.analyzer import ContextAnalyzer
from core.plugin_manager import plugin_manager
from ui.nube import CloudWindow
from voice.voice_registry import VoiceRegistry

# Configuración de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger("NuviaOrchestrator")

class Orchestrator:
    def __init__(self):
        logger.info("Inicializando Orquestador Asíncrono de Nuevi...")
        
        # 1. UI & Sistema
        self.ui = CloudWindow()
        self.security = SecurityManager()
        self.system = SystemController()
        self.search_engine = SearchEngine()
        self.ollama = OllamaClient()
        self.detector = ActiveWindowDetector()
        self.analyzer = ContextAnalyzer()
        self.chat_memory = ChatMemory(max_messages=10)
        self.plugin_manager = plugin_manager
        self.plugin_manager.load_plugins()
        self.registry = VoiceRegistry()
        self.model_manager = ModelManager.instance()
        
        # 2. Motor de Voz (Vosk)
        self.engine = VoiceEngine(model_path="model")
        
        # 3. Infraestructura Asíncrona
        self.loop = asyncio.new_event_loop()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
        self.async_thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self.async_thread.start()

        # 4. Registro de Voz
        self.registration_state = None
        self.registration_audios = []
        self.reg_phrases = {
            1: "Nuvia, activa el protocolo de seguridad.",
            2: "Mi voz es mi contraseña única y personal.",
            3: "Protege mis archivos y mi sistema operativo."
        }

        set_voice_callbacks(
            on_start=self._update_ui_speaking_start,
            on_stop=self._update_ui_idle
        )

    def _run_async_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def start(self):
        logger.info("Nuvia lista para la acción.")
        # El callback de voz ahora dispara el flujo asíncrono
        self.engine.start(on_command_callback=self.process_command)
        self.engine.on_partial = self.process_partial
        
        self.ui.create()
        
        # Conectar el chat modal para recibir texto del usuario
        if self.ui.chat_modal:
            self.ui.chat_modal.set_on_send(self.process_text_input)
        
        self.ui.start()

    def process_partial(self, text):
        """Si el usuario empieza a hablar mientras Nuvia habla, la detenemos inmediatamente."""
        from voice.speak import is_speaking, stop_speak, get_current_text
        if is_speaking():
            # IMPLEMENTACIÓN: Intelligent Echo Filtering
            # Si lo que oímos es básicamente lo que Nuvia está diciendo, es UN ECO.
            current_speech = get_current_text().lower()
            heard = text.lower()
            
            # Si el texto oído es una subcadena de lo que ella dice (o viceversa), ignoramos
            if heard in current_speech or (len(heard) > 3 and heard[:len(heard)//2] in current_speech):
                return
                
            logger.info(f"Barge-in detectado (Partial: {text})")
            stop_speak()
            self._update_ui_idle()
            self.engine.set_speaking_state(False)

    def say_greeting(self):
        speak("Hola, soy Nuvia. He sido optimizada para responderte más rápido.")

    def process_command(self, text, speaker, audio_data=None):
        """Trampolín de hilos -> asyncio loop."""
        asyncio.run_coroutine_threadsafe(self.process_command_async(text, speaker, audio_data), self.loop)

    async def process_command_async(self, text, speaker, audio_data=None):
        """Lógica central asíncrona."""
        try:
            logger.info(f"Comando async: '{text}' | Speaker: {speaker}")
            
            # --- FASE 1: REGISTRO ---
            if self.registration_state:
                self._handle_voice_registration(text, audio_data)
                return

            # --- FASE 2: FAST-PATH ---
            cmd_low = text.lower()
            if self._is_system_command(cmd_low):
                await self._handle_system_logic(text, speaker)
            else:
                await self._handle_chat_logic(text)

        except Exception as e:
            logger.error(f"Error fatal en orquestador: {e}")
            self._speak_and_chat("Hubo un error interno.")
        finally:
            if not is_speaking():
                self._update_ui_idle()
                try:
                    if not self.executor._shutdown:
                        self.engine.set_speaking_state(False)
                except: pass

    def _speak_and_chat(self, text: str):
        """Habla el texto Y lo muestra en el chat modal si está visible."""
        speak(text)
        self._send_to_chat_nuvia(text)

    def _send_to_chat_nuvia(self, text: str):
        """Envía un mensaje de Nuvia al chat modal (thread-safe)."""
        if self.ui.chat_modal:
            # Auto-abrir si Nuvia responde algo importante
            if not self.ui.chat_modal.is_visible:
                self.ui.show_chat()
            self.ui.chat_modal.append_nuvia_message(text)

    def process_text_input(self, text: str):
        """Procesa texto escrito por el usuario desde el chat modal."""
        logger.info(f"Texto del chat: '{text}'")
        
        # Asegurar que el modal esté visible si estamos procesando texto
        self.ui.show_chat()
        
        # Enviar al mismo pipeline de voz, con speaker=OWNER (teclado = confiable)
        asyncio.run_coroutine_threadsafe(
            self.process_command_async(text, "OWNER"),
            self.loop
        )

    def _is_system_command(self, cmd):
        keywords = [
            "volumen", "abrir", "cerrar", "apagar", "reiniciar",
            "stats", "cpu", "ram", "hora", "fecha", "tiempo",
            "registrar", "registra", "graba", "identidad", "biometría",
            # Voice change triggers
            "habla como", "habla en ", "habla con voz", "habla con acento",
            "cambia tu voz", "cambia la voz", "cambia el acento",
            "cambia idioma", "pon voz", "voz de", "habla diferente",
            # Chat triggers
            "muestra el chat", "abre el chat", "quiero escribir",
            "muestrame el chat", "cierra el chat", "oculta el chat",
            "esconde el chat", "abre el teclado",
        ]
        return any(k in cmd for k in keywords)

    async def _handle_system_logic(self, text, speaker):
        self.ui.set_state("thinking")
        
        # 1. Mapeo local inmediato
        intent_data = self._get_local_intent(text.lower())
        
        # 2. Si no es obvio, usar Gemini para clasificar
        if not intent_data:
            intent_data = await self.loop.run_in_executor(self.executor, classify_intent, text)
        
        intent = intent_data.get("intent")
        params = intent_data.get("parameters", {})

        if not self.security.is_authorized(intent, speaker):
            speak("Acceso denegado por seguridad de voz.")
            return

        # 3. Ejecutar plugin o sistema (pasando contexto y memoria)
        context_data = await self.loop.run_in_executor(self.executor, self.detector.get_current_context)
        analyzed_context = await self.loop.run_in_executor(self.executor, self.analyzer.analyze, context_data)
        plugin_res = await self.loop.run_in_executor(self.executor, self.plugin_manager.execute_plugin, intent, params, analyzed_context, None)
        if plugin_res:
            res_type, response_text, extra = plugin_res
            
            # Manejar comandos de UI desde plugins
            if res_type == "ui":
                action = extra.get("action")
                if action == "open_model_panel" and self.ui.chat_modal:
                    self.ui.chat_modal.toggle_model_panel(preselect=extra.get("preselect"))
                elif action == "hide_chat":
                    self.ui.hide_chat()

            # Manejar sentinels de texto directo (legado)
            if response_text == "__SHOW_CHAT__":
                self.ui.show_chat()
                speak("¡Aquí estoy! Escríbeme lo que quieras.")
                self._send_to_chat_nuvia("¡Hola! Escríbeme lo que necesites. ✨")
                return
            elif response_text == "__HIDE_CHAT__":
                self.ui.hide_chat()
                speak("Chat cerrado. Sigo escuchándote por voz.")
                return
            
            if response_text:
                self._speak_and_chat(response_text)
            return

        # 4. Fallback if no plugin handled it
        self._speak_and_chat("Lo siento, no tengo un plugin configurado para esa acción.")

    async def _handle_chat_logic(self, text):
        self.ui.set_state("thinking")
        
        # 1. Memoria Local
        memory_ans = await self.loop.run_in_executor(self.executor, query_memory, text)
        if memory_ans:
            self._speak_and_chat(memory_ans)
            return

        # 2. Ollama / Gemini Streaming
        full_response = ""
        is_google = await self.loop.run_in_executor(self.executor, self.ollama.classify, text)
        
        if is_google == "GOOGLE":
            logger.info("Usando Model Manager (Stream)...")
            generator = self.model_manager.stream_ask(text, self.chat_memory.get_history())
        else:
            logger.info("Usando Ollama Streaming...")
            generator = self.ollama.stream_chat_response(text, "", self.chat_memory.get_history())

        # Consumir sentencias y mostrar en chat + voz
        def consume_generator():
            nonlocal full_response
            for sentence in generator:
                if not sentence: continue
                speak(sentence)
                self._send_to_chat_nuvia(sentence)
                full_response += sentence + " "
        
        await self.loop.run_in_executor(self.executor, consume_generator)
        
        # 3. Background: Guardar memoria
        if full_response.strip():
            self.chat_memory.add_message("user", text)
            self.chat_memory.add_message("assistant", full_response.strip())
            # FIXED: run_in_executor returns a future, do not use run_coroutine_threadsafe here
            self.loop.run_in_executor(None, process_memory_storage, text)

    def _get_local_intent(self, cmd):
        if any(h in cmd for h in ["hora", "tiempo"]): return {"intent": "get_time", "parameters": {}}
        if any(s in cmd for s in ["stats", "cpu", "ram"]): return {"intent": "system_control", "parameters": {"action": "stats"}}
        
        # ── App Control (Local) ──
        open_triggers = ["abre ", "abrir ", "lanza ", "ejecuta "]
        for trigger in open_triggers:
            if cmd.startswith(trigger):
                app = cmd.replace(trigger, "").strip()
                if app: return {"intent": "open_app", "parameters": {"app": app}}

        close_triggers = ["cierra ", "cerrar ", "detén ", "detener ", "termina ", "quita "]
        for trigger in close_triggers:
            if cmd.startswith(trigger):
                app = cmd.replace(trigger, "").strip()
                if app: return {"intent": "close_app", "parameters": {"app": app}}
        
        # ── Voice Change Detection ──
        voice_triggers = [
            "habla como", "habla en ", "habla con voz de", "habla con voz",
            "habla con acento", "cambia tu voz a", "cambia la voz a",
            "cambia tu voz", "cambia la voz", "cambia el acento a",
            "cambia el acento", "cambia idioma a", "cambia idioma",
            "pon voz de", "pon voz", "voz de", "habla diferente",
        ]
        for trigger in voice_triggers:
            if trigger in cmd:
                voice_request = cmd.split(trigger, 1)[1].strip()
                if voice_request:
                    return {"intent": "change_voice", "parameters": {"voice_request": voice_request}}
                # Si no hay texto después del trigger, usar el comando completo
                return {"intent": "change_voice", "parameters": {"voice_request": cmd}}

        # ── Chat Modal Detection ──
        chat_open_triggers = ["muestra el chat", "abre el chat", "quiero escribir",
                              "muestrame el chat", "abre el teclado"]
        if any(t in cmd for t in chat_open_triggers):
            return {"intent": "show_chat", "parameters": {"action": "show"}}
        
        chat_close_triggers = ["cierra el chat", "oculta el chat", "esconde el chat"]
        if any(t in cmd for t in chat_close_triggers):
            return {"intent": "show_chat", "parameters": {"action": "hide"}}

        if any(r in cmd for r in ["registra", "graba", "identidad", "mi voz", "quien soy"]): 
            self.start_voice_registration()
            return {"intent": "VOICE_REG_STARTED", "parameters": {}}
        return None

    # --- UI Sync ---
    def _update_ui_thinking(self): self.ui.set_state("thinking")
    def _update_ui_idle(self): self.ui.set_state("idle"); self.ui.stop_mouth()
    def _update_ui_speaking_start(self): self.ui.set_state("speaking"); self.ui.start_mouth()

    def _handle_voice_registration(self, text, audio_data=None):
        """Maneja el flujo de registro de voz paso a paso con recolección de audio."""
        if not self.registration_state: return
        
        step = self.registration_state
        expected = self.reg_phrases.get(step, "").lower()
        
        # Similitud básica para avanzar
        clean_text = text.lower().strip()
        if any(word in clean_text for word in expected.split()[:3]) or len(clean_text) > 10:
            logger.info(f"Paso {step} de registro completado.")
            
            if audio_data is not None:
                self.registration_audios.append(audio_data)

            if step < 3:
                self.registration_state += 1
                next_phrase = self.reg_phrases[self.registration_state]
                speak(f"Muy bien. Ahora di: {next_phrase}")
                self._send_to_chat_nuvia(f"Paso {self.registration_state}/3. Repite:\n\"{next_phrase}\"")
            else:
                # Finalizar registro real
                if self.registration_audios:
                    logger.info("Procesando embeddings finales...")
                    success = self.registry.register_owner_from_list(self.registration_audios)
                    if success:
                        msg = "Proceso de registro finalizado. Tu identidad de voz ha sido guardada con éxito."
                        speak(msg)
                        self._send_to_chat_nuvia(msg)
                    else:
                        msg = "Hubo un problema al procesar tu voz. Por favor, intenta de nuevo más tarde."
                        speak(msg)
                        self._send_to_chat_nuvia(msg)
                else:
                    msg = "No pude capturar suficiente audio. El registro ha fallado."
                    speak(msg)
                
                # Cleanup y Cierre automático
                self.registration_state = None
                self.registration_audios = []
                self.engine.set_registration_mode(False)
                # Esperar un poco antes de cerrar el chat para que el usuario lea el resultado
                self.loop.call_later(4, self.ui.hide_chat)
        else:
            speak(f"No te entendí bien. Repite con claridad: {self.reg_phrases[step]}")
            self._send_to_chat_nuvia(f"⚠️ No te entendí. Repite por favor:\n\"{self.reg_phrases[step]}\"")

    def start_voice_registration(self):
        """Inicia el proceso de registro de voz."""
        self.registration_state = 1
        self.registration_audios = []
        self.engine.set_registration_mode(True)
        
        # UI Feedback
        self.ui.show_chat()
        first_phrase = self.reg_phrases[1]
        
        msg_intro = "Iniciando registro de voz. Por favor, repite conmigo las siguientes frases para conocerte mejor."
        speak(msg_intro)
        self._send_to_chat_nuvia(f"🎤 {msg_intro}")
        
        speak(first_phrase)
        self._send_to_chat_nuvia(f"Paso 1/3. Repite:\n\"{first_phrase}\"")

    def shutdown_nuvia(self):
        logger.info("Cerrando Nuvia...")
        self.engine.stop()
        self.ui.fade_out(callback=lambda: os._exit(0))
