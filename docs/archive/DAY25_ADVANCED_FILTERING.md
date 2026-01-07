# Day 25: Advanced Filtering and Faceted Search

**Date**: 2025-12-27
**Phase**: 4 - Advanced Features
**Status**: ✅ Completed

## Overview

Day 25 adds advanced filtering and faceted search capabilities to the API Assistant, enabling precise result filtering and building rich filter UIs. This completes Phase 4 with comprehensive search customization.

## Features Implemented

### 1. Advanced Filtering System

#### Filter Types

**Metadata Filters**:
- Equality: `eq()`, `ne()`
- Range: `gt()`, `gte()`, `lt()`, `lte()`
- Collection: `in_list()`, `not_in_list()`
- String: `contains()`, `not_contains()`, `starts_with()`, `ends_with()`, `regex()`

**Content Filters**:
- `content_contains()` - Match text in document content
- `content_not_contains()` - Exclude text from content
- Regex support for advanced pattern matching

**Combined Filters**:
- `and_filters()` - Combine filters with AND logic
- `or_filters()` - Combine filters with OR logic
- `not_filter()` - Negate a filter with NOT logic
- Nested combinations for complex queries

#### Filter Builder

Fluent API for creating filters:

```python
from src.core import FilterBuilder

# Simple filters
get_filter = FilterBuilder.eq("method", "GET")
priority_filter = FilterBuilder.lte("priority", 2)
category_filter = FilterBuilder.in_list("category", ["api", "webhook"])

# Complex filter: (GET OR POST) AND status != 'deprecated'
get = FilterBuilder.eq("method", "GET")
post = FilterBuilder.eq("method", "POST")
method_or = FilterBuilder.or_filters(get, post)

deprecated = FilterBuilder.eq("status", "deprecated")
not_deprecated = FilterBuilder.not_filter(deprecated)

final_filter = FilterBuilder.and_filters(method_or, not_deprecated)
```

### 2. Faceted Search

Compute aggregations to build filter UIs:

```python
# Search with facets
results, facets = vector_store.search_with_facets(
    query="api documentation",
    facet_fields=["category", "method", "version", "status"],
    n_results=20
)

# Display facet counts
for field, facet in facets.items():
    print(f"{field}:")
    for value, count in facet.get_top_values(5):
        percentage = facet.get_percentage(value)
        print(f"  {value}: {count} ({percentage:.1f}%)")
```

**Facet Features**:
- Count documents by field value
- Get top N values by frequency
- Calculate percentages
- Support multiple facet fields
- Progressive filtering (drill-down)

### 3. Vector Store Integration

**Filter Integration**:
- Filters work with vector, BM25, and hybrid search
- ChromaDB-native filtering for vector search
- Client-side filtering for BM25 results
- Automatic fallback for unsupported filter types

**Usage**:

```python
from src.core import VectorStore, FilterBuilder

vector_store = VectorStore()

# Search with filters
filter = FilterBuilder.and_filters(
    FilterBuilder.eq("method", "GET"),
    FilterBuilder.eq("category", "api")
)

results = vector_store.search(
    "authentication",
    n_results=10,
    where=filter
)
```

### 4. ChromaDB Filter Compatibility

**Automatic Conversion**:
- Filter objects → ChromaDB where clauses
- NOT (x = y) → (x != y) for ChromaDB compatibility
- Client-side filtering fallback for complex filters

**Supported Operators**:
- `$eq`, `$ne`, `$gt`, `$gte`, `$lt`, `$lte`
- `$in`, `$nin`
- `$contains`, `$not_contains` (content)
- `$and`, `$or` (logical)

## Architecture

### Core Components

```
src/core/advanced_filtering.py
├── FilterOperator (Enum)
│   ├── Comparison: EQ, NE, GT, GTE, LT, LTE
│   ├── String: CONTAINS, NOT_CONTAINS, STARTS_WITH, ENDS_WITH, REGEX
│   ├── Collection: IN, NOT_IN
│   └── Logical: AND, OR, NOT
│
├── Filter (ABC)
│   ├── to_chroma_where() - Convert to ChromaDB filter
│   ├── to_chroma_where_document() - Convert to content filter
│   └── matches() - Client-side filtering
│
├── MetadataFilter
│   └── Filter on metadata fields
│
├── ContentFilter
│   └── Filter on document content
│
├── CombinedFilter
│   └── Combine filters with AND/OR/NOT
│
├── FacetResult
│   ├── values: Dict[value, count]
│   ├── get_top_values(n) - Top N by frequency
│   └── get_percentage(value) - Percentage calculation
│
├── FilterBuilder
│   └── Fluent API for filter creation
│
└── FacetedSearch
    ├── compute_facets() - Aggregate by fields
    └── apply_client_side_filter() - Filter documents
```

### VectorStore Enhancements

```python
class VectorStore:
    def search(
        query: str,
        where: Optional[Union[dict, Filter]] = None,
        ...
    ) -> list[dict]:
        # 1. Convert Filter → ChromaDB dict
        # 2. Vector search with ChromaDB filters
        # 3. BM25 search with client-side filtering
        # 4. Merge results with RRF
        # 5. Apply client-side filters if needed
        pass

    def search_with_facets(
        query: str,
        facet_fields: List[str],
        where: Optional[Union[dict, Filter]] = None,
        ...
    ) -> tuple[list[dict], Dict[str, FacetResult]]:
        # 1. Search with filters
        # 2. Compute facets on results
        # 3. Return results + facets
        pass
```

## Implementation Details

### Filter Conversion

**ChromaDB-Compatible**:
```python
# MetadataFilter → ChromaDB
{"field": {"$eq": "value"}}
{"field": {"$gt": 5}}
{"field": {"$in": ["a", "b"]}}

# CombinedFilter → ChromaDB
{"$and": [filter1, filter2]}
{"$or": [filter1, filter2]}
```

**NOT Filter Handling**:
```python
# Simple NOT (x = y) → (x != y)
NOT (status = "deprecated")
→ {"status": {"$ne": "deprecated"}}

# Complex NOT → Client-side filtering
NOT (complex_combined_filter)
→ None (triggers client-side filtering)
```

### Client-Side Filtering

For filters that ChromaDB doesn't support:

```python
# 1. Filter returns None from to_chroma_where()
# 2. VectorStore detects None → no ChromaDB filter
# 3. Retrieve all results
# 4. Apply filter.matches() to each result
# 5. Return filtered results
```

### Hybrid Search Filtering

```python
# Vector search: Uses ChromaDB where clause
vector_results = chromadb.query(where=where_clause)

# BM25 search: Client-side filtering
bm25_results = bm25.search(query)
filtered_bm25 = [r for r in bm25_results if matches_filter(r)]

# Merge filtered results with RRF
merged = reciprocal_rank_fusion(vector_results, filtered_bm25)
```

## Usage Examples

### Example 1: Filter by Method and Category

```python
from src.core import VectorStore, FilterBuilder

vector_store = VectorStore()

# GET endpoints in authentication category
filter = FilterBuilder.and_filters(
    FilterBuilder.eq("method", "GET"),
    FilterBuilder.eq("category", "authentication")
)

results = vector_store.search(
    "how to verify user",
    n_results=5,
    where=filter
)
```

### Example 2: Range Filtering

```python
# High priority endpoints (priority <= 2)
priority_filter = FilterBuilder.lte("priority", 2)

results = vector_store.search(
    "important endpoints",
    where=priority_filter
)
```

### Example 3: Multiple Categories

```python
# API, webhook, or auth endpoints
category_filter = FilterBuilder.in_list(
    "category",
    ["api", "webhook", "authentication"]
)

results = vector_store.search(
    "endpoints",
    where=category_filter
)
```

### Example 4: Excluding Deprecated

```python
# Active endpoints only
deprecated_filter = FilterBuilder.eq("status", "deprecated")
active_filter = FilterBuilder.not_filter(deprecated_filter)

results = vector_store.search(
    "api documentation",
    where=active_filter
)
```

### Example 5: Complex Filter

```python
# (POST or PUT) AND category='api' AND status!='deprecated'
post = FilterBuilder.eq("method", "POST")
put = FilterBuilder.eq("method", "PUT")
method_or = FilterBuilder.or_filters(post, put)

category = FilterBuilder.eq("category", "api")

deprecated = FilterBuilder.eq("status", "deprecated")
not_deprecated = FilterBuilder.not_filter(deprecated)

final_filter = FilterBuilder.and_filters(
    method_or,
    category,
    not_deprecated
)

results = vector_store.search(
    "modify data",
    where=final_filter
)
```

### Example 6: Faceted Search UI

```python
# Build filter UI
results, facets = vector_store.search_with_facets(
    query="api",
    facet_fields=["category", "method", "version", "status"],
    n_results=50
)

# Display filters
print("Available Filters:")
for field, facet in facets.items():
    print(f"\n{field}:")
    for value, count in facet.get_top_values(10):
        print(f"  [{x] {value} ({count})")

# User selects: category='authentication'
# Refine search with filter
filter = FilterBuilder.eq("category", "authentication")
results, facets = vector_store.search_with_facets(
    query="api",
    facet_fields=["method", "version"],
    where=filter
)
```

### Example 7: Progressive Filtering

```python
# Step 1: Show all categories
results, facets = vector_store.search_with_facets(
    "api",
    facet_fields=["category"]
)

# Step 2: User selects category='users'
cat_filter = FilterBuilder.eq("category", "users")
results, facets = vector_store.search_with_facets(
    "api",
    facet_fields=["method"],
    where=cat_filter
)

# Step 3: User also selects method='POST'
method_filter = FilterBuilder.eq("method", "POST")
combined = FilterBuilder.and_filters(cat_filter, method_filter)
results, facets = vector_store.search_with_facets(
    "api",
    facet_fields=["version"],
    where=combined
)
```

## Performance Considerations

### ChromaDB vs Client-Side Filtering

**ChromaDB Filtering** (Faster):
- Filters applied at database level
- Reduces data transfer
- Uses indexes
- Limited to supported operators

**Client-Side Filtering** (Slower):
- Retrieves all results first
- Filters in Python
- No index usage
- Supports all filter types

### Optimization Tips

1. **Use ChromaDB-compatible filters when possible**:
   - Simple equality, range, IN operators
   - Avoid complex NOT combinations

2. **Limit facet fields**:
   - Only compute facets for displayed fields
   - More facets = more computation

3. **Cache facet results**:
   - For static catalogs, cache facet aggregations
   - Recompute only when data changes

4. **Retrieve appropriate top_k**:
   - Don't retrieve 1000 results to show 10
   - Facets computed on retrieved results

## Testing

### Test Coverage

- **67 unit tests** covering:
  - Filter operators (13 tests)
  - Metadata filtering (7 tests)
  - Content filtering (7 tests)
  - Combined filters (12 tests)
  - Filter builder (8 tests)
  - Faceted search (6 tests)
  - Edge cases (6 tests)
  - Integration scenarios (8 tests)

### Running Tests

```bash
# Run all filtering tests
pytest tests/test_core/test_advanced_filtering.py -v

# Run specific test class
pytest tests/test_core/test_advanced_filtering.py::TestMetadataFilter -v

# Run demo
python examples/advanced_filtering_demo.py
```

### Test Results

```
67 tests passed (100%)
Test execution time: ~16 seconds
```

## Integration with Phase 4

### Complete Phase 4 Pipeline

```python
from src.core import (
    VectorStore,
    FilterBuilder,
    QueryExpander,
    ResultDiversifier
)

# 1. Query expansion (Day 23)
expander = QueryExpander()
expanded = expander.expand_and_format("auth endpoints")

# 2. Search with filters (Day 25)
filter = FilterBuilder.and_filters(
    FilterBuilder.eq("method", "GET"),
    FilterBuilder.eq("status", "active")
)

# 3. Hybrid search (Day 21)
results = vector_store.search(
    expanded,
    n_results=20,
    where=filter,
    use_hybrid=True,
    use_reranker=True,  # Day 22: Cross-encoder re-ranking
)

# 4. Diversify results (Day 24)
diversifier = ResultDiversifier(lambda_param=0.5)
final_results = diversifier.diversify(results, top_k=10)
```

## Use Cases

### 1. E-Commerce

```python
# Filter products
filters = FilterBuilder.and_filters(
    FilterBuilder.in_list("category", ["electronics", "computers"]),
    FilterBuilder.gte("price", 100),
    FilterBuilder.lte("price", 1000),
    FilterBuilder.gte("rating", 4.0)
)

results, facets = store.search_with_facets(
    "laptop",
    facet_fields=["brand", "price_range", "rating"],
    where=filters
)
```

### 2. Job Boards

```python
# Filter jobs
filters = FilterBuilder.and_filters(
    FilterBuilder.in_list("location", ["Remote", "New York"]),
    FilterBuilder.gte("salary_min", 100000),
    FilterBuilder.eq("experience_level", "Senior"),
    FilterBuilder.contains("skills", "Python")
)

results = store.search("software engineer", where=filters)
```

### 3. API Documentation

```python
# Filter endpoints
filters = FilterBuilder.and_filters(
    FilterBuilder.eq("method", "GET"),
    FilterBuilder.eq("version", "v2"),
    FilterBuilder.not_filter(
        FilterBuilder.eq("status", "deprecated")
    )
)

results, facets = store.search_with_facets(
    "user data",
    facet_fields=["category", "method", "version"],
    where=filters
)
```

### 4. Content Management

```python
# Filter articles
filters = FilterBuilder.and_filters(
    FilterBuilder.in_list("author", ["John Doe", "Jane Smith"]),
    FilterBuilder.gte("publish_date", "2024-01-01"),
    FilterBuilder.contains("tags", "technology")
)

results = store.search("AI trends", where=filters)
```

## Future Enhancements

### Potential Improvements

1. **Geo-spatial Filtering**:
   - Distance-based filters
   - Bounding box queries
   - Polygon containment

2. **Date/Time Filters**:
   - Relative dates (last_7_days)
   - Date ranges
   - Time-based facets

3. **Nested Field Support**:
   - Filter on nested JSON
   - Array contains
   - Object field access

4. **Filter Suggestions**:
   - Auto-suggest filter values
   - Popular filter combinations
   - Smart defaults

5. **Filter Persistence**:
   - Save filter presets
   - Share filter URLs
   - Filter history

## Conclusion

Day 25 completes Phase 4 with comprehensive filtering and faceted search:

✅ **Advanced Filtering** - Precise result control
✅ **Faceted Search** - Build rich filter UIs
✅ **ChromaDB Integration** - Native and client-side filtering
✅ **Filter Builder** - Fluent, type-safe API
✅ **67 Unit Tests** - Comprehensive coverage
✅ **Complete Demo** - 12 real-world scenarios

### Phase 4 Summary (Complete)

- Day 21: Hybrid Search (BM25 + Vector)
- Day 22: Cross-Encoder Re-ranking
- Day 23: Query Expansion
- Day 24: Result Diversification (MMR)
- Day 25: Advanced Filtering and Faceted Search ✅

**Total Phase 4 Tests**: 48 + 28 + 40 + 27 + 67 = **210 tests**
**All tests passing**: ✅

The API Assistant now has a complete, production-ready advanced search system with filtering, expansion, re-ranking, and diversification capabilities!
