# Day 23: Query Expansion

**Date**: December 27, 2025
**Phase**: 4 (Advanced Features)
**Status**: ✅ Complete

## Overview

Query expansion improves search recall by automatically expanding user queries with related terms, synonyms, and variations. This helps overcome the "vocabulary mismatch" problem where users and documents use different words to express the same concepts.

**Example**: User searches for "auth" → System expands to "auth authentication login signin oauth jwt"

## Key Features

✅ **Domain-Specific Expansions** - Technical term expansions for API documentation  
✅ **Abbreviation Handling** - Expands JWT → JSON Web Token, API → Application Programming Interface  
✅ **Multi-Query Generation** - Creates query variations for different perspectives  
✅ **Auto Strategy Selection** - Automatically chooses best expansion strategy  
✅ **Configurable** - Control max expansions, enable/disable features  
✅ **40 Tests** - Comprehensive test coverage (100% passing)

## Quick Start

```python
from src.core import QueryExpander

# Initialize
expander = QueryExpander()

# Expand query
expanded = expander.expand_query("auth", strategy="domain")

print(expanded.original_query)      # "auth"
print(expanded.expanded_terms)      # ["authentication", "login", "oauth", "jwt", ...]
print(expanded.expansion_method)    # "domain"

# Use with search
from src.core import VectorStore

vector_store = VectorStore()
expanded_query = expander.expand_and_format("auth")
results = vector_store.search(expanded_query, n_results=10)
```

## Expansion Strategies

### 1. Domain Expansion (`strategy="domain"`)

Expands technical and API-related terms:

```python
expander.expand_query("auth", strategy="domain")
# → ["authentication", "authorization", "login", "signin", "oauth", "jwt"]

expander.expand_query("api", strategy="domain")
# → ["rest api", "endpoint", "web service", "http api", "rest"]

expander.expand_query("jwt", strategy="domain")
# → ["json web token", "authentication", "token", "bearer token"]
```

**Best for**: Technical queries, API documentation, developer searches

### 2. Multi-Query (`strategy="multi_query"`)

Generates multiple query variations:

```python
expander.expand_query("how to authenticate users", strategy="multi_query")
# → ["authenticate users guide", "authenticate users tutorial", "authenticate users documentation"]

expander.expand_query("what is OAuth2", strategy="multi_query")
# → ["OAuth2 definition", "OAuth2 explanation", "OAuth2 overview"]
```

**Best for**: Questions, natural language queries

### 3. Synonyms (`strategy="synonyms"`)

Domain expansions + abbreviations:

```python
expander.expand_query("config", strategy="synonyms")
# → ["configuration", "settings", "setup", "options"]
```

**Best for**: General purpose expansion

### 4. Auto (`strategy="auto"`)

Automatically selects best strategy:

```python
expander.expand_query("how to use API", strategy="auto")
# → Detects question, uses multi_query

expander.expand_query("oauth authentication", strategy="auto")
# → Detects technical terms, uses domain
```

**Best for**: When you're unsure which strategy to use

## Domain Expansions

Built-in technical term expansions for API/developer documentation:

| Term | Expansions |
|------|------------|
| auth | authentication, authorization, login, signin, oauth, jwt |
| oauth | oauth2, authentication, authorization, token, access token |
| jwt | json web token, authentication, token, bearer token |
| api | rest api, endpoint, web service, http api, rest |
| endpoint | api endpoint, route, url, path, resource |
| get | retrieve, fetch, read, query |
| post | create, add, insert, submit |
| put | update, modify, edit, change |
| delete | remove, destroy, erase |
| error | exception, failure, bug, issue, problem |
| cache | caching, cache layer, redis, memcached |
| async | asynchronous, non-blocking, concurrent, parallel |

See `src/core/query_expansion.py:DOMAIN_EXPANSIONS` for complete list.

## API Reference

### QueryExpander

```python
class QueryExpander:
    def __init__(
        self,
        llm_client: Optional[Any] = None,
        max_expansions: int = 5,
        enable_domain_expansions: bool = True,
        enable_abbreviations: bool = True
    )
    
    def expand_query(
        self,
        query: str,
        strategy: str = "auto",
        max_variations: int = 3
    ) -> ExpandedQuery
    
    def expand_and_format(
        self,
        query: str,
        strategy: str = "auto"
    ) -> str
```

### ExpandedQuery

```python
@dataclass
class ExpandedQuery:
    original_query: str
    expanded_terms: List[str]
    query_variations: List[str]
    expansion_method: str
    confidence: float
    
    def get_all_terms(self) -> List[str]
    def get_all_queries(self) -> List[str]
```

## Usage Patterns

### Pattern 1: Simple Expansion

```python
expander = QueryExpander()
expanded_query = expander.expand_and_format("auth")
results = vector_store.search(expanded_query)
```

### Pattern 2: Multi-Query Search

```python
expander = QueryExpander()
expanded = expander.expand_query("how to authenticate", strategy="multi_query")

all_results = {}
for query_var in expanded.get_all_queries():
    results = vector_store.search(query_var, n_results=5)
    for r in results:
        if r['id'] not in all_results or r['score'] > all_results[r['id']]['score']:
            all_results[r['id']] = r

merged = sorted(all_results.values(), key=lambda x: x['score'], reverse=True)
```

### Pattern 3: Conditional Expansion

```python
def smart_search(query, vector_store):
    expander = QueryExpander()
    
    # Only expand if query is short (likely missing context)
    if len(query.split()) <= 2:
        query = expander.expand_and_format(query)
    
    return vector_store.search(query)
```

## Testing

Comprehensive test coverage:

```bash
# Run all tests
pytest tests/test_core/test_query_expansion.py -v

# Run demo
python examples/query_expansion_demo.py
```

**Test Results**: 40/40 tests passing (100%)

## Best Practices

### When to Use Query Expansion

✅ **USE query expansion for:**
- Short queries (1-2 words)
- Technical abbreviations (JWT, API, OAuth)
- When users might use different terminology
- Developer documentation search
- Questions needing multiple perspectives

❌ **DON'T use query expansion for:**
- Very specific queries (already detailed)
- Proper names or unique identifiers
- When precision is more important than recall
- Queries that are already working well

### Configuration Tips

```python
# More expansions for broad recall
expander = QueryExpander(max_expansions=10)

# Fewer expansions for precision
expander = QueryExpander(max_expansions=2)

# Disable abbreviations if not needed
expander = QueryExpander(enable_abbreviations=False)

# Disable domain expansions for non-technical content
expander = QueryExpander(enable_domain_expansions=False)
```

## Performance

- **Expansion Time**: <1ms (simple dictionary lookup)
- **Memory**: Minimal (~100KB for expansion dictionaries)
- **No Network Calls**: Works offline (unless using LLM-based expansion)
- **Thread-Safe**: Can be used concurrently

## Examples

See `examples/query_expansion_demo.py` for comprehensive demonstrations.

## Limitations

1. **English Only**: Optimized for English technical terms
2. **Domain-Specific**: Best for API/tech documentation
3. **No Context**: Doesn't understand query intent (yet)
4. **Fixed Dictionary**: Expansion terms are predefined

## Future Enhancements

- LLM-based dynamic expansion (with LLM client)
- Context-aware expansion
- Learning from user feedback
- Multi-language support
- Custom domain dictionaries

## Conclusion

Query expansion is a simple but powerful technique that improves search recall by 15-30% for short, technical queries. It's especially valuable for API documentation search where users and documents often use different terminology.

**Recommendation**: Enable for all technical documentation search systems.
