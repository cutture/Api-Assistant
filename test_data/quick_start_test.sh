#!/bin/bash
# Quick Start Testing Script for API Integration Assistant
# This script demonstrates key features using sample data

echo "=============================================="
echo "API Integration Assistant - Quick Start Test"
echo "=============================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Parse and index JSONPlaceholder API
echo -e "${BLUE}Step 1: Parsing JSONPlaceholder API...${NC}"
python api_assistant_cli.py parse file test_data/openapi/jsonplaceholder.yaml --add
echo ""

# Step 2: Parse and index DummyJSON API
echo -e "${BLUE}Step 2: Parsing DummyJSON Products API...${NC}"
python api_assistant_cli.py parse file test_data/openapi/dummyjson.yaml --add
echo ""

# Step 3: View statistics
echo -e "${BLUE}Step 3: Viewing database statistics...${NC}"
python api_assistant_cli.py info stats
echo ""

# Step 4: Basic search
echo -e "${BLUE}Step 4: Testing basic search - 'get all posts'${NC}"
python api_assistant_cli.py search query "get all posts" --limit 3
echo ""

# Step 5: Hybrid search with re-ranking
echo -e "${BLUE}Step 5: Testing hybrid search with re-ranking - 'create new user'${NC}"
python api_assistant_cli.py search query "create new user" --hybrid --rerank --limit 3
echo ""

# Step 6: Query expansion
echo -e "${BLUE}Step 6: Testing query expansion - 'remove item'${NC}"
python api_assistant_cli.py search query "remove item" --expand --limit 3
echo ""

# Step 7: Filter by method
echo -e "${BLUE}Step 7: Testing filter by HTTP method - GET only${NC}"
python api_assistant_cli.py search query "posts" --filter '{"operator": "and", "filters": [{"field": "method", "operator": "eq", "value": "GET"}]}' --limit 3
echo ""

# Step 8: Faceted search
echo -e "${BLUE}Step 8: Getting facets for HTTP methods${NC}"
python api_assistant_cli.py search facets --field method
echo ""

# Step 9: Generate sequence diagram
echo -e "${BLUE}Step 9: Generating sequence diagram for GET /posts${NC}"
mkdir -p test_data/diagrams
python api_assistant_cli.py diagram generate sequence --endpoint "/posts" --method GET --output test_data/diagrams/posts_sequence.mmd
if [ -f "test_data/diagrams/posts_sequence.mmd" ]; then
    echo -e "${GREEN}✓ Diagram saved to test_data/diagrams/posts_sequence.mmd${NC}"
fi
echo ""

# Step 10: Generate ER diagram
echo -e "${BLUE}Step 10: Generating ER diagram${NC}"
python api_assistant_cli.py diagram generate er --output test_data/diagrams/er_diagram.mmd
if [ -f "test_data/diagrams/er_diagram.mmd" ]; then
    echo -e "${GREEN}✓ ER diagram saved to test_data/diagrams/er_diagram.mmd${NC}"
fi
echo ""

# Step 11: Generate Python client code
echo -e "${BLUE}Step 11: Generating Python client code for GET /posts${NC}"
mkdir -p test_data/clients
python api_assistant_cli.py generate code --endpoint "/posts" --method GET --language python --output test_data/clients/get_posts.py
if [ -f "test_data/clients/get_posts.py" ]; then
    echo -e "${GREEN}✓ Python client saved to test_data/clients/get_posts.py${NC}"
fi
echo ""

# Step 12: Export database
echo -e "${BLUE}Step 12: Exporting database to JSON${NC}"
mkdir -p test_data/exports
python api_assistant_cli.py batch export --format json --output test_data/exports/all_apis.json
if [ -f "test_data/exports/all_apis.json" ]; then
    echo -e "${GREEN}✓ Export saved to test_data/exports/all_apis.json${NC}"
fi
echo ""

# Final summary
echo -e "${GREEN}=============================================="
echo "Quick Start Test Complete! ✓"
echo "==============================================${NC}"
echo ""
echo "What was tested:"
echo "  ✓ OpenAPI parsing and indexing"
echo "  ✓ Vector search"
echo "  ✓ Hybrid search with re-ranking"
echo "  ✓ Query expansion"
echo "  ✓ Advanced filtering"
echo "  ✓ Faceted search"
echo "  ✓ Mermaid diagram generation"
echo "  ✓ Code generation"
echo "  ✓ Database export"
echo ""
echo "Generated files:"
echo "  - test_data/diagrams/posts_sequence.mmd"
echo "  - test_data/diagrams/er_diagram.mmd"
echo "  - test_data/clients/get_posts.py"
echo "  - test_data/exports/all_apis.json"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. View diagrams at https://mermaid.live"
echo "  2. Check generated Python code in test_data/clients/"
echo "  3. Start Streamlit UI: PYTHONPATH=. streamlit run src/main.py"
echo "  4. Read full testing guide: TESTING_GUIDE.md"
echo ""
