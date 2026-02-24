import pyttsx3
import threading
import queue
import time

class Speaker:
    def __init__(self):
        self._queue = queue.Queue()
        self.on_start = None  # Callback para cuando empieza a hablar
        self.on_stop = None   # Callback para cuando termina
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def _worker(self):
        while True:
            text = self._queue.get()
            if text is None: break
            
            try:
                # RE-INICIALIZAR CADA VEZ asegura que el driver de Windows no se pierda
                engine = pyttsx3.init()
                self._configure_engine(engine)
                
                print(f"[Nuvia TTS] Hablando: '{text[:50]}...'")
                engine.say(text)

                # Disparar callback de inicio (boca on) justo antes de empezar el sonido
                if self.on_start:
                    self.on_start()

                engine.runAndWait()
                print("[Nuvia TTS] Fin de habla.")
                
                # Forzar limpieza
                del engine

                # Disparar callback de fin (boca off)
                if self.on_stop:
                    self.on_stop()

            except Exception as e:
                print(f"[Nuvia TTS] Error al hablar: {e}")
                if self.on_stop:
                    self.on_stop()
            finally:
                self._queue.task_done()
                time.sleep(0.1) # Breve pausa entre frases

    def _configure_engine(self, engine):
        """Configura la voz femenina y velocidad."""
        voices = engine.getProperty('voices')
        female_voice = None

        print("[Nuvia TTS] Voces disponibles:")
        for v in voices:
            print(f" - {v.name} (id: {v.id})")
            name_lower = v.name.lower()
            if any(n in name_lower for n in ['zira', 'helena', 'sabina', 'elsy', 'pablo']):
                if 'spanish' in name_lower or 'español' in name_lower or not female_voice:
                    female_voice = v.id

        if female_voice:
            engine.setProperty('voice', female_voice)
            print(f"[Nuvia TTS] Voz seleccionada: {female_voice}")
        elif voices:
            engine.setProperty('voice', voices[0].id)
            print(f"[Nuvia TTS] Fallback voz: {voices[0].id}")

        engine.setProperty('rate', 180)
        engine.setProperty('volume', 1.0)

    def speak(self, text: str):
        self._queue.put(text)

# Instancia única
_speaker = Speaker()

def set_voice_callbacks(on_start, on_stop):
    """Permite a la UI suscribirse de inicio y fin de habla."""
    _speaker.on_start = on_start
    _speaker.on_stop = on_stop

def speak(text: str):
    """Agrega texto a la cola de habla."""
    _speaker.speak(text)

def speak_async(text: str):
    """Alias para compatibilidad, ya es asíncrono por la cola."""
    speak(text)
