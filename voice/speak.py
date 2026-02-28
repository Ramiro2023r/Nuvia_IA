"""
voice/speak.py — Motor TTS de Nuvia usando Edge TTS + pygame.

Arquitectura:
  - Clase Speaker con threading + queue + asyncio interno
  - Audio generado en memoria (BytesIO) sin archivos temporales
  - Reproducción con pygame.mixer
  - Soporte para cambio dinámico de voz en caliente
  - Callbacks de UI para sincronización de animaciones
"""

import threading
import queue
import time
import logging
import asyncio
from io import BytesIO

logger = logging.getLogger("NuviaTTS")

# ── Inicialización lazy de pygame ──
_pygame_available = False
try:
    import pygame
    _pygame_available = True
except ImportError:
    logger.warning("[Nuvia TTS] pygame no instalado. Instala con: pip install pygame")


class Speaker:
    """Motor TTS con Edge TTS y reproducción via pygame."""

    def __init__(self, default_voice="es-PE-AlexNeural"):
        self._queue = queue.Queue()
        self.on_start = None
        self.on_stop = None
        self.is_speaking = False
        self.current_text = ""
        self._current_voice = default_voice
        self._stop_requested = False
        self._lock = threading.Lock()
        self._mixer_ready = False

        # Inicializar pygame mixer
        if _pygame_available:
            try:
                pygame.mixer.init(frequency=24000, size=-16, channels=1, buffer=4096)
                self._mixer_ready = True
                logger.info("[Nuvia TTS] pygame mixer inicializado correctamente.")
            except Exception as e:
                logger.error(f"[Nuvia TTS] Error inicializando pygame mixer: {e}")

        # Worker thread con su propio event loop para edge_tts
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def _worker(self):
        """Hilo worker que procesa la cola de textos."""
        # Crear event loop dedicado para este hilo
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        while True:
            try:
                text = self._queue.get()
                if text is None:
                    break

                with self._lock:
                    if self._stop_requested:
                        self._stop_requested = False
                        self._queue.task_done()
                        continue
                    self.is_speaking = True
                    self._stop_requested = False

                # Notificar inicio
                if self.on_start:
                    try:
                        self.on_start()
                    except Exception:
                        pass

                with self._lock:
                    self.current_text = text

                logger.info(f"[Nuvia TTS] Hablando con voz {self._current_voice}: '{text[:60]}...'")

                try:
                    # Generar audio con Edge TTS
                    audio_buffer = loop.run_until_complete(
                        self._generate_audio(text, self._current_voice)
                    )

                    if audio_buffer and self._mixer_ready:
                        self._play_audio(audio_buffer)
                    elif not self._mixer_ready:
                        logger.warning("[Nuvia TTS] pygame no disponible, texto no reproducido.")

                except Exception as e:
                    logger.error(f"[Nuvia TTS] Error procesando TTS: {e}")

                with self._lock:
                    self.current_text = ""
                    self.is_speaking = False
                    self._stop_requested = False

                # Notificar fin
                if self.on_stop:
                    try:
                        self.on_stop()
                    except Exception:
                        pass

                self._queue.task_done()
                time.sleep(0.05)

            except Exception as e:
                logger.error(f"[Nuvia TTS] Error crítico en worker: {e}")
                with self._lock:
                    self.is_speaking = False
                    self.current_text = ""
                time.sleep(1)

        loop.close()

    async def _generate_audio(self, text: str, voice: str) -> BytesIO | None:
        """Genera audio MP3 en memoria usando Edge TTS."""
        try:
            import edge_tts
            communicate = edge_tts.Communicate(text, voice)
            audio_buffer = BytesIO()

            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_buffer.write(chunk["data"])
                # Verificar interrupción durante la generación
                with self._lock:
                    if self._stop_requested:
                        logger.info("[Nuvia TTS] Generación interrumpida por stop.")
                        return None

            if audio_buffer.tell() == 0:
                logger.warning("[Nuvia TTS] Edge TTS no generó audio.")
                return None

            audio_buffer.seek(0)
            return audio_buffer

        except Exception as e:
            logger.error(f"[Nuvia TTS] Error generando audio con Edge TTS: {e}")
            return None

    def _play_audio(self, audio_buffer: BytesIO):
        """Reproduce un buffer MP3 usando pygame.mixer."""
        try:
            pygame.mixer.music.load(audio_buffer, "speech.mp3")
            pygame.mixer.music.play()

            # Esperar a que termine o sea interrumpido
            while pygame.mixer.music.get_busy():
                with self._lock:
                    if self._stop_requested:
                        pygame.mixer.music.stop()
                        logger.info("[Nuvia TTS] Reproducción interrumpida.")
                        break
                time.sleep(0.05)

        except Exception as e:
            logger.error(f"[Nuvia TTS] Error reproduciendo audio: {e}")

    def speak(self, text: str):
        """Encola texto para ser hablado."""
        with self._lock:
            self._stop_requested = False
        self._queue.put(text)

    def stop(self):
        """Interrupción inmediata: limpia cola y detiene reproducción."""
        with self._lock:
            self._stop_requested = True
            # Vaciar cola
            try:
                while not self._queue.empty():
                    self._queue.get_nowait()
                    self._queue.task_done()
            except Exception:
                pass

        # Detener pygame
        if self._mixer_ready:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass

    def change_voice(self, voice_id: str):
        """Cambia la voz activa de Edge TTS."""
        old_voice = self._current_voice
        self._current_voice = voice_id
        logger.info(f"[Nuvia TTS] Voz cambiada: {old_voice} → {voice_id}")

    def get_current_voice(self) -> str:
        """Retorna el voice ID activo."""
        return self._current_voice


# ══════════════════════════════════════════════════════════════════════════════
# INSTANCIA SINGLETON Y FUNCIONES PÚBLICAS
# ══════════════════════════════════════════════════════════════════════════════

_speaker = Speaker()


def get_current_text() -> str:
    """Retorna el texto que se está hablando actualmente."""
    with _speaker._lock:
        return _speaker.current_text


def set_voice_callbacks(on_start, on_stop):
    """Registra callbacks de UI para inicio/fin de habla."""
    _speaker.on_start = on_start
    _speaker.on_stop = on_stop


def speak(text: str):
    """Habla el texto dado con la voz activa."""
    _speaker.speak(text)


def stop_speak():
    """Detiene la reproducción inmediatamente."""
    _speaker.stop()


def is_speaking() -> bool:
    """Retorna True si Nuvia está hablando."""
    with _speaker._lock:
        return _speaker.is_speaking


def speak_async(text: str):
    """Alias de speak() para compatibilidad."""
    speak(text)


def change_voice(voice_id: str):
    """Cambia la voz de Edge TTS activa."""
    _speaker.change_voice(voice_id)


def get_current_voice() -> str:
    """Retorna el voice ID activo."""
    return _speaker.get_current_voice()
