# Quick Start Testing Script for API Integration Assistant (Windows PowerShell)
# This script demonstrates key features using sample data

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "API Integration Assistant - Quick Start Test" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Parse and index JSONPlaceholder API
Write-Host "Step 1: Parsing JSONPlaceholder API..." -ForegroundColor Blue
python api_assistant_cli.py parse file test_data/openapi/jsonplaceholder.yaml --add
Write-Host ""

# Step 2: Parse and index DummyJSON API
Write-Host "Step 2: Parsing DummyJSON Products API..." -ForegroundColor Blue
python api_assistant_cli.py parse file test_data/openapi/dummyjson.yaml --add
Write-Host ""

# Step 3: View statistics
Write-Host "Step 3: Viewing database statistics..." -ForegroundColor Blue
python api_assistant_cli.py info stats
Write-Host ""

# Step 4: Basic search
Write-Host "Step 4: Testing basic search - 'get all posts'" -ForegroundColor Blue
python api_assistant_cli.py search query "get all posts" --limit 3
Write-Host ""

# Step 5: Hybrid search with re-ranking
Write-Host "Step 5: Testing hybrid search with re-ranking - 'create new user'" -ForegroundColor Blue
python api_assistant_cli.py search query "create new user" --hybrid --rerank --limit 3
Write-Host ""

# Step 6: Query expansion
Write-Host "Step 6: Testing query expansion - 'remove item'" -ForegroundColor Blue
python api_assistant_cli.py search query "remove item" --expand --limit 3
Write-Host ""

# Step 7: Filter by method
Write-Host "Step 7: Testing filter by HTTP method - GET only" -ForegroundColor Blue
python api_assistant_cli.py search query "posts" --filter '{\"operator\": \"and\", \"filters\": [{\"field\": \"method\", \"operator\": \"eq\", \"value\": \"GET\"}]}' --limit 3
Write-Host ""

# Step 8: Faceted search
Write-Host "Step 8: Getting facets for HTTP methods" -ForegroundColor Blue
python api_assistant_cli.py search facets --field method
Write-Host ""

# Step 9: Generate sequence diagram
Write-Host "Step 9: Generating sequence diagram for GET /posts" -ForegroundColor Blue
if (!(Test-Path "test_data/diagrams")) {
    New-Item -ItemType Directory -Path "test_data/diagrams" | Out-Null
}
python api_assistant_cli.py diagram generate sequence --endpoint "/posts" --method GET --output test_data/diagrams/posts_sequence.mmd
if (Test-Path "test_data/diagrams/posts_sequence.mmd") {
    Write-Host "✓ Diagram saved to test_data/diagrams/posts_sequence.mmd" -ForegroundColor Green
}
Write-Host ""

# Step 10: Generate ER diagram
Write-Host "Step 10: Generating ER diagram" -ForegroundColor Blue
python api_assistant_cli.py diagram generate er --output test_data/diagrams/er_diagram.mmd
if (Test-Path "test_data/diagrams/er_diagram.mmd") {
    Write-Host "✓ ER diagram saved to test_data/diagrams/er_diagram.mmd" -ForegroundColor Green
}
Write-Host ""

# Step 11: Generate Python client code
Write-Host "Step 11: Generating Python client code for GET /posts" -ForegroundColor Blue
if (!(Test-Path "test_data/clients")) {
    New-Item -ItemType Directory -Path "test_data/clients" | Out-Null
}
python api_assistant_cli.py generate code --endpoint "/posts" --method GET --language python --output test_data/clients/get_posts.py
if (Test-Path "test_data/clients/get_posts.py") {
    Write-Host "✓ Python client saved to test_data/clients/get_posts.py" -ForegroundColor Green
}
Write-Host ""

# Step 12: Export database
Write-Host "Step 12: Exporting database to JSON" -ForegroundColor Blue
if (!(Test-Path "test_data/exports")) {
    New-Item -ItemType Directory -Path "test_data/exports" | Out-Null
}
python api_assistant_cli.py batch export --format json --output test_data/exports/all_apis.json
if (Test-Path "test_data/exports/all_apis.json") {
    Write-Host "✓ Export saved to test_data/exports/all_apis.json" -ForegroundColor Green
}
Write-Host ""

# Final summary
Write-Host "==============================================" -ForegroundColor Green
Write-Host "Quick Start Test Complete! ✓" -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green
Write-Host ""
Write-Host "What was tested:"
Write-Host "  ✓ OpenAPI parsing and indexing"
Write-Host "  ✓ Vector search"
Write-Host "  ✓ Hybrid search with re-ranking"
Write-Host "  ✓ Query expansion"
Write-Host "  ✓ Advanced filtering"
Write-Host "  ✓ Faceted search"
Write-Host "  ✓ Mermaid diagram generation"
Write-Host "  ✓ Code generation"
Write-Host "  ✓ Database export"
Write-Host ""
Write-Host "Generated files:"
Write-Host "  - test_data/diagrams/posts_sequence.mmd"
Write-Host "  - test_data/diagrams/er_diagram.mmd"
Write-Host "  - test_data/clients/get_posts.py"
Write-Host "  - test_data/exports/all_apis.json"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. View diagrams at https://mermaid.live"
Write-Host "  2. Check generated Python code in test_data/clients/"
Write-Host "  3. Start Streamlit UI: `$env:PYTHONPATH = '.'; streamlit run src/main.py"
Write-Host "  4. Read full testing guide: TESTING_GUIDE.md"
Write-Host ""
