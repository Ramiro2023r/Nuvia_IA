import os
import sys
import pyaudio
import numpy as np
import logging
from voice import VoiceRegistry, VoiceEngine

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("NuviaSetup")

def setup_vosk_model():
    """Instructions/Placeholder to ensure Vosk model exists."""
    model_path = "model"
    if not os.path.exists(model_path):
        print("\n" + "="*50)
        print("VOSK MODEL MISSING")
        print("="*50)
        print(f"Por favor, descarga el modelo de español desde:")
        print("https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip")
        print(f"Descomprímelo y renombra la carpeta a '{model_path}' en la raíz del proyecto.")
        print("="*50 + "\n")
        return False
    return True

def register_owner_flow():
    """Interactive flow to register the owner's voice."""
    registry = VoiceRegistry()
    
    if registry.is_owner_registered():
        choice = input("Ya existe un OWNER registrado. ¿Deseas sobreescribirlo? (s/n): ")
        if choice.lower() != 's':
            return

    print("\n--- REGISTRO BIOMÉTRICO DE VOZ ---")
    print("Por favor, prepárate para hablar durante 5 segundos.")
    print("Lee una frase clara, por ejemplo: 'Nuvia, activa el protocolo de seguridad'.")
    input("Presiona ENTER para comenzar a grabar...")

    # Recording parameters
    sample_rate = 16000
    duration = 5 # seconds
    chunk_size = 1024
    
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=sample_rate, input=True, frames_per_buffer=chunk_size)
    
    print("GRABANDO...")
    frames = []
    for _ in range(0, int(sample_rate / chunk_size * duration)):
        data = stream.read(chunk_size)
        frames.append(np.frombuffer(data, dtype=np.int16))
    
    print("GRABACIÓN COMPLETA.")
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    # Convert to float32
    audio_data = np.concatenate(frames).astype(np.float32) / 32768.0
    
    # Register
    success = registry.register_owner(audio_data, sample_rate)
    if success:
        print("\n¡ÉXITO! Tu voz ha sido registrada como OWNER.")
    else:
        print("\nERROR: No se pudo registrar la voz. Asegúrate de que el micrófono funciona.")

if __name__ == "__main__":
    if setup_vosk_model():
        register_owner_flow()
    else:
        # Still allow registration if SpeechBrain is working
        register_owner_flow()
