# API Integration Assistant - Comprehensive Testing Guide

Version 1.0.0 - Production Testing Workflows

## ⚠️ IMPORTANT: Feature Availability

**The current Streamlit UI is minimal. Most features are in CLI or backend only!**

| Feature | CLI | Streamlit UI | Backend API |
|---------|-----|--------------|-------------|
| Basic Vector Search | ✅ | ✅ (via chat) | ✅ |
| **Hybrid Search (Vector + BM25)** | ❌ | ❌ | ✅ |
| **Cross-encoder Re-ranking** | ❌ | ❌ | ✅ |
| **Query Expansion** | ❌ | ❌ | ✅ |
| **Code Generation** | ❌ | ✅ (via chat) | ✅ |
| **Advanced AND/OR/NOT Filters** | ❌ | ❌ | ✅ |
| **Faceted Search** | ❌ | ❌ | ✅ |
| Simple Filters (method, source) | ✅ | ❌ | ✅ |
| Diagram Generation | ✅ | ❌ | ✅ |
| Session Management | ✅ | ❌ | ✅ |
| Data Export | ✅ | ❌ | ✅ |
| Interactive Chat | ❌ | ✅ | ✅ |
| File Upload (OpenAPI) | ✅ | ✅ | ✅ |
| File Upload (GraphQL/Postman) | ✅ | ❌ | ✅ |

**📌 Recommendation**:
- **For testing most features**: Use the CLI (see [CLI Testing Workflows](#cli-testing-workflows))
- **For chat/interactive queries**: Use the Streamlit UI (see [UI Testing Workflows](#ui-testing-workflows))
- **For full feature access**: Wait for new Next.js UI (see `docs/UI_REPLACEMENT_PLAN.md`)

**🚀 Start Streamlit UI**:
```bash
# Linux/Mac
PYTHONPATH=. streamlit run src/main.py

# Windows PowerShell
$env:PYTHONPATH = "."; streamlit run src/main.py
```

---

## 🎯 Quick Start Test Suite (Copy-Paste Ready)

### Complete CLI Test Workflow

Run this complete test suite to verify all CLI features in ~10 minutes:

**Bash/Linux/Mac:**
```bash
#!/bin/bash
echo "=== API Assistant CLI Test Suite ==="

# 1. Setup
echo "Step 1: Creating directories..."
mkdir -p test_data/diagrams test_data/exports

# 2. Parse and Index
echo "Step 2: Parsing and indexing APIs..."
python api_assistant_cli.py parse file test_data/openapi/jsonplaceholder.yaml --add
python api_assistant_cli.py parse file test_data/openapi/dummyjson.yaml --add
python api_assistant_cli.py parse file test_data/graphql/countries.graphql --format graphql --add
python api_assistant_cli.py parse file test_data/postman/reqres_collection.json --format postman --add

# 3. Collection Info
echo "Step 3: Checking collection..."
python api_assistant_cli.py collection info

# 4. Search Tests
echo "Step 4: Running search tests..."
echo "  - Basic search:"
python api_assistant_cli.py search query "get all posts" --limit 3

echo "  - Method filter:"
python api_assistant_cli.py search query "user" --method GET --limit 3

echo "  - Source filter:"
python api_assistant_cli.py search query "data" --source openapi --limit 3

echo "  - Combined filters:"
python api_assistant_cli.py search query "posts" --method POST --source openapi --limit 3

# 5. Diagram Generation
echo "Step 5: Generating diagrams..."
python api_assistant_cli.py diagram sequence test_data/openapi/jsonplaceholder.yaml --endpoint "/posts" --output test_data/diagrams/posts_sequence.mmd
python api_assistant_cli.py diagram overview test_data/openapi/jsonplaceholder.yaml --output test_data/diagrams/api_overview.mmd
python api_assistant_cli.py diagram er test_data/graphql/countries.graphql --output test_data/diagrams/countries_er.mmd
python api_assistant_cli.py diagram auth oauth2 --output test_data/diagrams/oauth2_flow.mmd
python api_assistant_cli.py diagram auth apikey --output test_data/diagrams/apikey_flow.mmd

# 6. Session Management
echo "Step 6: Testing session management..."
echo "  - Creating session..."
SESSION_OUTPUT=$(python api_assistant_cli.py session create --user "testuser" --ttl 120)
echo "$SESSION_OUTPUT"
SESSION_ID=$(echo "$SESSION_OUTPUT" | grep "Session ID" | awk '{print $3}')

echo "  - Listing sessions..."
python api_assistant_cli.py session list

echo "  - Session stats..."
python api_assistant_cli.py session stats

if [ ! -z "$SESSION_ID" ]; then
    echo "  - Session info for $SESSION_ID..."
    python api_assistant_cli.py session info $SESSION_ID --history

    echo "  - Extending session..."
    python api_assistant_cli.py session extend $SESSION_ID --minutes 30

    echo "  - Deleting session..."
    python api_assistant_cli.py session delete $SESSION_ID --yes
fi

# 7. Export
echo "Step 7: Exporting data..."
python api_assistant_cli.py export documents test_data/exports/all_docs.json
python api_assistant_cli.py export documents test_data/exports/sample_10.json --limit 10

# 8. Info Commands
echo "Step 8: Checking version and formats..."
python api_assistant_cli.py info version
python api_assistant_cli.py info formats

echo ""
echo "=== Test Suite Complete! ==="
echo "Check results in:"
echo "  - Diagrams: test_data/diagrams/"
echo "  - Exports: test_data/exports/"
```

**PowerShell:**
```powershell
Write-Host "=== API Assistant CLI Test Suite ===" -ForegroundColor Green

# 1. Setup
Write-Host "Step 1: Creating directories..." -ForegroundColor Cyan
New-Item -ItemType Directory -Path test_data/diagrams -Force | Out-Null
New-Item -ItemType Directory -Path test_data/exports -Force | Out-Null

# 2. Parse and Index
Write-Host "Step 2: Parsing and indexing APIs..." -ForegroundColor Cyan
python api_assistant_cli.py parse file test_data/openapi/jsonplaceholder.yaml --add
python api_assistant_cli.py parse file test_data/openapi/dummyjson.yaml --add
python api_assistant_cli.py parse file test_data/graphql/countries.graphql --format graphql --add
python api_assistant_cli.py parse file test_data/postman/reqres_collection.json --format postman --add

# 3. Collection Info
Write-Host "Step 3: Checking collection..." -ForegroundColor Cyan
python api_assistant_cli.py collection info

# 4. Search Tests
Write-Host "Step 4: Running search tests..." -ForegroundColor Cyan
Write-Host "  - Basic search:" -ForegroundColor Yellow
python api_assistant_cli.py search query "get all posts" --limit 3

Write-Host "  - Method filter:" -ForegroundColor Yellow
python api_assistant_cli.py search query "user" --method GET --limit 3

Write-Host "  - Source filter:" -ForegroundColor Yellow
python api_assistant_cli.py search query "data" --source openapi --limit 3

Write-Host "  - Combined filters:" -ForegroundColor Yellow
python api_assistant_cli.py search query "posts" --method POST --source openapi --limit 3

# 5. Diagram Generation
Write-Host "Step 5: Generating diagrams..." -ForegroundColor Cyan
python api_assistant_cli.py diagram sequence test_data/openapi/jsonplaceholder.yaml --endpoint "/posts" --output test_data/diagrams/posts_sequence.mmd
python api_assistant_cli.py diagram overview test_data/openapi/jsonplaceholder.yaml --output test_data/diagrams/api_overview.mmd
python api_assistant_cli.py diagram er test_data/graphql/countries.graphql --output test_data/diagrams/countries_er.mmd
python api_assistant_cli.py diagram auth oauth2 --output test_data/diagrams/oauth2_flow.mmd
python api_assistant_cli.py diagram auth apikey --output test_data/diagrams/apikey_flow.mmd

# 6. Session Management
Write-Host "Step 6: Testing session management..." -ForegroundColor Cyan
Write-Host "  - Creating session..." -ForegroundColor Yellow
$SESSION_OUTPUT = python api_assistant_cli.py session create --user "testuser" --ttl 120
Write-Host $SESSION_OUTPUT

# Extract session ID (parse from output)
$SESSION_ID = ($SESSION_OUTPUT | Select-String -Pattern "Session ID: ([a-f0-9\-]+)" | ForEach-Object { $_.Matches.Groups[1].Value })

Write-Host "  - Listing sessions..." -ForegroundColor Yellow
python api_assistant_cli.py session list

Write-Host "  - Session stats..." -ForegroundColor Yellow
python api_assistant_cli.py session stats

if ($SESSION_ID) {
    Write-Host "  - Session info for $SESSION_ID..." -ForegroundColor Yellow
    python api_assistant_cli.py session info $SESSION_ID --history

    Write-Host "  - Extending session..." -ForegroundColor Yellow
    python api_assistant_cli.py session extend $SESSION_ID --minutes 30

    Write-Host "  - Deleting session..." -ForegroundColor Yellow
    python api_assistant_cli.py session delete $SESSION_ID --yes
}

# 7. Export
Write-Host "Step 7: Exporting data..." -ForegroundColor Cyan
python api_assistant_cli.py export documents test_data/exports/all_docs.json
python api_assistant_cli.py export documents test_data/exports/sample_10.json --limit 10

# 8. Info Commands
Write-Host "Step 8: Checking version and formats..." -ForegroundColor Cyan
python api_assistant_cli.py info version
python api_assistant_cli.py info formats

Write-Host ""
Write-Host "=== Test Suite Complete! ===" -ForegroundColor Green
Write-Host "Check results in:" -ForegroundColor Yellow
Write-Host "  - Diagrams: test_data/diagrams/" -ForegroundColor White
Write-Host "  - Exports: test_data/exports/" -ForegroundColor White
```

**Expected Runtime:** ~10 minutes
**Expected Results:**
- ✅ 50+ endpoints indexed from 4 different sources
- ✅ 5 Mermaid diagrams generated
- ✅ 2 JSON export files created
- ✅ Session created, managed, and deleted
- ✅ All search filters working correctly

**To save as a script:**
- Bash: Save as `test_suite.sh`, run with `chmod +x test_suite.sh && ./test_suite.sh`
- PowerShell: Save as `test_suite.ps1`, run with `.\test_suite.ps1`

---

## Table of Contents

1. [Introduction](#introduction)
2. [Setup and Preparation](#setup-and-preparation)
3. [Sample API Specifications](#sample-api-specifications)
4. [CLI Testing Workflows](#cli-testing-workflows)
5. [UI Testing Workflows](#ui-testing-workflows)
6. [Feature-Specific Testing](#feature-specific-testing)
7. [Advanced Testing Scenarios](#advanced-testing-scenarios)
8. [Troubleshooting](#troubleshooting)

---

## Introduction

This guide provides comprehensive testing workflows for all features implemented in the API Integration Assistant v1.0.0. Each section includes:

- **Sample data** from real public APIs
- **Step-by-step instructions** for both CLI and UI
- **Expected results** for verification
- **Advanced scenarios** for power users

### Features Covered

- ✅ Multi-format parsing (OpenAPI, GraphQL, Postman)
- ✅ Hybrid search (Vector + BM25)
- ✅ Cross-encoder re-ranking
- ✅ Query expansion
- ✅ Mermaid diagram generation
- ✅ Session management
- ✅ Advanced filtering and faceted search
- ✅ Multi-language code generation
- ✅ Batch operations
- ✅ Export capabilities

---

## Setup and Preparation

### 1. Environment Setup

```bash
# Ensure you're in the project directory
cd Api-Assistant

# Activate virtual environment (if using one)
# On Windows:
.venv\Scripts\activate
# On Linux/Mac:
source .venv/bin/activate

# Verify installation
python api_assistant_cli.py info version
```

### 2. Download Sample API Specifications

Create a `test_data` directory for sample files:

```bash
mkdir -p test_data/openapi
mkdir -p test_data/graphql
mkdir -p test_data/postman
```

### 3. Public APIs for Testing

We'll use these public APIs (no authentication required):

| API | Type | URL | Purpose |
|-----|------|-----|---------|
| **JSONPlaceholder** | REST | https://jsonplaceholder.typicode.com | Testing basic CRUD operations |
| **Swagger Petstore** | OpenAPI | https://petstore.swagger.io | OpenAPI 3.0 parsing |
| **ReqRes** | REST | https://reqres.in | User management testing |
| **DummyJSON** | REST | https://dummyjson.com | Rich sample data |
| **RandomUser** | REST | https://randomuser.me | User data generation |
| **Dog CEO** | REST | https://dog.ceo/dog-api | Image API testing |
| **Cat Facts** | REST | https://catfact.ninja | Simple API testing |

---

## Sample API Specifications

### Sample 1: JSONPlaceholder OpenAPI Spec

Create `test_data/openapi/jsonplaceholder.yaml`:

```yaml
openapi: 3.0.0
info:
  title: JSONPlaceholder API
  description: Free fake API for testing and prototyping
  version: 1.0.0
  contact:
    name: JSONPlaceholder
    url: https://jsonplaceholder.typicode.com

servers:
  - url: https://jsonplaceholder.typicode.com
    description: Production server

paths:
  /posts:
    get:
      summary: Get all posts
      description: Retrieve a list of all posts
      operationId: getPosts
      tags:
        - Posts
      parameters:
        - name: userId
          in: query
          description: Filter by user ID
          schema:
            type: integer
        - name: _limit
          in: query
          description: Limit number of results
          schema:
            type: integer
            default: 10
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Post'

    post:
      summary: Create a new post
      description: Add a new post to the collection
      operationId: createPost
      tags:
        - Posts
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PostInput'
      responses:
        '201':
          description: Post created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Post'

  /posts/{id}:
    get:
      summary: Get a specific post
      description: Retrieve a post by its ID
      operationId: getPostById
      tags:
        - Posts
      parameters:
        - name: id
          in: path
          required: true
          description: Post ID
          schema:
            type: integer
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Post'
        '404':
          description: Post not found

    put:
      summary: Update a post
      description: Update an existing post
      operationId: updatePost
      tags:
        - Posts
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PostInput'
      responses:
        '200':
          description: Post updated successfully

    delete:
      summary: Delete a post
      description: Remove a post from the collection
      operationId: deletePost
      tags:
        - Posts
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: Post deleted successfully

  /users:
    get:
      summary: Get all users
      description: Retrieve a list of all users
      operationId: getUsers
      tags:
        - Users
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/User'

  /users/{id}:
    get:
      summary: Get a specific user
      description: Retrieve a user by their ID
      operationId: getUserById
      tags:
        - Users
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'

  /comments:
    get:
      summary: Get all comments
      description: Retrieve a list of all comments
      operationId: getComments
      tags:
        - Comments
      parameters:
        - name: postId
          in: query
          description: Filter by post ID
          schema:
            type: integer
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Comment'

components:
  schemas:
    Post:
      type: object
      properties:
        id:
          type: integer
          description: Post ID
        userId:
          type: integer
          description: ID of the user who created the post
        title:
          type: string
          description: Post title
        body:
          type: string
          description: Post content
      required:
        - userId
        - title
        - body

    PostInput:
      type: object
      properties:
        userId:
          type: integer
          description: ID of the user creating the post
        title:
          type: string
          description: Post title
        body:
          type: string
          description: Post content
      required:
        - userId
        - title
        - body

    User:
      type: object
      properties:
        id:
          type: integer
        name:
          type: string
        username:
          type: string
        email:
          type: string
          format: email
        address:
          $ref: '#/components/schemas/Address'
        phone:
          type: string
        website:
          type: string
        company:
          $ref: '#/components/schemas/Company'

    Address:
      type: object
      properties:
        street:
          type: string
        suite:
          type: string
        city:
          type: string
        zipcode:
          type: string
        geo:
          $ref: '#/components/schemas/Geo'

    Geo:
      type: object
      properties:
        lat:
          type: string
        lng:
          type: string

    Company:
      type: object
      properties:
        name:
          type: string
        catchPhrase:
          type: string
        bs:
          type: string

    Comment:
      type: object
      properties:
        id:
          type: integer
        postId:
          type: integer
        name:
          type: string
        email:
          type: string
          format: email
        body:
          type: string
```

### Sample 2: DummyJSON Products API

Create `test_data/openapi/dummyjson.yaml`:

```yaml
openapi: 3.0.0
info:
  title: DummyJSON Products API
  description: Fake REST API for product data
  version: 1.0.0

servers:
  - url: https://dummyjson.com
    description: Production server

paths:
  /products:
    get:
      summary: Get all products
      description: Retrieve a paginated list of products
      operationId: getProducts
      tags:
        - Products
      parameters:
        - name: limit
          in: query
          schema:
            type: integer
            default: 30
        - name: skip
          in: query
          schema:
            type: integer
            default: 0
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                type: object
                properties:
                  products:
                    type: array
                    items:
                      $ref: '#/components/schemas/Product'
                  total:
                    type: integer
                  skip:
                    type: integer
                  limit:
                    type: integer

  /products/{id}:
    get:
      summary: Get a single product
      operationId: getProductById
      tags:
        - Products
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Product'

  /products/search:
    get:
      summary: Search products
      operationId: searchProducts
      tags:
        - Products
      parameters:
        - name: q
          in: query
          required: true
          description: Search query
          schema:
            type: string
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                type: object
                properties:
                  products:
                    type: array
                    items:
                      $ref: '#/components/schemas/Product'

  /products/category/{category}:
    get:
      summary: Get products by category
      operationId: getProductsByCategory
      tags:
        - Products
      parameters:
        - name: category
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                type: object
                properties:
                  products:
                    type: array
                    items:
                      $ref: '#/components/schemas/Product'

components:
  schemas:
    Product:
      type: object
      properties:
        id:
          type: integer
        title:
          type: string
        description:
          type: string
        price:
          type: number
          format: float
        discountPercentage:
          type: number
          format: float
        rating:
          type: number
          format: float
        stock:
          type: integer
        brand:
          type: string
        category:
          type: string
        thumbnail:
          type: string
        images:
          type: array
          items:
            type: string
```

### Sample 3: GraphQL Schema

Create `test_data/graphql/countries.graphql`:

```graphql
"""
Countries GraphQL API
"""
type Query {
  """
  Get all countries
  """
  countries(filter: CountryFilterInput): [Country!]!

  """
  Get a specific country by code
  """
  country(code: ID!): Country

  """
  Get all continents
  """
  continents(filter: ContinentFilterInput): [Continent!]!

  """
  Get a specific continent by code
  """
  continent(code: ID!): Continent

  """
  Get all languages
  """
  languages(filter: LanguageFilterInput): [Language!]!

  """
  Get a specific language by code
  """
  language(code: ID!): Language
}

"""
Country filter options
"""
input CountryFilterInput {
  code: StringQueryOperatorInput
  currency: StringQueryOperatorInput
  continent: StringQueryOperatorInput
}

"""
Continent filter options
"""
input ContinentFilterInput {
  code: StringQueryOperatorInput
}

"""
Language filter options
"""
input LanguageFilterInput {
  code: StringQueryOperatorInput
}

"""
String query operators
"""
input StringQueryOperatorInput {
  eq: String
  ne: String
  in: [String]
  nin: [String]
  regex: String
  glob: String
}

"""
Country information
"""
type Country {
  code: ID!
  name: String!
  native: String!
  phone: String!
  continent: Continent!
  capital: String
  currency: String
  languages: [Language!]!
  emoji: String!
  emojiU: String!
  states: [State!]!
}

"""
Continent information
"""
type Continent {
  code: ID!
  name: String!
  countries: [Country!]!
}

"""
Language information
"""
type Language {
  code: ID!
  name: String
  native: String
  rtl: Boolean!
}

"""
State information
"""
type State {
  code: String
  name: String!
  country: Country!
}
```

### Sample 4: Postman Collection

Create `test_data/postman/reqres_collection.json`:

```json
{
  "info": {
    "name": "ReqRes API Collection",
    "description": "User management API testing collection",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Users",
      "item": [
        {
          "name": "List Users",
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "https://reqres.in/api/users?page=2",
              "protocol": "https",
              "host": ["reqres", "in"],
              "path": ["api", "users"],
              "query": [
                {
                  "key": "page",
                  "value": "2"
                }
              ]
            },
            "description": "Get a paginated list of users"
          },
          "response": []
        },
        {
          "name": "Single User",
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "https://reqres.in/api/users/2",
              "protocol": "https",
              "host": ["reqres", "in"],
              "path": ["api", "users", "2"]
            },
            "description": "Get a single user by ID"
          },
          "response": []
        },
        {
          "name": "Create User",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "value": "application/json"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n    \"name\": \"morpheus\",\n    \"job\": \"leader\"\n}"
            },
            "url": {
              "raw": "https://reqres.in/api/users",
              "protocol": "https",
              "host": ["reqres", "in"],
              "path": ["api", "users"]
            },
            "description": "Create a new user"
          },
          "response": []
        },
        {
          "name": "Update User",
          "request": {
            "method": "PUT",
            "header": [
              {
                "key": "Content-Type",
                "value": "application/json"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n    \"name\": \"morpheus\",\n    \"job\": \"zion resident\"\n}"
            },
            "url": {
              "raw": "https://reqres.in/api/users/2",
              "protocol": "https",
              "host": ["reqres", "in"],
              "path": ["api", "users", "2"]
            },
            "description": "Update an existing user"
          },
          "response": []
        },
        {
          "name": "Delete User",
          "request": {
            "method": "DELETE",
            "header": [],
            "url": {
              "raw": "https://reqres.in/api/users/2",
              "protocol": "https",
              "host": ["reqres", "in"],
              "path": ["api", "users", "2"]
            },
            "description": "Delete a user"
          },
          "response": []
        }
      ]
    },
    {
      "name": "Authentication",
      "item": [
        {
          "name": "Register Successful",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "value": "application/json"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n    \"email\": \"eve.holt@reqres.in\",\n    \"password\": \"pistol\"\n}"
            },
            "url": {
              "raw": "https://reqres.in/api/register",
              "protocol": "https",
              "host": ["reqres", "in"],
              "path": ["api", "register"]
            },
            "description": "Register a new user"
          },
          "response": []
        },
        {
          "name": "Login Successful",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "value": "application/json"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n    \"email\": \"eve.holt@reqres.in\",\n    \"password\": \"cityslicka\"\n}"
            },
            "url": {
              "raw": "https://reqres.in/api/login",
              "protocol": "https",
              "host": ["reqres", "in"],
              "path": ["api", "login"]
            },
            "description": "Login with credentials"
          },
          "response": []
        }
      ]
    }
  ]
}
```

---

## CLI Testing Workflows

> **⚠️ IMPORTANT**: The CLI has LIMITED features. For hybrid search, re-ranking, query expansion, code generation, and advanced filtering, use the [Streamlit UI](#ui-testing-workflows).
>
> **Start UI**: `PYTHONPATH=. streamlit run src/main.py`

### Workflow 1: Parse and Index API Specifications

**Objective**: Parse API specs and add them to the vector store

```bash
# Parse OpenAPI specification
python api_assistant_cli.py parse file test_data/openapi/jsonplaceholder.yaml --add

# Parse GraphQL schema
python api_assistant_cli.py parse file test_data/graphql/countries.graphql --format graphql --add

# Parse Postman collection
python api_assistant_cli.py parse file test_data/postman/reqres_collection.json --format postman --add

# View collection info
python api_assistant_cli.py collection info
```

### Workflow 2: Basic Vector Search

**Objective**: Search indexed APIs using vector similarity

```bash
# Basic search
python api_assistant_cli.py search query "get all posts" --limit 5

# Search with result limit
python api_assistant_cli.py search query "create user" --limit 3

# Hide content, show only metadata
python api_assistant_cli.py search query "update data" --no-content --limit 5
```

### Workflow 3: Simple Filtering

**Objective**: Filter search results by method or source

```bash
# Filter by HTTP method
python api_assistant_cli.py search query "posts" --method GET --limit 5

# Filter by source type
python api_assistant_cli.py search query "user" --source openapi --limit 3

# Combined filters
python api_assistant_cli.py search query "data" --method POST --source openapi --limit 5
```

**Note**: For complex AND/OR/NOT filters, use the Streamlit UI.

### Workflow 4: Diagram Generation

**Objective**: Generate Mermaid diagrams from API specs

> **⚠️ PowerShell Users**: Use backtick `` ` `` for line continuation (not backslash `\`), or use single-line commands

**First, create the output directory:**

**PowerShell:**
```powershell
New-Item -ItemType Directory -Path test_data/diagrams -Force
```

**Bash/Linux/Mac:**
```bash
mkdir -p test_data/diagrams
```

**Now generate diagrams:**

**Bash/Linux/Mac:**
```bash
# Sequence diagram (requires file path)
python api_assistant_cli.py diagram sequence test_data/openapi/jsonplaceholder.yaml \
  --endpoint "/posts" \
  --output test_data/diagrams/posts_sequence.mmd

# ER diagram (GraphQL only)
python api_assistant_cli.py diagram er test_data/graphql/countries.graphql \
  --output test_data/diagrams/countries_er.mmd

# API overview flowchart (OpenAPI only)
python api_assistant_cli.py diagram overview test_data/openapi/jsonplaceholder.yaml \
  --output test_data/diagrams/api_overview.mmd

# Authentication flow
python api_assistant_cli.py diagram auth oauth2 \
  --output test_data/diagrams/oauth2_flow.mmd
```

**PowerShell:**
```powershell
# Sequence diagram - use backticks for line continuation
python api_assistant_cli.py diagram sequence test_data/openapi/jsonplaceholder.yaml `
  --endpoint "/posts" `
  --output test_data/diagrams/posts_sequence.mmd

# OR as single line (easier in PowerShell):
python api_assistant_cli.py diagram sequence test_data/openapi/jsonplaceholder.yaml --endpoint "/posts" --output test_data/diagrams/posts_sequence.mmd

# ER diagram
python api_assistant_cli.py diagram er test_data/graphql/countries.graphql --output test_data/diagrams/countries_er.mmd

# API overview
python api_assistant_cli.py diagram overview test_data/openapi/jsonplaceholder.yaml --output test_data/diagrams/api_overview.mmd

# Authentication flows
python api_assistant_cli.py diagram auth oauth2 --output test_data/diagrams/oauth2_flow.mmd
python api_assistant_cli.py diagram auth apikey --output test_data/diagrams/apikey_flow.mmd
python api_assistant_cli.py diagram auth bearer --output test_data/diagrams/bearer_flow.mmd
```

### Workflow 5: Session Management

**Objective**: Create and manage user sessions

> **⚠️ CRITICAL**: Session IDs are unique UUIDs. You MUST copy the actual ID from the create command output!

**Basic Commands (No Session ID Required):**
```bash
# Create a new session
python api_assistant_cli.py session create --user "testuser" --ttl 60

# List all sessions
python api_assistant_cli.py session list

# Session statistics
python api_assistant_cli.py session stats

# Clean up expired sessions
python api_assistant_cli.py session cleanup
```

**Commands Requiring Session ID:**

**Bash/Linux/Mac - Automated Method (Recommended):**
```bash
# Create session and capture ID automatically
SESSION_OUTPUT=$(python api_assistant_cli.py session create --user "testuser" --ttl 60)
echo "$SESSION_OUTPUT"
SESSION_ID=$(echo "$SESSION_OUTPUT" | grep "Session ID" | awk '{print $3}')

# Verify ID was captured
echo "Captured Session ID: $SESSION_ID"

# Use the session
python api_assistant_cli.py session info $SESSION_ID --history
python api_assistant_cli.py session extend $SESSION_ID --minutes 30
python api_assistant_cli.py session delete $SESSION_ID --yes
```

**PowerShell - Automated Method (Recommended):**
```powershell
# Create session and capture ID automatically
$OUTPUT = python api_assistant_cli.py session create --user "testuser" --ttl 60
Write-Host $OUTPUT

# Extract session ID using regex
$SESSION_ID = ($OUTPUT | Select-String -Pattern "Session ID:\s+([a-f0-9\-]+)").Matches.Groups[1].Value

# Verify ID was captured
Write-Host "Captured Session ID: $SESSION_ID" -ForegroundColor Green

# Use the session
python api_assistant_cli.py session info $SESSION_ID --history
python api_assistant_cli.py session extend $SESSION_ID --minutes 30
python api_assistant_cli.py session delete $SESSION_ID --yes
```

**Manual Method (if automated extraction fails):**
```powershell
# 1. Create session and look for the Session ID in output
python api_assistant_cli.py session create --user "testuser" --ttl 60
# Example output: Session ID: dc34ec44-44e5-42ca-9a78-d955e229db72

# 2. Copy that exact ID and set the variable
$SESSION_ID = "dc34ec44-44e5-42ca-9a78-d955e229db72"  # Use YOUR actual ID!

# 3. Now use it
python api_assistant_cli.py session info $SESSION_ID --history
python api_assistant_cli.py session extend $SESSION_ID --minutes 30
python api_assistant_cli.py session delete $SESSION_ID --yes
```

### Workflow 6: Data Export

**Objective**: Export indexed documents and data

**First, create the output directory:**

**PowerShell:**
```powershell
New-Item -ItemType Directory -Path test_data/exports -Force
```

**Bash/Linux/Mac:**
```bash
mkdir -p test_data/exports
```

**Now export data:**

```bash
# Export all documents
python api_assistant_cli.py export documents test_data/exports/all_docs.json

# Export with limit
python api_assistant_cli.py export documents test_data/exports/sample.json --limit 20
```

### Workflow 7: Collection Management

**Objective**: Manage the vector store collection

```bash
# View collection information
python api_assistant_cli.py collection info

# Clear all documents (CAUTION!)
python api_assistant_cli.py collection clear --yes
```

### CLI Quick Reference

```bash
# Most common commands
python api_assistant_cli.py parse file <path> --add          # Index API
python api_assistant_cli.py search query "<text>" --limit 5  # Search
python api_assistant_cli.py collection info                  # View stats
python api_assistant_cli.py info version                     # Version info
python api_assistant_cli.py info formats                     # Supported formats
```

---

## ⚠️ IMPORTANT: Current UI Limitations

**The current Streamlit UI is minimal and does NOT include most advanced features.**

**Currently Available in Streamlit UI:**
- ✅ **File Upload** (OpenAPI/Swagger only, via sidebar)
- ✅ **Interactive Chat** (Natural language queries)
- ✅ **Code Generation** (via chat responses)
- ✅ **Basic Settings** (Model selection, temperature)

**NOT Available in Current UI (Backend Implemented, No Frontend):**
- ❌ **Hybrid Search Toggle** (uses vector search only)
- ❌ **Cross-encoder Re-ranking Toggle**
- ❌ **Query Expansion Toggle**
- ❌ **Advanced Filtering UI** (method/source filters)
- ❌ **Faceted Search Interface**
- ❌ **GraphQL/Postman Upload** (backend supports, UI doesn't)
- ❌ **Session Management UI**
- ❌ **Diagram Generation UI**
- ❌ **Search Interface** (only chat available)
- ❌ **Document Management** (view/delete indexed docs)

**📌 To use the current Streamlit UI:**

```bash
# Linux/Mac
PYTHONPATH=. streamlit run src/main.py

# Windows PowerShell
$env:PYTHONPATH = "."; streamlit run src/main.py
```

**⚠️ Note:** A new Next.js UI is being developed to expose all backend features. See `docs/UI_REPLACEMENT_PLAN.md` for details.


## UI Testing Workflows (Current Streamlit UI)

> **⚠️ DISCLAIMER:** These workflows describe the CURRENT minimal Streamlit UI.
> A new Next.js UI with full feature parity is under development.
> See `docs/UI_REPLACEMENT_PLAN.md` for details.

### Starting the Streamlit UI

```bash
# Windows PowerShell
$env:PYTHONPATH = "."; streamlit run src/main.py

# Linux/Mac
PYTHONPATH=. streamlit run src/main.py

# Expected: Browser opens at http://localhost:8501
```

### Workflow 1: Document Upload and Chat (Current UI)

**What You'll See:**
- Single page with chat interface (main area)
- Sidebar with settings and file upload
- No tabs or separate pages

**Steps**:

1. **Upload API Specification** (Sidebar):
   - In sidebar, find "📄 API Documentation" section
   - Click "Browse files" or drag & drop
   - Select `test_data/openapi/jsonplaceholder.yaml`
   - Click "🔄 Process Files" button

2. **Verify Upload**:
   - Wait for processing progress bar
   - Check success message: "✅ Processed jsonplaceholder.yaml: 8 endpoints"
   - Check final message: "🎉 Processing complete! Added 8 endpoints to the knowledge base."
   - See "Documents Indexed" metric in sidebar update

3. **Upload Additional Files** (Optional):
   - Repeat upload process for `test_data/openapi/dummyjson.yaml`
   - Each file processes independently
   - Document count increments with each upload

4. **Ask Questions via Chat**:
   - In main area, see "📚 **X documents** indexed and ready for questions!"
   - Click example questions on the right, OR
   - Type your own question in chat input at bottom
   - Examples:
     - "What endpoints are available?"
     - "How do I authenticate?"
     - "Generate code to call the /users endpoint"

5. **View Chat Response**:
   - AI responds with relevant information from indexed APIs
   - Code blocks with syntax highlighting
   - Copy button for code snippets

**Expected Result**:
- Files uploaded and processed successfully
- Document count shows total indexed documents
- Chat provides intelligent answers about your APIs
- Code generation works via chat

**Limitations** (Features NOT in current UI):
- ❌ Cannot view list of indexed documents
- ❌ Cannot delete individual documents (use CLI: `collection clear`)
- ❌ Cannot toggle search modes or advanced features
- ❌ Cannot upload GraphQL/Postman (UI only shows OpenAPI/Swagger)
- ❌ No filtering, faceted search, or session management UI

### Additional Features (Use CLI or Await New UI)

The current Streamlit UI does not provide interfaces for the following features. Please use the CLI workflows described earlier in this guide:

**Features Available via CLI Only:**
- ✅ **Advanced Search** - Use CLI `search` command with `--method`, `--source` filters
- ✅ **Diagram Generation** - Use CLI `diagram` command for sequence/ER/overview/auth diagrams
- ✅ **Session Management** - Use CLI `session` commands for create/list/stats/delete
- ✅ **Data Export** - Use CLI `export` command
- ✅ **GraphQL/Postman Upload** - Use CLI `parse` command with `--format` flag
- ✅ **Collection Management** - Use CLI `collection` commands

**Features Not Currently Available (Backend Implemented, Awaiting UI):**
- ⏳ **Hybrid Search Toggle** - Backend ready, no UI controls
- ⏳ **Re-ranking Toggle** - Backend ready, no UI controls
- ⏳ **Query Expansion** - Backend ready, no UI controls
- ⏳ **Advanced AND/OR/NOT Filtering** - Backend ready, no UI builder
- ⏳ **Faceted Search** - Backend ready, no UI interface
- ⏳ **Visual Analytics** - Backend ready, no dashboard

**📢 Coming Soon:**
A new Next.js UI is under development to expose all backend features with a modern, professional interface.

**Progress:** See `docs/UI_REPLACEMENT_PLAN.md` for full implementation plan and timeline.

**For now:** Use the [CLI Testing Workflows](#cli-testing-workflows) section above to access all advanced features through the command line.

---

## Feature-Specific Testing

### Feature 1: GraphQL Schema Parsing

**CLI Test**:

```bash
# Parse GraphQL schema
python api_assistant_cli.py parse file test_data/graphql/countries.graphql --format graphql --add

# Search GraphQL types
python api_assistant_cli.py search query "country information" --limit 3

# Expected: Country type and queries
```

**UI Support**: ❌ Current Streamlit UI does not support GraphQL uploads. Use CLI only.

### Feature 2: Postman Collection Parsing

**CLI Test**:

```bash
# Parse Postman collection
python api_assistant_cli.py parse file test_data/postman/reqres_collection.json --format postman --add

# Search collection
python api_assistant_cli.py search query "list users" --limit 3

# Expected: Postman requests with descriptions
```

**UI Support**: ❌ Current Streamlit UI does not support Postman uploads. Use CLI only.

### Feature 3: Multi-API Search

**CLI Test**:

```bash
# Index multiple APIs
python api_assistant_cli.py parse file test_data/openapi/jsonplaceholder.yaml --add
python api_assistant_cli.py parse file test_data/openapi/dummyjson.yaml --add

# Search across all APIs
python api_assistant_cli.py search query "get products or posts" --limit 5

# Expected: Results from both APIs
```

**UI Test** (Limited):

1. Upload `jsonplaceholder.yaml` via sidebar → Process Files
2. Upload `dummyjson.yaml` via sidebar → Process Files
3. Use chat to ask: "What endpoints are available?"
4. See combined results from both APIs in chat response

**Note**: Current UI has no filtering dropdown. Use CLI for filtered searches.

### Feature 4: Session Management and History

**CLI Test**:

```bash
# Create session
python api_assistant_cli.py session create --user "testuser" --ttl 60

# List sessions
python api_assistant_cli.py session list

# View session stats
python api_assistant_cli.py session stats

# Session info with history
python api_assistant_cli.py session info <SESSION_ID> --history
```

**UI Support**: ❌ Current Streamlit UI does not have session management UI. Use CLI only.

### Feature 5: Advanced Search Features

**Hybrid Search, Re-ranking, and Query Expansion**:

**Backend Status**: ✅ Fully implemented in FastAPI backend
**CLI Support**: ❌ Not available in CLI (search is basic vector only)
**UI Support**: ❌ Not available in current Streamlit UI (no toggles or controls)

**To test these features**: Wait for the new Next.js UI (see `docs/UI_REPLACEMENT_PLAN.md`) or directly test the FastAPI backend:

```bash
# Test backend directly with curl/httpx
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "user authentication",
    "use_hybrid": true,
    "use_reranking": true,
    "use_query_expansion": true,
    "n_results": 5
  }'
```

---

## Advanced Testing Scenarios

### Scenario 1: Complete API Integration Workflow

**Objective**: Simulate real-world API integration project

**Steps**:

1. **Discovery Phase**:
   ```bash
   # Index new API
   python api_assistant_cli.py parse file test_data/openapi/jsonplaceholder.yaml --add

   # Explore available endpoints
   python api_assistant_cli.py search query "available endpoints" --limit 20

   # Get API overview
   python api_assistant_cli.py info stats
   ```

2. **Design Phase**:
   ```bash
   # Generate ER diagram
   python api_assistant_cli.py diagram generate er --output design/data_model.mmd

   # Generate API overview
   python api_assistant_cli.py diagram generate overview --output design/api_structure.mmd
   ```

3. **Implementation Phase**:
   ```bash
   # Generate client code for all CRUD operations
   python api_assistant_cli.py generate code --endpoint "/posts" --method GET --language python --output src/clients/get_posts.py
   python api_assistant_cli.py generate code --endpoint "/posts" --method POST --language python --output src/clients/create_post.py
   python api_assistant_cli.py generate code --endpoint "/posts/{id}" --method PUT --language python --output src/clients/update_post.py
   python api_assistant_cli.py generate code --endpoint "/posts/{id}" --method DELETE --language python --output src/clients/delete_post.py
   ```

4. **Documentation Phase**:
   ```bash
   # Export complete API documentation
   python api_assistant_cli.py batch export --format markdown --output docs/api_reference.md

   # Generate sequence diagrams for key workflows
   python api_assistant_cli.py diagram generate sequence --endpoint "/posts" --method POST --output docs/create_post_flow.mmd
   ```

5. **Testing Phase**:
   ```bash
   # Create test session
   python api_assistant_cli.py session create --name "integration_test"

   # Test each endpoint
   python api_assistant_cli.py search query "create post endpoint" --session integration_test
   # ... execute actual API calls ...

   # Export test results
   python api_assistant_cli.py session export --name "integration_test" --output test_results.json
   ```

### Scenario 2: Multi-API Comparison

**Objective**: Compare similar endpoints across different APIs

**Steps**:

1. **Index competing APIs**:
   ```bash
   python api_assistant_cli.py parse file test_data/openapi/jsonplaceholder.yaml --add
   python api_assistant_cli.py parse file test_data/openapi/dummyjson.yaml --add
   ```

2. **Compare user endpoints**:
   ```bash
   # Search for user endpoints in all APIs
   python api_assistant_cli.py search query "get user by id" --limit 10

   # Filter by specific API
   python api_assistant_cli.py search query "user" --filter '{"operator": "and", "filters": [{"field": "api_name", "operator": "eq", "value": "JSONPlaceholder API"}]}'
   ```

3. **Compare features**:
   ```bash
   # List all unique tags
   python api_assistant_cli.py search facets --field tags

   # Compare endpoint counts
   python api_assistant_cli.py info list-apis
   ```

4. **Generate comparison report**:
   ```bash
   # Export both APIs for side-by-side comparison
   python api_assistant_cli.py batch export --format json --output comparison_report.json
   ```

### Scenario 3: Incremental API Updates

**Objective**: Update API documentation as it evolves

**Steps**:

1. **Initial index**:
   ```bash
   python api_assistant_cli.py parse file test_data/openapi/api_v1.yaml --add
   python api_assistant_cli.py info stats
   # Note: 20 documents indexed
   ```

2. **Update API spec** (simulate API version 2):
   - Add new endpoints to spec file
   - Modify existing endpoints

3. **Re-index with updates**:
   ```bash
   # Clear old version
   python api_assistant_cli.py database clear --confirm

   # Index new version
   python api_assistant_cli.py parse file test_data/openapi/api_v2.yaml --add
   python api_assistant_cli.py info stats
   # Note: 25 documents indexed (5 new endpoints)
   ```

4. **Compare versions**:
   ```bash
   # Search for new features
   python api_assistant_cli.py search query "new endpoints" --limit 5
   ```

### Scenario 4: Team Collaboration

**Objective**: Share indexed APIs across team

**Steps**:

1. **Developer 1: Index APIs**:
   ```bash
   python api_assistant_cli.py parse file test_data/openapi/jsonplaceholder.yaml --add
   python api_assistant_cli.py batch export --format json --output shared_apis.json
   ```

2. **Developer 2: Import shared data**:
   ```bash
   # Import exported data
   python api_assistant_cli.py database import --file shared_apis.json

   # Verify import
   python api_assistant_cli.py info list-apis
   ```

3. **Developer 3: Add more APIs**:
   ```bash
   # Import base data
   python api_assistant_cli.py database import --file shared_apis.json

   # Add additional APIs
   python api_assistant_cli.py parse file test_data/openapi/dummyjson.yaml --add

   # Export updated collection
   python api_assistant_cli.py batch export --format json --output shared_apis_v2.json
   ```

### Scenario 5: Performance Optimization

**Objective**: Optimize search performance for large API collections

**Steps**:

1. **Baseline measurement**:
   ```bash
   # Index sample APIs
   python api_assistant_cli.py batch parse --file-list batch_files.txt --add

   # Benchmark baseline
   python api_assistant_cli.py benchmark search --query "user authentication" --iterations 50
   ```

2. **Test different strategies**:
   ```bash
   # Vector only
   python api_assistant_cli.py search query "user authentication" --no-hybrid

   # Hybrid
   python api_assistant_cli.py search query "user authentication" --hybrid

   # Hybrid + Re-rank
   python api_assistant_cli.py search query "user authentication" --hybrid --rerank

   # With query expansion
   python api_assistant_cli.py search query "user authentication" --hybrid --rerank --expand
   ```

3. **Analyze results**:
   ```bash
   # Export benchmark results
   python api_assistant_cli.py benchmark export --output performance_report.json
   ```

---

## Troubleshooting

### Issue 1: "No documents found" after indexing

**Symptoms**: Search returns no results despite successful indexing

**Solution**:
```bash
# Check if documents are actually indexed
python api_assistant_cli.py info stats

# Verify database location
ls -la ./data/chroma_db/

# Re-index if needed
python api_assistant_cli.py database clear --confirm
python api_assistant_cli.py parse file test_data/openapi/jsonplaceholder.yaml --add
```

### Issue 2: Slow search performance

**Symptoms**: Searches take >2 seconds

**Solutions**:

1. **Disable re-ranking for faster results**:
   ```bash
   python api_assistant_cli.py search query "user" --no-rerank
   ```

2. **Reduce result limit**:
   ```bash
   python api_assistant_cli.py search query "user" --limit 5
   ```

3. **Use simpler search strategies**:
   ```bash
   # Vector only (fastest)
   python api_assistant_cli.py search query "user" --no-hybrid
   ```

### Issue 3: Diagram generation fails

**Symptoms**: Mermaid diagrams don't render

**Solutions**:

1. **Verify endpoint exists**:
   ```bash
   python api_assistant_cli.py search query "exact endpoint path" --limit 1
   ```

2. **Check diagram syntax**:
   ```bash
   # Generate and save to file
   python api_assistant_cli.py diagram generate sequence --endpoint "/posts" --method GET --output test.mmd

   # Validate with Mermaid Live Editor: https://mermaid.live
   ```

### Issue 4: Import/Export errors

**Symptoms**: Cannot import previously exported data

**Solutions**:

1. **Verify file format**:
   ```bash
   # Check JSON structure
   cat exported_data.json | head -n 20
   ```

2. **Clear database before import**:
   ```bash
   python api_assistant_cli.py database clear --confirm
   python api_assistant_cli.py database import --file exported_data.json
   ```

### Issue 5: Session not persisting

**Symptoms**: Session history lost between runs

**Solutions**:

1. **Use explicit session names**:
   ```bash
   python api_assistant_cli.py session create --name "my_session"
   python api_assistant_cli.py search query "test" --session "my_session" --save-history
   ```

2. **Export sessions regularly**:
   ```bash
   python api_assistant_cli.py session export --name "my_session" --output session_backup.json
   ```

### Issue 6: UI not starting

**Symptoms**: Streamlit won't launch

**Solutions**:

1. **Check Python path**:
   ```bash
   # Windows
   $env:PYTHONPATH = "."; python -m streamlit run src/main.py

   # Linux/Mac
   PYTHONPATH=. python -m streamlit run src/main.py
   ```

2. **Verify dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Check port availability**:
   ```bash
   # Use different port
   PYTHONPATH=. streamlit run src/main.py --server.port 8502
   ```

---

## Quick Reference

### Most Common CLI Commands

```bash
# Parse and index
python api_assistant_cli.py parse file <file> --add

# Search
python api_assistant_cli.py search query "<query>" --hybrid --rerank --limit 5

# Generate diagram
python api_assistant_cli.py diagram generate <type> --output <file>

# Generate code
python api_assistant_cli.py generate code --endpoint "<path>" --method <method> --language <lang>

# View stats
python api_assistant_cli.py info stats

# Create session
python api_assistant_cli.py session create --name "<name>"

# Export all
python api_assistant_cli.py batch export --format json --output <file>
```

### Most Common UI Actions (Current Streamlit UI)

1. **Upload & Index**: Sidebar → 📄 API Documentation → Upload files → 🔄 Process Files
2. **Chat**: Main area → Type question in chat input → Get AI response
3. **Settings**: Sidebar → Adjust model, temperature, max tokens
4. **Clear Data**: Sidebar → 🗑️ Clear button → Confirms and clears session state
5. **Refresh**: Sidebar → 🔍 Refresh button → Reloads the UI

**Note**: Advanced features (Search UI, Diagram Generator, Code Generator, Export) are not available in current UI. Use CLI or wait for new Next.js UI.

---

## Next Steps

After completing these testing workflows:

1. **✅ Verify All Features Work**: Check off each feature as you test it
2. **📝 Document Issues**: Note any bugs or unexpected behavior
3. **💡 Provide Feedback**: Share improvement suggestions
4. **🚀 Real-World Testing**: Try with your actual API specifications
5. **📊 Performance Tuning**: Optimize based on your use case

---

## Additional Resources

- **Mermaid Live Editor**: https://mermaid.live (for viewing diagrams)
- **Public API Lists**:
  - https://github.com/public-apis/public-apis
  - https://rapidapi.com/collection/list-of-free-apis
- **OpenAPI Examples**: https://github.com/OAI/OpenAPI-Specification/tree/main/examples
- **GraphQL Schemas**: https://github.com/APIs-guru/graphql-apis

---

**Happy Testing! 🎉**

For questions or issues, please refer to the main README.md or create an issue on GitHub.
