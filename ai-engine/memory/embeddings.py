"""
Embedding Generation Utility for IncidentOS Engineering Memory Layer.

Provides vector embeddings for repository summaries, architecture descriptions,
and git metrics to enable semantic search in ChromaDB.
"""
import logging
from typing import List, Optional
import hashlib

logger = logging.getLogger(__name__)

# Try to import sentence-transformers for high-quality embeddings
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
    logger.info("sentence-transformers library available")
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers not available - using fallback embeddings")

# Global model instance (lazy loaded)
_embedding_model: Optional['SentenceTransformer'] = None


def _get_embedding_model() -> Optional['SentenceTransformer']:
    """
    Lazy-loads and returns the sentence-transformers model.
    
    Uses 'all-MiniLM-L6-v2' which is:
    - Fast (only 80MB)
    - Good quality (384-dimensional embeddings)
    - Optimized for semantic similarity
    
    Returns:
        SentenceTransformer model instance or None if unavailable
    """
    global _embedding_model
    
    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        return None
    
    if _embedding_model is None:
        try:
            logger.info("Loading sentence-transformers model: all-MiniLM-L6-v2")
            _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Successfully loaded embedding model")
        except Exception as e:
            logger.error(f"Failed to load sentence-transformers model: {e}")
            return None
    
    return _embedding_model


def generate_embeddings(text: str) -> List[float]:
    """
    Generates vector embeddings for the given text.
    
    Attempts to use sentence-transformers for high-quality embeddings.
    Falls back to a deterministic hash-based embedding if unavailable.
    
    Args:
        text: Input text to embed (repository summary, architecture description, etc.)
        
    Returns:
        List of floats representing the embedding vector
        - 384 dimensions if using sentence-transformers
        - 128 dimensions if using fallback
    """
    if not text or not text.strip():
        logger.warning("Empty text provided for embedding generation")
        return _generate_fallback_embedding("")
    
    # Try to use sentence-transformers
    model = _get_embedding_model()
    if model is not None:
        try:
            # Generate embedding using the model
            embedding = model.encode(text, convert_to_numpy=True)
            # Convert numpy array to list
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding with sentence-transformers: {e}")
            # Fall through to fallback
    
    # Use fallback embedding
    return _generate_fallback_embedding(text)


def _generate_fallback_embedding(text: str, dimensions: int = 128) -> List[float]:
    """
    Generates a deterministic fallback embedding using hash-based approach.
    
    This is a lightweight alternative when sentence-transformers is unavailable.
    While not as semantically rich, it provides consistent embeddings for
    identical text and maintains some distributional properties.
    
    Args:
        text: Input text to embed
        dimensions: Number of dimensions for the embedding vector (default: 128)
        
    Returns:
        List of floats representing the embedding vector
    """
    # Create a deterministic hash of the text
    text_hash = hashlib.sha256(text.encode('utf-8')).digest()
    
    # Generate embedding by converting hash bytes to normalized floats
    embedding = []
    for i in range(dimensions):
        # Use modulo to cycle through hash bytes
        byte_value = text_hash[i % len(text_hash)]
        # Normalize to [-1, 1] range
        normalized_value = (byte_value / 127.5) - 1.0
        embedding.append(normalized_value)
    
    return embedding


def generate_batch_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generates embeddings for multiple texts efficiently.
    
    Args:
        texts: List of text strings to embed
        
    Returns:
        List of embedding vectors, one for each input text
    """
    if not texts:
        return []
    
    # Try to use sentence-transformers batch encoding
    model = _get_embedding_model()
    if model is not None:
        try:
            embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
            return [emb.tolist() for emb in embeddings]
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            # Fall through to fallback
    
    # Use fallback for each text
    return [_generate_fallback_embedding(text) for text in texts]


def get_embedding_dimension() -> int:
    """
    Returns the dimensionality of embeddings generated by this module.
    
    Returns:
        384 if using sentence-transformers, 128 if using fallback
    """
    model = _get_embedding_model()
    if model is not None:
        return 384  # all-MiniLM-L6-v2 produces 384-dimensional embeddings
    return 128  # Fallback embedding dimension


def is_using_sentence_transformers() -> bool:
    """
    Checks if sentence-transformers is being used for embeddings.
    
    Returns:
        True if sentence-transformers is available and loaded, False otherwise
    """
    return _get_embedding_model() is not None


# Module-level info logging
logger.info(
    f"Embeddings module initialized. "
    f"Using {'sentence-transformers' if SENTENCE_TRANSFORMERS_AVAILABLE else 'fallback'} embeddings."
)

# Made with Bob
