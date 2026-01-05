"""
Cross-Encoder Re-ranking Module

Provides cross-encoder based re-ranking for improved search result accuracy.
Cross-encoders process query-document pairs together for more accurate scoring,
but are slower than bi-encoders, so they're used as a second-stage re-ranker.

Typical usage:
1. Retrieve top-k candidates (k=50-100) with fast retrieval (vector/BM25/hybrid)
2. Re-rank top-n (n=10-20) with cross-encoder for final results

Author: API Assistant Team
Date: 2025-12-27
"""

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import structlog
from sentence_transformers import CrossEncoder as STCrossEncoder

from src.core.cache import LRUCache

logger = structlog.get_logger(__name__)


@dataclass
class RerankResult:
    """Result from cross-encoder re-ranking."""

    doc_id: str
    content: str
    metadata: Dict[str, Any]
    original_score: float
    rerank_score: float
    original_rank: int
    rerank_rank: int
    method: str = "cross_encoder"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "doc_id": self.doc_id,
            "content": self.content,
            "metadata": self.metadata,
            "score": self.rerank_score,
            "original_score": self.original_score,
            "original_rank": self.original_rank,
            "rank": self.rerank_rank,
            "method": self.method,
        }


class CrossEncoderReranker:
    """
    Cross-encoder based re-ranker for improving search result accuracy.

    Cross-encoders process query and document together, allowing them to
    capture fine-grained interactions and provide more accurate relevance scores.

    This is used as a second-stage re-ranker after fast retrieval methods.
    """

    # Popular cross-encoder models
    MODELS = {
        "ms-marco-mini-lm-6": "cross-encoder/ms-marco-MiniLM-L-6-v2",  # Fast, good quality
        "ms-marco-mini-lm-12": "cross-encoder/ms-marco-MiniLM-L-12-v2",  # Slower, better
        "ms-marco-electra": "cross-encoder/ms-marco-electra-base",  # Best quality, slowest
    }

    def __init__(
        self,
        model_name: str = "ms-marco-mini-lm-6",
        device: Optional[str] = None,
        max_length: int = 512,
        batch_size: int = 32,
        use_cache: bool = True,
    ):
        """
        Initialize cross-encoder re-ranker.

        Args:
            model_name: Model to use (see MODELS dict)
            device: Device to use (None=auto, 'cuda', 'cpu')
            max_length: Maximum sequence length
            batch_size: Batch size for processing
            use_cache: Whether to cache rerank scores
        """
        self.model_name = model_name
        self.max_length = max_length
        self.batch_size = batch_size
        self.use_cache = use_cache

        # Get model path
        if model_name in self.MODELS:
            model_path = self.MODELS[model_name]
        else:
            model_path = model_name  # Allow custom model paths

        logger.info(
            "Initializing CrossEncoder",
            model_name=model_name,
            model_path=model_path,
            max_length=max_length,
            batch_size=batch_size,
        )

        # Load model
        start_time = time.time()
        self.model = STCrossEncoder(model_path, max_length=max_length, device=device)
        load_time = time.time() - start_time

        logger.info(
            "CrossEncoder loaded successfully",
            model_name=model_name,
            load_time_seconds=round(load_time, 2),
        )

        # Cache for rerank scores
        if use_cache:
            self.cache = LRUCache(
                max_size=10000,
                ttl=3600,
                name="cross_encoder_cache",
            )
        else:
            self.cache = None

    def _compute_scores(
        self, query: str, documents: List[str]
    ) -> List[float]:
        """
        Compute relevance scores for query-document pairs.

        Args:
            query: Search query
            documents: List of document texts

        Returns:
            List of relevance scores
        """
        # Create query-document pairs
        pairs = [(query, doc) for doc in documents]

        # Check cache
        if self.cache:
            cached_scores = []
            uncached_pairs = []
            uncached_indices = []

            for i, (q, doc) in enumerate(pairs):
                cache_key = f"{q}||{doc}"
                cached_score = self.cache.get(cache_key)
                if cached_score is not None:
                    cached_scores.append((i, cached_score))
                else:
                    uncached_pairs.append((q, doc))
                    uncached_indices.append(i)

            logger.debug(
                "cross_encoder_cache_stats",
                total=len(pairs),
                cached=len(cached_scores),
                uncached=len(uncached_pairs),
                hit_rate=round(len(cached_scores) / len(pairs), 3) if pairs else 0,
            )

            # Compute uncached scores
            if uncached_pairs:
                uncached_scores = self.model.predict(
                    uncached_pairs, batch_size=self.batch_size
                ).tolist()

                # Cache the new scores
                for (q, doc), score in zip(uncached_pairs, uncached_scores):
                    cache_key = f"{q}||{doc}"
                    self.cache.put(cache_key, score)
            else:
                uncached_scores = []

            # Combine cached and uncached scores in original order
            all_scores = [0.0] * len(pairs)
            for i, score in cached_scores:
                all_scores[i] = score
            for i, score in zip(uncached_indices, uncached_scores):
                all_scores[i] = score

            return all_scores
        else:
            # No caching
            scores = self.model.predict(pairs, batch_size=self.batch_size)
            return scores.tolist()

    def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: Optional[int] = None,
    ) -> List[RerankResult]:
        """
        Re-rank search results using cross-encoder.

        Args:
            query: Search query
            results: List of search results (must have 'content', 'score', 'metadata')
            top_k: Number of top results to return (None=all)

        Returns:
            List of re-ranked results
        """
        if not results:
            logger.debug("No results to rerank")
            return []

        logger.debug(
            "Reranking with cross-encoder",
            query=query,
            num_results=len(results),
            top_k=top_k,
        )

        start_time = time.time()

        # Extract documents
        documents = [r.get("content", "") for r in results]

        # Compute cross-encoder scores
        rerank_scores = self._compute_scores(query, documents)

        # Create RerankResult objects
        rerank_results = []
        for i, (result, rerank_score) in enumerate(zip(results, rerank_scores)):
            rerank_result = RerankResult(
                doc_id=result.get("id", result.get("doc_id", f"doc_{i}")),
                content=result.get("content", ""),
                metadata=result.get("metadata", {}),
                original_score=result.get("score", 0.0),
                rerank_score=float(rerank_score),
                original_rank=i + 1,
                rerank_rank=0,  # Will be set after sorting
            )
            rerank_results.append(rerank_result)

        # Sort by rerank score
        rerank_results.sort(key=lambda x: x.rerank_score, reverse=True)

        # Update rerank ranks
        for i, result in enumerate(rerank_results):
            result.rerank_rank = i + 1

        # Limit to top_k
        if top_k is not None:
            rerank_results = rerank_results[:top_k]

        rerank_time = time.time() - start_time

        logger.info(
            "Reranking completed",
            query_length=len(query),
            num_results=len(results),
            top_k=top_k or len(results),
            rerank_time_seconds=round(rerank_time, 3),
        )

        return rerank_results

    def rerank_to_dicts(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Re-rank and return results as dictionaries.

        Args:
            query: Search query
            results: List of search results
            top_k: Number of top results to return

        Returns:
            List of re-ranked results as dictionaries
        """
        rerank_results = self.rerank(query, results, top_k)
        return [r.to_dict() for r in rerank_results]

    def score_pairs(
        self, query_doc_pairs: List[Tuple[str, str]]
    ) -> List[float]:
        """
        Score query-document pairs directly.

        Args:
            query_doc_pairs: List of (query, document) tuples

        Returns:
            List of relevance scores
        """
        if not query_doc_pairs:
            return []

        logger.debug(
            "Scoring query-document pairs",
            num_pairs=len(query_doc_pairs),
        )

        # Check cache
        if self.cache:
            cached_scores = []
            uncached_pairs = []
            uncached_indices = []

            for i, (q, doc) in enumerate(query_doc_pairs):
                cache_key = f"{q}||{doc}"
                cached_score = self.cache.get(cache_key)
                if cached_score is not None:
                    cached_scores.append((i, cached_score))
                else:
                    uncached_pairs.append((q, doc))
                    uncached_indices.append(i)

            # Compute uncached
            if uncached_pairs:
                uncached_scores = self.model.predict(
                    uncached_pairs, batch_size=self.batch_size
                ).tolist()

                # Cache
                for (q, doc), score in zip(uncached_pairs, uncached_scores):
                    cache_key = f"{q}||{doc}"
                    self.cache.put(cache_key, score)
            else:
                uncached_scores = []

            # Combine
            all_scores = [0.0] * len(query_doc_pairs)
            for i, score in cached_scores:
                all_scores[i] = score
            for i, score in zip(uncached_indices, uncached_scores):
                all_scores[i] = score

            return all_scores
        else:
            scores = self.model.predict(query_doc_pairs, batch_size=self.batch_size)
            return scores.tolist()

    def get_cache_stats(self) -> Optional[Dict[str, Any]]:
        """Get cache statistics."""
        if self.cache:
            return self.cache.stats()
        return None

    def clear_cache(self) -> None:
        """Clear the rerank score cache."""
        if self.cache:
            self.cache.clear()
            logger.info("Cross-encoder cache cleared")


# Convenience functions
_default_reranker: Optional[CrossEncoderReranker] = None


def get_cross_encoder_reranker(
    model_name: str = "ms-marco-mini-lm-6",
    device: Optional[str] = None,
    use_cache: bool = True,
) -> CrossEncoderReranker:
    """
    Get or create a cross-encoder reranker instance.

    Note: Only the first call with default parameters uses singleton.
    Custom parameters always create a new instance.

    Args:
        model_name: Model to use
        device: Device to use (None=auto)
        use_cache: Whether to use caching

    Returns:
        CrossEncoderReranker instance
    """
    global _default_reranker

    # Check if using default parameters
    is_default = (
        model_name == "ms-marco-mini-lm-6" and
        device is None and
        use_cache is True
    )

    # Return singleton for default params, create new for custom
    if is_default:
        if _default_reranker is None:
            _default_reranker = CrossEncoderReranker(
                model_name=model_name,
                device=device,
                use_cache=use_cache,
            )
        return _default_reranker
    else:
        # Custom parameters - create new instance
        return CrossEncoderReranker(
            model_name=model_name,
            device=device,
            use_cache=use_cache,
        )


def rerank_results(
    query: str,
    results: List[Dict[str, Any]],
    top_k: Optional[int] = None,
    model_name: str = "ms-marco-mini-lm-6",
) -> List[Dict[str, Any]]:
    """
    Quick helper to re-rank search results.

    Args:
        query: Search query
        results: List of search results
        top_k: Number of top results to return
        model_name: Cross-encoder model to use

    Returns:
        Re-ranked results as dictionaries
    """
    reranker = get_cross_encoder_reranker(model_name=model_name)
    return reranker.rerank_to_dicts(query, results, top_k)


__all__ = [
    "CrossEncoderReranker",
    "RerankResult",
    "get_cross_encoder_reranker",
    "rerank_results",
]
