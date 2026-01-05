"""
Advanced caching system for performance optimization.

Features:
- LRU cache for embeddings
- Semantic cache for query results
- TTL-based expiration
- Cache hit/miss tracking
- Integration with performance monitoring
"""

import hashlib
import pickle
import time
from collections import OrderedDict
from dataclasses import dataclass
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import structlog

from src.core.performance import PerformanceMonitor

logger = structlog.get_logger(__name__)


# ============================================================================
# LRU Cache with TTL
# ============================================================================


@dataclass
class CacheEntry:
    """Cache entry with value and metadata."""

    value: Any
    created_at: float
    access_count: int = 0
    last_accessed: float = 0.0

    def is_expired(self, ttl: Optional[float] = None) -> bool:
        """Check if entry is expired."""
        if ttl is None:
            return False
        return (time.time() - self.created_at) > ttl


class LRUCache:
    """
    Thread-safe LRU cache with TTL support.

    Features:
    - Least Recently Used eviction
    - Time-To-Live expiration
    - Thread-safe operations
    - Performance metrics tracking

    Usage:
        cache = LRUCache(max_size=1000, ttl=3600)
        cache.put("key", "value")
        value = cache.get("key")
    """

    def __init__(
        self,
        max_size: int = 1000,
        ttl: Optional[float] = None,
        name: str = "lru_cache",
    ):
        """
        Initialize LRU cache.

        Args:
            max_size: Maximum number of entries
            ttl: Time-to-live in seconds (None = no expiration)
            name: Cache name for metrics
        """
        self.max_size = max_size
        self.ttl = ttl
        self.name = name
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = Lock()

        # Register with performance monitor
        monitor = PerformanceMonitor.get_instance()
        monitor.register_cache(self.name, max_size)

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        monitor = PerformanceMonitor.get_instance()

        with self._lock:
            if key not in self._cache:
                monitor.record_cache_miss(self.name)
                return None

            entry = self._cache[key]

            # Check expiration
            if entry.is_expired(self.ttl):
                del self._cache[key]
                monitor.record_cache_miss(self.name)
                monitor.record_cache_eviction(self.name)
                monitor.update_cache_size(self.name, len(self._cache))
                return None

            # Update access metadata
            entry.access_count += 1
            entry.last_accessed = time.time()

            # Move to end (most recently used)
            self._cache.move_to_end(key)

            monitor.record_cache_hit(self.name)
            return entry.value

    def put(self, key: str, value: Any) -> None:
        """
        Put value in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        monitor = PerformanceMonitor.get_instance()

        with self._lock:
            # Update existing entry
            if key in self._cache:
                entry = self._cache[key]
                entry.value = value
                entry.created_at = time.time()
                self._cache.move_to_end(key)
                return

            # Create new entry
            entry = CacheEntry(
                value=value,
                created_at=time.time(),
                last_accessed=time.time(),
            )
            self._cache[key] = entry

            # Evict if over capacity
            if len(self._cache) > self.max_size:
                evicted_key, _ = self._cache.popitem(last=False)
                monitor.record_cache_eviction(self.name)
                logger.debug(
                    "cache_eviction",
                    cache=self.name,
                    evicted_key=evicted_key[:50],
                )

            monitor.update_cache_size(self.name, len(self._cache))

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            monitor = PerformanceMonitor.get_instance()
            monitor.update_cache_size(self.name, 0)

    def size(self) -> int:
        """Get current cache size."""
        with self._lock:
            return len(self._cache)

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_accesses = sum(entry.access_count for entry in self._cache.values())
            return {
                "name": self.name,
                "size": len(self._cache),
                "max_size": self.max_size,
                "total_accesses": total_accesses,
                "ttl": self.ttl,
            }


# ============================================================================
# Embedding Cache
# ============================================================================


class EmbeddingCache:
    """
    Cache for text embeddings.

    Caches embeddings to avoid redundant computation.
    Uses content hashing for cache keys.

    Usage:
        cache = EmbeddingCache(max_size=5000)
        embedding = cache.get_embedding(text, embed_fn)
    """

    def __init__(self, max_size: int = 5000, ttl: float = 3600):
        """
        Initialize embedding cache.

        Args:
            max_size: Maximum number of cached embeddings
            ttl: Time-to-live in seconds (default: 1 hour)
        """
        self.cache = LRUCache(
            max_size=max_size,
            ttl=ttl,
            name="embedding_cache",
        )

    def _get_key(self, text: str) -> str:
        """Generate cache key from text."""
        return hashlib.sha256(text.encode()).hexdigest()

    def get_embedding(
        self,
        text: str,
        embed_fn: Any,
    ) -> np.ndarray:
        """
        Get embedding with caching.

        Args:
            text: Text to embed
            embed_fn: Function to generate embedding

        Returns:
            Embedding vector
        """
        key = self._get_key(text)
        cached = self.cache.get(key)

        if cached is not None:
            logger.debug("embedding_cache_hit", text_length=len(text))
            return cached

        # Generate embedding
        logger.debug("embedding_cache_miss", text_length=len(text))
        embedding = embed_fn(text)

        # Cache it
        self.cache.put(key, embedding)

        return embedding

    def get_embeddings_batch(
        self,
        texts: List[str],
        embed_fn: Any,
    ) -> List[np.ndarray]:
        """
        Get multiple embeddings with caching.

        Args:
            texts: List of texts to embed
            embed_fn: Function to generate embeddings (single or batch)

        Returns:
            List of embedding vectors
        """
        embeddings = []
        uncached_indices = []
        uncached_texts = []

        # Check cache for each text
        for i, text in enumerate(texts):
            key = self._get_key(text)
            cached = self.cache.get(key)

            if cached is not None:
                embeddings.append(cached)
            else:
                embeddings.append(None)  # Placeholder
                uncached_indices.append(i)
                uncached_texts.append(text)

        # Generate uncached embeddings
        if uncached_texts:
            logger.debug(
                "embedding_batch_cache_miss",
                total=len(texts),
                uncached=len(uncached_texts),
                hit_rate=round((1 - len(uncached_texts) / len(texts)) * 100, 2),
            )

            # Generate embeddings for uncached texts
            new_embeddings = embed_fn(uncached_texts)

            # Fill in placeholders and cache
            for idx, text, embedding in zip(uncached_indices, uncached_texts, new_embeddings):
                embeddings[idx] = embedding
                key = self._get_key(text)
                self.cache.put(key, embedding)

        return embeddings

    def clear(self) -> None:
        """Clear all cached embeddings."""
        self.cache.clear()


# ============================================================================
# Semantic Query Cache
# ============================================================================


class SemanticQueryCache:
    """
    Cache for query results with semantic similarity matching.

    Caches query results and retrieves them for semantically similar queries.
    Uses cosine similarity for matching.

    Usage:
        cache = SemanticQueryCache(max_size=100, similarity_threshold=0.95)
        result = cache.get(query, query_embedding)
        cache.put(query, query_embedding, result)
    """

    def __init__(
        self,
        max_size: int = 100,
        similarity_threshold: float = 0.95,
        ttl: float = 1800,
    ):
        """
        Initialize semantic query cache.

        Args:
            max_size: Maximum number of cached queries
            similarity_threshold: Minimum cosine similarity for cache hit (0-1)
            ttl: Time-to-live in seconds (default: 30 minutes)
        """
        self.max_size = max_size
        self.similarity_threshold = similarity_threshold
        self.ttl = ttl
        self.name = "semantic_query_cache"
        self._cache: List[Tuple[str, np.ndarray, Any, float]] = []
        self._lock = Lock()

        # Register with performance monitor
        monitor = PerformanceMonitor.get_instance()
        monitor.register_cache(self.name, max_size)

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    def get(self, query: str, query_embedding: np.ndarray) -> Optional[Any]:
        """
        Get cached result for semantically similar query.

        Args:
            query: Query text
            query_embedding: Query embedding vector

        Returns:
            Cached result if similar query found, None otherwise
        """
        monitor = PerformanceMonitor.get_instance()

        with self._lock:
            current_time = time.time()

            # Find most similar cached query
            best_similarity = 0.0
            best_result = None

            for cached_query, cached_embedding, cached_result, created_at in self._cache:
                # Check expiration
                if self.ttl and (current_time - created_at) > self.ttl:
                    continue

                # Calculate similarity
                similarity = self._cosine_similarity(query_embedding, cached_embedding)

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_result = cached_result

            # Check if similarity meets threshold
            if best_similarity >= self.similarity_threshold:
                monitor.record_cache_hit(self.name)
                logger.info(
                    "semantic_cache_hit",
                    query=query[:100],
                    similarity=round(best_similarity, 4),
                )
                return best_result

            monitor.record_cache_miss(self.name)
            return None

    def put(self, query: str, query_embedding: np.ndarray, result: Any) -> None:
        """
        Cache query result.

        Args:
            query: Query text
            query_embedding: Query embedding vector
            result: Query result to cache
        """
        monitor = PerformanceMonitor.get_instance()

        with self._lock:
            # Remove expired entries
            current_time = time.time()
            self._cache = [
                entry
                for entry in self._cache
                if not self.ttl or (current_time - entry[3]) <= self.ttl
            ]

            # Add new entry
            self._cache.append((query, query_embedding, result, current_time))

            # Evict oldest if over capacity
            if len(self._cache) > self.max_size:
                self._cache.pop(0)
                monitor.record_cache_eviction(self.name)

            monitor.update_cache_size(self.name, len(self._cache))

    def clear(self) -> None:
        """Clear all cached queries."""
        with self._lock:
            self._cache.clear()
            monitor = PerformanceMonitor.get_instance()
            monitor.update_cache_size(self.name, 0)

    def size(self) -> int:
        """Get current cache size."""
        with self._lock:
            return len(self._cache)


# ============================================================================
# Global Cache Instances
# ============================================================================

# Singleton cache instances
_embedding_cache: Optional[EmbeddingCache] = None
_query_cache: Optional[SemanticQueryCache] = None


def get_embedding_cache() -> EmbeddingCache:
    """Get global embedding cache instance."""
    global _embedding_cache
    if _embedding_cache is None:
        _embedding_cache = EmbeddingCache(max_size=5000, ttl=3600)
    return _embedding_cache


def get_query_cache() -> SemanticQueryCache:
    """Get global query cache instance."""
    global _query_cache
    if _query_cache is None:
        _query_cache = SemanticQueryCache(
            max_size=100,
            similarity_threshold=0.95,
            ttl=1800,
        )
    return _query_cache
