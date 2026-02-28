import torch
import torchaudio
import numpy as np
import os
import logging

# --- MONKEY-PATCH PARA TORCHAUDIO (Compatibilidad con SpeechBrain) ---
# Las versiones nuevas de torchaudio eliminaron list_audio_backends, pero SpeechBrain lo busca.
if not hasattr(torchaudio, "list_audio_backends"):
    torchaudio.list_audio_backends = lambda: [] # Simular que no hay backends específicos
# -------------------------------------------------------------------

# --- MONKEY-PATCH PARA HUGGINGFACE_HUB (Compatibilidad con SpeechBrain) ---
# SpeechBrain usa 'use_auth_token', pero las versiones nuevas de HF esperan 'token'.
try:
    import huggingface_hub
    import huggingface_hub.file_download
    
    # Algunas versiones de HF Hub pueden tener hf_hub_download en diferentes lugares
    if hasattr(huggingface_hub.file_download, "hf_hub_download"):
        original_hf_download = huggingface_hub.file_download.hf_hub_download

        def patched_hf_hub_download(*args, **kwargs):
            if 'use_auth_token' in kwargs:
                kwargs['token'] = kwargs.pop('use_auth_token')
            
            filename = kwargs.get('filename') or (args[1] if len(args) > 1 else "")
            repo_id = kwargs.get('repo_id') or (args[0] if len(args) > 0 else "")
            savedir = kwargs.get('local_dir')
            
            try:
                return original_hf_download(*args, **kwargs)
            except Exception as e:
                # Si falló la descarga remota de custom.py, intentamos ver si existe local
                if "custom.py" in str(filename) and ("404" in str(e) or "Entry Not Found" in str(e)):
                    if savedir and os.path.exists(os.path.join(savedir, "custom.py")):
                        return os.path.join(savedir, "custom.py")
                    # Si no existe, pero es el modelo ecapa-voxceleb, sabemos que NO lo necesita
                    if "spkrec-ecapa-voxceleb" in str(repo_id):
                        # Retornar un path a un archivo vacío temporal si es necesario
                        dummy_path = os.path.join(os.getcwd(), "models", "spkrec-ecapa-voxceleb", "custom.py")
                        if os.path.exists(dummy_path):
                            return dummy_path
                raise e

        huggingface_hub.file_download.hf_hub_download = patched_hf_hub_download
        if hasattr(huggingface_hub, "hf_hub_download"):
            huggingface_hub.hf_hub_download = patched_hf_hub_download
except ImportError:
    pass
# -------------------------------------------------------------------

try:
    # Intentar importar de la ubicación más común en SpeechBrain v0.5.15+
    from speechbrain.inference.speaker import EncoderClassifier
except ImportError:
    try:
        from speechbrain.inference import EncoderClassifier
    except ImportError:
        try:
            from speechbrain.pretrained import EncoderClassifier
        except ImportError:
            EncoderClassifier = None

logger = logging.getLogger("NuviaVoice")

class SpeakerRecognition:
    """
    Handles speaker identification using SpeechBrain embeddings.
    """
    def __init__(self, model_source="speechbrain/spkrec-ecapa-voxceleb"):
        if EncoderClassifier is None:
            logger.error("SpeechBrain not installed. Speaker recognition will not work.")
            self.classifier = None
            return

        logger.info(f"Loading speaker recognition model: {model_source}")
        # Create models directory if it doesn't exist
        models_dir = os.path.join(os.getcwd(), "models", "spkrec-ecapa-voxceleb")
        os.makedirs(models_dir, exist_ok=True)
        
        try:
            self.classifier = EncoderClassifier.from_hparams(
                source=model_source, 
                savedir=models_dir,
                run_opts={"device": "cpu"} # Force CPU for 8GB RAM optimization
            )
        except Exception as e:
            logger.error(f"Error loading SpeechBrain model: {e}")
            self.classifier = None

    def get_embedding(self, wav_path):
        """
        Extracts speaker embedding from a wav file.
        Returns a numpy array.
        """
        if self.classifier is None:
            logger.error("Classifier not initialized.")
            return None

        try:
            signal, fs = torchaudio.load(wav_path)
            # Ensure audio is mono and at the correct sample rate (usually 16kHz for this model)
            # SpeechBrain's EncoderClassifier usually handles resample if needed via hparams
            embeddings = self.classifier.encode_batch(signal)
            # Squeeze and convert to numpy
            return embeddings.squeeze(0).detach().cpu().numpy().flatten()
        except Exception as e:
            logger.error(f"Error extracting embedding from {wav_path}: {e}")
            return None

    def get_embedding_from_signal(self, signal_numpy, sample_rate=16000):
        """
        Extracts speaker embedding from a numpy array.
        """
        if self.classifier is None:
            return None

        try:
            # Convert numpy to torch tensor
            signal = torch.from_numpy(signal_numpy).float().unsqueeze(0)
            embeddings = self.classifier.encode_batch(signal)
            return embeddings.squeeze(0).detach().cpu().numpy().flatten()
        except Exception as e:
            logger.error(f"Error extracting embedding from signal: {e}")
            return None
