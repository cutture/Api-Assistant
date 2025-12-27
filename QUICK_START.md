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

```bash
# Basic search
python api_assistant_cli.py search query "get all posts"

# Limit results
python api_assistant_cli.py search query "create user" --limit 3

# Filter by HTTP method
python api_assistant_cli.py search query "posts" --method GET

# Filter by source
python api_assistant_cli.py search query "user" --source openapi
```

### 3. Generate Mermaid Diagrams

**Sequence Diagram (from OpenAPI):**
```bash
# Generate sequence diagram for a specific endpoint
python api_assistant_cli.py diagram sequence test_data/openapi/jsonplaceholder.yaml \
  --endpoint "/posts" \
  --output test_data/diagrams/posts_sequence.mmd
```

**ER Diagram (from GraphQL):**
```bash
# Generate entity-relationship diagram
python api_assistant_cli.py diagram er test_data/graphql/countries.graphql \
  --output test_data/diagrams/countries_er.mmd
```

**API Overview (from OpenAPI):**
```bash
# Generate API overview flowchart
python api_assistant_cli.py diagram overview test_data/openapi/jsonplaceholder.yaml \
  --output test_data/diagrams/api_overview.mmd
```

**Authentication Flow:**
```bash
# Generate OAuth2 flow diagram
python api_assistant_cli.py diagram auth oauth2 \
  --output test_data/diagrams/oauth2_flow.mmd

# Generate API Key flow
python api_assistant_cli.py diagram auth apikey \
  --output test_data/diagrams/apikey_flow.mmd
```

### 4. Session Management

```bash
# Create a new session
python api_assistant_cli.py session create --user "testuser" --ttl 60

# List all sessions
python api_assistant_cli.py session list

# Show session statistics
python api_assistant_cli.py session stats

# Get session info (replace SESSION_ID with actual ID from create command)
python api_assistant_cli.py session info SESSION_ID --history

# Extend session expiration
python api_assistant_cli.py session extend SESSION_ID --minutes 30

# Clean up expired sessions
python api_assistant_cli.py session cleanup

# Delete a session
python api_assistant_cli.py session delete SESSION_ID --yes
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

Here's a complete workflow that works with the current CLI:

```bash
# 1. Index sample APIs
echo "Indexing APIs..."
python api_assistant_cli.py parse file test_data/openapi/jsonplaceholder.yaml --add
python api_assistant_cli.py parse file test_data/openapi/dummyjson.yaml --add

# 2. View collection info
echo "Checking collection..."
python api_assistant_cli.py collection info

# 3. Search for endpoints
echo "Searching for posts endpoints..."
python api_assistant_cli.py search query "get all posts" --limit 3

# 4. Generate diagrams
echo "Generating diagrams..."
mkdir -p test_data/diagrams
python api_assistant_cli.py diagram sequence test_data/openapi/jsonplaceholder.yaml \
  --endpoint "/posts" --output test_data/diagrams/posts_sequence.mmd
python api_assistant_cli.py diagram overview test_data/openapi/jsonplaceholder.yaml \
  --output test_data/diagrams/api_overview.mmd

# 5. Create session
echo "Creating session..."
python api_assistant_cli.py session create --user "test" --ttl 60

# 6. Export data
echo "Exporting data..."
mkdir -p test_data/exports
python api_assistant_cli.py export documents test_data/exports/all_docs.json

echo "Done! Check test_data/ directory for outputs."
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
