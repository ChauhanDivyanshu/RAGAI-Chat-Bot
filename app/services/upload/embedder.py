"""
BGE-M3 Embedding Service
Converts text to 1024-dimensional vectors
"""
from typing import List, Union
from sentence_transformers import SentenceTransformer
from loguru import logger
import numpy as np
from app.config import settings


class EmbedderService:
    """Singleton service for text embeddings using BGE-M3"""
    
    _instance = None
    _model = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def load_model(self):
        """Load BGE-M3 model (lazy loading)"""
        if self._model is None:
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
            logger.info("This will download ~2.5GB on first run, please wait...")
            
            self._model = SentenceTransformer(
                settings.EMBEDDING_MODEL,
                cache_folder=settings.MODELS_CACHE_DIR
            )
            
            logger.info(f"Model loaded! Embedding dimension: {self.dimension}")
        return self._model
    
    @property
    def dimension(self) -> int:
        """Get embedding dimension"""
        if self._model:
            return self._model.get_sentence_embedding_dimension()
        return 1024  # BGE-M3 default
    
    def embed_text(self, text: str) -> List[float]:
        """
        Embed single text to vector
        
        Args:
            text: Input text string
            
        Returns:
            List of 1024 floats (vector)
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        model = self.load_model()
        embedding = model.encode(
            text,
            normalize_embeddings=True,  # Important for cosine similarity
            show_progress_bar=False
        )
        return embedding.tolist()
    
    def embed_batch(self, texts: List[str], batch_size: int = None) -> List[List[float]]:
        """
        Embed multiple texts efficiently in batches
        
        Args:
            texts: List of text strings
            batch_size: How many to process at once
            
        Returns:
            List of embeddings (each is list of 1024 floats)
        """
        if not texts:
            return []
        
        # Filter empty texts
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            return []
        
        model = self.load_model()
        batch_size = batch_size or settings.EMBEDDING_BATCH_SIZE
        
        logger.info(f"Embedding {len(valid_texts)} texts in batches of {batch_size}")
        
        embeddings = model.encode(
            valid_texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        return embeddings.tolist()
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))


# Global instance
embedder = EmbedderService()
