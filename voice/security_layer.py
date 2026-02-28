import numpy as np
from .voice_registry import VoiceRegistry
import logging

logger = logging.getLogger("NuviaVoice")

class SecurityLayer:
    """
    Compares speaker embeddings to determine if the speaker is the OWNER.
    """
    def __init__(self, threshold=0.75):
        self.threshold = threshold
        self.registry = VoiceRegistry()
        self.owner_embedding = self.registry.load_owner_embedding()

    def set_threshold(self, new_threshold):
        """Allows dynamic adjustment of the security sensitivity."""
        self.threshold = new_threshold
        logger.info(f"Security threshold updated to: {self.threshold}")

    def reload_owner_embedding(self):
        """Force reload the owner embedding from the pkl file."""
        self.owner_embedding = self.registry.load_owner_embedding()

    def verify_speaker(self, current_embedding):
        """
        Compares current voice embedding with owner's.
        Returns "OWNER" or "GUEST".
        """
        if self.owner_embedding is None:
            # No owner registered yet
            return "GUEST"

        if current_embedding is None:
            return "GUEST"

        # Calculate Cosine Similarity
        similarity = self._calculate_similarity(self.owner_embedding, current_embedding)
        
        # Log the result for debugging/audit
        is_owner = similarity >= self.threshold
        result = "OWNER" if is_owner else "GUEST"
        
        logger.info(f"Security Check: Similarity={similarity:.4f} | Result={result} | Threshold={self.threshold}")
        
        return result

    def _calculate_similarity(self, embedding1, embedding2):
        """Internal helper for cosine similarity."""
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return dot_product / (norm1 * norm2)
