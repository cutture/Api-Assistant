"""
Hybrid search combining BM25 keyword search and vector similarity search.

This module implements:
1. BM25 (Best Matching 25) algorithm for keyword-based relevance
2. Reciprocal Rank Fusion (RRF) for combining BM25 and vector results
3. Hybrid search strategy with configurable weights
"""

import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class SearchResult:
    """Unified search result from any retrieval method."""

    doc_id: str
    content: str
    metadata: Dict[str, Any]
    score: float
    method: str  # "bm25", "vector", or "hybrid"
    rank: int = 0  # Rank position in results


class BM25:
    """
    BM25 (Best Matching 25) ranking function for keyword-based retrieval.

    BM25 is a probabilistic ranking function that:
    - Considers term frequency (TF) - how often terms appear in documents
    - Considers inverse document frequency (IDF) - rarity of terms across corpus
    - Applies saturation to prevent over-weighting of common terms
    - Handles document length normalization

    Parameters:
    - k1: Controls term frequency saturation (default: 1.5, range: [1.2, 2.0])
    - b: Controls document length normalization (default: 0.75, range: [0, 1])

    Higher k1 = more weight on term frequency
    Higher b = more aggressive length normalization
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Initialize BM25 with tuning parameters.

        Args:
            k1: Term frequency saturation parameter (default: 1.5)
            b: Document length normalization parameter (default: 0.75)
        """
        self.k1 = k1
        self.b = b

        # Will be populated during fit()
        self.corpus: List[str] = []
        self.doc_ids: List[str] = []
        self.doc_freqs: List[Counter] = []  # Term frequencies per document
        self.idf: Dict[str, float] = {}  # Inverse document frequency
        self.avgdl: float = 0.0  # Average document length
        self.num_docs: int = 0

        logger.debug("Initialized BM25", k1=k1, b=b)

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """
        Tokenize text into terms for BM25 scoring.

        Preprocessing:
        - Convert to lowercase
        - Split on word boundaries
        - Remove very short tokens (< 2 chars)
        - Keep alphanumeric and underscores

        Args:
            text: Input text to tokenize

        Returns:
            List of tokens
        """
        # Lowercase and split on non-alphanumeric (except underscores)
        text = text.lower()
        tokens = re.findall(r'\w+', text)

        # Filter out very short tokens (single characters)
        tokens = [t for t in tokens if len(t) >= 2]

        return tokens

    def fit(self, corpus: List[str], doc_ids: Optional[List[str]] = None):
        """
        Fit BM25 on a document corpus.

        This calculates:
        - Document term frequencies
        - Inverse document frequencies (IDF)
        - Average document length

        Args:
            corpus: List of document texts
            doc_ids: Optional list of document IDs (generated if not provided)
        """
        self.corpus = corpus
        self.num_docs = len(corpus)

        # Generate doc IDs if not provided
        if doc_ids is None:
            self.doc_ids = [f"doc_{i}" for i in range(self.num_docs)]
        else:
            if len(doc_ids) != len(corpus):
                raise ValueError("doc_ids length must match corpus length")
            self.doc_ids = doc_ids

        # Calculate term frequencies for each document
        self.doc_freqs = []
        doc_lengths = []

        for doc in corpus:
            tokens = self.tokenize(doc)
            self.doc_freqs.append(Counter(tokens))
            doc_lengths.append(len(tokens))

        # Calculate average document length
        self.avgdl = sum(doc_lengths) / self.num_docs if self.num_docs > 0 else 0

        # Calculate IDF for each term
        # IDF(term) = log((N - df + 0.5) / (df + 0.5) + 1)
        # Where N = total documents, df = documents containing term
        df = defaultdict(int)  # Document frequency per term

        for doc_freq in self.doc_freqs:
            for term in doc_freq.keys():
                df[term] += 1

        for term, doc_freq in df.items():
            # Standard BM25 IDF formula
            idf = math.log((self.num_docs - doc_freq + 0.5) / (doc_freq + 0.5) + 1)
            self.idf[term] = idf

        logger.info(
            "BM25 fitted on corpus",
            num_docs=self.num_docs,
            avg_doc_length=round(self.avgdl, 2),
            unique_terms=len(self.idf),
        )

    def score(self, query: str, doc_idx: int) -> float:
        """
        Calculate BM25 score for a query-document pair.

        BM25 Score Formula:
        score = Σ(IDF(qi) * (f(qi, D) * (k1 + 1)) / (f(qi, D) + k1 * (1 - b + b * |D| / avgdl)))

        Where:
        - qi = query term i
        - f(qi, D) = frequency of qi in document D
        - |D| = length of document D
        - avgdl = average document length

        Args:
            query: Search query
            doc_idx: Document index in the corpus

        Returns:
            BM25 relevance score
        """
        if doc_idx >= len(self.doc_freqs):
            return 0.0

        score = 0.0
        doc_freq = self.doc_freqs[doc_idx]
        doc_len = sum(doc_freq.values())

        query_tokens = self.tokenize(query)

        for term in query_tokens:
            if term not in self.idf:
                continue  # Term not in corpus

            # Term frequency in this document
            tf = doc_freq.get(term, 0)

            # IDF for this term
            idf = self.idf[term]

            # BM25 formula
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)

            score += idf * (numerator / denominator)

        return score

    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Search for top-k most relevant documents using BM25.

        Args:
            query: Search query
            top_k: Number of top results to return

        Returns:
            List of (doc_id, score) tuples sorted by relevance
        """
        if not self.corpus:
            logger.warning("BM25 not fitted, returning empty results")
            return []

        # Calculate scores for all documents
        scores = []
        for idx in range(self.num_docs):
            score = self.score(query, idx)
            if score > 0:  # Only include documents with non-zero scores
                scores.append((self.doc_ids[idx], score))

        # Sort by score (descending) and return top-k
        scores.sort(key=lambda x: x[1], reverse=True)
        results = scores[:top_k]

        logger.debug(
            "BM25 search completed",
            query=query[:50],
            total_results=len(scores),
            returned=len(results),
        )

        return results


class HybridSearch:
    """
    Hybrid search combining BM25 keyword search and vector similarity search.

    Uses Reciprocal Rank Fusion (RRF) to merge results from both methods:
    - BM25: Good for exact keyword matches, technical terms, acronyms
    - Vector: Good for semantic similarity, context understanding
    - RRF: Combines ranks from both methods

    RRF Formula:
    score(d) = Σ(1 / (k + rank(d))) for each method

    Where k is a constant (typically 60) to reduce impact of high ranks.
    """

    def __init__(
        self,
        bm25_weight: float = 0.5,
        vector_weight: float = 0.5,
        rrf_k: int = 60,
    ):
        """
        Initialize hybrid search.

        Args:
            bm25_weight: Weight for BM25 scores (0.0 to 1.0)
            vector_weight: Weight for vector scores (0.0 to 1.0)
            rrf_k: RRF constant parameter (default: 60)
        """
        if abs((bm25_weight + vector_weight) - 1.0) > 0.01:
            logger.warning(
                "BM25 and vector weights do not sum to 1.0, normalizing",
                bm25_weight=bm25_weight,
                vector_weight=vector_weight,
            )
            total = bm25_weight + vector_weight
            bm25_weight /= total
            vector_weight /= total

        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        self.rrf_k = rrf_k

        logger.info(
            "Initialized HybridSearch",
            bm25_weight=bm25_weight,
            vector_weight=vector_weight,
            rrf_k=rrf_k,
        )

    @staticmethod
    def reciprocal_rank_fusion(
        bm25_results: List[Tuple[str, float]],
        vector_results: List[SearchResult],
        k: int = 60,
    ) -> List[Tuple[str, float]]:
        """
        Merge results from BM25 and vector search using Reciprocal Rank Fusion.

        RRF is more robust than score fusion because:
        - Doesn't require score normalization
        - Handles different score scales naturally
        - Emphasizes top-ranked results from both methods

        Args:
            bm25_results: List of (doc_id, bm25_score) tuples
            vector_results: List of SearchResult objects from vector search
            k: RRF constant (higher k reduces impact of rank differences)

        Returns:
            List of (doc_id, rrf_score) tuples sorted by RRF score
        """
        rrf_scores = defaultdict(float)

        # Add BM25 ranks
        for rank, (doc_id, _) in enumerate(bm25_results, start=1):
            rrf_scores[doc_id] += 1.0 / (k + rank)

        # Add vector ranks
        for rank, result in enumerate(vector_results, start=1):
            rrf_scores[result.doc_id] += 1.0 / (k + rank)

        # Sort by RRF score
        merged = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

        logger.debug(
            "RRF fusion completed",
            bm25_count=len(bm25_results),
            vector_count=len(vector_results),
            merged_count=len(merged),
        )

        return merged

    @staticmethod
    def weighted_score_fusion(
        bm25_results: List[Tuple[str, float]],
        vector_results: List[SearchResult],
        bm25_weight: float,
        vector_weight: float,
    ) -> List[Tuple[str, float]]:
        """
        Merge results using weighted score fusion (alternative to RRF).

        This method:
        1. Normalizes scores from both methods to [0, 1]
        2. Applies weights
        3. Combines scores

        Args:
            bm25_results: List of (doc_id, bm25_score) tuples
            vector_results: List of SearchResult objects
            bm25_weight: Weight for BM25 scores
            vector_weight: Weight for vector scores

        Returns:
            List of (doc_id, combined_score) tuples
        """
        combined_scores = defaultdict(float)

        # Normalize BM25 scores
        if bm25_results:
            max_bm25 = max(score for _, score in bm25_results)
            if max_bm25 > 0:
                for doc_id, score in bm25_results:
                    normalized_score = score / max_bm25
                    combined_scores[doc_id] += bm25_weight * normalized_score

        # Add normalized vector scores
        for result in vector_results:
            # Vector scores are already in [0, 1] range
            combined_scores[result.doc_id] += vector_weight * result.score

        # Sort by combined score
        merged = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)

        logger.debug(
            "Weighted fusion completed",
            bm25_count=len(bm25_results),
            vector_count=len(vector_results),
            merged_count=len(merged),
        )

        return merged


def create_bm25_index(
    documents: List[Dict[str, Any]],
    content_field: str = "content",
    id_field: str = "id",
    k1: float = 1.5,
    b: float = 0.75,
) -> BM25:
    """
    Create and fit a BM25 index from documents.

    Args:
        documents: List of document dictionaries
        content_field: Field name containing document text
        id_field: Field name containing document ID
        k1: BM25 k1 parameter
        b: BM25 b parameter

    Returns:
        Fitted BM25 instance
    """
    corpus = [doc[content_field] for doc in documents]
    doc_ids = [doc[id_field] for doc in documents]

    bm25 = BM25(k1=k1, b=b)
    bm25.fit(corpus, doc_ids)

    return bm25


# Convenience functions
def get_bm25(k1: float = 1.5, b: float = 0.75) -> BM25:
    """Get a BM25 instance with specified parameters."""
    return BM25(k1=k1, b=b)


def get_hybrid_search(
    bm25_weight: float = 0.5,
    vector_weight: float = 0.5,
    rrf_k: int = 60,
) -> HybridSearch:
    """Get a HybridSearch instance with specified parameters."""
    return HybridSearch(
        bm25_weight=bm25_weight,
        vector_weight=vector_weight,
        rrf_k=rrf_k,
    )
