# Day 24: Result Diversification (Maximum Marginal Relevance)

**Date**: December 27, 2025  
**Phase**: 4 (Advanced Features)  
**Status**: ✅ Complete

## Overview

Result diversification using Maximum Marginal Relevance (MMR) improves search quality by balancing relevance and diversity. This prevents returning redundant or overly similar results, ensuring users see a broader range of relevant information.

**Problem**: Traditional search returns most relevant results, which are often very similar to each other.  
**Solution**: MMR selects results that are both relevant to the query AND different from already selected results.

## MMR Algorithm

Maximum Marginal Relevance balances two competing factors:

```
MMR = λ × Relevance(doc, query) - (1-λ) × MaxSimilarity(doc, selected_docs)
```

Where:
- **λ (lambda)**: Controls relevance-diversity tradeoff (0-1)
  - λ=1.0: Pure relevance (no diversity)
  - λ=0.5: Balanced (default, recommended)
  - λ=0.0: Pure diversity
- **Relevance**: How well the document matches the query
- **MaxSimilarity**: Highest similarity to already selected documents

## Quick Start

```python
from src.core import ResultDiversifier, VectorStore

# Initialize
vector_store = VectorStore()
diversifier = ResultDiversifier(lambda_param=0.5)  # Balanced

# Search
query = "authentication"
candidates = vector_store.search(query, n_results=20)  # Get more candidates

# Diversify
diverse_results = diversifier.diversify(candidates, top_k=5)  # Return 5 diverse results
```

## Key Features

✅ **MMR Algorithm** - Industry-standard diversification  
✅ **Configurable λ** - Control relevance-diversity tradeoff  
✅ **Embedding-Based** - Uses semantic embeddings for accuracy  
✅ **Content Fallback** - Works without embeddings (Jaccard similarity)  
✅ **Diversity Metrics** - Compute diversity scores  
✅ **27 Tests** - Comprehensive coverage (100% passing)

## API Reference

### ResultDiversifier

```python
class ResultDiversifier:
    def __init__(
        self,
        lambda_param: float = 0.5,
        embedding_service: Optional[Any] = None
    )
    
    def diversify(
        self,
        results: List[Dict[str, Any]],
        top_k: int,
        embeddings: Optional[List[np.ndarray]] = None
    ) -> List[Dict[str, Any]]
    
    @staticmethod
    def compute_diversity_score(
        results: List[Dict[str, Any]]
    ) -> float
```

### Convenience Functions

```python
# Get singleton instance
diversifier = get_result_diversifier(lambda_param=0.5)

# Quick helper
diverse_results = diversify_results(
    results,
    top_k=5,
    lambda_param=0.5,
    embeddings=None
)
```

## Usage Examples

### Example 1: Basic Diversification

```python
from src.core import VectorStore, ResultDiversifier

# Search
vector_store = VectorStore()
results = vector_store.search("authentication", n_results=20)

# Diversify
diversifier = ResultDiversifier(lambda_param=0.5)
diverse = diversifier.diversify(results, top_k=5)

# Now 'diverse' contains 5 relevant AND diverse results
```

### Example 2: Lambda Parameter Effects

```python
from src.core import ResultDiversifier

# High relevance (λ=0.9) - mostly by relevance
diversifier_relevant = ResultDiversifier(lambda_param=0.9)
relevant_results = diversifier_relevant.diversify(candidates, top_k=5)

# Balanced (λ=0.5) - equal weight
diversifier_balanced = ResultDiversifier(lambda_param=0.5)
balanced_results = diversifier_balanced.diversify(candidates, top_k=5)

# High diversity (λ=0.1) - mostly by diversity
diversifier_diverse = ResultDiversifier(lambda_param=0.1)
diverse_results = diversifier_diverse.diversify(candidates, top_k=5)
```

### Example 3: With Embeddings

```python
import numpy as np
from src.core import ResultDiversifier

# Get search results and their embeddings
results = vector_store.search(query, n_results=20)
embeddings = [vector_store.embedding_service.embed_query(r['content']) for r in results]

# Diversify using embeddings (more accurate)
diversifier = ResultDiversifier()
diverse = diversifier.diversify(results, top_k=5, embeddings=embeddings)
```

### Example 4: Compute Diversity Score

```python
from src.core import ResultDiversifier

# Compare diversity of two result sets
original_results = vector_store.search(query, n_results=5)
diversified_results = diversifier.diversify(candidates, top_k=5)

# Compute diversity scores (0-1, higher = more diverse)
orig_diversity = ResultDiversifier.compute_diversity_score(original_results)
div_diversity = ResultDiversifier.compute_diversity_score(diversified_results)

print(f"Original diversity: {orig_diversity:.3f}")
print(f"Diversified diversity: {div_diversity:.3f}")
print(f"Improvement: {div_diversity - orig_diversity:.3f}")
```

## Lambda Parameter Guide

Choose λ based on your use case:

| λ Value | Use Case | Example |
|---------|----------|---------|
| 0.9-1.0 | Precision-critical | Exact answer lookup |
| 0.7-0.8 | Relevance-focused | Q&A systems |
| **0.5-0.6** | **Balanced (recommended)** | **General search** |
| 0.3-0.4 | Diversity-focused | Topic exploration |
| 0.0-0.2 | Maximum diversity | Research, discovery |

## When to Use

### ✅ USE Result Diversification:

- Search results tend to be similar/redundant
- Displaying multiple results to users
- Topic exploration and discovery
- User needs overview (not just best match)
- API endpoint discovery (avoid showing all POST endpoints)

### ❌ DON'T USE:

- Single result expected (autocomplete)
- Speed is critical (<5ms latency)
- Results are already diverse
- Exact match queries

## Performance

| Metric | Value |
|--------|-------|
| **Time Complexity** | O(n² × k) where n=candidates, k=top_k |
| **Latency** | 1-10ms for typical use (k=5-10, n=20-50) |
| **Memory** | O(n) for embeddings |
| **Scalability** | Good up to n=100, k=20 |

**Optimization Tips:**
- Retrieve 3-5x candidates (n=15-25 for k=5)
- Use embeddings for better accuracy
- Cache embeddings if available
- Use lower λ for faster computation

## Algorithm Details

### Embedding-Based (Recommended)

1. Normalize embeddings for cosine similarity
2. Select first document (highest relevance)
3. For each remaining position:
   - Compute MMR score for all unselected docs
   - Select document with highest MMR score
4. Return selected documents in order

### Content-Based (Fallback)

1. Tokenize document content
2. Use Jaccard similarity: `|A ∩ B| / |A ∪ B|`
3. Same selection process as embedding-based

## Testing

Comprehensive test suite:

```bash
# Run all tests
pytest tests/test_core/test_result_diversification.py -v

# Run demo
python examples/result_diversification_demo.py
```

**Test Coverage**: 27/27 tests passing (100%)

## Examples from Demo

### Before Diversification (λ=1.0)

Query: "authentication"

```
1. POST /api/auth/login
2. POST /api/auth/signin      ← Very similar to #1
3. POST /api/auth/authenticate ← Very similar to #1
4. POST /api/auth/logout
5. POST /api/auth/refresh
```

All results are authentication endpoints, 3 are essentially the same (login variations).

### After Diversification (λ=0.5)

```
1. POST /api/auth/login       ← Most relevant login
2. POST /api/auth/logout      ← Different: logout
3. POST /api/auth/refresh     ← Different: refresh
4. GET /api/auth/verify       ← Different: verify + different method
5. POST /api/users            ← Different category entirely
```

Better coverage of authentication-related functionality!

## Best Practices

### 1. Candidate Retrieval

```python
# GOOD: Retrieve 3-5x candidates
candidates = vector_store.search(query, n_results=20)
diverse = diversifier.diversify(candidates, top_k=5)

# BAD: Same number of candidates
candidates = vector_store.search(query, n_results=5)
diverse = diversifier.diversify(candidates, top_k=5)  # No benefit!
```

### 2. Lambda Selection

```python
# Start with balanced
diversifier = ResultDiversifier(lambda_param=0.5)

# Tune based on feedback
if users_want_more_precision:
    lambda_param = 0.7  # Increase for relevance
if users_want_more_variety:
    lambda_param = 0.3  # Decrease for diversity
```

### 3. Integration with Search Pipeline

```python
def search_with_diversification(query, top_k=5):
    # Step 1: Retrieve candidates (3-5x)
    candidates = vector_store.search(
        query, 
        n_results=top_k * 4,
        use_hybrid=True,
        use_reranker=False  # Diversify before reranking
    )
    
    # Step 2: Diversify
    diversified = diversifier.diversify(candidates, top_k=top_k * 2)
    
    # Step 3: Optional reranking
    if use_reranking:
        final = reranker.rerank(query, diversified, top_k=top_k)
    else:
        final = diversified[:top_k]
    
    return final
```

## Limitations

1. **Quadratic Complexity**: O(n²) can be slow for large n
2. **Cold Start**: First result always highest relevance
3. **No Global Optimization**: Greedy algorithm (not optimal)
4. **Content-Based Less Accurate**: Jaccard similarity is approximate

## Future Enhancements

- Submodular optimization for global optimum
- Parallel MMR computation
- Category-aware diversification
- Temporal diversification (recent vs older)
- User preference learning

## References

- [Original MMR Paper](https://www.cs.cmu.edu/~jgc/publication/The_Use_MMR_Diversity_Based_LTMIR_1998.pdf) (Carbonell & Goldstein, 1998)
- [Modern Applications](https://arxiv.org/abs/2004.14348)

## Conclusion

Result diversification using MMR is a simple yet powerful technique that significantly improves user experience by reducing redundancy and providing broader topic coverage. With configurable relevance-diversity tradeoff (λ parameter) and support for both embedding-based and content-based similarity, it's suitable for a wide range of search applications.

**Recommendation**: Enable for user-facing search interfaces with λ=0.5 (balanced).
