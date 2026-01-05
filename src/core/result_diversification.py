"""
Result Diversification Module - Maximum Marginal Relevance (MMR)

Provides result diversification using MMR algorithm to balance relevance and diversity.
This helps avoid returning redundant or overly similar results by ensuring selected
results are both relevant to the query AND different from each other.

MMR Formula:
    MMR = λ * Relevance(doc, query) - (1-λ) * MaxSimilarity(doc, selected_docs)

Where:
- λ (lambda): Balance between relevance and diversity (0-1)
  - λ=1: Pure relevance (no diversity)
  - λ=0.5: Balanced (default)
  - λ=0: Pure diversity (no relevance)

Author: API Assistant Team
Date: 2025-12-27
"""

import numpy as np
import structlog
from typing import Any, Dict, List, Optional, Tuple

logger = structlog.get_logger(__name__)


class ResultDiversifier:
    """
    Result diversification using Maximum Marginal Relevance (MMR).

    MMR selects results that are both relevant to the query and diverse
    from already selected results, preventing redundant information.
    """

    def __init__(
        self,
        lambda_param: float = 0.5,
        embedding_service: Optional[Any] = None,
    ):
        """
        Initialize result diversifier.

        Args:
            lambda_param: Balance between relevance (1.0) and diversity (0.0)
                         Default 0.5 = balanced
            embedding_service: Optional embedding service for computing similarities
        """
        if not 0 <= lambda_param <= 1:
            raise ValueError("lambda_param must be between 0 and 1")

        self.lambda_param = lambda_param
        self.embedding_service = embedding_service

        logger.debug(
            "Initialized ResultDiversifier",
            lambda_param=lambda_param,
        )

    def diversify(
        self,
        results: List[Dict[str, Any]],
        top_k: int,
        embeddings: Optional[List[np.ndarray]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Diversify search results using MMR algorithm.

        Args:
            results: List of search results with 'score' field
            top_k: Number of diverse results to return
            embeddings: Optional pre-computed embeddings for each result
                       If None, will use content similarity

        Returns:
            List of diversified results (top_k items)
        """
        if not results:
            return []

        if top_k <= 0:
            return []

        if top_k >= len(results):
            # No need to diversify if we're returning all results
            return results[:top_k]

        logger.debug(
            "Starting MMR diversification",
            total_results=len(results),
            top_k=top_k,
            lambda_param=self.lambda_param,
        )

        # Use embeddings if provided, otherwise compute content-based similarity
        if embeddings is not None:
            return self._diversify_with_embeddings(results, top_k, embeddings)
        else:
            return self._diversify_with_content(results, top_k)

    def _diversify_with_embeddings(
        self,
        results: List[Dict[str, Any]],
        top_k: int,
        embeddings: List[np.ndarray],
    ) -> List[Dict[str, Any]]:
        """
        Diversify using embedding-based similarity.

        This is the most accurate method as it uses semantic embeddings.
        """
        if len(embeddings) != len(results):
            raise ValueError("Number of embeddings must match number of results")

        # Convert to numpy arrays
        embeddings_array = np.array(embeddings)

        # Normalize embeddings for cosine similarity
        norms = np.linalg.norm(embeddings_array, axis=1, keepdims=True)
        norms[norms == 0] = 1  # Avoid division by zero
        normalized_embeddings = embeddings_array / norms

        # Track selected indices
        selected_indices = []
        remaining_indices = list(range(len(results)))

        # Select first document (highest relevance)
        first_idx = 0  # Results are already sorted by relevance
        selected_indices.append(first_idx)
        remaining_indices.remove(first_idx)

        # Select remaining documents using MMR
        while len(selected_indices) < top_k and remaining_indices:
            best_idx = None
            best_score = float('-inf')

            for idx in remaining_indices:
                # Relevance score (from original ranking)
                relevance = results[idx].get('score', 0.0)

                # Max similarity to already selected documents
                if selected_indices:
                    # Compute cosine similarity to all selected documents
                    similarities = np.dot(
                        normalized_embeddings[idx],
                        normalized_embeddings[selected_indices].T
                    )
                    max_similarity = np.max(similarities)
                else:
                    max_similarity = 0.0

                # MMR score
                mmr_score = (
                    self.lambda_param * relevance -
                    (1 - self.lambda_param) * max_similarity
                )

                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = idx

            if best_idx is not None:
                selected_indices.append(best_idx)
                remaining_indices.remove(best_idx)

        # Return selected results in order
        diversified = [results[idx] for idx in selected_indices]

        logger.info(
            "MMR diversification completed",
            total_results=len(results),
            selected=len(diversified),
            lambda_param=self.lambda_param,
        )

        return diversified

    def _diversify_with_content(
        self,
        results: List[Dict[str, Any]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """
        Diversify using content-based text similarity.

        Fallback method when embeddings are not available.
        Uses simple Jaccard similarity on content tokens.
        """
        # Extract content from results
        contents = [r.get('content', '') for r in results]

        # Tokenize content (simple whitespace + lowercase)
        token_sets = [
            set(content.lower().split()) for content in contents
        ]

        # Track selected indices
        selected_indices = []
        remaining_indices = list(range(len(results)))

        # Select first document (highest relevance)
        selected_indices.append(0)
        remaining_indices.remove(0)

        # Select remaining documents using MMR with Jaccard similarity
        while len(selected_indices) < top_k and remaining_indices:
            best_idx = None
            best_score = float('-inf')

            for idx in remaining_indices:
                # Relevance score
                relevance = results[idx].get('score', 0.0)

                # Max Jaccard similarity to selected documents
                if selected_indices:
                    similarities = []
                    for sel_idx in selected_indices:
                        # Jaccard similarity
                        intersection = len(
                            token_sets[idx] & token_sets[sel_idx]
                        )
                        union = len(token_sets[idx] | token_sets[sel_idx])
                        similarity = intersection / union if union > 0 else 0.0
                        similarities.append(similarity)
                    max_similarity = max(similarities)
                else:
                    max_similarity = 0.0

                # MMR score
                mmr_score = (
                    self.lambda_param * relevance -
                    (1 - self.lambda_param) * max_similarity
                )

                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = idx

            if best_idx is not None:
                selected_indices.append(best_idx)
                remaining_indices.remove(best_idx)

        diversified = [results[idx] for idx in selected_indices]

        logger.info(
            "Content-based diversification completed",
            total_results=len(results),
            selected=len(diversified),
        )

        return diversified

    @staticmethod
    def compute_diversity_score(results: List[Dict[str, Any]]) -> float:
        """
        Compute diversity score for a set of results.

        Returns average pairwise dissimilarity (0-1, higher = more diverse).

        Args:
            results: List of results with 'content' field

        Returns:
            Diversity score (0-1)
        """
        if len(results) <= 1:
            return 1.0  # Single result is maximally diverse

        # Tokenize content
        token_sets = [
            set(r.get('content', '').lower().split()) for r in results
        ]

        # Compute average pairwise dissimilarity
        total_dissimilarity = 0.0
        pair_count = 0

        for i in range(len(token_sets)):
            for j in range(i + 1, len(token_sets)):
                # Jaccard dissimilarity = 1 - Jaccard similarity
                intersection = len(token_sets[i] & token_sets[j])
                union = len(token_sets[i] | token_sets[j])
                similarity = intersection / union if union > 0 else 0.0
                dissimilarity = 1.0 - similarity

                total_dissimilarity += dissimilarity
                pair_count += 1

        avg_diversity = total_dissimilarity / pair_count if pair_count > 0 else 0.0

        return avg_diversity


# Convenience functions
_default_diversifier: Optional[ResultDiversifier] = None


def get_result_diversifier(lambda_param: float = 0.5) -> ResultDiversifier:
    """
    Get or create a result diversifier instance.

    Args:
        lambda_param: Balance between relevance and diversity

    Returns:
        ResultDiversifier instance
    """
    global _default_diversifier

    if _default_diversifier is None or _default_diversifier.lambda_param != lambda_param:
        _default_diversifier = ResultDiversifier(lambda_param=lambda_param)

    return _default_diversifier


def diversify_results(
    results: List[Dict[str, Any]],
    top_k: int,
    lambda_param: float = 0.5,
    embeddings: Optional[List[np.ndarray]] = None,
) -> List[Dict[str, Any]]:
    """
    Quick helper to diversify search results.

    Args:
        results: Search results to diversify
        top_k: Number of diverse results to return
        lambda_param: Balance between relevance and diversity
        embeddings: Optional embeddings for similarity computation

    Returns:
        Diversified results
    """
    diversifier = ResultDiversifier(lambda_param=lambda_param)
    return diversifier.diversify(results, top_k, embeddings)


__all__ = [
    "ResultDiversifier",
    "get_result_diversifier",
    "diversify_results",
]
