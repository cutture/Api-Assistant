# Quick Start Guide - API Integration Assistant v1.0.0

## 🚀 Getting Started in 5 Minutes

This guide provides working examples you can run immediately to test all features.

### Prerequisites

```bash
# Make sure you're in the project directory
cd Api-Assistant

# Virtual environment should be activated (if using one)
```

---

## 🎯 Copy-Paste Ready: Complete Test Workflow

Run these commands in sequence to test all features in 5 minutes:

### Bash/Linux/Mac:
```bash
# 1. Create output directories
mkdir -p test_data/diagrams test_data/exports

# 2. Index sample APIs
python api_assistant_cli.py parse file test_data/openapi/jsonplaceholder.yaml --add
python api_assistant_cli.py parse file test_data/openapi/dummyjson.yaml --add
python api_assistant_cli.py parse file test_data/graphql/countries.graphql --format graphql --add

# 3. View indexed data
python api_assistant_cli.py collection info

# 4. Search for endpoints
python api_assistant_cli.py search query "get all posts" --limit 3
python api_assistant_cli.py search query "create user" --method POST --limit 3
python api_assistant_cli.py search query "user data" --source openapi --limit 3

# 5. Generate diagrams
python api_assistant_cli.py diagram sequence test_data/openapi/jsonplaceholder.yaml --endpoint "/posts" --output test_data/diagrams/posts_sequence.mmd
python api_assistant_cli.py diagram overview test_data/openapi/jsonplaceholder.yaml --output test_data/diagrams/api_overview.mmd
python api_assistant_cli.py diagram er test_data/graphql/countries.graphql --output test_data/diagrams/countries_er.mmd
python api_assistant_cli.py diagram auth oauth2 --output test_data/diagrams/oauth2_flow.mmd

# 6. Session management
python api_assistant_cli.py session create --user "testuser" --ttl 60
python api_assistant_cli.py session list
python api_assistant_cli.py session stats

# 7. Export data
python api_assistant_cli.py export documents test_data/exports/all_docs.json

# 8. View version
python api_assistant_cli.py info version
```

### PowerShell:
```powershell
# 1. Create output directories
New-Item -ItemType Directory -Path test_data/diagrams -Force
New-Item -ItemType Directory -Path test_data/exports -Force

# 2. Index sample APIs
python api_assistant_cli.py parse file test_data/openapi/jsonplaceholder.yaml --add
python api_assistant_cli.py parse file test_data/openapi/dummyjson.yaml --add
python api_assistant_cli.py parse file test_data/graphql/countries.graphql --format graphql --add

# 3. View indexed data
python api_assistant_cli.py collection info

# 4. Search for endpoints
python api_assistant_cli.py search query "get all posts" --limit 3
python api_assistant_cli.py search query "create user" --method POST --limit 3
python api_assistant_cli.py search query "user data" --source openapi --limit 3

# 5. Generate diagrams (single line - easier in PowerShell)
python api_assistant_cli.py diagram sequence test_data/openapi/jsonplaceholder.yaml --endpoint "/posts" --output test_data/diagrams/posts_sequence.mmd
python api_assistant_cli.py diagram overview test_data/openapi/jsonplaceholder.yaml --output test_data/diagrams/api_overview.mmd
python api_assistant_cli.py diagram er test_data/graphql/countries.graphql --output test_data/diagrams/countries_er.mmd
python api_assistant_cli.py diagram auth oauth2 --output test_data/diagrams/oauth2_flow.mmd

# 6. Session management
python api_assistant_cli.py session create --user "testuser" --ttl 60
python api_assistant_cli.py session list
python api_assistant_cli.py session stats

# 7. Export data
python api_assistant_cli.py export documents test_data/exports/all_docs.json

# 8. View version
python api_assistant_cli.py info version
```

**Expected Time**: ~5 minutes
**Expected Results**:
- Collection with 50+ indexed endpoints
- Multiple Mermaid diagrams in `test_data/diagrams/`
- JSON export in `test_data/exports/`
- Active session visible in session list

---

## ✅ Working CLI Commands

### 1. Parse and Index an API

```bash
# Index the JSONPlaceholder API
python api_assistant_cli.py parse file test_data/openapi/jsonplaceholder.yaml --add

# Index the DummyJSON Products API
python api_assistant_cli.py parse file test_data/openapi/dummyjson.yaml --add

# Index a GraphQL schema
python api_assistant_cli.py parse file test_data/graphql/countries.graphql --format graphql --add

# Index a Postman collection
python api_assistant_cli.py parse file test_data/postman/reqres_collection.json --format postman --add
```

### 2. Search for API Endpoints

**Basic Search:**
```bash
# Search for posts endpoints
python api_assistant_cli.py search query "get all posts"

# Limit results to 3
python api_assistant_cli.py search query "create user" --limit 3

# Hide content, show only metadata
python api_assistant_cli.py search query "update data" --no-content --limit 5
```

**Filtered Search:**
```bash
# Filter by HTTP method only
python api_assistant_cli.py search query "posts" --method GET --limit 5

# Filter by source only
python api_assistant_cli.py search query "user" --source openapi --limit 5

# Combined filters (method AND source)
python api_assistant_cli.py search query "data" --method POST --source openapi --limit 5
```

**Real-World Example Queries:**
```bash
# Find authentication endpoints
python api_assistant_cli.py search query "login authentication" --limit 5

# Find user management endpoints
python api_assistant_cli.py search query "user profile management" --method GET --limit 5

# Find data creation endpoints
python api_assistant_cli.py search query "create new record" --method POST --limit 5

# Find product-related endpoints
python api_assistant_cli.py search query "product catalog inventory" --limit 5

# Find deletion endpoints
python api_assistant_cli.py search query "delete remove" --method DELETE --limit 5
```

**Expected Output:**
```
╭──────────────────── Search Results (3 matches) ────────────────────╮
│                                                                     │
│  [1] GET /posts                                                     │
│  Summary: Get all posts                                             │
│  Description: Retrieve a list of all posts                          │
│  Source: openapi | Method: GET | Score: 0.89                        │
│                                                                     │
│  [2] GET /posts/{id}                                                │
│  Summary: Get a specific post                                       │
│  Description: Retrieve a post by its ID                             │
│  Source: openapi | Method: GET | Score: 0.85                        │
│                                                                     │
│  [3] POST /posts                                                    │
│  Summary: Create a new post                                         │
│  Description: Add a new post to the collection                      │
│  Source: openapi | Method: POST | Score: 0.82                       │
╰─────────────────────────────────────────────────────────────────────╯
```

### 3. Generate Mermaid Diagrams

> **⚠️ Windows PowerShell Users**: Use backtick `` ` `` for line continuation, not backslash `\`

**First, create the output directory:**

**PowerShell:**
```powershell
New-Item -ItemType Directory -Path test_data/diagrams -Force
```

**Bash/Linux/Mac:**
```bash
mkdir -p test_data/diagrams
```

**Sequence Diagram (from OpenAPI):**

**Bash/Linux/Mac:**
```bash
python api_assistant_cli.py diagram sequence test_data/openapi/jsonplaceholder.yaml \
  --endpoint "/posts" \
  --output test_data/diagrams/posts_sequence.mmd
```

**PowerShell:**
```powershell
python api_assistant_cli.py diagram sequence test_data/openapi/jsonplaceholder.yaml `
  --endpoint "/posts" `
  --output test_data/diagrams/posts_sequence.mmd

# OR as a single line:
python api_assistant_cli.py diagram sequence test_data/openapi/jsonplaceholder.yaml --endpoint "/posts" --output test_data/diagrams/posts_sequence.mmd
```

**ER Diagram (from GraphQL):**

**Bash/Linux/Mac:**
```bash
python api_assistant_cli.py diagram er test_data/graphql/countries.graphql \
  --output test_data/diagrams/countries_er.mmd
```

**PowerShell:**
```powershell
python api_assistant_cli.py diagram er test_data/graphql/countries.graphql --output test_data/diagrams/countries_er.mmd
```

**API Overview (from OpenAPI):**

**Bash/Linux/Mac:**
```bash
python api_assistant_cli.py diagram overview test_data/openapi/jsonplaceholder.yaml \
  --output test_data/diagrams/api_overview.mmd
```

**PowerShell:**
```powershell
python api_assistant_cli.py diagram overview test_data/openapi/jsonplaceholder.yaml --output test_data/diagrams/api_overview.mmd
```

**Authentication Flow:**

```bash
# OAuth2 flow
python api_assistant_cli.py diagram auth oauth2 --output test_data/diagrams/oauth2_flow.mmd

# API Key flow
python api_assistant_cli.py diagram auth apikey --output test_data/diagrams/apikey_flow.mmd

# Other types: bearer, basic
python api_assistant_cli.py diagram auth bearer --output test_data/diagrams/bearer_flow.mmd
```

### 4. Session Management

> **⚠️ IMPORTANT**: Session IDs are unique UUIDs generated when you create a session. You must copy the actual ID from the command output!

**Basic Commands (No Session ID Required):**
```bash
# Create a new session
python api_assistant_cli.py session create --user "testuser" --ttl 60

# List all sessions
python api_assistant_cli.py session list

# Show session statistics
python api_assistant_cli.py session stats

# Clean up expired sessions
python api_assistant_cli.py session cleanup
```

**Commands Requiring Session ID:**

**Bash/Linux/Mac - Manual Method:**
```bash
# 1. Create session and copy the Session ID from output
python api_assistant_cli.py session create --user "testuser" --ttl 60
# Output: Session ID: abc12345-6789-...  ← COPY THIS ID

# 2. Paste the actual ID into these commands:
python api_assistant_cli.py session info abc12345-6789-... --history
python api_assistant_cli.py session extend abc12345-6789-... --minutes 30
python api_assistant_cli.py session delete abc12345-6789-... --yes
```

**Bash/Linux/Mac - Automated Method:**
```bash
# Capture session ID automatically
SESSION_OUTPUT=$(python api_assistant_cli.py session create --user "testuser" --ttl 60)
echo "$SESSION_OUTPUT"
SESSION_ID=$(echo "$SESSION_OUTPUT" | grep "Session ID" | awk '{print $3}')

# Use the captured ID
python api_assistant_cli.py session info $SESSION_ID --history
python api_assistant_cli.py session extend $SESSION_ID --minutes 30
python api_assistant_cli.py session delete $SESSION_ID --yes
```

**PowerShell - Manual Method:**
```powershell
# 1. Create session and copy the Session ID from output
python api_assistant_cli.py session create --user "testuser" --ttl 60
# Output: Session ID: abc12345-6789-...  ← COPY THIS ID

# 2. Set the variable with YOUR ACTUAL ID (not this example!)
$SESSION_ID = "abc12345-6789-..."  # REPLACE with your actual ID!

# 3. Now use the variable
python api_assistant_cli.py session info $SESSION_ID --history
python api_assistant_cli.py session extend $SESSION_ID --minutes 30
python api_assistant_cli.py session delete $SESSION_ID --yes
```

**PowerShell - Automated Method (Recommended):**
```powershell
# Capture session ID automatically
$OUTPUT = python api_assistant_cli.py session create --user "testuser" --ttl 60
Write-Host $OUTPUT

# Extract session ID using regex
$SESSION_ID = ($OUTPUT | Select-String -Pattern "Session ID:\s+([a-f0-9\-]+)").Matches.Groups[1].Value

# Verify it was captured
Write-Host "Captured Session ID: $SESSION_ID" -ForegroundColor Green

# Use the captured ID
python api_assistant_cli.py session info $SESSION_ID --history
python api_assistant_cli.py session extend $SESSION_ID --minutes 30
python api_assistant_cli.py session delete $SESSION_ID --yes
```

### 5. Collection Management

```bash
# View collection information
python api_assistant_cli.py collection info

# Clear all documents (use with caution!)
python api_assistant_cli.py collection clear --yes
```

### 6. Export Data

```bash
# Export all documents to JSON
python api_assistant_cli.py export documents test_data/exports/all_docs.json

# Export with limit
python api_assistant_cli.py export documents test_data/exports/sample_docs.json --limit 10
```

### 7. Information Commands

```bash
# Show version
python api_assistant_cli.py info version

# Show supported formats
python api_assistant_cli.py info formats
```

---

## 🖥️ Streamlit UI (Recommended)

The UI provides access to ALL features including those not available in CLI:

### Start the UI

**Windows PowerShell:**
```powershell
$env:PYTHONPATH = "."; streamlit run src/main.py
```

**Linux/Mac:**
```bash
PYTHONPATH=. streamlit run src/main.py
```

**Or use different port:**
```bash
PYTHONPATH=. streamlit run src/main.py --server.port 8502
```

### UI Features (Not in CLI)

The Streamlit UI has features that are NOT available in the CLI:

✅ **Hybrid Search** - Combine vector + BM25 search
✅ **Re-ranking** - Cross-encoder re-ranking for better results
✅ **Query Expansion** - Automatic query variations
✅ **Code Generation** - Python, JavaScript, cURL client code
✅ **Advanced Filtering** - Complex AND/OR/NOT filters
✅ **Faceted Search** - Browse by categories
✅ **Interactive Chat** - Natural language queries
✅ **Visual Analytics** - Charts and statistics

---

## 📋 Complete Test Workflow

### Option 1: Use the Automated Script (Easiest)

**PowerShell:**
```powershell
cd test_data
.\quick_start_test.ps1
```

**Bash/Linux/Mac:**
```bash
cd test_data
./quick_start_test.sh
```

### Option 2: Manual Commands

**Bash/Linux/Mac:**
```bash
# 1. Index sample APIs
python api_assistant_cli.py parse file test_data/openapi/jsonplaceholder.yaml --add
python api_assistant_cli.py parse file test_data/openapi/dummyjson.yaml --add

# 2. View collection info
python api_assistant_cli.py collection info

# 3. Search for endpoints
python api_assistant_cli.py search query "get all posts" --limit 3

# 4. Generate diagrams
python api_assistant_cli.py diagram sequence test_data/openapi/jsonplaceholder.yaml --endpoint "/posts" --output test_data/diagrams/posts_sequence.mmd
python api_assistant_cli.py diagram overview test_data/openapi/jsonplaceholder.yaml --output test_data/diagrams/api_overview.mmd

# 5. Create session
python api_assistant_cli.py session create --user "test" --ttl 60

# 6. Export data
python api_assistant_cli.py export documents test_data/exports/all_docs.json
```

**PowerShell:**
```powershell
# 1. Index sample APIs
python api_assistant_cli.py parse file test_data/openapi/jsonplaceholder.yaml --add
python api_assistant_cli.py parse file test_data/openapi/dummyjson.yaml --add

# 2. View collection info
python api_assistant_cli.py collection info

# 3. Search for endpoints
python api_assistant_cli.py search query "get all posts" --limit 3

# 4. Generate diagrams (single line - no continuation needed)
python api_assistant_cli.py diagram sequence test_data/openapi/jsonplaceholder.yaml --endpoint "/posts" --output test_data/diagrams/posts_sequence.mmd
python api_assistant_cli.py diagram overview test_data/openapi/jsonplaceholder.yaml --output test_data/diagrams/api_overview.mmd

# 5. Create session
python api_assistant_cli.py session create --user "test" --ttl 60

# 6. Export data
python api_assistant_cli.py export documents test_data/exports/all_docs.json
```

---

## 🎯 Feature Availability Matrix

| Feature | CLI | Streamlit UI |
|---------|-----|--------------|
| Parse OpenAPI/GraphQL/Postman | ✅ | ✅ |
| Basic Vector Search | ✅ | ✅ |
| Hybrid Search (Vector + BM25) | ❌ | ✅ |
| Cross-encoder Re-ranking | ❌ | ✅ |
| Query Expansion | ❌ | ✅ |
| Simple Method/Source Filters | ✅ | ✅ |
| Advanced AND/OR/NOT Filters | ❌ | ✅ |
| Faceted Search | ❌ | ✅ |
| Mermaid Diagrams | ✅ | ✅ |
| Code Generation | ❌ | ✅ |
| Session Management | ✅ | ✅ |
| Data Export | ✅ | ✅ |
| Interactive Chat | ❌ | ✅ |
| Visual Analytics | ❌ | ✅ |

**Recommendation**: Use Streamlit UI for full feature access. Use CLI for automation and scripting.

---

## 🐛 Troubleshooting

### Error: "No such option: --hybrid"
**Solution**: This feature is only available in the Streamlit UI, not the CLI.

### Error: "No such command 'generate'"
**Solution**: Use commands directly under `diagram`:
- `diagram sequence` (not `diagram generate sequence`)
- `diagram er` (not `diagram generate er`)

### Error: "No documents found"
**Solution**: Make sure to use `--add` flag when parsing:
```bash
python api_assistant_cli.py parse file your_file.yaml --add
```

### Slow Performance
**Solution**: The first search may be slow due to model loading. Subsequent searches are faster due to caching.

---

## 📚 Next Steps

1. ✅ **Run the quick test workflow** above to verify everything works
2. ✅ **Start the Streamlit UI** for full feature access
3. ✅ **Read TESTING_GUIDE.md** for comprehensive UI testing workflows
4. ✅ **Upload your own API specs** for real-world testing

---

## 🔗 Resources

- **Full Testing Guide**: `TESTING_GUIDE.md` (UI workflows and advanced scenarios)
- **Test Data**: `test_data/README.md` (Sample API specifications)
- **Main Documentation**: `README.md` (Project overview)
- **View Diagrams**: https://mermaid.live (Paste `.mmd` file content)

---

**Happy Testing!** 🎉

For advanced features like hybrid search, re-ranking, query expansion, and code generation, use the Streamlit UI.
