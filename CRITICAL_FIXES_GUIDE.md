# Critical Fixes - Quick Reference Guide

This document provides immediate, actionable fixes for the CRITICAL issues identified in the project audit.

---

## 🔴 CRITICAL FIX #1: CORS Configuration

### Current Problem
```python
# src/api/app.py:111
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ SECURITY RISK - Any website can access API
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Fix Implementation

**Step 1:** Add to `.env.example`:
```bash
# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
```

**Step 2:** Add to `src/config.py`:
```python
class Settings(BaseSettings):
    # ... existing fields ...

    allowed_origins: str = Field(
        default="http://localhost:3000",
        description="Comma-separated list of allowed CORS origins"
    )

    @property
    def cors_origins(self) -> list[str]:
        """Parse allowed origins into list."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]
```

**Step 3:** Update `src/api/app.py:111`:
```python
from src.config import get_settings

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # ✅ From environment variable
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Step 4:** Update production `.env`:
```bash
ALLOWED_ORIGINS=https://your-frontend-domain.com
```

---

## 🔴 CRITICAL FIX #2: Remove Hardcoded SECRET_KEY

### Current Problem
```bash
# .env:57
SECRET_KEY=prod-secret-key-78b34dca104943501a458dd2aa9f3444d770f554cd6677f52b2b6cef86e06be5
```
**⚠️ This is committed to git - anyone with repo access has your secret!**

### Fix Implementation

**Step 1:** Remove from `.env`:
```bash
# Delete this line from .env (keep only in .env.example as template)
```

**Step 2:** Generate unique secret per environment:
```bash
# Generate new secret key
python -c "import secrets; print(secrets.token_hex(32))"
```

**Step 3:** Add to `.env.example` (as template only):
```bash
# Security - CRITICAL: Generate unique key per deployment
# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=your-secret-key-here-CHANGE-THIS
```

**Step 4:** Update `.gitignore` to ensure .env is never committed:
```bash
# Environment files
.env
.env.local
.env.production
*.env.backup
```

**Step 5:** Remove from git history (if committed):
```bash
# WARNING: This rewrites git history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (coordinate with team first!)
git push origin --force --all
```

**Step 6:** Use secrets management in production:
```python
# For production, use AWS Secrets Manager, Azure Key Vault, etc.
import boto3
from botocore.exceptions import ClientError

def get_secret_key():
    """Get SECRET_KEY from AWS Secrets Manager in production."""
    if os.getenv("ENVIRONMENT") == "production":
        client = boto3.client("secretsmanager", region_name="us-east-1")
        try:
            response = client.get_secret_value(SecretId="api-assistant/secret-key")
            return response["SecretString"]
        except ClientError as e:
            logger.error(f"Failed to retrieve secret: {e}")
            raise
    return os.getenv("SECRET_KEY")
```

---

## 🔴 CRITICAL FIX #3: Implement API Authentication

### Current Problem
All API endpoints are completely open - no authentication required.

### Fix Implementation (API Key Approach)

**Step 1:** Add to `src/api/auth.py` (create new file):
```python
"""API Authentication middleware."""
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from src.config import get_settings

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(API_KEY_HEADER)) -> str:
    """Verify API key from request header."""
    settings = get_settings()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Include 'X-API-Key' header."
        )

    # In production, validate against database or secrets manager
    valid_keys = settings.api_keys.split(",")

    if api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )

    return api_key
```

**Step 2:** Add to `src/config.py`:
```python
class Settings(BaseSettings):
    # ... existing fields ...

    api_keys: str = Field(
        default="",
        description="Comma-separated list of valid API keys"
    )

    require_auth: bool = Field(
        default=True,
        description="Require API key authentication"
    )
```

**Step 3:** Protect endpoints in `src/api/app.py`:
```python
from fastapi import Depends
from src.api.auth import verify_api_key

# Add to protected endpoints
@app.post("/documents/upload")
async def upload_documents(
    files: List[UploadFile] = File(...),
    api_key: str = Depends(verify_api_key),  # ✅ Add this
    # ... rest of parameters
):
    # ... implementation

@app.post("/search")
async def search_documents(
    request: SearchRequest,
    api_key: str = Depends(verify_api_key),  # ✅ Add this
):
    # ... implementation

# Repeat for all endpoints except /health
```

**Step 4:** Add to `.env.example`:
```bash
# API Authentication
REQUIRE_AUTH=true
API_KEYS=key1-generate-with-secrets-token-hex,key2-another-key
```

**Step 5:** Generate API keys:
```bash
# Generate API key
python -c "import secrets; print(f'api-key-{secrets.token_urlsafe(32)}')"
```

**Step 6:** Update frontend to include API key:
```typescript
// frontend/src/lib/api/client.ts

const API_KEY = process.env.NEXT_PUBLIC_API_KEY;

api.interceptors.request.use((config) => {
  // Add API key to all requests
  if (API_KEY) {
    config.headers['X-API-Key'] = API_KEY;
  }
  return config;
});
```

**Step 7:** Add to `frontend/.env.local`:
```bash
NEXT_PUBLIC_API_KEY=your-api-key-here
```

---

## 🔴 CRITICAL FIX #4: SQL Injection Pattern Fix

### Current Problem
```python
# src/core/security.py:59-64
SQL_INJECTION_PATTERNS = [
    r"(\bOR\b.*=.*)",  # ⚠️ Blocks "GET OR POST", "True OR False"
]
```

### Fix Implementation

**Replace with context-aware patterns:**
```python
# src/core/security.py:59-64
SQL_INJECTION_PATTERNS = [
    # More specific patterns that won't block legitimate queries
    r"(\bOR\b\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?)",  # OR with = sign
    r"(\bAND\b\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?)", # AND with = sign
    r"(;\s*DROP\s+)",
    r"(;\s*DELETE\s+)",
    r"(;\s*UPDATE\s+)",
    r"(UNION\s+SELECT)",
    r"(--\s*$)",  # SQL comment at end
    r"(/\*.*\*/)",  # SQL block comment
    r"(\bEXEC\b\s*\()",
    r"(\bEXECUTE\b\s*\()",
]

# Add separate validation for filter objects (not plain text queries)
def validate_filter_object(filter_obj: dict) -> bool:
    """Validate filter object for SQL injection in values."""
    for key, value in filter_obj.items():
        if isinstance(value, str):
            # Check for obvious SQL injection patterns
            if any(pattern in value.upper() for pattern in [
                "DROP TABLE", "DELETE FROM", "UPDATE SET",
                "UNION SELECT", "'; --"
            ]):
                return False
        elif isinstance(value, dict):
            if not validate_filter_object(value):
                return False
    return True
```

**Update usage in `src/api/app.py`:**
```python
from src.core.security import validate_input, validate_filter_object

@app.post("/search")
async def search_documents(request: SearchRequest):
    # Validate query text for SQL injection (allow "GET OR POST")
    if not validate_input(request.query):
        raise HTTPException(400, "Invalid query")

    # Validate filter object separately
    if request.filter and not validate_filter_object(request.filter):
        raise HTTPException(400, "Invalid filter")

    # ... continue with search
```

---

## ⚡ CRITICAL FIX #5: BM25 Performance Bottleneck

### Current Problem
```python
# src/core/vector_store.py:192, 293
def add_document(self, ...):
    # ... add one document ...
    if self.enable_hybrid_search:
        self._rebuild_bm25_index()  # ⚠️ O(n) - rebuilds ENTIRE index for ONE doc!
```

**Impact:** With 10,000 documents, adding 1 document processes all 10,000.

### Fix Implementation - Option 1: Lazy Rebuild with Dirty Flag

```python
# src/core/vector_store.py

class VectorStore:
    def __init__(self, ...):
        # ... existing init ...
        self._bm25_index = None
        self._bm25_dirty = False  # ✅ Track if index needs rebuild

    def add_document(self, content: str, metadata: dict, doc_id: Optional[str] = None):
        """Add a single document to the collection."""
        # ... existing add logic ...

        if self.enable_hybrid_search:
            self._bm25_dirty = True  # ✅ Mark as dirty, don't rebuild yet
            logger.debug("BM25 index marked as dirty, will rebuild on next search")

    def add_documents(self, documents: list[dict], batch_size: int = 100):
        """Add multiple documents in batches."""
        # ... existing batch add logic ...

        if self.enable_hybrid_search:
            self._bm25_dirty = True  # ✅ Mark as dirty
            logger.debug("BM25 index marked as dirty, will rebuild on next search")

    def _ensure_bm25_index(self):
        """Rebuild BM25 index only if dirty or not built."""
        if not self.enable_hybrid_search:
            return

        if self._bm25_index is None or self._bm25_dirty:
            logger.info("Rebuilding BM25 index...")
            self._rebuild_bm25_index()
            self._bm25_dirty = False  # ✅ Clear dirty flag
            logger.info("BM25 index rebuilt successfully")

    def search(self, query: str, ...):
        """Search with automatic BM25 rebuild if needed."""
        self._ensure_bm25_index()  # ✅ Only rebuild if dirty

        # ... rest of search implementation
```

**Benefits:**
- Adding 1 document: O(1) instead of O(n)
- Adding 1000 documents: Still O(1) marking, rebuild once on search
- Search performance unchanged

### Fix Implementation - Option 2: Incremental Updates

```python
# src/core/vector_store.py

def _update_bm25_index_incremental(self, new_doc_ids: list[str]):
    """Update BM25 index incrementally with new documents."""
    if not self.enable_hybrid_search or not self._bm25_index:
        return

    # Fetch new documents
    results = self.collection.get(ids=new_doc_ids)

    if not results["documents"]:
        return

    # Tokenize new documents
    new_tokenized = [doc.lower().split() for doc in results["documents"]]

    # Update BM25 corpus (requires modified BM25 implementation)
    # This is more complex and requires BM25Okapi to support incremental updates
    # For now, lazy rebuild (Option 1) is simpler and effective

    logger.info(f"Incrementally updated BM25 index with {len(new_doc_ids)} documents")
```

**Recommendation:** Use **Option 1 (Lazy Rebuild)** - simpler, effective, and proven pattern.

### Testing the Fix

```python
# Test performance improvement
import time

# Before fix:
start = time.time()
for i in range(100):
    vector_store.add_document(f"Document {i}", {"index": i})
print(f"Before: {time.time() - start:.2f}s")  # ~30-60s with 1000 existing docs

# After fix:
start = time.time()
for i in range(100):
    vector_store.add_document(f"Document {i}", {"index": i})
print(f"After: {time.time() - start:.2f}s")   # ~0.5-1s

# Index rebuilds once on first search
start = time.time()
vector_store.search("test query")
print(f"First search: {time.time() - start:.2f}s")  # Includes rebuild time

start = time.time()
vector_store.search("another query")
print(f"Second search: {time.time() - start:.2f}s")  # No rebuild, fast
```

---

## 🎯 CRITICAL FIX #6: Frontend Type Misalignment

### Current Problem
```typescript
// frontend/src/types/index.ts:62-72
export interface SearchResponse {
  results: SearchResult[];
  query: string;
  total_results: number;      // ❌ Backend sends "total"
  search_time_ms: number;     // ❌ Backend doesn't send this
  metadata: {                 // ❌ Backend sends different structure
    use_hybrid: boolean;
    use_reranking: boolean;
    use_query_expansion: boolean;
  };
}
```

### Fix Implementation

**Step 1:** Check actual backend response:
```python
# src/api/models.py:209-217
class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int                    # ✅ Not "total_results"
    query: str
    expanded_query: Optional[str]
    mode: SearchMode              # ✅ Not "metadata"
```

**Step 2:** Update frontend type to match:
```typescript
// frontend/src/types/index.ts:62-72
export interface SearchResponse {
  results: SearchResult[];
  query: string;
  total: number;                  // ✅ Match backend
  expanded_query?: string;        // ✅ Add this
  mode: 'vector' | 'hybrid' | 'reranked';  // ✅ Add this
}
```

**Step 3:** Update all usages:
```typescript
// Find and replace in all files:
// total_results → total

// frontend/src/components/search/SearchResults.tsx
<p className="text-sm text-muted-foreground">
  Found {results.total} results  {/* ✅ Changed from total_results */}
</p>

// frontend/src/hooks/useSearch.ts
const totalResults = data?.total || 0;  {/* ✅ Changed from total_results */}
```

---

## 🎯 CRITICAL FIX #7: Fix clearAllDocuments Endpoint

### Current Problem
```typescript
// frontend/src/lib/api/documents.ts:92
export async function clearAllDocuments(): Promise<ApiResponse<void>> {
  return apiRequest<void>({
    method: "DELETE",
    url: "/documents",  // ❌ This endpoint doesn't exist on backend!
  });
}
```

### Fix Implementation - Option 1: Remove Function (Recommended)

```typescript
// frontend/src/lib/api/documents.ts:92
// DELETE THIS FUNCTION - endpoint doesn't exist

// If UI uses it, replace with bulkDeleteDocuments:
export async function clearAllDocuments(): Promise<ApiResponse<void>> {
  // First, get all document IDs
  const allDocs = await exportDocuments();
  if (!allDocs.data) {
    throw new Error("Failed to fetch documents");
  }

  const docIds = allDocs.data.map(doc => doc.id);

  // Then bulk delete
  return bulkDeleteDocuments(docIds);
}
```

### Fix Implementation - Option 2: Add Backend Endpoint

```python
# src/api/app.py (add new endpoint)
@app.delete("/documents")
async def clear_all_documents():
    """Delete all documents from the collection."""
    try:
        vector_store = get_vector_store()

        # Get all document IDs
        all_docs = vector_store.collection.get()
        doc_ids = all_docs["ids"]

        if doc_ids:
            vector_store.collection.delete(ids=doc_ids)
            logger.info(f"Cleared {len(doc_ids)} documents")

        return {"message": f"Cleared {len(doc_ids)} documents", "count": len(doc_ids)}

    except Exception as e:
        logger.error(f"Clear all failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Recommendation:** Use **Option 1** - reuse existing bulk delete endpoint.

---

## 🛡️ CRITICAL FIX #8: Fix Bare Exception Handlers

### Current Problem (9 instances)
```python
# src/parsers/pdf_parser.py:60
try:
    content_str = content.decode('utf-8')
except:  # ⚠️ Catches EVERYTHING including KeyboardInterrupt!
    content_str = content
```

### Fix Implementation

```python
# src/parsers/pdf_parser.py:60
try:
    content_str = content.decode('utf-8')
except (UnicodeDecodeError, AttributeError) as e:  # ✅ Specific exceptions
    logger.warning(f"Failed to decode content as UTF-8: {e}")
    content_str = str(content)  # Fallback

# src/parsers/format_handler.py:133
try:
    api_spec = self.openapi_parser.parse(content_str)
    return api_spec, "openapi"
except Exception as e:  # If catching all, at least log it
    logger.debug(f"Not OpenAPI format: {e}")
    # Continue trying other formats
```

### Systematic Fix Script

```bash
# Find all bare except blocks
grep -rn "except:" src/

# Replace pattern:
# Old: except:
# New: except Exception as e:
#      logger.error(f"Error in <function_name>: {e}")
```

---

## Testing Critical Fixes

### Test Suite for Critical Fixes

```python
# tests/test_critical_fixes.py
import pytest
from src.api.app import app
from src.core.vector_store import VectorStore
from fastapi.testclient import TestClient

def test_cors_not_allow_all():
    """Ensure CORS is not set to allow all origins."""
    from src.api.app import app

    cors_middleware = None
    for middleware in app.user_middleware:
        if middleware.cls.__name__ == "CORSMiddleware":
            cors_middleware = middleware
            break

    assert cors_middleware is not None
    # Should not be ["*"]
    assert cors_middleware.options["allow_origins"] != ["*"]

def test_api_key_required():
    """Ensure API key is required for protected endpoints."""
    client = TestClient(app)

    # Should reject without API key
    response = client.post("/search", json={"query": "test"})
    assert response.status_code == 401

def test_bm25_lazy_rebuild():
    """Ensure BM25 index uses lazy rebuild."""
    vector_store = VectorStore()

    # Add document should not trigger rebuild
    import time
    start = time.time()
    vector_store.add_document("test content", {"test": "metadata"})
    duration = time.time() - start

    # Should be fast (< 0.1s) even with many docs
    assert duration < 0.1, "add_document took too long - likely rebuilding index"

    # Dirty flag should be set
    assert vector_store._bm25_dirty == True

def test_search_response_type():
    """Ensure frontend SearchResponse type matches backend."""
    client = TestClient(app)

    response = client.post("/search", json={"query": "test"}, headers={"X-API-Key": "valid-key"})
    data = response.json()

    # Backend should send "total", not "total_results"
    assert "total" in data
    assert "total_results" not in data
```

---

## Quick Verification Checklist

After implementing fixes, verify:

- [ ] `git grep "allow_origins=\[\"\\*\"\]"` returns no results
- [ ] `.env` file does not contain SECRET_KEY
- [ ] `curl http://localhost:8000/search` without API key returns 401
- [ ] Adding 100 documents completes in < 2 seconds
- [ ] Frontend search displays results without console errors
- [ ] No bare `except:` statements remain (use `git grep "except:" src/`)
- [ ] All tests pass: `pytest tests/test_critical_fixes.py`

---

## Next Steps

1. Implement these 8 critical fixes
2. Test each fix thoroughly
3. Update documentation
4. Move to HIGH priority fixes (documentation consolidation, test coverage)
5. Review PROJECT_AUDIT_REPORT.md for complete remediation plan

**Estimated time for critical fixes:** 4-6 days for experienced developer
