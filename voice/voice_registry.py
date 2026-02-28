# pickle removed for security — using numpy instead
import os
import logging
import numpy as np
from .speaker_recognition import SpeakerRecognition

logger = logging.getLogger("NuviaVoice")

class VoiceRegistry:
    """
    Handles registering and loading the OWNER's voice embedding.
    """
    def __init__(self, registry_path="owner_voice.npy"):
        self.registry_path = os.path.join(os.getcwd(), registry_path)
        self._sr = None

    @property
    def sr(self):
        if self._sr is None:
            from .speaker_recognition import SpeakerRecognition
            self._sr = SpeakerRecognition()
        return self._sr

    def is_owner_registered(self):
        """Checks if the OWNER's voice is already registered."""
        return os.path.exists(self.registry_path)

    def register_owner(self, audio_data, sample_rate=16000):
        """
        Extracts embedding from audio data and saves it as OWNER.
        """
        logger.info("Extracting embedding for OWNER registration...")
        embedding = self.sr.get_embedding_from_signal(audio_data, sample_rate)
        return self.register_owner_with_embedding(embedding)

    def register_owner_from_list(self, audio_list, sample_rate=16000):
        """
        Extracts embeddings from multiple audio chunks, averages them, and saves as OWNER.
        """
        embeddings = []
        for audio in audio_list:
            emb = self.sr.get_embedding_from_signal(audio, sample_rate)
            if emb is not None:
                embeddings.append(emb)
        
        if not embeddings:
            logger.error("No valid embeddings extracted from the list.")
            return False
            
        # Average the embeddings
        mean_embedding = np.mean(embeddings, axis=0)
        # Normalize the result (crucial for cosine similarity later)
        norm = np.linalg.norm(mean_embedding)
        if norm > 0:
            mean_embedding = mean_embedding / norm
            
        return self.register_owner_with_embedding(mean_embedding)

    def register_owner_with_embedding(self, embedding):
        """Saves a pre-calculated embedding as OWNER."""
        if embedding is not None:
            try:
                np.save(self.registry_path, embedding)
                logger.info(f"OWNER voice registered successfully at {self.registry_path}")
                return True
            except Exception as e:
                logger.error(f"Failed to save OWNER embedding: {e}")
        return False

    def load_owner_embedding(self):
        """Loads and returns the OWNER's embedding."""
        if not self.is_owner_registered():
            return None
        
        try:
            return np.load(self.registry_path, allow_pickle=False)
        except Exception as e:
            logger.error(f"Failed to load OWNER embedding: {e}")
            return None

    def delete_owner_registration(self):
        """Removes the OWNER's voice registration."""
        if self.is_owner_registered():
            os.remove(self.registry_path)
            logger.info("OWNER registration deleted.")
            return True
        return False
