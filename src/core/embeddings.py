"""
Embedding service for generating vector embeddings from text.
Uses sentence-transformers for local, free embedding generation.
Includes caching and performance monitoring for optimization.
"""

import structlog
from sentence_transformers import SentenceTransformer

from src.config import settings
from src.core.cache import get_embedding_cache
from src.core.performance import monitor_performance

logger = structlog.get_logger(__name__)


class EmbeddingService:
    """
    Service for generating text embeddings using sentence-transformers.
    
    Uses the all-MiniLM-L6-v2 model by default:
    - 384 dimensions
    - ~80MB model size
    - Fast inference on CPU
    - Good quality for semantic search
    """

    _instance: "EmbeddingService | None" = None
    _model: SentenceTransformer | None = None

    def __new__(cls) -> "EmbeddingService":
        """Singleton pattern to avoid loading model multiple times."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the embedding service."""
        if self._model is None:
            self._load_model()
        self._cache = get_embedding_cache()

    def _load_model(self) -> None:
        """Load the sentence transformer model."""
        model_name = settings.embedding_model
        logger.info("Loading embedding model", model=model_name)
        
        try:
            self._model = SentenceTransformer(model_name)
            logger.info(
                "Embedding model loaded successfully",
                model=model_name,
                embedding_dimension=self._model.get_sentence_embedding_dimension(),
            )
        except Exception as e:
            logger.error("Failed to load embedding model", model=model_name, error=str(e))
            raise

    @property
    def model(self) -> SentenceTransformer:
        """Get the loaded model."""
        if self._model is None:
            self._load_model()
        return self._model

    @property
    def embedding_dimension(self) -> int:
        """Get the dimension of the embedding vectors."""
        return self.model.get_sentence_embedding_dimension()

    @monitor_performance("embed_text")
    def embed_text(self, text: str) -> list[float]:
        """
        Generate embedding for a single text string with caching.

        Args:
            text: The text to embed.

        Returns:
            List of floats representing the embedding vector.
        """
        # Use cache to avoid redundant computation
        embedding = self._cache.get_embedding(
            text,
            lambda t: self.model.encode(t, convert_to_numpy=True),
        )
        return embedding.tolist()

    @monitor_performance("embed_texts_batch")
    def embed_texts(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """
        Generate embeddings for multiple texts in batches with caching.

        Args:
            texts: List of texts to embed.
            batch_size: Number of texts to process at once.

        Returns:
            List of embedding vectors.
        """
        if not texts:
            return []

        logger.debug("Embedding texts", count=len(texts), batch_size=batch_size)

        # Use batch caching for efficiency
        embeddings = self._cache.get_embeddings_batch(
            texts,
            lambda txts: self.model.encode(
                txts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=len(txts) > 100,
            ),
        )

        return [emb.tolist() for emb in embeddings]

    @monitor_performance("embed_query")
    def embed_query(self, query: str) -> list[float]:
        """
        Generate embedding for a search query with caching.

        Note: For most models, this is the same as embed_text.
        Some models have different encoding for queries vs documents.

        Args:
            query: The search query to embed.

        Returns:
            List of floats representing the query embedding.
        """
        return self.embed_text(query)


# Convenience function for getting embeddings
def get_embedding_service() -> EmbeddingService:
    """Get the singleton embedding service instance."""
    return EmbeddingService()
