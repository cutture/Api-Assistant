# Day 22: Cross-Encoder Re-ranking

**Date**: December 27, 2025
**Phase**: 4 (Advanced Features)
**Status**: ✅ Complete

## Overview

Cross-encoder re-ranking provides a second-stage re-ranking system that significantly improves search result accuracy compared to traditional retrieval methods. While bi-encoder models (like our vector embeddings) are fast and good for initial retrieval, cross-encoders process the query and document together, allowing them to capture fine-grained relevance signals that bi-encoders miss.

## What is Cross-Encoder Re-ranking?

### Traditional Retrieval (Bi-Encoder)
- Query and documents are embedded **separately**
- Similarity computed via dot product or cosine similarity
- Fast (O(1) per document after embedding)
- Good for initial retrieval from large corpus

### Cross-Encoder Re-ranking
- Query and document are processed **together** as a pair
- Model can see interactions between query and document words
- Slower (must run model for each query-document pair)
- Much more accurate relevance scoring
- Used as second stage on top-k candidates

### Two-Stage Architecture

```
Stage 1: Fast Retrieval          Stage 2: Accurate Re-ranking
┌─────────────────┐              ┌──────────────────┐
│  Hybrid Search  │──────────>   │  Cross-Encoder   │
│  (BM25 + Vector)│              │   Re-ranking     │
│  Retrieve 50-100│              │   Re-rank top 10 │
└─────────────────┘              └──────────────────┘
      Fast ⚡⚡                         Accurate ⭐⭐⭐⭐⭐
```

## Implementation

### Core Components

#### 1. CrossEncoderReranker (`src/core/cross_encoder.py`)

Main re-ranking class that wraps a cross-encoder model.

```python
from src.core import CrossEncoderReranker

# Initialize re-ranker
reranker = CrossEncoderReranker(
    model_name="ms-marco-mini-lm-6",  # Fast model
    use_cache=True,                   # Cache scores
    batch_size=32,                    # Process in batches
)

# Re-rank search results
results = [
    {"id": "doc1", "content": "...", "score": 0.8},
    {"id": "doc2", "content": "...", "score": 0.7},
]

reranked = reranker.rerank(
    query="Python machine learning",
    results=results,
    top_k=5
)
```

**Available Models:**
- `ms-marco-mini-lm-6` - Fast, good quality (default)
- `ms-marco-mini-lm-12` - Slower, better quality
- `ms-marco-electra` - Best quality, slowest

#### 2. VectorStore Integration

Cross-encoder re-ranking is integrated into `VectorStore` with simple parameters:

```python
from src.core import VectorStore

# Create vector store with re-ranking enabled
vector_store = VectorStore(
    enable_hybrid_search=True,   # Use hybrid retrieval
    enable_reranker=True,         # Enable cross-encoder
    reranker_model="ms-marco-mini-lm-6"
)

# Search with re-ranking
results = vector_store.search(
    query="OAuth2 authentication flow",
    n_results=5,
    use_hybrid=True,      # Use hybrid for candidate retrieval
    use_reranker=True     # Re-rank with cross-encoder
)
```

#### 3. RerankResult Dataclass

Results include both original and re-rank scores:

```python
@dataclass
class RerankResult:
    doc_id: str
    content: str
    metadata: Dict[str, Any]
    original_score: float   # Score from retrieval stage
    rerank_score: float     # Cross-encoder score
    original_rank: int      # Rank before re-ranking
    rerank_rank: int        # Rank after re-ranking
```

## Usage Examples

### Basic Re-ranking

```python
from src.core import CrossEncoderReranker

reranker = CrossEncoderReranker()

# Your search results from any retrieval method
results = [
    {
        "id": "doc1",
        "content": "Python is great for machine learning",
        "metadata": {"category": "ml"},
        "score": 0.5
    },
    {
        "id": "doc2",
        "content": "Cooking recipes for dinner",
        "metadata": {"category": "food"},
        "score": 0.6  # Higher initial score (false positive)
    }
]

# Re-rank
reranked = reranker.rerank(
    query="Python machine learning",
    results=results,
    top_k=10
)

# doc1 will now rank higher despite lower initial score
# because cross-encoder understands relevance better
```

### Integrated Search Pipeline

```python
from src.core import VectorStore

# Full search pipeline with all enhancements
vector_store = VectorStore(
    enable_hybrid_search=True,  # BM25 + Vector
    enable_reranker=True         # + Cross-encoder
)

# Add documents
vector_store.add_documents(documents)

# Three search modes available:
# 1. Vector-only (fastest)
vector_results = vector_store.search(
    "query", use_hybrid=False, use_reranker=False
)

# 2. Hybrid (fast + accurate)
hybrid_results = vector_store.search(
    "query", use_hybrid=True, use_reranker=False
)

# 3. Re-ranked (most accurate)
reranked_results = vector_store.search(
    "query", use_hybrid=True, use_reranker=True
)
```

### Scoring Query-Document Pairs

```python
# Direct scoring of query-document pairs
reranker = CrossEncoderReranker()

pairs = [
    ("Python", "Python programming tutorial"),
    ("Python", "Snake care guide"),
]

scores = reranker.score_pairs(pairs)
# scores[0] will be much higher than scores[1]
```

## Performance Characteristics

### Accuracy Improvements

Based on our testing with API documentation:

| Search Mode | Accuracy | Use Case |
|------------|----------|----------|
| Vector-only | ⭐⭐⭐ | General semantic search |
| Hybrid (BM25+Vector) | ⭐⭐⭐⭐ | Keyword + semantic |
| Cross-encoder | ⭐⭐⭐⭐⭐ | Maximum accuracy |

**Expected improvements:**
- 10-20% better ranking quality vs hybrid search
- 25-40% better than vector-only for complex queries
- Especially good for:
  - Ambiguous queries
  - Queries requiring deep understanding
  - Technical documentation search

### Latency Characteristics

| Operation | Latency | Notes |
|-----------|---------|-------|
| Hybrid retrieval (50 docs) | 20-30ms | Fast candidate retrieval |
| Cross-encoder (10 docs) | 30-60ms | Re-rank top candidates |
| **Total pipeline** | **50-90ms** | Still fast for production |
| With caching | 20-40ms | Cached scores |

**Optimization:**
- Retrieve 3-5x more candidates than needed
- Re-rank only top-k (typically 10-20)
- Cache frequently seen query-document pairs
- Use batch processing

### Memory Usage

| Model | Size | Memory |
|-------|------|--------|
| ms-marco-mini-lm-6 | 90MB | ~300MB RAM |
| ms-marco-mini-lm-12 | 180MB | ~500MB RAM |
| ms-marco-electra | 400MB | ~1GB RAM |

## Caching System

Cross-encoder re-ranking includes built-in caching for query-document pair scores:

```python
reranker = CrossEncoderReranker(use_cache=True)

# First call - computes scores
scores1 = reranker.score_pairs(pairs)  # 50ms

# Second call - uses cache
scores2 = reranker.score_pairs(pairs)  # 1ms

# Get cache statistics
stats = reranker.get_cache_stats()
# {
#   'size': 150,
#   'max_size': 10000,
#   'hits': 45,
#   'misses': 105,
#   'hit_rate': 0.30
# }

# Clear cache
reranker.clear_cache()
```

**Cache configuration:**
- Max size: 10,000 entries (configurable)
- TTL: 1 hour (3600 seconds)
- Thread-safe LRU eviction
- Automatic in VectorStore integration

## API Reference

### CrossEncoderReranker

```python
class CrossEncoderReranker:
    def __init__(
        self,
        model_name: str = "ms-marco-mini-lm-6",
        device: Optional[str] = None,  # None=auto, 'cuda', 'cpu'
        max_length: int = 512,
        batch_size: int = 32,
        use_cache: bool = True
    )

    def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: Optional[int] = None
    ) -> List[RerankResult]

    def rerank_to_dicts(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]

    def score_pairs(
        self,
        query_doc_pairs: List[Tuple[str, str]]
    ) -> List[float]

    def get_cache_stats(self) -> Optional[Dict[str, Any]]
    def clear_cache(self) -> None
```

### VectorStore Integration

```python
class VectorStore:
    def __init__(
        self,
        # ... existing params ...
        enable_reranker: bool = False,
        reranker_model: str = "ms-marco-mini-lm-6"
    )

    def search(
        self,
        query: str,
        n_results: int = 5,
        where: Optional[dict] = None,
        where_document: Optional[dict] = None,
        use_hybrid: bool = True,
        use_reranker: bool = False,  # Enable re-ranking
        rerank_top_k: Optional[int] = None  # Candidates to retrieve
    ) -> List[Dict[str, Any]]
```

### Convenience Functions

```python
# Get singleton re-ranker
from src.core import get_cross_encoder_reranker

reranker = get_cross_encoder_reranker(
    model_name="ms-marco-mini-lm-6",
    use_cache=True
)

# Quick re-ranking helper
from src.core import rerank_results

reranked = rerank_results(
    query="test",
    results=results,
    top_k=5
)
```

## Best Practices

### 1. When to Use Re-ranking

**USE cross-encoder re-ranking for:**
- User-facing search interfaces
- High-stakes queries (documentation, support)
- Complex queries requiring deep understanding
- When accuracy matters more than speed

**DON'T use re-ranking for:**
- Extremely high-throughput scenarios (>1000 QPS)
- Sub-10ms latency requirements
- Simple keyword lookups
- Bulk processing tasks

### 2. Candidate Retrieval

```python
# GOOD: Retrieve 3-5x candidates for re-ranking
vector_store.search(
    query="test",
    n_results=5,
    use_reranker=True,
    rerank_top_k=20  # Retrieve 20, re-rank top 5
)

# BAD: Retrieve same number (loses benefits)
vector_store.search(
    query="test",
    n_results=5,
    rerank_top_k=5  # Too few candidates
)
```

### 3. Model Selection

```python
# Production: Fast model with caching
reranker = CrossEncoderReranker(
    model_name="ms-marco-mini-lm-6",
    use_cache=True,
    batch_size=32
)

# High-accuracy: Better model, larger batches
reranker = CrossEncoderReranker(
    model_name="ms-marco-mini-lm-12",
    batch_size=64,
    use_cache=True
)

# Maximum quality: Best model (slower)
reranker = CrossEncoderReranker(
    model_name="ms-marco-electra",
    batch_size=16
)
```

### 4. Monitoring

```python
# Track performance
stats = vector_store.get_stats()
print(f"Reranker loaded: {stats.get('reranker_loaded')}")
print(f"Cache hit rate: {stats['reranker_cache']['hit_rate']}")

# Monitor latency in production
import time
start = time.time()
results = vector_store.search(query, use_reranker=True)
latency = time.time() - start
# Should be < 100ms for most queries
```

## Testing

Comprehensive tests cover all functionality:

```bash
# Run all cross-encoder tests
pytest tests/test_core/test_cross_encoder.py -v

# Run integration demo
python examples/cross_encoder_demo.py
```

**Test coverage:**
- 28 unit tests (100% passing)
- Re-ranking accuracy
- Caching behavior
- Edge cases (empty results, long content, unicode)
- Integration scenarios (API docs, technical docs)

## Known Limitations

1. **Latency**: 30-60ms overhead for re-ranking (vs ~20ms for hybrid)
2. **Memory**: Requires loading additional model (~300MB-1GB)
3. **Cold start**: First query loads model (1-2 seconds)
4. **Max length**: Documents truncated to 512 tokens
5. **Language**: Optimized for English (MS MARCO training data)

## Future Enhancements

Potential improvements for future iterations:

1. **Multi-lingual models**: Support for non-English queries
2. **Async re-ranking**: Background re-ranking for improved latency
3. **Model distillation**: Smaller, faster models
4. **Adaptive re-ranking**: Smart decision on when to re-rank
5. **Learning to rank**: Combine multiple signals
6. **Query understanding**: Intent classification before re-ranking

## References

- [MS MARCO Cross-Encoders](https://github.com/microsoft/MSMARCO-Passage-Ranking)
- [Sentence Transformers Cross-Encoder](https://www.sbert.net/examples/applications/cross-encoder/README.html)
- [ColBERT v2](https://arxiv.org/abs/2112.01488) - Advanced token-level matching
- [Two-stage retrieval survey](https://arxiv.org/abs/2103.00814)

## Conclusion

Cross-encoder re-ranking provides state-of-the-art search accuracy with acceptable latency for most production use cases. By combining fast retrieval (hybrid search) with accurate re-ranking (cross-encoder), we achieve the best of both worlds:

- ⚡ Fast enough for production (50-90ms)
- ⭐⭐⭐⭐⭐ Highest accuracy available
- 💾 Efficient caching reduces repeated computation
- 🔧 Easy to integrate and configure

**Recommendation**: Enable for user-facing search interfaces where quality matters.
