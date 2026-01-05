# Quick Start Testing Script for API Integration Assistant (Windows PowerShell)
# This script demonstrates key features using correct CLI commands

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

# Step 3: View collection information
Write-Host "Step 3: Viewing collection information..." -ForegroundColor Blue
python api_assistant_cli.py collection info
Write-Host ""

# Step 4: Basic search
Write-Host "Step 4: Testing basic search - 'get all posts'" -ForegroundColor Blue
python api_assistant_cli.py search query "get all posts" --limit 3
Write-Host ""

# Step 5: Search with method filter
Write-Host "Step 5: Testing search with method filter - GET only" -ForegroundColor Blue
python api_assistant_cli.py search query "posts" --method GET --limit 3
Write-Host ""

# Step 6: Search with source filter
Write-Host "Step 6: Testing search with source filter - openapi only" -ForegroundColor Blue
python api_assistant_cli.py search query "user" --source openapi --limit 3
Write-Host ""

# Step 7: Generate sequence diagram
Write-Host "Step 7: Generating sequence diagram for GET /posts" -ForegroundColor Blue
if (!(Test-Path "test_data/diagrams")) {
    New-Item -ItemType Directory -Path "test_data/diagrams" | Out-Null
}
python api_assistant_cli.py diagram sequence test_data/openapi/jsonplaceholder.yaml --endpoint "/posts" --output test_data/diagrams/posts_sequence.mmd
if (Test-Path "test_data/diagrams/posts_sequence.mmd") {
    Write-Host "✓ Diagram saved to test_data/diagrams/posts_sequence.mmd" -ForegroundColor Green
}
Write-Host ""

# Step 8: Generate API overview
Write-Host "Step 8: Generating API overview flowchart" -ForegroundColor Blue
python api_assistant_cli.py diagram overview test_data/openapi/jsonplaceholder.yaml --output test_data/diagrams/api_overview.mmd
if (Test-Path "test_data/diagrams/api_overview.mmd") {
    Write-Host "✓ Overview saved to test_data/diagrams/api_overview.mmd" -ForegroundColor Green
}
Write-Host ""

# Step 9: Generate GraphQL ER diagram
Write-Host "Step 9: Parsing GraphQL schema and generating ER diagram" -ForegroundColor Blue
python api_assistant_cli.py parse file test_data/graphql/countries.graphql --format graphql --add
python api_assistant_cli.py diagram er test_data/graphql/countries.graphql --output test_data/diagrams/countries_er.mmd
if (Test-Path "test_data/diagrams/countries_er.mmd") {
    Write-Host "✓ ER diagram saved to test_data/diagrams/countries_er.mmd" -ForegroundColor Green
}
Write-Host ""

# Step 10: Generate authentication flow
Write-Host "Step 10: Generating OAuth2 authentication flow" -ForegroundColor Blue
python api_assistant_cli.py diagram auth oauth2 --output test_data/diagrams/oauth2_flow.mmd
if (Test-Path "test_data/diagrams/oauth2_flow.mmd") {
    Write-Host "✓ Auth flow saved to test_data/diagrams/oauth2_flow.mmd" -ForegroundColor Green
}
Write-Host ""

# Step 11: Create session
Write-Host "Step 11: Creating a test session" -ForegroundColor Blue
python api_assistant_cli.py session create --user "testuser" --ttl 60
Write-Host ""

# Step 12: View session statistics
Write-Host "Step 12: Viewing session statistics" -ForegroundColor Blue
python api_assistant_cli.py session stats
Write-Host ""

# Step 13: Export database
Write-Host "Step 13: Exporting database to JSON" -ForegroundColor Blue
if (!(Test-Path "test_data/exports")) {
    New-Item -ItemType Directory -Path "test_data/exports" | Out-Null
}
python api_assistant_cli.py export documents test_data/exports/all_docs.json --limit 20
if (Test-Path "test_data/exports/all_docs.json") {
    Write-Host "✓ Export saved to test_data/exports/all_docs.json" -ForegroundColor Green
}
Write-Host ""

# Step 14: Show version
Write-Host "Step 14: Showing API Assistant version" -ForegroundColor Blue
python api_assistant_cli.py info version
Write-Host ""

# Final summary
Write-Host "==============================================" -ForegroundColor Green
Write-Host "Quick Start Test Complete! ✓" -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green
Write-Host ""
Write-Host "What was tested:"
Write-Host "  ✓ OpenAPI parsing and indexing (2 APIs)"
Write-Host "  ✓ GraphQL parsing and indexing"
Write-Host "  ✓ Vector search"
Write-Host "  ✓ Method filtering"
Write-Host "  ✓ Source filtering"
Write-Host "  ✓ Sequence diagram generation"
Write-Host "  ✓ API overview diagram"
Write-Host "  ✓ GraphQL ER diagram"
Write-Host "  ✓ Authentication flow diagram"
Write-Host "  ✓ Session management"
Write-Host "  ✓ Database export"
Write-Host ""
Write-Host "Generated files:"
Write-Host "  - test_data/diagrams/posts_sequence.mmd"
Write-Host "  - test_data/diagrams/api_overview.mmd"
Write-Host "  - test_data/diagrams/countries_er.mmd"
Write-Host "  - test_data/diagrams/oauth2_flow.mmd"
Write-Host "  - test_data/exports/all_docs.json"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. View diagrams at https://mermaid.live"
Write-Host "  2. Start Streamlit UI for advanced features:"
Write-Host "     `$env:PYTHONPATH = '.'; streamlit run src/main.py"
Write-Host ""
Write-Host "Note:" -ForegroundColor Yellow -NoNewline
Write-Host " For hybrid search, re-ranking, query expansion, and code"
Write-Host "generation, use the Streamlit UI (these features are not in CLI)."
Write-Host ""
Write-Host "See QUICK_START.md for feature availability matrix."
Write-Host ""
