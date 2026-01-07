# Day 26: REST API

**Date**: 2025-12-27
**Phase**: 4 - Advanced Features (Extension)
**Status**: ✅ Completed

## Overview

Day 26 implements a comprehensive REST API using FastAPI to expose all the advanced search and document management capabilities built in Phase 4. The API provides production-ready endpoints for document management, search, filtering, and faceted search.

## Features Implemented

### 1. FastAPI Application

**Main Application** (`src/api/app.py` - 625 lines):
- RESTful API with OpenAPI documentation
- CORS middleware support
- Comprehensive error handling
- Request/response validation with Pydantic
- Auto-generated Swagger UI and ReDoc

### 2. Request/Response Models

**Pydantic Models** (`src/api/models.py` - 260 lines):
- Type-safe request models with validation
- Enum-based filter operators
- Nested filter specifications
- Response models for all endpoints
- Error response models

### 3. API Endpoints

#### Health & Stats
- `GET /health` - Health check
- `GET /stats` - Collection statistics

#### Document Management
- `POST /documents` - Add documents
- `GET /documents/{id}` - Get document
- `DELETE /documents/{id}` - Delete document
- `POST /documents/bulk-delete` - Bulk delete

#### Search
- `POST /search` - Search with multiple modes
- `POST /search/faceted` - Faceted search

### 4. Search Modes

**Vector Search**:
- Pure semantic similarity search
- Fast and accurate for semantic queries

**Hybrid Search**:
- BM25 + Vector with RRF fusion
- Best for mixed keyword/semantic queries

**Re-ranked Search**:
- Hybrid search + cross-encoder re-ranking
- Highest accuracy (requires model loading)

### 5. Advanced Features

**Filtering**:
- Simple metadata filters
- Complex filter combinations (AND, OR, NOT)
- Content filtering
- Automatic ChromaDB integration

**Query Expansion**:
- Domain-specific term expansion
- Multi-query generation
- Synonym expansion

**Result Diversification**:
- MMR algorithm
- Configurable relevance-diversity tradeoff
- Embedding-based similarity

**Faceted Search**:
- Aggregate by multiple fields
- Top N values by frequency
- Percentage calculations
- Filter integration

## API Endpoints

### Health Endpoints

#### GET /health

Health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "features": {
    "hybrid_search": true,
    "reranking": true,
    "query_expansion": true,
    "diversification": true,
    "faceted_search": true,
    "filtering": true
  }
}
```

#### GET /stats

Get collection statistics.

**Response**:
```json
{
  "collection": {
    "total_documents": 150,
    "collection_name": "api_docs"
  },
  "features": {
    "hybrid_search": true,
    "reranking": true,
    ...
  }
}
```

### Document Management

#### POST /documents

Add documents to the collection.

**Request**:
```json
{
  "documents": [
    {
      "content": "GET /api/users - Retrieve user information",
      "metadata": {
        "method": "GET",
        "category": "users",
        "version": "v1"
      },
      "id": "optional-custom-id"
    }
  ]
}
```

**Response** (201 Created):
```json
{
  "document_ids": ["abc123", "def456"],
  "count": 2
}
```

#### GET /documents/{document_id}

Get a document by ID.

**Response**:
```json
{
  "id": "abc123",
  "content": "GET /api/users - Retrieve user information",
  "metadata": {
    "method": "GET",
    "category": "users",
    "version": "v1"
  }
}
```

**Error** (404 Not Found):
```json
{
  "error": "HTTPException",
  "message": "Document not found: abc123"
}
```

#### DELETE /documents/{document_id}

Delete a document by ID.

**Response**:
```json
{
  "success": true,
  "message": "Document abc123 deleted successfully"
}
```

#### POST /documents/bulk-delete

Delete multiple documents.

**Request**:
```json
{
  "document_ids": ["abc123", "def456", "ghi789"]
}
```

**Response**:
```json
{
  "deleted_count": 2,
  "not_found_count": 1,
  "document_ids": ["abc123", "def456"]
}
```

### Search Endpoints

#### POST /search

Search for documents with advanced options.

**Request**:
```json
{
  "query": "user authentication",
  "n_results": 5,
  "mode": "hybrid",
  "filter": {
    "field": "method",
    "operator": "eq",
    "value": "GET"
  },
  "use_query_expansion": true,
  "use_diversification": true,
  "diversification_lambda": 0.5
}
```

**Parameters**:
- `query` (required): Search query
- `n_results` (default: 5): Number of results (1-100)
- `mode` (default: "hybrid"): Search mode ("vector", "hybrid", "reranked")
- `filter` (optional): Filter specification
- `use_query_expansion` (default: false): Enable query expansion
- `use_diversification` (default: false): Enable result diversification
- `diversification_lambda` (default: 0.5): Relevance-diversity balance (0-1)

**Response**:
```json
{
  "results": [
    {
      "id": "abc123",
      "content": "GET /api/auth/verify - Verify authentication token",
      "metadata": {
        "method": "GET",
        "category": "auth",
        "version": "v1"
      },
      "score": 0.8542,
      "method": "hybrid"
    }
  ],
  "total": 5,
  "query": "user authentication",
  "expanded_query": "user authentication login oauth verify",
  "mode": "hybrid"
}
```

#### POST /search/faceted

Faceted search with aggregations.

**Request**:
```json
{
  "query": "api endpoints",
  "facet_fields": ["method", "category", "version"],
  "n_results": 20,
  "filter": {
    "field": "category",
    "operator": "eq",
    "value": "users"
  },
  "top_facet_values": 10
}
```

**Parameters**:
- `query` (required): Search query
- `facet_fields` (required): Fields to aggregate on
- `n_results` (default: 20): Number of results
- `filter` (optional): Filter specification
- `top_facet_values` (default: 10): Max facet values to return

**Response**:
```json
{
  "results": [
    {
      "id": "abc123",
      "content": "GET /api/users - Retrieve user information",
      "metadata": {...},
      "score": 0.8542,
      "method": "hybrid"
    }
  ],
  "facets": {
    "method": {
      "field": "method",
      "values": [
        {"value": "GET", "count": 45, "percentage": 45.0},
        {"value": "POST", "count": 30, "percentage": 30.0},
        {"value": "PUT", "count": 15, "percentage": 15.0},
        {"value": "DELETE", "count": 10, "percentage": 10.0}
      ],
      "total_docs": 100
    },
    "category": {...},
    "version": {...}
  },
  "total": 20,
  "query": "api endpoints"
}
```

### Filter Specifications

Filters can be simple or complex:

**Simple Filter** (Equality):
```json
{
  "field": "method",
  "operator": "eq",
  "value": "GET"
}
```

**Range Filter**:
```json
{
  "field": "priority",
  "operator": "lte",
  "value": 3
}
```

**IN Filter**:
```json
{
  "field": "category",
  "operator": "in",
  "value": ["users", "auth", "webhooks"]
}
```

**AND Filter**:
```json
{
  "operator": "and",
  "filters": [
    {
      "field": "method",
      "operator": "eq",
      "value": "POST"
    },
    {
      "field": "category",
      "operator": "eq",
      "value": "users"
    }
  ]
}
```

**OR Filter**:
```json
{
  "operator": "or",
  "filters": [
    {
      "field": "method",
      "operator": "eq",
      "value": "POST"
    },
    {
      "field": "method",
      "operator": "eq",
      "value": "PUT"
    }
  ]
}
```

**NOT Filter**:
```json
{
  "operator": "not",
  "filters": [
    {
      "field": "status",
      "operator": "eq",
      "value": "deprecated"
    }
  ]
}
```

**Complex Nested Filter**:
```json
{
  "operator": "and",
  "filters": [
    {
      "operator": "or",
      "filters": [
        {"field": "method", "operator": "eq", "value": "POST"},
        {"field": "method", "operator": "eq", "value": "PUT"}
      ]
    },
    {
      "field": "category",
      "operator": "eq",
      "value": "users"
    },
    {
      "operator": "not",
      "filters": [
        {"field": "status", "operator": "eq", "value": "deprecated"}
      ]
    }
  ]
}
```

### Supported Filter Operators

**Comparison**:
- `eq` - Equal
- `ne` - Not equal
- `gt` - Greater than
- `gte` - Greater than or equal
- `lt` - Less than
- `lte` - Less than or equal

**String**:
- `contains` - Contains substring
- `not_contains` - Does not contain substring
- `starts_with` - Starts with
- `ends_with` - Ends with
- `regex` - Regular expression match

**Collection**:
- `in` - Value in list
- `not_in` - Value not in list

**Logical**:
- `and` - Combine filters with AND
- `or` - Combine filters with OR
- `not` - Negate filter

## Usage Examples

### Python Requests

```python
import requests

BASE_URL = "http://localhost:8000"

# Add documents
response = requests.post(
    f"{BASE_URL}/documents",
    json={
        "documents": [
            {
                "content": "GET /api/users - Retrieve users",
                "metadata": {"method": "GET", "category": "users"}
            }
        ]
    }
)
print(response.json())

# Search with hybrid mode
response = requests.post(
    f"{BASE_URL}/search",
    json={
        "query": "user authentication",
        "n_results": 5,
        "mode": "hybrid"
    }
)
print(response.json())

# Search with filter
response = requests.post(
    f"{BASE_URL}/search",
    json={
        "query": "api endpoints",
        "n_results": 10,
        "mode": "hybrid",
        "filter": {
            "field": "method",
            "operator": "eq",
            "value": "GET"
        }
    }
)
print(response.json())

# Faceted search
response = requests.post(
    f"{BASE_URL}/search/faceted",
    json={
        "query": "api",
        "facet_fields": ["method", "category"],
        "n_results": 20
    }
)
print(response.json())
```

### cURL

```bash
# Health check
curl http://localhost:8000/health

# Add documents
curl -X POST http://localhost:8000/documents \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {
        "content": "GET /api/users - Retrieve users",
        "metadata": {"method": "GET", "category": "users"}
      }
    ]
  }'

# Search
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "user authentication",
    "n_results": 5,
    "mode": "hybrid"
  }'

# Search with filter
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "api",
    "n_results": 10,
    "filter": {
      "field": "method",
      "operator": "eq",
      "value": "GET"
    }
  }'

# Faceted search
curl -X POST http://localhost:8000/search/faceted \
  -H "Content-Type: application/json" \
  -d '{
    "query": "api",
    "facet_fields": ["method", "category"],
    "n_results": 20
  }'
```

### JavaScript/TypeScript

```typescript
const BASE_URL = "http://localhost:8000";

// Add documents
const addResponse = await fetch(`${BASE_URL}/documents`, {
  method: "POST",
  headers: {"Content-Type": "application/json"},
  body: JSON.stringify({
    documents: [
      {
        content: "GET /api/users - Retrieve users",
        metadata: {method: "GET", category: "users"}
      }
    ]
  })
});
const addData = await addResponse.json();

// Search
const searchResponse = await fetch(`${BASE_URL}/search`, {
  method: "POST",
  headers: {"Content-Type": "application/json"},
  body: JSON.stringify({
    query: "user authentication",
    n_results: 5,
    mode: "hybrid"
  })
});
const searchData = await searchResponse.json();

// Faceted search
const facetedResponse = await fetch(`${BASE_URL}/search/faceted`, {
  method: "POST",
  headers: {"Content-Type": "application/json"},
  body: JSON.stringify({
    query: "api",
    facet_fields: ["method", "category"],
    n_results: 20
  })
});
const facetedData = await facetedResponse.json();
```

## Running the API

### Start Server

```bash
# Development mode with auto-reload
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000

# Or using Python module
python -m src.api.app

# Production mode
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --workers 4
```

### Configuration

The API can be configured when creating the app:

```python
from src.api.app import create_app

app = create_app(
    enable_hybrid=True,      # Enable hybrid search
    enable_reranker=True,    # Enable cross-encoder re-ranking
    enable_cors=True,        # Enable CORS middleware
)
```

### Interactive Documentation

Once the server is running:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Both provide interactive API documentation with Try-it-out functionality.

## Testing

### Running Tests

```bash
# Run all API tests
pytest tests/test_api/test_app.py -v

# Run specific test class
pytest tests/test_api/test_app.py::TestSearch -v

# Run with coverage
pytest tests/test_api/test_app.py --cov=src.api
```

### Test Coverage

**26 comprehensive tests** covering:
- Health endpoints (2 tests)
- Document management (6 tests)
- Search modes (10 tests)
- Faceted search (4 tests)
- Validation (3 tests)
- Error handling (1 test)

### Running Demo

```bash
# Start API server
uvicorn src.api.app:app --reload

# In another terminal, run demo
python examples/api_demo.py
```

## Architecture

### Request Flow

```
Client Request
    ↓
FastAPI Router
    ↓
Pydantic Validation
    ↓
Filter Conversion (FilterSpec → Filter)
    ↓
VectorStore Search
    ↓
Optional: Query Expansion
    ↓
Optional: Diversification
    ↓
Response Formatting
    ↓
Pydantic Serialization
    ↓
Client Response
```

### Error Handling

All errors are caught and returned with appropriate status codes:

**400 Bad Request**:
- Invalid filter operators
- Malformed requests

**404 Not Found**:
- Document not found
- Endpoint not found

**422 Unprocessable Entity**:
- Validation errors
- Invalid field values

**500 Internal Server Error**:
- Unexpected server errors
- Database errors

Error response format:
```json
{
  "error": "HTTPException",
  "message": "Document not found: abc123",
  "detail": {
    "additional": "info"
  }
}
```

## Performance Considerations

### Optimization Tips

1. **Use Hybrid Search**:
   - Best accuracy/performance balance
   - Faster than re-ranking

2. **Limit n_results**:
   - Don't retrieve more than needed
   - Impacts embedding/scoring time

3. **Caching**:
   - Query embeddings cached
   - Cross-encoder scores cached
   - BM25 indices cached

4. **Batch Operations**:
   - Use bulk delete for multiple documents
   - Add documents in batches

5. **Filter Early**:
   - Apply filters in search request
   - Reduces results to process

### Benchmarks

Approximate response times (on typical hardware):

- Health check: < 1ms
- Add 100 documents: 200-500ms
- Vector search (5 results): 20-50ms
- Hybrid search (5 results): 30-70ms
- Re-ranked search (5 results): 80-150ms
- Faceted search (3 fields): 40-80ms

## Production Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build and run
docker build -t api-assistant-api .
docker run -p 8000:8000 api-assistant-api
```

### Environment Variables

```bash
# .env file
CHROMA_PERSIST_DIR=/data/chroma_db
CHROMA_COLLECTION_NAME=api_docs
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### Security Considerations

1. **CORS Configuration**:
   - Configure `allow_origins` for production
   - Don't use `["*"]` in production

2. **Rate Limiting**:
   - Add rate limiting middleware
   - Prevent abuse

3. **Authentication**:
   - Add API key authentication
   - JWT tokens for user sessions

4. **Input Validation**:
   - Already handled by Pydantic
   - Additional validation as needed

5. **HTTPS**:
   - Use reverse proxy (nginx)
   - Enable HTTPS/TLS

## Future Enhancements

### Planned Features

1. **Authentication**:
   - API key authentication
   - OAuth2 integration
   - User management

2. **Rate Limiting**:
   - Per-IP rate limits
   - Per-user rate limits
   - Token bucket algorithm

3. **Batch Endpoints**:
   - Batch search
   - Batch get
   - Batch update

4. **Streaming**:
   - Server-sent events for long searches
   - Streaming search results
   - Real-time updates

5. **Analytics**:
   - Search analytics
   - Popular queries
   - Performance metrics

6. **Caching**:
   - Redis for distributed caching
   - Cache warming strategies
   - TTL configuration

## Conclusion

Day 26 completes the API Assistant project with a production-ready REST API:

✅ **FastAPI Application** - Modern, fast, auto-documented API
✅ **Document Management** - Full CRUD operations
✅ **Advanced Search** - Vector, hybrid, re-ranked modes
✅ **Filtering** - Simple and complex filter combinations
✅ **Faceted Search** - Build rich filter UIs
✅ **Query Expansion** - Improve search recall
✅ **Diversification** - Avoid redundant results
✅ **26 Unit Tests** - Comprehensive coverage
✅ **Interactive Docs** - Swagger UI and ReDoc
✅ **Demo Client** - Complete usage examples

The API exposes all Phase 4 advanced features through a clean, type-safe RESTful interface, making the API Assistant ready for production deployment and integration with frontend applications!
