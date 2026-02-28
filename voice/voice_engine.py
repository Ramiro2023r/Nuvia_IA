import logging
import threading
import queue
import multiprocessing
from .voice_process import VoiceProcess

logger = logging.getLogger("NuviaVoice")

class VoiceEngine:
    """
    Gestor del motor de voz que ahora corre en un proceso independiente (multiprocessing)
    para evitar bloqueos del GIL y liberar RAM del proceso principal.
    """
    def __init__(self, model_path="model", sample_rate=16000, threshold=0.75):
        self.model_path = model_path
        self.sample_rate = sample_rate
        self.threshold = threshold
        
        # Comunicacion inter-proceso
        self.result_queue = multiprocessing.Queue()
        self.voice_process = None
        self.is_running = False
        self.on_command = None

    def start(self, on_command_callback):
        """Inicia el proceso de voz y el hilo de escucha de resultados."""
        if self.is_running:
            return
            
        self.on_command = on_command_callback
        self.is_running = True
        
        # 1. Crear e Iniciar el Proceso Secundario
        self.voice_process = VoiceProcess(
            result_queue=self.result_queue,
            model_path=self.model_path,
            sample_rate=self.sample_rate,
            threshold=self.threshold
        )
        self.voice_process.start()
        
        # 2. Hilo para leer la cola de resultados sin bloquear el proceso principal
        self.listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listener_thread.start()
        
        logger.info("VoiceEngine: Gestor de voz iniciado (Multiprocessing).")

    def _listen_loop(self):
        """Bucle que escucha la cola de multiprocessing y dispara los callbacks."""
        while self.is_running:
            try:
                # Esperar resultados del proceso de voz
                msg = self.result_queue.get(timeout=1)
                
                if msg.get("type") == "command":
                    text = msg.get("text")
                    speaker = msg.get("speaker")
                    audio_data = msg.get("audio_data") # Opcional, solo en modo registro
                    
                    if self.on_command:
                        self.on_command(text, speaker, audio_data)
                elif msg.get("type") == "partial":
                    if hasattr(self, 'on_partial'):
                        self.on_partial(msg.get("text"))
                        
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error en listener_thread: {e}")

    def set_speaking_state(self, is_speaking):
        """Notifica al proceso de voz si Nuvia está hablando."""
        if self.voice_process:
            if is_speaking:
                self.voice_process.nuvia_is_speaking.set()
            else:
                self.voice_process.nuvia_is_speaking.clear()

    def set_registration_mode(self, is_registering):
        """Activa o desactiva el envío de audio raw para el registro de voz."""
        if self.voice_process:
            if is_registering:
                self.voice_process.send_audio_event.set()
                logger.info("VoiceEngine: Modo registro ACTIVADO (enviando audio data).")
            else:
                self.voice_process.send_audio_event.clear()
                logger.info("VoiceEngine: Modo registro DESACTIVADO.")

    def stop(self):
        """Detiene el proceso y libera recursos."""
        self.is_running = False
        if self.voice_process:
            self.voice_process.stop() # Llamar al método stop del proceso
            self.voice_process.terminate()
            self.voice_process.join()
        logger.info("VoiceEngine: Proceso de voz detenido.")
