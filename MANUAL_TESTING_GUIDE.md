# 🧪 API Assistant - Comprehensive Manual Testing Guide

**Version:** 2.0.0 (Enhanced Edition)
**Last Updated:** 2025-12-30
**Test Cases:** 199 comprehensive scenarios
**Purpose:** Complete manual testing guide covering all features with UI, API, CLI, E2E, Security, Accessibility, and Mobile testing

---

## 📋 Table of Contents

1. [Prerequisites & Setup](#prerequisites--setup)
2. [Test Data Preparation](#test-data-preparation)
3. [Backend API Testing](#backend-api-testing) - 30 tests
4. [Frontend UI Testing](#frontend-ui-testing) - 75 tests
5. [CLI Testing](#cli-testing) - 35 tests
6. [End-to-End Testing](#end-to-end-testing) - 10 tests
7. [Performance & Edge Cases](#performance--edge-cases) - 12 tests
8. [Security & Validation Testing](#security--validation-testing) - 12 tests
9. [Advanced Integration Testing](#advanced-integration-testing) - 10 tests
10. [Accessibility Testing](#accessibility-testing) - 8 tests
11. [Mobile & Responsive Testing](#mobile--responsive-testing) - 7 tests
12. [Advanced CLI Testing](#advanced-cli-testing) - 10 tests (within CLI section)
13. [Test Results Template](#test-results-template)
14. [Test Coverage Summary](#test-coverage-summary)

---

## Prerequisites & Setup

### Environment Setup

1. **Start Backend Server**

   **For Linux/Mac:**
   ```bash
   # Terminal 1 - Backend
   cd /path/to/Api-Assistant
   source venv/bin/activate
   uvicorn src.api.app:app --reload --port 8000
   ```

   **For Windows PowerShell:**
   ```powershell
   # Terminal 1 - Backend
   cd C:\path\to\Api-Assistant
   .\venv\Scripts\Activate.ps1
   uvicorn src.api.app:app --reload --port 8000
   ```

2. **Start Frontend Server**
   ```bash
   # Terminal 2 - Frontend
   cd frontend
   npm run dev
   ```

3. **Verify LLM Provider**
   - Check `.env` file has `LLM_PROVIDER=ollama` or `LLM_PROVIDER=groq`
   - If using Ollama: verify `ollama serve` is running and model is pulled
   - If using Groq: verify `GROQ_API_KEY` is set

4. **Access Points**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Alternative Docs: http://localhost:8000/redoc

---

## Test Data Preparation

### Sample Files Location

All sample files are in the `examples/` directory:
- `examples/sample-openapi.json` - OpenAPI 3.0 specification
- `examples/sample-text.txt` - Plain text documentation
- `examples/sample-markdown.md` - Markdown API guide
- `examples/sample-data.json` - Generic JSON data
- `examples/graphql/` - GraphQL schema files

### Create Additional Test Files

**1. Create a PDF test file** (if needed):
```bash
# Use any PDF file or create one from examples/sample-markdown.md
# You can use online tools to convert MD to PDF
```

**2. Create invalid test files**:

**For Linux/Mac:**
```bash
# Create invalid JSON
echo '{"invalid": json}' > examples/invalid.json

# Create empty file
touch examples/empty.txt

# Create large file (for performance testing)
for i in {1..1000}; do cat examples/sample-text.txt >> examples/large-text.txt; done
```

**For Windows PowerShell:**
```powershell
# Create invalid JSON
Set-Content -Path examples/invalid.json -Value '{"invalid": json}'

# Create empty file
New-Item -Path examples/empty.txt -ItemType File -Force

# Create large file (for performance testing)
1..1000 | ForEach-Object { Get-Content examples/sample-text.txt | Add-Content examples/large-text.txt }
```

---

## Backend API Testing

> **Note for Windows PowerShell Users:**
> - Most test cases below use `curl` commands, which work in PowerShell 7+ and Windows 10/11 (curl is aliased to `Invoke-WebRequest`)
> - If you encounter issues with `curl`, you can use native PowerShell cmdlets:
>   - Replace `curl` with `Invoke-RestMethod` for JSON responses
>   - Replace `curl` with `Invoke-WebRequest` for detailed HTTP responses
> - Example: `curl -X POST "http://localhost:8000/search" -H "Content-Type: application/json" -d '{"query":"test"}'`
>   becomes: `Invoke-RestMethod -Uri "http://localhost:8000/search" -Method POST -ContentType "application/json" -Body '{"query":"test"}'`

### Test Category: Health & Stats Endpoints

#### TEST-API-001: Health Check Endpoint
**Type:** API Test
**Endpoint:** `GET /health`
**Method:** cURL or Postman

**Steps:**
1. Open terminal
2. Execute:
   ```bash
   curl http://localhost:8000/health
   ```

**Expected Result:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-12-30T..."
}
```

**Pass Criteria:**
- Status code: 200
- Response contains all 3 fields
- Status is "healthy"

---

#### TEST-API-002: Statistics Endpoint
**Type:** API Test
**Endpoint:** `GET /stats`

**Steps:**
1. Execute:
   ```bash
   curl http://localhost:8000/stats
   ```

**Expected Result:**
```json
{
  "total_documents": 0,
  "unique_apis": 0,
  "total_endpoints": 0,
  "avg_endpoints_per_api": 0.0,
  "format_distribution": {},
  "method_distribution": {}
}
```

**Pass Criteria:**
- Status code: 200
- All numeric fields present
- Values >= 0

---

### Test Category: Document Upload & Management

#### TEST-API-003: Upload OpenAPI Specification
**Type:** API Test
**Endpoint:** `POST /documents/upload`

**Steps:**
1. Use Swagger UI at http://localhost:8000/docs or cURL:
   ```bash
   curl -X POST "http://localhost:8000/documents/upload" \
     -H "Content-Type: multipart/form-data" \
     -F "files=@examples/sample-openapi.json"
   ```

**Expected Result:**
```json
{
  "uploaded_count": 1,
  "failed_count": 0,
  "results": [
    {
      "filename": "sample-openapi.json",
      "success": true,
      "format": "openapi",
      "endpoints_found": 3,
      "chunks_created": 6,
      "message": "Successfully parsed and indexed"
    }
  ]
}
```

**Pass Criteria:**
- Status code: 200
- uploaded_count = 1
- failed_count = 0
- format detected as "openapi"
- chunks_created > 0

---

#### TEST-API-004: Upload General Document (PDF)
**Type:** API Test
**Endpoint:** `POST /documents/upload`

**Test Data:** Use any PDF file or create from examples/sample-markdown.md

**Steps:**
```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "files=@path/to/test.pdf"
```

**Expected Result:**
```json
{
  "uploaded_count": 1,
  "failed_count": 0,
  "results": [
    {
      "filename": "test.pdf",
      "success": true,
      "format": "pdf",
      "chunks_created": 5
    }
  ]
}
```

**Pass Criteria:**
- Status code: 200
- Format detected as "pdf"
- chunks_created > 0

---

#### TEST-API-005: Upload Text File
**Type:** API Test
**Test Data:** `examples/sample-text.txt`

**Steps:**
```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -F "files=@examples/sample-text.txt"
```

**Expected Result:**
- Format: "text"
- Success: true
- Chunks created based on content

---

#### TEST-API-006: Upload Markdown File
**Type:** API Test
**Test Data:** `examples/sample-markdown.md`

**Steps:**
```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -F "files=@examples/sample-markdown.md"
```

**Expected Result:**
- Format: "markdown"
- Multiple chunks (one per section based on headers)

---

#### TEST-API-007: Upload Generic JSON
**Type:** API Test
**Test Data:** `examples/sample-data.json`

**Steps:**
```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -F "files=@examples/sample-data.json"
```

**Expected Result:**
- Format: "json_generic"
- Chunks created for each top-level key

---

#### TEST-API-008: Batch Upload Multiple Files
**Type:** API Test

**Steps:**
```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -F "files=@examples/sample-openapi.json" \
  -F "files=@examples/sample-text.txt" \
  -F "files=@examples/sample-markdown.md"
```

**Expected Result:**
- uploaded_count: 3
- All files successfully processed
- Different formats detected

---

#### TEST-API-009: Upload Invalid File
**Type:** API Test - Negative Case
**Test Data:** `examples/invalid.json`

**Steps:**
```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -F "files=@examples/invalid.json"
```

**Expected Result:**
- failed_count: 1
- Error message describing parse failure

---

#### TEST-API-010: Get Document by ID
**Type:** API Test
**Prerequisite:** Upload a document first and note its ID

**Steps:**
```bash
# First upload
curl -X POST "http://localhost:8000/documents/upload" \
  -F "files=@examples/sample-openapi.json"

# Note the document IDs from response, then get one:
curl "http://localhost:8000/documents/{document_id}"
```

**Expected Result:**
- Document details returned
- Content and metadata present

---

#### TEST-API-011: Delete Document
**Type:** API Test

**Steps:**
```bash
# Get a document ID first, then delete:
curl -X DELETE "http://localhost:8000/documents/{document_id}"
```

**Expected Result:**
```json
{
  "deleted_count": 1,
  "message": "Successfully deleted document"
}
```

---

#### TEST-API-012: Bulk Delete Documents
**Type:** API Test

**Steps:**
```bash
curl -X POST "http://localhost:8000/documents/bulk-delete" \
  -H "Content-Type: application/json" \
  -d '{"document_ids": ["id1", "id2", "id3"]}'
```

**Expected Result:**
- deleted_count equals number of valid IDs
- Success confirmation

---

### Test Category: Search Functionality

#### TEST-API-013: Vector Search
**Type:** API Test
**Prerequisite:** Documents uploaded

**Steps:**
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "user authentication",
    "mode": "vector",
    "n_results": 5
  }'
```

**Expected Result:**
```json
{
  "results": [
    {
      "content": "...",
      "score": 0.85,
      "metadata": {
        "source": "...",
        "endpoint": "..."
      }
    }
  ],
  "total_results": 5,
  "search_mode": "vector"
}
```

**Pass Criteria:**
- Results sorted by score (descending)
- All scores between 0 and 1

---

#### TEST-API-014: Hybrid Search
**Type:** API Test

**Steps:**
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "GET request users",
    "mode": "hybrid",
    "n_results": 10
  }'
```

**Expected Result:**
- search_mode: "hybrid"
- Results combine vector and BM25 scores

---

#### TEST-API-015: Search with Query Expansion
**Type:** API Test

**Steps:**
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "auth",
    "mode": "hybrid",
    "use_query_expansion": true
  }'
```

**Expected Result:**
- expanded_queries field present
- More diverse results (auth, authentication, authorization)

---

#### TEST-API-016: Search with Filters
**Type:** API Test

**Steps:**
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "user",
    "mode": "vector",
    "filter": {
      "field": "method",
      "operator": "eq",
      "value": "GET"
    }
  }'
```

**Expected Result:**
- Only GET method results returned
- Filter applied correctly

---

#### TEST-API-017: Faceted Search
**Type:** API Test

**Steps:**
```bash
curl -X POST "http://localhost:8000/faceted-search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "api",
    "facet_fields": ["method", "format", "source"],
    "n_results": 20
  }'
```

**Expected Result:**
```json
{
  "results": [...],
  "facets": [
    {
      "field": "method",
      "values": [
        {"value": "GET", "count": 10},
        {"value": "POST", "count": 5}
      ]
    }
  ]
}
```

---

### Test Category: Chat & AI Features

#### TEST-API-018: Chat - Simple Question
**Type:** API Test

**Steps:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What APIs are available?",
    "enable_url_scraping": false,
    "enable_auto_indexing": false
  }'
```

**Expected Result:**
```json
{
  "response": "Based on the indexed documents...",
  "sources": [...],
  "scraped_urls": [],
  "indexed_docs": 0,
  "context_results": 5
}
```

---

#### TEST-API-019: Chat with URL Scraping
**Type:** API Test

**Steps:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tell me about this API: https://jsonplaceholder.typicode.com/users",
    "enable_url_scraping": true,
    "enable_auto_indexing": true
  }'
```

**Expected Result:**
- scraped_urls contains the URL
- indexed_docs > 0
- Response includes information from scraped content

---

#### TEST-API-020: Chat with File Upload
**Type:** API Test

**Steps:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -F "message=Explain this document" \
  -F "files=@examples/sample-text.txt" \
  -F "enable_auto_indexing=true"
```

**Expected Result:**
- File processed and indexed
- Response references file content
- indexed_docs > 0

---

#### TEST-API-021: Chat - Code Generation Request
**Type:** API Test

**Steps:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Write Python code to fetch users from the API",
    "agent_type": "code"
  }'
```

**Expected Result:**
- Response contains Python code
- Code includes proper imports
- Code has docstrings and examples

---

### Test Category: Session Management

#### TEST-API-022: Create Session
**Type:** API Test

**Steps:**
```bash
curl -X POST "http://localhost:8000/sessions" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_001",
    "ttl_minutes": 60,
    "settings": {
      "default_search_mode": "hybrid",
      "use_reranking": true
    }
  }'
```

**Expected Result:**
```json
{
  "session": {
    "session_id": "uuid-here",
    "user_id": "test_user_001",
    "status": "active",
    "created_at": "...",
    "expires_at": "...",
    "settings": {...}
  }
}
```

---

#### TEST-API-023: List Sessions
**Type:** API Test

**Steps:**
```bash
curl "http://localhost:8000/sessions?limit=10&status=active"
```

**Expected Result:**
- List of active sessions
- Pagination info included

---

#### TEST-API-024: Get Session Details
**Type:** API Test

**Steps:**
```bash
curl "http://localhost:8000/sessions/{session_id}"
```

**Expected Result:**
- Full session details
- Conversation history if any
- Settings object

---

#### TEST-API-025: Update Session
**Type:** API Test

**Steps:**
```bash
curl -X PATCH "http://localhost:8000/sessions/{session_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "ttl_minutes": 120,
    "settings": {
      "default_search_mode": "vector"
    }
  }'
```

**Expected Result:**
- Session updated
- New expires_at time
- Settings updated

---

#### TEST-API-026: Delete Session
**Type:** API Test

**Steps:**
```bash
curl -X DELETE "http://localhost:8000/sessions/{session_id}"
```

**Expected Result:**
- Success confirmation
- Session no longer in list

---

### Test Category: Diagram Generation

#### TEST-API-027: Generate Sequence Diagram
**Type:** API Test

**Steps:**
```bash
curl -X POST "http://localhost:8000/diagrams/sequence" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "examples/sample-openapi.json",
    "endpoint_path": "/users/{id}",
    "method": "GET"
  }'
```

**Expected Result:**
```json
{
  "diagram": "sequenceDiagram\n    participant Client...",
  "diagram_type": "sequence",
  "format": "mermaid"
}
```

---

#### TEST-API-028: Generate ER Diagram (GraphQL)
**Type:** API Test
**Prerequisite:** GraphQL schema file

**Steps:**
```bash
curl -X POST "http://localhost:8000/diagrams/er" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "examples/graphql/schema.graphql"
  }'
```

**Expected Result:**
- ER diagram in Mermaid format
- Shows entities and relationships

---

#### TEST-API-029: Generate Auth Flow Diagram
**Type:** API Test

**Steps:**
```bash
curl -X POST "http://localhost:8000/diagrams/auth-flow" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "examples/sample-openapi.json",
    "auth_type": "bearer"
  }'
```

**Expected Result:**
- Auth flow diagram
- Shows token acquisition and usage

---

#### TEST-API-030: Generate API Overview
**Type:** API Test

**Steps:**
```bash
curl -X POST "http://localhost:8000/diagrams/overview" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "examples/sample-openapi.json"
  }'
```

**Expected Result:**
- High-level API overview flowchart
- Shows all endpoints grouped by category

---

## Frontend UI Testing

### Test Category: Authentication & Navigation

#### TEST-UI-001: Login Page
**Type:** UI Test

**Steps:**
1. Navigate to http://localhost:3000
2. Click "Login" or access login page
3. Enter test credentials (or use guest mode if available)
4. Click "Sign In"

**Expected Result:**
- Redirects to home/dashboard
- User menu shows logged-in state
- Session persists on page refresh

**Pass Criteria:**
- No console errors
- Successful authentication
- Proper redirect

---

#### TEST-UI-002: Guest Mode Access
**Type:** UI Test

**Steps:**
1. Navigate to http://localhost:3000
2. Look for "Continue as Guest" option
3. Click guest access

**Expected Result:**
- Access granted to main features
- No authentication required
- Limited features if applicable

---

#### TEST-UI-003: Navigation Between Pages
**Type:** UI Test

**Steps:**
1. Login to application
2. Click each navigation menu item:
   - Home/Dashboard
   - Documents
   - Chat
   - Search
   - Diagrams
   - Sessions
   - Settings

**Expected Result:**
- Each page loads without errors
- Active page highlighted in nav
- Smooth transitions

---

#### TEST-UI-004: Logout Functionality
**Type:** UI Test

**Steps:**
1. Login to application
2. Click user menu/profile icon
3. Click "Logout"

**Expected Result:**
- Redirects to login page
- Session cleared
- Cannot access protected routes

---

### Test Category: Document Upload & Management

#### TEST-UI-005: Upload OpenAPI File via UI
**Type:** UI Test
**Test Data:** `examples/sample-openapi.json`

**Steps:**
1. Navigate to Documents page
2. Click "Upload Documents" or similar button
3. Select file from file picker: `examples/sample-openapi.json`
4. Click "Upload" button

**Expected Result:**
- File uploads successfully
- Success toast/notification appears
- Stats show:
  - Format: OpenAPI
  - Endpoints found: 3
  - Chunks created: 6+
- Document appears in documents list

**Pass Criteria:**
- No errors in console
- Toast shows success
- Document indexed

---

#### TEST-UI-006: Upload PDF via UI
**Type:** UI Test
**Test Data:** Any PDF file

**Steps:**
1. Go to Documents page
2. Click upload area
3. Select PDF file
4. Upload

**Expected Result:**
- PDF accepted (check accept attribute includes .pdf)
- Processing indicator shown
- Success message
- Format detected as "pdf"

---

#### TEST-UI-007: Upload Text File via UI
**Type:** UI Test
**Test Data:** `examples/sample-text.txt`

**Steps:**
1. Documents page → Upload
2. Select `sample-text.txt`
3. Upload

**Expected Result:**
- Accepted as text file
- Chunked appropriately
- Success confirmation

---

#### TEST-UI-008: Upload Markdown via UI
**Type:** UI Test
**Test Data:** `examples/sample-markdown.md`

**Steps:**
1. Upload `sample-markdown.md`
2. Check format detection

**Expected Result:**
- Format: markdown
- Multiple chunks (by sections)
- Success message

---

#### TEST-UI-009: Upload Multiple Files at Once
**Type:** UI Test

**Steps:**
1. Documents page → Upload
2. Select multiple files:
   - sample-openapi.json
   - sample-text.txt
   - sample-markdown.md
3. Upload all

**Expected Result:**
- All files processed
- Progress indicator for each
- Summary shows all uploads
- Individual success/failure per file

---

#### TEST-UI-010: Upload Invalid File
**Type:** UI Test - Negative Case
**Test Data:** `examples/invalid.json`

**Steps:**
1. Try to upload invalid.json
2. Observe error handling

**Expected Result:**
- Error message shown
- User-friendly error description
- Upload doesn't crash page

---

#### TEST-UI-011: View Uploaded Documents List
**Type:** UI Test

**Steps:**
1. Navigate to Documents page
2. View the list of uploaded documents

**Expected Result:**
- Documents displayed in table/cards
- Shows: filename, format, upload date, chunks
- Pagination if many documents
- Sort/filter options available

---

#### TEST-UI-012: Delete Document from UI
**Type:** UI Test

**Steps:**
1. Documents page
2. Find a document
3. Click delete/trash icon
4. Confirm deletion if prompted

**Expected Result:**
- Confirmation dialog appears
- After confirm: document removed from list
- Success notification
- Stats updated

---

#### TEST-UI-013: Bulk Delete Documents
**Type:** UI Test

**Steps:**
1. Documents page
2. Select multiple documents (checkboxes)
3. Click "Delete Selected" or bulk action
4. Confirm

**Expected Result:**
- All selected documents deleted
- Success message with count
- List updated

---

#### TEST-UI-014: Format Selection Override
**Type:** UI Test

**Steps:**
1. Upload page
2. Select a file
3. Before uploading, manually select format (e.g., "OpenAPI")
4. Upload

**Expected Result:**
- Selected format used instead of auto-detection
- Proper parsing with selected format

---

#### TEST-UI-056: View Document Library
**Type:** UI Test

**Steps:**
1. Navigate to Documents/Home page
2. Click "Document Library" tab
3. View list of uploaded documents

**Expected Result:**
- All uploaded documents displayed
- Shows: filename, format, date, chunks, size
- Sortable by different columns
- Pagination if many documents

---

#### TEST-UI-057: Filter Documents by Format
**Type:** UI Test

**Steps:**
1. Document Library tab
2. Use format filter dropdown
3. Select "OpenAPI"
4. Observe filtered results

**Expected Result:**
- Only OpenAPI documents shown
- Filter badge displayed
- Count updated
- Can clear filter

---

#### TEST-UI-058: Sort Documents
**Type:** UI Test

**Steps:**
1. Document Library
2. Click column headers to sort:
   - By name (A-Z, Z-A)
   - By date (newest/oldest)
   - By size

**Expected Result:**
- Documents reorder correctly
- Sort indicator shown
- Persists during session

---

#### TEST-UI-059: Search Within Documents
**Type:** UI Test

**Steps:**
1. Document Library
2. Use search box to filter by filename
3. Type: "openapi"

**Expected Result:**
- Only matching documents shown
- Search is case-insensitive
- Real-time filtering

---

#### TEST-UI-060: View Document Details Modal
**Type:** UI Test

**Steps:**
1. Document Library
2. Click on a document row
3. View details modal/page

**Expected Result:**
- Full document information shown
- Content preview available
- Metadata displayed
- Chunk count and IDs
- Can edit tags/metadata
- Can delete from here

---

#### TEST-UI-061: Document Stats Per File
**Type:** UI Test

**Steps:**
1. View document details
2. Check statistics:
   - Chunk count
   - Token count
   - Format type
   - Upload date
   - File size

**Expected Result:**
- All stats accurate
- Formatted nicely
- Helpful tooltips

---

#### TEST-UI-062: Tab Switching (Upload ↔ Library)
**Type:** UI Test

**Steps:**
1. Documents page
2. Switch between tabs:
   - Upload Documents
   - Document Library
3. Perform actions in each tab
4. Switch tabs again

**Expected Result:**
- Tab content loads instantly
- State preserved when switching back
- No data loss
- Active tab highlighted

---

#### TEST-UI-063: Refresh Document List
**Type:** UI Test

**Steps:**
1. Document Library
2. Upload new document in another tab/window
3. Click refresh button in Library
4. Verify new document appears

**Expected Result:**
- List refreshes
- New documents appear
- Maintains scroll position
- Loading indicator shown

---

#### TEST-UI-064: Empty State Handling
**Type:** UI Test

**Steps:**
1. Clear all documents
2. Navigate to Document Library

**Expected Result:**
- Empty state UI shown
- Helpful message: "No documents yet"
- Call-to-action: "Upload your first document"
- Link to upload tab

---

#### TEST-UI-065: Document Count Display
**Type:** UI Test
**Prerequisite:** Upload 5+ documents

**Steps:**
1. Document Library
2. Check document count display
3. Apply filters
4. Check count updates

**Expected Result:**
- Total count shown: "Showing 5 of 12 documents"
- Updates when filtering
- Accurate at all times

---

### Test Category: Chat Interface

#### TEST-UI-015: Basic Chat Question
**Type:** UI Test
**Prerequisite:** Documents uploaded

**Steps:**
1. Navigate to Chat page
2. Type: "What APIs are available?"
3. Press Enter or click Send

**Expected Result:**
- Message appears in chat
- Loading indicator shown
- AI response received
- Response includes source citations
- Conversation history maintained

---

#### TEST-UI-016: Chat with File Attachment
**Type:** UI Test
**Test Data:** `examples/sample-text.txt`

**Steps:**
1. Chat page
2. Click paperclip/attachment icon
3. Select `sample-text.txt`
4. See file preview (name, size)
5. Type: "Summarize this document"
6. Send

**Expected Result:**
- File shown in "Attached Files" section
- File size displayed (XX KB)
- Remove (X) button available
- After send: file uploaded and processed
- Toast shows: "Uploaded 1 file, Indexed X documents"
- AI response references the document

---

#### TEST-UI-017: Chat with Multiple File Attachments
**Type:** UI Test

**Steps:**
1. Chat page
2. Attach multiple files:
   - sample-text.txt
   - sample-markdown.md
   - sample-data.json
3. Send message: "Compare these documents"

**Expected Result:**
- All 3 files shown in attached files area
- Each has remove button
- All files uploaded
- Toast: "Uploaded 3 files"
- Response references all documents

---

#### TEST-UI-018: Remove Attached File Before Sending
**Type:** UI Test

**Steps:**
1. Attach a file
2. Click X (remove) button on the file
3. Verify file removed

**Expected Result:**
- File removed from attached files list
- Can send message without file
- Or can attach different file

---

#### TEST-UI-019: Chat with URL in Message
**Type:** UI Test

**Steps:**
1. Type message with URL:
   ```
   Tell me about this API: https://jsonplaceholder.typicode.com/users
   ```
2. Send

**Expected Result:**
- URL detected and scraped
- Toast: "Scraped 1 URL, Indexed X documents"
- Response includes info from URL
- Sources section shows scraped URL

---

#### TEST-UI-020: Code Generation Request
**Type:** UI Test

**Steps:**
1. Type: "Write Python code to fetch users from /users endpoint"
2. Send

**Expected Result:**
- Response contains formatted code block
- Syntax highlighting applied
- Code includes imports and examples
- Code is copyable

---

#### TEST-UI-021: Session Management in Chat
**Type:** UI Test

**Steps:**
1. Chat page - observe session selector
2. Check current session ID displayed
3. Click "New Session" button
4. Verify new session created
5. Switch between sessions using dropdown

**Expected Result:**
- Current session ID shown
- Can create new sessions
- Switching sessions loads correct history
- Each session maintains separate conversation

---

#### TEST-UI-022: Clear Chat History
**Type:** UI Test

**Steps:**
1. Have some messages in chat
2. Click "Clear" button
3. Confirm if prompted

**Expected Result:**
- All messages cleared
- Fresh welcome message shown
- Session still active

---

#### TEST-UI-023: Export Chat History
**Type:** UI Test

**Steps:**
1. Have conversation with several messages
2. Click "Export" button

**Expected Result:**
- File download initiated
- File format: .txt or .json
- Contains all messages with timestamps
- Properly formatted

---

#### TEST-UI-024: Chat Input Keyboard Shortcuts
**Type:** UI Test

**Steps:**
1. Type message in input
2. Test keyboard shortcuts:
   - Enter: Send message
   - Shift+Enter: New line in message
3. Verify behavior

**Expected Result:**
- Enter sends message
- Shift+Enter adds new line without sending
- Textarea auto-resizes with content

---

### Test Category: Search Interface

#### TEST-UI-025: Basic Search
**Type:** UI Test
**Prerequisite:** Documents indexed

**Steps:**
1. Navigate to Search page
2. Enter query: "user authentication"
3. Click Search button

**Expected Result:**
- Results displayed
- Each result shows:
  - Content snippet
  - Relevance score
  - Source metadata
  - Endpoint/method if applicable
- Results sorted by relevance

---

#### TEST-UI-026: Search Mode Selection
**Type:** UI Test

**Steps:**
1. Search page
2. Try each search mode:
   - Vector
   - Hybrid
   - Keyword (if available)
3. Run same query with different modes

**Expected Result:**
- Mode selector works
- Different modes return different result rankings
- Current mode indicated in UI

---

#### TEST-UI-027: Search with Filters
**Type:** UI Test

**Steps:**
1. Search page
2. Expand filter options
3. Add filter:
   - Field: method
   - Operator: equals
   - Value: GET
4. Search for: "users"

**Expected Result:**
- Only GET endpoints in results
- Filter badge shown
- Can remove filter easily

---

#### TEST-UI-028: Advanced Search Options
**Type:** UI Test

**Steps:**
1. Search page
2. Enable advanced options:
   - ✓ Query Expansion
   - ✓ Re-ranking
   - ✓ Diversification
3. Search for: "auth"

**Expected Result:**
- Options toggle on/off
- Results change based on options
- Expanded queries shown (if query expansion enabled)

---

#### TEST-UI-029: Pagination in Search Results
**Type:** UI Test

**Steps:**
1. Search with broad query to get many results
2. Check pagination controls
3. Navigate to page 2, 3, etc.

**Expected Result:**
- Page numbers shown
- Next/Previous buttons work
- Results per page configurable
- Page number in URL for bookmarking

---

#### TEST-UI-030: View Document from Search Results
**Type:** UI Test

**Steps:**
1. Perform search
2. Click on a search result
3. View full document

**Expected Result:**
- Document opens in modal/new view
- Full content visible
- Metadata displayed
- Can close and return to search

---

#### TEST-UI-066: Search Re-ranking Toggle
**Type:** UI Test

**Steps:**
1. Search page
2. Perform search with re-ranking OFF
3. Note result order
4. Enable re-ranking
5. Search again with same query

**Expected Result:**
- Results re-order when re-ranking enabled
- Toggle works smoothly
- Setting persists

---

#### TEST-UI-067: Search Diversification
**Type:** UI Test

**Steps:**
1. Search page → Advanced options
2. Enable "Result Diversification"
3. Search for: "API users"
4. Observe results

**Expected Result:**
- More diverse results (not all from same source)
- MMR algorithm applied
- Different document sources represented

---

#### TEST-UI-068: Score Threshold Filtering
**Type:** UI Test

**Steps:**
1. Search page
2. Set minimum score threshold: 0.7
3. Search for: "authentication"

**Expected Result:**
- Only results with score ≥ 0.7 shown
- Lower scored results filtered out
- Threshold indicated in UI

---

#### TEST-UI-069: Search Result Highlighting
**Type:** UI Test

**Steps:**
1. Search for: "GET users"
2. Check if matching terms highlighted in results

**Expected Result:**
- Query terms highlighted in result snippets
- Highlighting visible
- Different color/style for highlights

---

#### TEST-UI-070: Save Search Query
**Type:** UI Test

**Steps:**
1. Perform search with specific filters
2. Click "Save Search" or bookmark
3. Name the search
4. Load saved search later

**Expected Result:**
- Query and filters saved
- Can load from saved searches list
- Quick access to common searches

---

#### TEST-UI-071: Search Export Results
**Type:** UI Test

**Steps:**
1. Perform search
2. Click "Export Results"
3. Choose format (CSV, JSON, PDF)
4. Download

**Expected Result:**
- File downloads successfully
- Contains all results with metadata
- Proper formatting

---

#### TEST-UI-072: Search Keyboard Shortcuts
**Type:** UI Test

**Steps:**
1. Search page
2. Try keyboard shortcuts:
   - `/` to focus search box
   - `Enter` to search
   - `Esc` to clear
   - Arrow keys to navigate results

**Expected Result:**
- All shortcuts work
- Improves user efficiency
- No conflicts with browser shortcuts

---

#### TEST-UI-073: Search Results Copy
**Type:** UI Test

**Steps:**
1. Perform search
2. Select result text
3. Right-click → Copy
4. Or click "Copy" button on result

**Expected Result:**
- Content copies to clipboard
- Formatting preserved or plain text option
- Success notification

---

### Test Category: Diagram Generation

#### TEST-UI-031: Generate Sequence Diagram
**Type:** UI Test
**Prerequisite:** OpenAPI file uploaded

**Steps:**
1. Navigate to Diagrams page
2. Select "Sequence Diagram" tab
3. Choose file: sample-openapi.json
4. Select endpoint: GET /users/{id}
5. Click "Generate Diagram"

**Expected Result:**
- Diagram renders in preview
- Mermaid syntax shown
- Shows: Client → Server → Database flow
- Copy button available
- Download button available

---

#### TEST-UI-032: Generate ER Diagram
**Type:** UI Test
**Prerequisite:** GraphQL schema uploaded

**Steps:**
1. Diagrams page → ER Diagram tab
2. Select GraphQL schema file
3. Generate

**Expected Result:**
- Entity-relationship diagram shown
- Tables/types with fields
- Relationships indicated
- Mermaid format

---

#### TEST-UI-033: Generate Auth Flow Diagram
**Type:** UI Test

**Steps:**
1. Diagrams page → Auth Flow tab
2. Select API spec file
3. Choose auth type: Bearer/OAuth2/API Key
4. Generate

**Expected Result:**
- Auth flow diagram
- Shows token acquisition
- Shows API calls with token
- Refresh flow if applicable

---

#### TEST-UI-034: Generate API Overview
**Type:** UI Test

**Steps:**
1. Diagrams page → Overview tab
2. Select API spec file
3. Generate

**Expected Result:**
- High-level flowchart
- All endpoints grouped
- Clear hierarchy
- Easy to understand

---

#### TEST-UI-035: Copy Diagram Code
**Type:** UI Test

**Steps:**
1. Generate any diagram
2. Click "Copy" button

**Expected Result:**
- Mermaid code copied to clipboard
- Success notification
- Can paste in GitHub/other tools

---

#### TEST-UI-036: Download Diagram
**Type:** UI Test

**Steps:**
1. Generate diagram
2. Click "Download" button

**Expected Result:**
- File download initiated
- Format: .mmd or .md
- Contains diagram code
- Proper filename

---

#### TEST-UI-037: Diagram Error Handling
**Type:** UI Test - Negative Case

**Steps:**
1. Try to generate diagram without selecting file
2. Or select file with no compatible endpoints

**Expected Result:**
- Validation error shown
- User-friendly message
- No diagram rendered
- Form still usable

---

### Test Category: Session Management UI

#### TEST-UI-038: View Sessions List
**Type:** UI Test

**Steps:**
1. Navigate to Sessions page
2. View list of sessions

**Expected Result:**
- Sessions displayed in table/cards
- Shows: Session ID, User, Status, Created, Expires, Message count
- Active/Inactive indicators
- Sort options

---

#### TEST-UI-039: Create New Session
**Type:** UI Test

**Steps:**
1. Sessions page
2. Click "New Session" or "Create Session"
3. Fill form:
   - User ID: test_user_123
   - TTL: 120 minutes
   - Settings: default
4. Create

**Expected Result:**
- Session created
- Appears in list
- Success notification
- Shows active status

---

#### TEST-UI-040: Filter Sessions
**Type:** UI Test

**Steps:**
1. Sessions page
2. Use filter controls:
   - Status: Active only
   - User ID: specific user
3. Apply filters

**Expected Result:**
- List filtered correctly
- Filter badges shown
- Can clear filters

---

#### TEST-UI-041: Update Session Settings
**Type:** UI Test

**Steps:**
1. Find a session in list
2. Click "Edit" or settings icon
3. Change TTL to 240 minutes
4. Change default search mode
5. Save

**Expected Result:**
- Session updated
- New expiry time calculated
- Settings saved
- Success notification

---

#### TEST-UI-042: Extend Session Expiration
**Type:** UI Test

**Steps:**
1. Find session near expiration
2. Click "Extend" button
3. Add 60 minutes
4. Confirm

**Expected Result:**
- Expiration time extended
- Updated in list
- Still active status

---

#### TEST-UI-043: Delete Session from UI
**Type:** UI Test

**Steps:**
1. Select a session
2. Click delete icon
3. Confirm deletion

**Expected Result:**
- Confirmation prompt
- Session deleted
- Removed from list
- Success message

---

#### TEST-UI-044: View Session Details
**Type:** UI Test

**Steps:**
1. Click on a session row/card
2. View details modal/page

**Expected Result:**
- Full session info shown
- Conversation history if any
- Settings object
- Timestamps
- Can edit from details view

---

### Test Category: Settings Page

#### TEST-UI-045: Change LLM Provider
**Type:** UI Test

**Steps:**
1. Navigate to Settings page
2. Find "LLM Provider" section
3. Switch between Ollama and Groq
4. If Groq: enter API key
5. Save changes

**Expected Result:**
- Provider switches
- Appropriate config fields shown
- Settings saved
- Toast confirmation
- Takes effect immediately or on next request

---

#### TEST-UI-046: Configure Search Defaults
**Type:** UI Test

**Steps:**
1. Settings page → Search Defaults
2. Change:
   - Default mode: Hybrid
   - Enable re-ranking: ON
   - Query expansion: ON
   - Results per page: 20
3. Save

**Expected Result:**
- Settings saved
- Used as defaults in search page
- Persists across sessions

---

#### TEST-UI-047: Theme Selection
**Type:** UI Test

**Steps:**
1. Settings page → Appearance
2. Try each theme:
   - Light
   - Dark
   - System
3. Observe changes

**Expected Result:**
- Theme changes immediately
- Persists on page refresh
- System theme matches OS setting

---

#### TEST-UI-048: Configure Session Defaults
**Type:** UI Test

**Steps:**
1. Settings → Session Defaults
2. Set:
   - Default TTL: 1440 minutes (24 hours)
   - Auto-cleanup: Enabled
3. Save

**Expected Result:**
- New sessions use these defaults
- Settings saved
- Cleanup runs if enabled

---

#### TEST-UI-049: Reset Settings to Default
**Type:** UI Test

**Steps:**
1. Change several settings
2. Click "Reset to Defaults" or similar
3. Confirm

**Expected Result:**
- All settings revert to defaults
- Confirmation shown
- Page refreshes or updates

---

### Test Category: Error Handling & Edge Cases

#### TEST-UI-050: Network Error Handling
**Type:** UI Test - Negative Case

**Steps:**
1. Stop backend server
2. Try to perform any action (search, upload, chat)
3. Observe error handling

**Expected Result:**
- User-friendly error message
- Suggests checking connection
- Retry option available
- No crash

---

#### TEST-UI-051: Invalid Session Handling
**Type:** UI Test - Negative Case

**Steps:**
1. Note current session ID
2. Delete session via API or CLI
3. Try to use chat with deleted session

**Expected Result:**
- Error detected
- Creates new session automatically
- Or prompts user to create session
- Graceful handling

---

#### TEST-UI-052: File Size Limit
**Type:** UI Test - Edge Case

**Steps:**
1. Try to upload very large file (>10MB)
2. Observe behavior

**Expected Result:**
- Size validation
- Error message if too large
- Suggests file size limit
- Upload rejected gracefully

---

#### TEST-UI-053: Empty Search Query
**Type:** UI Test - Edge Case

**Steps:**
1. Search page
2. Leave query empty
3. Click Search

**Expected Result:**
- Validation error
- "Query required" message
- Search button disabled or validation shown

---

#### TEST-UI-054: Special Characters in Input
**Type:** UI Test - Edge Case

**Steps:**
1. Try inputs with special characters:
   - Chat: "What's the <script>alert('test')</script> endpoint?"
   - Search: `"SELECT * FROM users"`
2. Verify proper escaping

**Expected Result:**
- No XSS vulnerabilities
- Special chars properly escaped
- No SQL injection
- Safe rendering

---

#### TEST-UI-055: Concurrent Operations
**Type:** UI Test - Edge Case

**Steps:**
1. Start file upload
2. While uploading, navigate away
3. Return and check upload status

**Expected Result:**
- Upload continues in background
- Or cancels gracefully
- Status updated correctly
- No memory leaks

---

## CLI Testing

### Test Category: CLI - Parse Commands

#### TEST-CLI-001: Parse Single OpenAPI File
**Type:** CLI Test
**Test Data:** `examples/sample-openapi.json`

**Steps:**
```bash
python -m src.cli.app parse file examples/sample-openapi.json
```

**Expected Output:**
```
✓ Successfully parsed: sample-openapi.json
Format: OpenAPI 3.0
Endpoints found: 3
Details:
  GET /users
  GET /users/{id}
  POST /users
```

**Pass Criteria:**
- Exit code: 0
- Correct endpoint count
- No errors

---

#### TEST-CLI-002: Parse with Format Hint
**Type:** CLI Test

**Steps:**
```bash
python -m src.cli.app parse file examples/sample-openapi.json --format openapi
```

**Expected Result:**
- Uses specified format
- Parses successfully
- Output shows format used

---

#### TEST-CLI-003: Parse and Save Output
**Type:** CLI Test

**Steps:**
```bash
python -m src.cli.app parse file examples/sample-openapi.json --output parsed-output.json
```

**Expected Result:**
- File created: parsed-output.json
- Contains parsed data
- Valid JSON format

---

#### TEST-CLI-004: Batch Parse Multiple Files
**Type:** CLI Test

**Steps:**
```bash
python -m src.cli.app parse batch examples/*.json
```

**Expected Result:**
- All JSON files parsed
- Summary table shown:
  - Filename
  - Status
  - Format
  - Endpoints
- Failed files indicated

---

#### TEST-CLI-005: Parse Invalid File
**Type:** CLI Test - Negative Case

**Steps:**
```bash
python -m src.cli.app parse file examples/invalid.json
```

**Expected Result:**
- Exit code: non-zero
- Error message shown
- Describes parse error
- Doesn't crash

---

### Test Category: CLI - Search Commands

#### TEST-CLI-006: Basic Search
**Type:** CLI Test
**Prerequisite:** Documents indexed

**Steps:**
```bash
python -m src.cli.app search "user authentication"
```

**Expected Output:**
```
Search Results (10 found):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Score: 0.87 | Source: sample-openapi.json
   GET /users/{id} - Retrieve user by ID

2. Score: 0.82 | Source: sample-text.txt
   Authentication methods include...
```

**Pass Criteria:**
- Results displayed in table
- Scores shown
- Source attribution

---

#### TEST-CLI-007: Search with Mode
**Type:** CLI Test

**Steps:**
```bash
python -m src.cli.app search "users" --mode hybrid --limit 5
```

**Expected Result:**
- 5 results max
- Hybrid mode used
- Indicated in output

---

#### TEST-CLI-008: Search with JSON Output
**Type:** CLI Test

**Steps:**
```bash
python -m src.cli.app search "api" --output-format json > results.json
```

**Expected Result:**
- JSON output
- Parseable format
- Contains all result fields

---

### Test Category: CLI - Collection Management

#### TEST-CLI-009: Collection Info
**Type:** CLI Test

**Steps:**
```bash
python -m src.cli.app collection info
```

**Expected Output:**
```
Collection Statistics:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Documents: 45
Total Endpoints: 12
Formats:
  - OpenAPI: 2
  - GraphQL: 1
  - Text: 3
```

---

#### TEST-CLI-010: Clear Collection
**Type:** CLI Test

**Steps:**
```bash
python -m src.cli.app collection clear --confirm
```

**Expected Result:**
- Confirmation required
- All documents removed
- Success message
- Stats show 0 documents

---

### Test Category: CLI - Diagram Generation

#### TEST-CLI-011: Generate Sequence Diagram
**Type:** CLI Test

**Steps:**
```bash
python -m src.cli.app diagram sequence \
  examples/sample-openapi.json \
  --endpoint "/users/{id}" \
  --method GET \
  --output sequence.mmd
```

**Expected Result:**
- File created: sequence.mmd
- Valid Mermaid syntax
- Shows sequence flow

---

#### TEST-CLI-012: Generate ER Diagram
**Type:** CLI Test

**Steps:**
```bash
python -m src.cli.app diagram er examples/graphql/schema.graphql \
  --output er-diagram.mmd
```

**Expected Result:**
- ER diagram created
- Shows entities and relationships

---

#### TEST-CLI-013: Generate Auth Flow
**Type:** CLI Test

**Steps:**
```bash
python -m src.cli.app diagram auth examples/sample-openapi.json \
  --auth-type bearer
```

**Expected Result:**
- Auth flow diagram printed to stdout
- Or saved to file if --output specified

---

#### TEST-CLI-014: Generate Overview
**Type:** CLI Test

**Steps:**
```bash
python -m src.cli.app diagram overview examples/sample-openapi.json
```

**Expected Result:**
- API overview flowchart
- All endpoints included
- Grouped by tags/paths

---

### Test Category: CLI - Session Management

#### TEST-CLI-015: Create Session via CLI
**Type:** CLI Test

**Steps:**
```bash
python -m src.cli.app session create \
  --user-id cli_user_001 \
  --ttl 120
```

**Expected Output:**
```
✓ Session created successfully
Session ID: abc-123-def-456
User: cli_user_001
Expires: 2025-12-30 14:30:00
Status: active
```

---

#### TEST-CLI-016: List Sessions
**Type:** CLI Test

**Steps:**
```bash
python -m src.cli.app session list --status active
```

**Expected Output:**
```
Active Sessions (3):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Session ID          User            Status   Expires
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
abc-123...          user_001        active   2025-12-30 14:00
def-456...          user_002        active   2025-12-30 15:00
```

---

#### TEST-CLI-017: Get Session Info
**Type:** CLI Test

**Steps:**
```bash
python -m src.cli.app session info abc-123-def-456
```

**Expected Result:**
- Full session details
- Conversation history
- Settings object
- Timestamps

---

#### TEST-CLI-018: Extend Session
**Type:** CLI Test

**Steps:**
```bash
python -m src.cli.app session extend abc-123-def-456 --minutes 60
```

**Expected Result:**
- Session expiration extended
- New expiry time shown
- Success confirmation

---

#### TEST-CLI-019: Delete Session via CLI
**Type:** CLI Test

**Steps:**
```bash
python -m src.cli.app session delete abc-123-def-456 --confirm
```

**Expected Result:**
- Confirmation required
- Session deleted
- Success message

---

#### TEST-CLI-020: Cleanup Expired Sessions
**Type:** CLI Test

**Steps:**
```bash
python -m src.cli.app session cleanup
```

**Expected Result:**
- Scans for expired sessions
- Removes them
- Shows count deleted

---

#### TEST-CLI-021: Session Statistics
**Type:** CLI Test

**Steps:**
```bash
python -m src.cli.app session stats
```

**Expected Output:**
```
Session Statistics:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Sessions: 5
Active: 3
Expired: 2
Average Messages: 12.4
Total Users: 3
```

---

### Test Category: CLI - Info Commands

#### TEST-CLI-022: List Supported Formats
**Type:** CLI Test

**Steps:**
```bash
python -m src.cli.app info formats
```

**Expected Output:**
```
Supported API Formats:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Format          Extensions              Version
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OpenAPI         .json, .yaml, .yml     3.0+
GraphQL         .graphql, .gql         SDL
Postman         .json                  v2.0, v2.1
PDF             .pdf                   Any
Text            .txt                   Any
Markdown        .md, .markdown         Any
```

---

### Test Category: CLI - Export/Import

#### TEST-CLI-023: Export Collection
**Type:** CLI Test

**Steps:**
```bash
python -m src.cli.app export collection --output backup.json
```

**Expected Result:**
- File created: backup.json
- Contains all documents
- Includes metadata
- Valid JSON format

---

#### TEST-CLI-024: Import Collection
**Type:** CLI Test

**Steps:**
```bash
python -m src.cli.app import collection backup.json
```

**Expected Result:**
- Documents imported
- Success count shown
- Duplicate handling noted

---

### Test Category: CLI - Verbose Output

#### TEST-CLI-025: Verbose Mode
**Type:** CLI Test

**Steps:**
```bash
python -m src.cli.app -v parse file examples/sample-openapi.json
```

**Expected Result:**
- Detailed logs shown
- Debug information
- Step-by-step progress
- Helpful for troubleshooting

---

## End-to-End Testing

### Test Category: Complete User Workflows

#### TEST-E2E-001: Complete Document Upload to Search Flow
**Type:** End-to-End Test
**Components:** UI + Backend + Database

**Scenario:** User uploads API spec and searches for endpoints

**Steps:**
1. **Setup:** Clear existing documents
2. **Upload:**
   - Navigate to Documents page (UI)
   - Upload `examples/sample-openapi.json` (UI)
   - Verify success notification (UI)
3. **Wait:** 2 seconds for indexing
4. **Search:**
   - Navigate to Search page (UI)
   - Search for "users" (UI)
   - Verify results contain endpoints from uploaded file (UI)
5. **Verify Backend:**
   ```bash
   curl http://localhost:8000/stats
   ```
   - Check total_documents increased
   - Check total_endpoints shows 3

**Expected End State:**
- Document in database
- Searchable via UI
- Stats reflect new document

**Pass Criteria:**
- All steps complete without errors
- Search returns uploaded content
- Stats accurate

---

#### TEST-E2E-002: Chat with Document Context Flow
**Type:** End-to-End Test

**Scenario:** User uploads document, then asks questions about it

**Steps:**
1. **Upload via UI:**
   - Documents page
   - Upload `examples/sample-markdown.md`
2. **Navigate to Chat:**
   - Go to Chat page
   - Ensure session is active
3. **Ask Question:**
   - Type: "What are the best practices for API design?"
   - Send message
4. **Verify Response:**
   - Response references content from uploaded markdown
   - Sources section shows sample-markdown.md
   - Response quality check

**Expected Result:**
- Uploaded doc used as context
- Accurate answer based on document
- Source attribution correct

---

#### TEST-E2E-003: File Upload in Chat Flow
**Type:** End-to-End Test

**Scenario:** User uploads file directly in chat for analysis

**Steps:**
1. **Chat Page:**
   - Click paperclip icon
   - Attach `examples/sample-text.txt`
2. **Ask:**
   - Type: "What is this document about?"
   - Send
3. **Verify:**
   - File uploaded (check toast)
   - File indexed (toast shows indexed count)
   - Response analyzes the document
   - Can ask follow-up questions about same document

**Expected Result:**
- File processing successful
- Context maintained for follow-ups
- Accurate analysis

---

#### TEST-E2E-004: CLI to UI Workflow
**Type:** End-to-End Test

**Scenario:** Upload via CLI, verify in UI

**Steps:**
1. **CLI Upload:**
   ```bash
   python -m src.cli.app parse file examples/sample-openapi.json
   ```
2. **Verify Backend:**
   ```bash
   curl http://localhost:8000/stats
   ```
3. **Check UI:**
   - Open browser to Documents page
   - Refresh if needed
   - Verify document appears in list

**Expected Result:**
- CLI upload successful
- Document visible in UI
- Stats match

---

#### TEST-E2E-005: Session Persistence Across Pages
**Type:** End-to-End Test

**Scenario:** Create session, use across different pages

**Steps:**
1. **Create Session:**
   - Chat page → New Session
   - Note session ID
2. **Send Messages:**
   - Ask 3 different questions
   - Verify conversation history builds
3. **Navigate Away:**
   - Go to Search page
   - Perform a search
4. **Return to Chat:**
   - Go back to Chat page
   - Verify same session loaded
   - Verify conversation history intact
5. **Reload Browser:**
   - F5 to refresh
   - Verify session persists

**Expected Result:**
- Session maintains state
- History preserved across navigation
- LocalStorage working

---

#### TEST-E2E-006: Diagram Generation Pipeline
**Type:** End-to-End Test

**Scenario:** Upload API spec → Generate all diagram types

**Steps:**
1. **Upload:**
   - Upload `examples/sample-openapi.json`
2. **Generate Each Diagram Type:**
   - Diagrams page → Sequence Diagram
   - Select file and endpoint
   - Generate → Verify
   - Repeat for ER, Auth Flow, Overview
3. **Verify Each:**
   - Diagram renders
   - Mermaid syntax valid
   - Can copy code
   - Can download

**Expected Result:**
- All 4 diagram types generate successfully
- Each has valid syntax
- Export functions work

---

#### TEST-E2E-007: Settings Persistence Flow
**Type:** End-to-End Test

**Scenario:** Change settings, verify applied everywhere

**Steps:**
1. **Change Settings:**
   - Settings page
   - Set default search mode: Hybrid
   - Set re-ranking: ON
   - Set theme: Dark
   - Save
2. **Verify Search:**
   - Search page
   - Observe defaults applied
   - Mode is Hybrid
   - Re-ranking enabled
3. **Verify Theme:**
   - Navigate to different pages
   - All pages in dark mode
4. **Reload Browser:**
   - F5
   - Verify settings persist

**Expected Result:**
- Settings saved
- Applied across all pages
- Persists after reload

---

#### TEST-E2E-008: Error Recovery Flow
**Type:** End-to-End Test

**Scenario:** Simulate errors and verify recovery

**Steps:**
1. **Simulate Network Error:**
   - Stop backend server
   - Try to upload document
   - Observe error handling
2. **Recover:**
   - Restart backend
   - Click retry or re-attempt upload
   - Verify success
3. **Simulate Invalid Input:**
   - Upload invalid file
   - See error
   - Upload valid file
   - Verify works

**Expected Result:**
- Errors handled gracefully
- User-friendly messages
- Recovery possible
- No state corruption

---

#### TEST-E2E-009: Multi-Format Upload and Search
**Type:** End-to-End Test

**Scenario:** Upload different formats, search across all

**Steps:**
1. **Upload Multiple Formats:**
   - OpenAPI: sample-openapi.json
   - Text: sample-text.txt
   - Markdown: sample-markdown.md
   - JSON: sample-data.json
2. **Wait for Indexing:**
   - 3-5 seconds
3. **Search with Query:**
   - "API best practices"
4. **Verify Results:**
   - Results from multiple sources
   - Different formats represented
   - All searchable

**Expected Result:**
- All formats indexed
- Cross-format search works
- Results prioritized by relevance

---

#### TEST-E2E-010: CLI Full Workflow
**Type:** End-to-End CLI Test

**Scenario:** Complete CLI workflow

**Steps:**
```bash
# 1. Create session
python -m src.cli.app session create --user-id e2e_test --ttl 60

# 2. Parse and upload
python -m src.cli.app parse batch examples/*.json

# 3. Search
python -m src.cli.app search "users" --mode hybrid

# 4. Generate diagram
python -m src.cli.app diagram overview examples/sample-openapi.json --output overview.mmd

# 5. Get stats
python -m src.cli.app collection info

# 6. Cleanup
python -m src.cli.app session delete <session-id> --confirm
```

**Expected Result:**
- All commands execute successfully
- Exit code 0 for each
- Data persists between commands
- Final cleanup successful

---

## Performance & Edge Cases

### Test Category: Performance Testing

#### TEST-PERF-001: Large File Upload
**Type:** Performance Test
**Test Data:** Create large text file (see Test Data Preparation)

**Steps:**
1. Upload `examples/large-text.txt` (10MB+)
2. Monitor:
   - Upload time
   - Processing time
   - Memory usage
   - UI responsiveness

**Acceptance Criteria:**
- Upload completes within 30 seconds
- Progress indicator shown
- No UI freeze
- Memory usage reasonable (<500MB increase)

---

#### TEST-PERF-002: Concurrent Searches
**Type:** Performance Test

**Steps:**
1. Open 5 browser tabs
2. Simultaneously search from each tab
3. Monitor response times

**Acceptance Criteria:**
- All searches complete
- Response time < 3 seconds each
- No crashes
- No 429 rate limit errors (or proper handling)

---

#### TEST-PERF-003: Large Search Results
**Type:** Performance Test

**Steps:**
1. Upload many documents (50+)
2. Search with broad query returning 100+ results
3. Test pagination performance

**Acceptance Criteria:**
- Results load within 2 seconds
- Pagination smooth
- No memory leaks
- Can navigate all pages

---

#### TEST-PERF-004: Session with Long History
**Type:** Performance Test

**Steps:**
1. Create chat session
2. Send 50 messages
3. Check loading time when reopening session
4. Test scrolling through history

**Acceptance Criteria:**
- History loads within 3 seconds
- Scrolling smooth
- All messages render
- No lag

---

### Test Category: Edge Cases

#### TEST-EDGE-001: Empty File Upload
**Type:** Edge Case Test

**Steps:**
1. Create 0-byte file:
   - **Linux/Mac:** `touch empty.txt`
   - **Windows PowerShell:** `New-Item -Path empty.txt -ItemType File -Force`
2. Try to upload

**Expected Result:**
- Validation error or graceful handling
- User-friendly message
- No crash

---

#### TEST-EDGE-002: Duplicate Document Upload
**Type:** Edge Case Test

**Steps:**
1. Upload `sample-openapi.json`
2. Upload same file again

**Expected Result:**
- Duplicate detection (if implemented)
- Or both versions indexed
- Clear indication to user

---

#### TEST-EDGE-003: Special Characters in Filenames
**Type:** Edge Case Test

**Steps:**
1. Create file with special chars: `api-spec (v2.0) [final].json`
2. Upload

**Expected Result:**
- Filename handled correctly
- No parsing errors
- Properly escaped in UI

---

#### TEST-EDGE-004: Very Long Chat Message
**Type:** Edge Case Test

**Steps:**
1. Type or paste 5000+ character message
2. Send

**Expected Result:**
- Message accepted or length validation
- If accepted: proper rendering
- If rejected: clear limit message

---

#### TEST-EDGE-005: Expired Session Recovery
**Type:** Edge Case Test

**Steps:**
1. Create session with 1-minute TTL
2. Wait for expiration
3. Try to send chat message

**Expected Result:**
- Session expiration detected
- Auto-creates new session
- Or prompts user to create session
- No data loss

---

#### TEST-EDGE-006: Malformed API Spec
**Type:** Edge Case Test

**Steps:**
1. Upload malformed OpenAPI file
2. Observe error handling

**Expected Result:**
- Parse error caught
- Specific error message
- Suggests fix if possible
- No crash

---

#### TEST-EDGE-007: Search with No Results
**Type:** Edge Case Test

**Steps:**
1. Search for: "xyzabc123nonexistent"
2. Verify no results handling

**Expected Result:**
- "No results found" message
- Helpful suggestions (check spelling, try different terms)
- Empty state UI shown

---

#### TEST-EDGE-008: Browser Compatibility
**Type:** Edge Case Test

**Steps:**
1. Test application in:
   - Chrome
   - Firefox
   - Safari
   - Edge
2. Verify core functions work

**Expected Result:**
- Consistent behavior
- No browser-specific bugs
- Responsive design works

---

## Security & Validation Testing

### Test Category: Security Tests

#### TEST-SEC-001: XSS Prevention in Chat
**Type:** Security Test - UI

**Steps:**
1. Chat page
2. Send message: `<script>alert('XSS')</script>`
3. Observe rendering

**Expected Result:**
- Script not executed
- Special characters escaped
- Displayed as plain text
- No alert popup

---

#### TEST-SEC-002: XSS Prevention in Search
**Type:** Security Test - UI

**Steps:**
1. Search page
2. Search for: `<img src=x onerror=alert('XSS')>`
3. Check results display

**Expected Result:**
- No script execution
- HTML tags escaped
- Safe rendering

---

#### TEST-SEC-003: SQL Injection Prevention
**Type:** Security Test - API

**Steps:**
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "test OR 1=1; DROP TABLE documents--"}'
```

**Expected Result:**
- Query treated as literal string
- No SQL execution
- Normal search results
- No database errors

---

#### TEST-SEC-004: File Upload Type Validation
**Type:** Security Test - UI

**Steps:**
1. Try to upload .exe file
2. Try to upload .sh script
3. Try to upload file with double extension: file.pdf.exe

**Expected Result:**
- Invalid file types rejected
- Clear error message
- Only allowed extensions accepted
- MIME type validation

---

#### TEST-SEC-005: File Size Limits
**Type:** Security Test - UI

**Steps:**
1. Create file larger than limit (e.g., 50MB)
2. Try to upload

**Expected Result:**
- Upload rejected
- Error: "File size exceeds maximum (X MB)"
- No partial upload
- No server crash

---

#### TEST-SEC-006: Path Traversal Prevention
**Type:** Security Test - API

**Steps:**
```bash
curl "http://localhost:8000/documents/../../../etc/passwd"
```

**Expected Result:**
- 404 Not Found or 400 Bad Request
- No file system access
- Path traversal blocked
- Logged as security event

---

#### TEST-SEC-007: Rate Limiting
**Type:** Security Test - API

**Steps:**

**For Linux/Mac:**
```bash
# Send 100 requests rapidly
for i in {1..100}; do
  curl -X POST "http://localhost:8000/search" \
    -H "Content-Type: application/json" \
    -d '{"query": "test"}' &
done
wait
```

**For Windows PowerShell:**
```powershell
# Send 100 requests rapidly
1..100 | ForEach-Object {
  Start-Job -ScriptBlock {
    Invoke-RestMethod -Uri "http://localhost:8000/search" `
      -Method POST `
      -ContentType "application/json" `
      -Body '{"query": "test"}'
  }
}
Get-Job | Wait-Job | Remove-Job
```

**Expected Result:**
- Rate limit enforced
- 429 Too Many Requests after threshold
- Retry-After header present
- IP temporarily blocked

---

#### TEST-SEC-008: Session Hijacking Prevention
**Type:** Security Test - UI

**Steps:**
1. Login and get session token
2. Open incognito window
3. Try to use same session token manually

**Expected Result:**
- Session tied to user agent/IP
- Token invalidation on suspicious activity
- Cannot reuse from different context

---

#### TEST-SEC-009: API Authentication
**Type:** Security Test - API

**Steps:**
```bash
# Try API without auth (if auth implemented)
curl -X POST "http://localhost:8000/documents/upload" \
  -F "files=@test.txt"
```

**Expected Result:**
- 401 Unauthorized (if auth required)
- Clear error message
- No data leak
- Proper WWW-Authenticate header

---

#### TEST-SEC-010: CORS Policy
**Type:** Security Test - API

**Steps:**
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Origin: http://malicious-site.com" \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'
```

**Expected Result:**
- CORS headers present
- Only allowed origins accepted
- Preflight requests handled
- No cross-origin data leak

---

#### TEST-SEC-011: Content Security Policy
**Type:** Security Test - UI

**Steps:**
1. Open browser DevTools → Network
2. Check response headers for CSP
3. Verify CSP directives

**Expected Result:**
- CSP header present
- Proper directives set
- Inline scripts blocked (unless whitelisted)
- External resources controlled

---

#### TEST-SEC-012: Sensitive Data in Logs
**Type:** Security Test - Backend

**Steps:**
1. Upload document with sensitive data
2. Check backend logs
3. Search for API keys, passwords

**Expected Result:**
- No sensitive data in logs
- Data masked/redacted
- Proper log sanitization
- Secure logging practices

---

## Advanced Integration Testing

### Test Category: Cross-Component Integration

#### TEST-INT-001: Upload via UI, Search via CLI
**Type:** Integration Test - UI + CLI

**Steps:**
1. **UI:** Upload `sample-openapi.json` via web interface
2. Wait 3 seconds for indexing
3. **CLI:** Search using command line:
   ```bash
   python -m src.cli.app search "users" --mode hybrid
   ```

**Expected Result:**
- CLI finds document uploaded via UI
- Results include the uploaded file
- Cross-interface data consistency

---

#### TEST-INT-002: Session Created in UI, Used in CLI
**Type:** Integration Test - UI + CLI

**Steps:**
1. **UI:** Create session, note session ID
2. **CLI:** Use session in CLI commands
3. Verify session updates from both interfaces

**Expected Result:**
- Session accessible from both UI and CLI
- Conversation history synced
- Settings applied consistently

---

#### TEST-INT-003: Multi-Tab Concurrent Uploads
**Type:** Integration Test - UI

**Steps:**
1. Open 3 browser tabs
2. Simultaneously upload different files in each tab
3. Check all uploads succeed
4. Verify no conflicts

**Expected Result:**
- All 3 uploads succeed
- No race conditions
- Stats update correctly
- No duplicate indexing

---

#### TEST-INT-004: Chat with Multi-Source Context
**Type:** Integration Test - E2E

**Steps:**
1. Upload OpenAPI spec
2. Upload PDF document
3. Upload text file
4. Chat: "Compare authentication methods from all documents"

**Expected Result:**
- AI retrieves context from all 3 sources
- Response references each document
- Sources section shows all 3
- Accurate cross-document analysis

---

#### TEST-INT-005: Diagram from Uploaded then Deleted Document
**Type:** Integration Test - UI

**Steps:**
1. Upload API spec
2. Generate diagram from it
3. Delete the document
4. Try to regenerate diagram

**Expected Result:**
- Error: "Source document not found"
- Graceful handling
- Suggest re-uploading document
- Previous diagram still accessible if saved

---

#### TEST-INT-006: Settings Change Affects All Features
**Type:** Integration Test - UI

**Steps:**
1. Settings → Set LLM Provider to Groq
2. Set API key
3. Test in Chat: Send message
4. Test in Diagram: Generate diagram
5. Verify both use Groq

**Expected Result:**
- Settings apply globally
- All features use new provider
- No restart needed
- Consistent behavior

---

#### TEST-INT-007: Search After Bulk Upload
**Type:** Integration Test - CLI + API

**Steps:**
```bash
# Bulk upload
python -m src.cli.app parse batch examples/*.json

# Immediately search
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "authentication", "n_results": 20}'
```

**Expected Result:**
- All uploaded documents searchable
- Indexing completed before search
- Results from all uploaded files
- No missing documents

---

#### TEST-INT-008: Real-time Updates Across Sessions
**Type:** Integration Test - UI

**Steps:**
1. User A: Create and switch to session X
2. User B: Add message to session X (if multi-user supported)
3. User A: Refresh or auto-update
4. Verify User A sees User B's message

**Expected Result:**
- Real-time updates work
- Or polling updates correctly
- No conflicts
- Message ordering preserved

---

#### TEST-INT-009: Document Metadata Propagation
**Type:** Integration Test - E2E

**Steps:**
1. Upload document with metadata tags
2. Search and verify tags in results
3. Chat and verify AI can access metadata
4. Export and verify metadata included

**Expected Result:**
- Metadata flows through all systems
- Searchable by metadata
- AI aware of metadata
- Exports include metadata

---

#### TEST-INT-010: Error Cascade Prevention
**Type:** Integration Test - Error Handling

**Steps:**
1. Stop LLM service (Ollama/Groq)
2. Try chat (should fail)
3. Try document upload (should succeed)
4. Try search (should succeed)
5. Restart LLM
6. Try chat again (should succeed)

**Expected Result:**
- LLM failure doesn't break other features
- Clear error messages
- Graceful degradation
- Recovery without restart

---

## Accessibility Testing

### Test Category: Accessibility & Usability

#### TEST-ACC-001: Keyboard Navigation
**Type:** Accessibility Test - UI

**Steps:**
1. Navigate entire app using only keyboard
2. Tab through all interactive elements
3. Activate buttons with Enter/Space
4. Test all pages

**Expected Result:**
- All interactive elements reachable via Tab
- Focus indicators visible
- Logical tab order
- No keyboard traps
- Skip to content link available

---

#### TEST-ACC-002: Screen Reader Compatibility
**Type:** Accessibility Test - UI

**Tools:** NVDA, JAWS, or VoiceOver

**Steps:**
1. Enable screen reader
2. Navigate through app
3. Check announcements for:
   - Page titles
   - Form labels
   - Button purposes
   - Error messages
   - Status updates

**Expected Result:**
- All content accessible
- Proper ARIA labels
- Semantic HTML used
- Meaningful announcements
- No missing alt text

---

#### TEST-ACC-003: Focus Management
**Type:** Accessibility Test - UI

**Steps:**
1. Open modal/dialog
2. Check focus moves to modal
3. Close modal
4. Check focus returns to trigger

**Expected Result:**
- Focus trapped in modals
- Focus restored on close
- Esc key closes modals
- Proper focus indicators

---

#### TEST-ACC-004: Color Contrast
**Type:** Accessibility Test - UI

**Tools:** Browser DevTools, Contrast Checker

**Steps:**
1. Check contrast ratios for:
   - Text on backgrounds
   - Button text
   - Link text
   - Icons
2. Test in both light and dark modes

**Expected Result:**
- Minimum 4.5:1 for normal text
- Minimum 3:1 for large text
- WCAG AA compliance
- Both themes pass

---

#### TEST-ACC-005: Form Labels and Errors
**Type:** Accessibility Test - UI

**Steps:**
1. Submit forms with errors
2. Check error associations
3. Verify label connections

**Expected Result:**
- All inputs have labels
- Error messages announced
- aria-describedby used
- Required fields indicated
- Clear error guidance

---

#### TEST-ACC-006: Alternative Text
**Type:** Accessibility Test - UI

**Steps:**
1. Check all images for alt text
2. Verify icons have aria-labels
3. Check decorative images have empty alt

**Expected Result:**
- All meaningful images have alt
- Alt text descriptive
- Decorative images hidden from screen readers
- Icon buttons labeled

---

#### TEST-ACC-007: Responsive Text Sizing
**Type:** Accessibility Test - UI

**Steps:**
1. Zoom browser to 200%
2. Check text readability
3. Verify no horizontal scrolling
4. Test at 400% zoom (WCAG AAA)

**Expected Result:**
- Text remains readable
- Layout adapts
- No content loss
- Controls still usable

---

#### TEST-ACC-008: Skip Links
**Type:** Accessibility Test - UI

**Steps:**
1. Tab from page load
2. First Tab should show "Skip to content"
3. Activate skip link
4. Verify focus moves to main content

**Expected Result:**
- Skip link visible on focus
- Works correctly
- Bypasses navigation
- Improves keyboard efficiency

---

## Mobile & Responsive Testing

### Test Category: Mobile Compatibility

#### TEST-MOB-001: Mobile Layout - Documents Page
**Type:** Mobile Test - UI

**Steps:**
1. Open app on mobile device or resize browser to 375px
2. Navigate to Documents page
3. Test upload, view library

**Expected Result:**
- Layout adapts to mobile
- Upload button accessible
- Table becomes cards or scrollable
- Touch targets ≥ 44x44px
- No horizontal scroll

---

#### TEST-MOB-002: Mobile Layout - Chat
**Type:** Mobile Test - UI

**Steps:**
1. Mobile viewport
2. Chat page
3. Type message, attach file

**Expected Result:**
- Input area stays at bottom
- Virtual keyboard doesn't break layout
- Attach button visible and usable
- Messages readable
- Scroll works smoothly

---

#### TEST-MOB-003: Mobile Layout - Search
**Type:** Mobile Test - UI

**Steps:**
1. Mobile viewport
2. Search page
3. Perform search, apply filters

**Expected Result:**
- Search box usable
- Filters accessible (drawer or collapsible)
- Results readable
- Tap targets adequate
- No text overflow

---

#### TEST-MOB-004: Touch Gestures
**Type:** Mobile Test - UI

**Steps:**
1. Test swipe gestures (if applicable)
2. Test pinch to zoom on diagrams
3. Test long-press menus

**Expected Result:**
- Gestures work correctly
- No conflicts with browser gestures
- Smooth animations
- Feedback on touch

---

#### TEST-MOB-005: Mobile Performance
**Type:** Mobile Test - Performance

**Steps:**
1. Test on actual mobile device (not emulator)
2. Upload document
3. Search
4. Chat
5. Check performance

**Expected Result:**
- Load time < 3 seconds
- Smooth scrolling
- No lag in typing
- Acceptable battery usage
- Works on 3G/4G

---

#### TEST-MOB-006: Orientation Changes
**Type:** Mobile Test - UI

**Steps:**
1. Portrait mode: Test features
2. Rotate to landscape
3. Test same features
4. Rotate back to portrait

**Expected Result:**
- Layout adapts smoothly
- No data loss on rotation
- Content repositions correctly
- State preserved

---

#### TEST-MOB-007: Mobile Browser Compatibility
**Type:** Mobile Test - Cross-Browser

**Steps:**
1. Test on mobile browsers:
   - iOS Safari
   - Chrome Mobile
   - Firefox Mobile
   - Samsung Internet

**Expected Result:**
- Works on all major mobile browsers
- No browser-specific bugs
- Consistent appearance
- All features functional

---

## Advanced CLI Testing

### Test Category: Advanced CLI Operations

#### TEST-CLI-026: CLI Output Formatting
**Type:** CLI Test

**Steps:**
```bash
# Test different output formats
python -m src.cli.app search "users" --output-format table
python -m src.cli.app search "users" --output-format json
python -m src.cli.app search "users" --output-format csv
```

**Expected Result:**
- All formats work correctly
- Data properly formatted
- Easy to read/parse
- No formatting errors

---

#### TEST-CLI-027: CLI Piping and Redirection
**Type:** CLI Test

**Steps:**
```bash
# Pipe to other commands
python -m src.cli.app search "users" | grep "GET"

# Redirect output
python -m src.cli.app collection info > stats.txt

# Chain commands
python -m src.cli.app parse file examples/sample-openapi.json && \
  python -m src.cli.app search "users"
```

**Expected Result:**
- Piping works correctly
- Redirection successful
- Command chaining behaves as expected
- Exit codes correct

---

#### TEST-CLI-028: CLI Progress Indicators
**Type:** CLI Test

**Steps:**
```bash
# Batch operation with progress
python -m src.cli.app parse batch examples/*.json
```

**Expected Result:**
- Progress bar shown
- ETA displayed
- Current file indicated
- Can cancel (Ctrl+C)
- Final summary shown

---

#### TEST-CLI-029: CLI Color Output
**Type:** CLI Test

**Steps:**
```bash
# With colors (default)
python -m src.cli.app search "users"

# Without colors
NO_COLOR=1 python -m src.cli.app search "users"
```

**Expected Result:**
- Colors enhance readability
- Can disable colors
- Respects NO_COLOR env var
- Works in all terminals

---

#### TEST-CLI-030: CLI Interactive Mode
**Type:** CLI Test

**Steps:**
```bash
# Interactive prompt (if implemented)
python -m src.cli.app search
# Should prompt for query
```

**Expected Result:**
- Interactive prompts work
- Can cancel with Ctrl+C
- Input validation
- Help available with ?

---

#### TEST-CLI-031: CLI Configuration File
**Type:** CLI Test

**Steps:**

**For Linux/Mac:**
```bash
# Create config file
cat > ~/.api-assistant/config.yaml <<EOF
default_search_mode: hybrid
default_n_results: 20
EOF

# Use config
python -m src.cli.app search "users"
```

**For Windows PowerShell:**
```powershell
# Create config file
$configContent = @"
default_search_mode: hybrid
default_n_results: 20
"@
New-Item -Path "$env:USERPROFILE\.api-assistant" -ItemType Directory -Force
Set-Content -Path "$env:USERPROFILE\.api-assistant\config.yaml" -Value $configContent

# Use config
python -m src.cli.app search "users"
```

**Expected Result:**
- Config file loaded
- Defaults applied
- Can override with flags
- Multiple config locations supported

---

#### TEST-CLI-032: CLI Auto-completion
**Type:** CLI Test

**Steps:**
```bash
# Install completion
python -m src.cli.app --install-completion

# Test in new shell
python -m src.cli.app se<TAB>
```

**Expected Result:**
- Completion installed
- Commands auto-complete
- Arguments suggested
- File paths completed

---

#### TEST-CLI-033: CLI Help Documentation
**Type:** CLI Test

**Steps:**
```bash
# Test help at all levels
python -m src.cli.app --help
python -m src.cli.app search --help
python -m src.cli.app diagram sequence --help
```

**Expected Result:**
- Help clear and comprehensive
- Examples provided
- Options documented
- Consistent formatting

---

#### TEST-CLI-034: CLI Error Messages
**Type:** CLI Test

**Steps:**
```bash
# Trigger various errors
python -m src.cli.app search
python -m src.cli.app parse file nonexistent.json
python -m src.cli.app diagram sequence missing.json
```

**Expected Result:**
- Clear error messages
- Suggest fixes
- Show usage hints
- Non-zero exit codes
- No stack traces (unless --debug)

---

#### TEST-CLI-035: CLI Batch Operations with Errors
**Type:** CLI Test

**Steps:**
```bash
# Mix of valid and invalid files
python -m src.cli.app parse batch examples/*.json examples/invalid.json
```

**Expected Result:**
- Continues despite errors
- Failed files listed
- Summary shows success/fail count
- Exit code indicates partial failure

---

---

## Test Results Template

### Test Execution Record

**Test ID:** _____________________
**Test Name:** _____________________
**Tester:** _____________________
**Date:** _____________________
**Environment:**
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- LLM Provider: Ollama / Groq

**Preconditions:**
- [ ] Backend running
- [ ] Frontend running
- [ ] Test data available
- [ ] Database clean/seeded as needed

**Execution Steps:**

| Step | Action | Expected Result | Actual Result | Pass/Fail |
|------|--------|----------------|---------------|-----------|
| 1    |        |                |               |           |
| 2    |        |                |               |           |
| 3    |        |                |               |           |

**Overall Result:** ✅ PASS / ❌ FAIL

**Issues Found:**
-

**Screenshots/Logs:**
-

**Notes:**
-

---

## Quick Test Checklist

Use this checklist for rapid smoke testing:

### 🚀 Smoke Test - Backend (5 minutes)
- [ ] GET /health returns 200
- [ ] GET /stats returns valid JSON
- [ ] POST /documents/upload with sample-openapi.json succeeds
- [ ] POST /search returns results
- [ ] POST /chat generates response

### 🎨 Smoke Test - Frontend (10 minutes)
- [ ] Login page loads
- [ ] Can navigate to all pages
- [ ] Documents upload works
- [ ] Search returns results
- [ ] Chat responds to messages
- [ ] Diagrams generate
- [ ] Settings save

### ⚙️ Smoke Test - CLI (5 minutes)
- [ ] `python -m src.cli.app --help` works
- [ ] Parse command succeeds
- [ ] Search command returns results
- [ ] Session create/list works

---

## Test Coverage Summary

| Category | Total Tests | Test IDs | Priority |
|----------|-------------|----------|----------|
| **Backend API** | 30 | TEST-API-001 to 030 | High |
| **Frontend UI - Core** | 55 | TEST-UI-001 to 055 | High |
| **Frontend UI - Document Library** | 12 | TEST-UI-056 to 065 | High |
| **Frontend UI - Advanced Search** | 8 | TEST-UI-066 to 073 | High |
| **CLI - Basic** | 25 | TEST-CLI-001 to 025 | Medium |
| **CLI - Advanced** | 10 | TEST-CLI-026 to 035 | Medium |
| **End-to-End** | 10 | TEST-E2E-001 to 010 | High |
| **Performance** | 4 | TEST-PERF-001 to 004 | Medium |
| **Edge Cases** | 8 | TEST-EDGE-001 to 008 | Medium |
| **Security & Validation** | 12 | TEST-SEC-001 to 012 | High |
| **Integration** | 10 | TEST-INT-001 to 010 | High |
| **Accessibility** | 8 | TEST-ACC-001 to 008 | High |
| **Mobile & Responsive** | 7 | TEST-MOB-001 to 007 | High |
| **TOTAL** | **199** | - | - |

### Test Distribution by Type
- **UI Tests:** 83 (42%)
- **API Tests:** 30 (15%)
- **CLI Tests:** 35 (18%)
- **Integration/E2E Tests:** 20 (10%)
- **Security Tests:** 12 (6%)
- **Accessibility Tests:** 8 (4%)
- **Mobile Tests:** 7 (4%)
- **Performance Tests:** 4 (2%)

---

## Reporting Issues

When reporting issues found during testing:

1. **Issue Title:** Clear, concise description
2. **Test ID:** Which test failed
3. **Environment:** Backend/Frontend versions, LLM provider
4. **Steps to Reproduce:** Detailed steps
5. **Expected vs Actual:** What should happen vs what happened
6. **Screenshots/Logs:** Visual evidence
7. **Severity:** Critical / High / Medium / Low
8. **Impact:** What functionality is broken

---

## Continuous Testing

### Daily Testing (Critical Path - 15 minutes)
- **Health Checks:** TEST-API-001, TEST-API-002
- **Core Upload:** TEST-UI-005, TEST-API-003
- **Basic Search:** TEST-UI-025, TEST-API-013
- **Chat Functionality:** TEST-UI-015, TEST-API-018
- **Document Library:** TEST-UI-056, TEST-UI-062

### Weekly Testing (Comprehensive - 4-6 hours)
- **All API Endpoints:** TEST-API-001 to 030 (30 tests)
- **All UI Features:** TEST-UI-001 to 073 (73 tests)
- **CLI Commands:** TEST-CLI-001 to 035 (35 tests)
- **Diagram Generation:** TEST-UI-031 to 037 (7 tests)
- **Session Management:** TEST-UI-038 to 044 (7 tests)

### Before Release (Full Suite - 8-12 hours)
- **Complete Test Suite:** All 199 tests
- **Performance Testing:** TEST-PERF-001 to 004
- **Edge Cases:** TEST-EDGE-001 to 008
- **Security Testing:** TEST-SEC-001 to 012
- **Accessibility:** TEST-ACC-001 to 008
- **Mobile Testing:** TEST-MOB-001 to 007
- **Integration Tests:** TEST-INT-001 to 010, TEST-E2E-001 to 010
- **Cross-browser Testing:** Chrome, Firefox, Safari, Edge
- **Load Testing:** Concurrent users, large datasets

### Monthly Security Audit
- **Security Scan:** TEST-SEC-001 to 012
- **Penetration Testing:** XSS, SQL injection, CSRF
- **Dependency Audit:** Check for vulnerable packages
- **Access Control:** Verify authentication and authorization
- **Data Protection:** Check sensitive data handling

### Quarterly Accessibility Audit
- **WCAG Compliance:** TEST-ACC-001 to 008
- **Screen Reader Testing:** NVDA, JAWS, VoiceOver
- **Keyboard Navigation:** Full app testing
- **Contrast Checking:** Light and dark modes
- **Third-party Audit:** Consider external accessibility review

---

**End of Manual Testing Guide**

For automated test results, see:
- Backend: `pytest tests/ -v`
- Frontend: `npm test` in frontend/
- E2E: `npx playwright test` in frontend/

