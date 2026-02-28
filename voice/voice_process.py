"""
voice/voice_process.py — Proceso independiente para STT y reconocimiento de voz.
"""

import os
import json
import queue
import logging
import pyaudio
import vosk
import numpy as np
import threading
from collections import deque
from multiprocessing import Process, Queue as MPQueue, Event as MPEvent
from .speaker_recognition import SpeakerRecognition
from .security_layer import SecurityLayer

logger = logging.getLogger("VoiceProcess")

class VoiceProcess(Process):
    """
    Proceso secundario que maneja el micrófono y los modelos pesados (Vosk, SpeechBrain).
    Se comunica con el proceso principal a través de una cola de multiprocessing.
    """
    def __init__(self, result_queue, model_path="model", sample_rate=16000, threshold=0.75):
        super().__init__(daemon=True)
        self.result_queue = result_queue
        self.model_path = os.path.join(os.getcwd(), model_path)
        self.sample_rate = sample_rate
        self.threshold = threshold
        self.chunk_size = 4000
        self.is_running = MPEvent()
        self.nuvia_is_speaking = MPEvent() # Señal de que Nuvia está hablando
        self.send_audio_event = MPEvent()  # Señal para enviar audio de vuelta (usado en registro)

    def run(self):
        """Punto de entrada del proceso secundario."""
        logger.info(f"[VoiceProcess] Iniciando proceso de voz (PID: {os.getpid()})...")
        
        # 1. Cargar Modelos (DENTRO del proceso secundario)
        try:
            self.model = vosk.Model(self.model_path)
            self.recognizer = vosk.KaldiRecognizer(self.model, self.sample_rate)
            self.sr = SpeakerRecognition()
            self.security = SecurityLayer(threshold=self.threshold)
            logger.info("[VoiceProcess] Modelos cargados correctamente.")
        except Exception as e:
            logger.error(f"[VoiceProcess] Error cargando modelos: {e}")
            return

        # 2. Configurar el Micrófono
        self.p = pyaudio.PyAudio()
        self.audio_queue = queue.Queue()
        self.is_running.set()
        max_chunks = (self.sample_rate * 5) // self.chunk_size
        self._audio_buffer = deque(maxlen=max_chunks)

        try:
            self.stream = self.p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._pyaudio_callback
            )
        except Exception as e:
            logger.error(f"[VoiceProcess] Error abriendo micrófono: {e}")
            return

        # 3. Bucle de Procesamiento
        while self.is_running.is_set():
            try:
                data = self.audio_queue.get(timeout=1)
                
                # Biometría
                raw_floats = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                self._audio_buffer.append(raw_floats)
                
                # STT
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get("text", "")
                    
                    if text:
                        audio_utterance = np.concatenate(list(self._audio_buffer)) if self._audio_buffer else np.array([])
                        self._audio_buffer.clear()  # Reset
                        
                        speaker = self._identify_speaker(audio_utterance)
                        
                        msg = {
                            "type": "command",
                            "text": text,
                            "speaker": speaker
                        }
                        
                        # Si estamos en modo registro, adjuntamos el audio capturado
                        if self.send_audio_event.is_set():
                            msg["audio_data"] = audio_utterance
                            
                        self.result_queue.put(msg)
                else:
                    partial_res = json.loads(self.recognizer.PartialResult())
                    partial_text = partial_res.get("partial", "").strip()
                    
                    if partial_text:
                        # IMPLEMENTACIÓN: Dynamic Energy Gating
                        # Si Nuvia habla, requerimos más volumen para que cuente como interrupción
                        if self.nuvia_is_speaking.is_set(): # Use .is_set() for MPEvent
                            audio_np = np.frombuffer(data, dtype=np.int16)
                            rms = np.sqrt(np.mean(audio_np.astype(np.float32)**2))
                            
                            # Umbral experimental: 800 (Ajustable según mic)
                            if rms < 800:
                                continue
                                
                        self.result_queue.put({
                            "type": "partial",
                            "text": partial_text
                        })
                        # deque auto-descarta los chunks más viejos
                        
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"[VoiceProcess] Error en bucle: {e}")

    def _pyaudio_callback(self, in_data, frame_count, time_info, status):
        if self.is_running.is_set():
            self.audio_queue.put(in_data)
        return (None, pyaudio.paContinue)

    def _identify_speaker(self, audio_data):
        if len(audio_data) < self.sample_rate * 0.3:
            return "GUEST"
        embedding = self.sr.get_embedding_from_signal(audio_data, self.sample_rate)
        if embedding is not None:
            return self.security.verify_speaker(embedding)
        return "GUEST"

    def stop(self):
        self.is_running.clear()
        if hasattr(self, 'stream'):
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception:
                pass
        if hasattr(self, 'p'):
            try:
                self.p.terminate()
            except Exception:
                pass
