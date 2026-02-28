"""
voice/listen.py — Escucha continua y procesamiento de comandos directos (sin Wake Word).
"""

import os
import logging
import threading
import time
import speech_recognition as sr
from dotenv import load_dotenv

load_dotenv()

# Logger configuration
logger = logging.getLogger("NuviaVoice")

class ContinuousListener:
    """
    Escucha continua y procesamiento automático de comandos.
    Elimina la necesidad de decir "Nuevi".
    """

    def __init__(self, on_command, on_listening=None, on_processing=None):
        self.on_command = on_command
        self.on_listening = on_listening
        self.on_processing = on_processing
        
        self._recognizer = sr.Recognizer()
        # Ajustes de sensibilidad para evitar capturar ruidos de fondo constantes
        self._recognizer.energy_threshold = 400
        self._recognizer.dynamic_energy_threshold = True
        self._recognizer.pause_threshold = 0.8 # Esperar 0.8s de silencio para finalizar frase
        
        self._microphone = sr.Microphone()
        self._running = False
        self._thread = None

    def start(self):
        """Inicia el detector en un hilo dedicado."""
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("Modo escucha continua activado. Proceando comandos directos...")

    def stop(self):
        """Detiene la escucha."""
        self._running = False

    def recalibrate(self, source):
        """Calibra el ruido ambiental."""
        logger.info("Calibrando ruido ambiental...")
        self._recognizer.adjust_for_ambient_noise(source, duration=1.5)

    def _run_loop(self):
        """Bucle de escucha continua."""
        try:
            with self._microphone as source:
                self.recalibrate(source)
                
                while self._running:
                    # Notificar a la UI que estamos listos para escuchar
                    if self.on_listening:
                        self.on_listening()

                    try:
                        logger.info("Escuchando...")
                        # Escuchar con timeout pequeño para poder revisar self._running frecuentemente
                        audio = self._recognizer.listen(source, timeout=1, phrase_time_limit=10)
                        
                        # Notificar que estamos procesando el audio
                        if self.on_processing:
                            self.on_processing()

                        text = self._recognizer.recognize_google(audio, language="es-ES")
                        
                        if text:
                            logger.info(f"Comando detectado: '{text}'")
                            if self.on_command:
                                self.on_command(text)
                            
                            # Pequeña pausa tras un comando para evitar autoretrolimentación de los altavoces
                            time.sleep(1.0)
                            
                    except (sr.UnknownValueError, sr.WaitTimeoutError):
                        # No se detectó voz o no se entendió, simplemente continuamos
                        continue
                    except Exception as e:
                        logger.error(f"Error en reconocimiento: {e}")
                        time.sleep(1)

                    time.sleep(0.1)
                    
        except Exception as e:
            logger.error(f"Error fatal en el micrófono: {e}")
            self._running = False

# Alias para mantener compatibilidad con el orquestador
VoiceListener = ContinuousListener
WakeWordListener = ContinuousListener
