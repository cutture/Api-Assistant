#!/bin/bash
# Quick Start Testing Script for API Integration Assistant
# This script demonstrates key features using correct CLI commands

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

# Step 3: View collection information
echo -e "${BLUE}Step 3: Viewing collection information...${NC}"
python api_assistant_cli.py collection info
echo ""

# Step 4: Basic search
echo -e "${BLUE}Step 4: Testing basic search - 'get all posts'${NC}"
python api_assistant_cli.py search query "get all posts" --limit 3
echo ""

# Step 5: Search with method filter
echo -e "${BLUE}Step 5: Testing search with method filter - GET only${NC}"
python api_assistant_cli.py search query "posts" --method GET --limit 3
echo ""

# Step 6: Search with source filter
echo -e "${BLUE}Step 6: Testing search with source filter - openapi only${NC}"
python api_assistant_cli.py search query "user" --source openapi --limit 3
echo ""

# Step 7: Generate sequence diagram
echo -e "${BLUE}Step 7: Generating sequence diagram for GET /posts${NC}"
mkdir -p test_data/diagrams
python api_assistant_cli.py diagram sequence test_data/openapi/jsonplaceholder.yaml \
  --endpoint "/posts" \
  --output test_data/diagrams/posts_sequence.mmd
if [ -f "test_data/diagrams/posts_sequence.mmd" ]; then
    echo -e "${GREEN}✓ Diagram saved to test_data/diagrams/posts_sequence.mmd${NC}"
fi
echo ""

# Step 8: Generate API overview
echo -e "${BLUE}Step 8: Generating API overview flowchart${NC}"
python api_assistant_cli.py diagram overview test_data/openapi/jsonplaceholder.yaml \
  --output test_data/diagrams/api_overview.mmd
if [ -f "test_data/diagrams/api_overview.mmd" ]; then
    echo -e "${GREEN}✓ Overview saved to test_data/diagrams/api_overview.mmd${NC}"
fi
echo ""

# Step 9: Generate GraphQL ER diagram
echo -e "${BLUE}Step 9: Parsing GraphQL schema and generating ER diagram${NC}"
python api_assistant_cli.py parse file test_data/graphql/countries.graphql --format graphql --add
python api_assistant_cli.py diagram er test_data/graphql/countries.graphql \
  --output test_data/diagrams/countries_er.mmd
if [ -f "test_data/diagrams/countries_er.mmd" ]; then
    echo -e "${GREEN}✓ ER diagram saved to test_data/diagrams/countries_er.mmd${NC}"
fi
echo ""

# Step 10: Generate authentication flow
echo -e "${BLUE}Step 10: Generating OAuth2 authentication flow${NC}"
python api_assistant_cli.py diagram auth oauth2 \
  --output test_data/diagrams/oauth2_flow.mmd
if [ -f "test_data/diagrams/oauth2_flow.mmd" ]; then
    echo -e "${GREEN}✓ Auth flow saved to test_data/diagrams/oauth2_flow.mmd${NC}"
fi
echo ""

# Step 11: Create session
echo -e "${BLUE}Step 11: Creating a test session${NC}"
python api_assistant_cli.py session create --user "testuser" --ttl 60
echo ""

# Step 12: View session statistics
echo -e "${BLUE}Step 12: Viewing session statistics${NC}"
python api_assistant_cli.py session stats
echo ""

# Step 13: Export database
echo -e "${BLUE}Step 13: Exporting database to JSON${NC}"
mkdir -p test_data/exports
python api_assistant_cli.py export documents test_data/exports/all_docs.json --limit 20
if [ -f "test_data/exports/all_docs.json" ]; then
    echo -e "${GREEN}✓ Export saved to test_data/exports/all_docs.json${NC}"
fi
echo ""

# Step 14: Show version
echo -e "${BLUE}Step 14: Showing API Assistant version${NC}"
python api_assistant_cli.py info version
echo ""

# Final summary
echo -e "${GREEN}=============================================="
echo "Quick Start Test Complete! ✓"
echo "==============================================${NC}"
echo ""
echo "What was tested:"
echo "  ✓ OpenAPI parsing and indexing (2 APIs)"
echo "  ✓ GraphQL parsing and indexing"
echo "  ✓ Vector search"
echo "  ✓ Method filtering"
echo "  ✓ Source filtering"
echo "  ✓ Sequence diagram generation"
echo "  ✓ API overview diagram"
echo "  ✓ GraphQL ER diagram"
echo "  ✓ Authentication flow diagram"
echo "  ✓ Session management"
echo "  ✓ Database export"
echo ""
echo "Generated files:"
echo "  - test_data/diagrams/posts_sequence.mmd"
echo "  - test_data/diagrams/api_overview.mmd"
echo "  - test_data/diagrams/countries_er.mmd"
echo "  - test_data/diagrams/oauth2_flow.mmd"
echo "  - test_data/exports/all_docs.json"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. View diagrams at https://mermaid.live"
echo "  2. Start Streamlit UI for advanced features:"
echo "     PYTHONPATH=. streamlit run src/main.py"
echo ""
echo -e "${YELLOW}Note:${NC} For hybrid search, re-ranking, query expansion, and code"
echo "generation, use the Streamlit UI (these features are not in CLI)."
echo ""
echo "See QUICK_START.md for feature availability matrix."
echo ""
