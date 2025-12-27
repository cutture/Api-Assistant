# API Integration Assistant - Comprehensive Testing Guide

Version 1.0.0 - Production Testing Workflows

## ⚠️ IMPORTANT: Feature Availability

**Most advanced features are ONLY available in the Streamlit UI, NOT the CLI!**

| Feature | CLI | Streamlit UI |
|---------|-----|--------------|
| Basic Vector Search | ✅ | ✅ |
| **Hybrid Search (Vector + BM25)** | ❌ | ✅ |
| **Cross-encoder Re-ranking** | ❌ | ✅ |
| **Query Expansion** | ❌ | ✅ |
| **Code Generation** | ❌ | ✅ |
| **Advanced AND/OR/NOT Filters** | ❌ | ✅ |
| **Faceted Search** | ❌ | ✅ |
| Simple Filters (method, source) | ✅ | ✅ |
| Diagram Generation | ✅ | ✅ |
| Session Management | ✅ | ✅ |
| Data Export | ✅ | ✅ |
| Interactive Chat | ❌ | ✅ |

**📌 Recommendation**: Use the Streamlit UI for comprehensive testing. See [UI Testing Workflows](#ui-testing-workflows) section.

**🚀 Start UI**: `PYTHONPATH=. streamlit run src/main.py` (Linux/Mac) or `$env:PYTHONPATH = "."; streamlit run src/main.py` (Windows)

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

```bash
# Create a session
python api_assistant_cli.py session create --user "testuser" --ttl 60

# List all sessions
python api_assistant_cli.py session list

# Get session info (replace SESSION_ID with actual ID)
python api_assistant_cli.py session info SESSION_ID --history

# Session statistics
python api_assistant_cli.py session stats

# Extend session expiration
python api_assistant_cli.py session extend SESSION_ID --minutes 30

# Clean up expired sessions
python api_assistant_cli.py session cleanup

# Delete a session
python api_assistant_cli.py session delete SESSION_ID --yes
```

### Workflow 6: Data Export

**Objective**: Export indexed documents and data

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

## ⚠️ Features NOT Available in CLI

The following features can **ONLY** be accessed through the Streamlit UI:

- ❌ **Hybrid Search** (Vector + BM25 with RRF fusion)
- ❌ **Cross-encoder Re-ranking** (Better relevance)
- ❌ **Query Expansion** (Automatic query variations)
- ❌ **Code Generation** (Python, JavaScript, cURL)
- ❌ **Advanced Filtering** (Complex AND/OR/NOT logic)
- ❌ **Faceted Search** (Browse by categories)
- ❌ **Interactive Chat** (Natural language queries)
- ❌ **Visual Analytics** (Charts and statistics)

**📌 To use these features, start the Streamlit UI:**

```bash
# Linux/Mac
PYTHONPATH=. streamlit run src/main.py

# Windows PowerShell
$env:PYTHONPATH = "."; streamlit run src/main.py
```

Then see the [UI Testing Workflows](#ui-testing-workflows) section below for comprehensive testing.


## UI Testing Workflows

### Starting the Streamlit UI

```bash
# Windows PowerShell
$env:PYTHONPATH = "."; streamlit run src/main.py

# Linux/Mac
PYTHONPATH=. streamlit run src/main.py

# Expected: Browser opens at http://localhost:8501
```

### Workflow 1: Document Upload and Indexing (UI)

**Steps**:

1. **Navigate to "📄 Document Manager"** tab
2. **Upload API Specification**:
   - Click "Browse files"
   - Select `test_data/openapi/jsonplaceholder.yaml`
   - Choose format: "OpenAPI/Swagger"
   - Click "Parse and Index"

3. **Verify Indexing**:
   - Check success message: "✓ Successfully indexed 14 documents"
   - See document count update in sidebar

4. **View Indexed Documents**:
   - Scroll to "Indexed Documents" section
   - Filter by API name: "JSONPlaceholder"
   - Review endpoint list

**Expected Result**: All 14 endpoints from JSONPlaceholder API are indexed and searchable

### Workflow 2: Semantic Search (UI)

**Steps**:

1. **Navigate to "🔍 API Search"** tab
2. **Basic Search**:
   - Enter query: "get all posts"
   - Click "Search"
   - Review top 5 results

3. **Hybrid Search**:
   - Enable "Use Hybrid Search" checkbox
   - Search again: "get all posts"
   - Compare results with basic search

4. **Re-ranking**:
   - Enable "Enable Re-ranking" checkbox
   - Search: "create new user"
   - Note improved relevance scores

5. **Query Expansion**:
   - Enable "Enable Query Expansion"
   - Search: "delete item"
   - See expanded query variations in results

**Expected Result**: More relevant results with hybrid search and re-ranking enabled

### Workflow 3: Advanced Filtering (UI)

**Steps**:

1. **Navigate to "🔍 API Search"** tab
2. **Filter by Method**:
   - Expand "Advanced Filters" section
   - Select "Filter by HTTP Method"
   - Choose "POST"
   - Search: "user"
   - See only POST endpoints

3. **Filter by Tag**:
   - Select "Filter by Tag"
   - Enter tag: "Users"
   - Search: "get data"
   - See only User-related endpoints

4. **Combined Filters**:
   - Select both "GET" method and "Posts" tag
   - Search: "retrieve"
   - See only GET endpoints tagged "Posts"

**Expected Result**: Filtered results matching selected criteria

### Workflow 4: Diagram Generation (UI)

**Steps**:

1. **Navigate to "📊 Diagram Generator"** tab
2. **Generate Sequence Diagram**:
   - Select diagram type: "Sequence Diagram"
   - Choose endpoint: "GET /posts"
   - Click "Generate Diagram"
   - View rendered Mermaid diagram

3. **Generate ER Diagram**:
   - Select diagram type: "ER Diagram"
   - Click "Generate Diagram"
   - See all entities and relationships

4. **Generate API Overview**:
   - Select diagram type: "API Overview"
   - Click "Generate Diagram"
   - View high-level API structure

5. **Download Diagram**:
   - Click "Download Mermaid Code"
   - Save `.mmd` file for external use

**Expected Result**: Professional diagrams generated and downloadable

### Workflow 5: Code Generation (UI)

**Steps**:

1. **Navigate to "💻 Code Generator"** tab
2. **Select Endpoint**:
   - Choose API: "JSONPlaceholder API"
   - Choose endpoint: "POST /posts"

3. **Generate Python Code**:
   - Select language: "Python"
   - Select library: "requests"
   - Click "Generate Code"
   - Review generated client code

4. **Generate JavaScript Code**:
   - Select language: "JavaScript"
   - Select library: "axios"
   - Click "Generate Code"
   - Review generated code

5. **Generate cURL**:
   - Select language: "cURL"
   - Click "Generate Code"
   - Copy command to clipboard

**Expected Result**: Working client code ready to use

### Workflow 6: Interactive Chat Agent (UI)

**Steps**:

1. **Navigate to "💬 Chat Assistant"** tab
2. **Basic Question**:
   - Type: "What endpoints are available for managing posts?"
   - Press Enter
   - Review AI response with endpoint list

3. **Complex Query**:
   - Type: "How do I create a new user and then update their information?"
   - Review step-by-step workflow

4. **Code Request**:
   - Type: "Show me Python code to get all posts filtered by user ID 1"
   - Review generated code with explanation

5. **Diagram Request**:
   - Type: "Generate a sequence diagram for creating a post"
   - See inline Mermaid diagram

6. **Session History**:
   - Scroll up to review conversation
   - Click "Export Chat" to save conversation

**Expected Result**: Natural language interaction with API documentation

### Workflow 7: Faceted Navigation (UI)

**Steps**:

1. **Navigate to "📊 Analytics"** tab
2. **View Method Distribution**:
   - See pie chart of HTTP methods
   - Click on "GET" segment
   - Filter results to GET endpoints only

3. **View Tag Distribution**:
   - See bar chart of tags
   - Click on "Users" bar
   - See all User-related endpoints

4. **View API Coverage**:
   - See statistics for each indexed API
   - Compare endpoint counts
   - Review version information

**Expected Result**: Visual analytics and interactive filtering

### Workflow 8: Batch Upload (UI)

**Steps**:

1. **Navigate to "📄 Document Manager"** tab
2. **Upload Multiple Files**:
   - Click "Upload Multiple Files" section
   - Select both:
     - `test_data/openapi/jsonplaceholder.yaml`
     - `test_data/openapi/dummyjson.yaml`
   - Click "Parse All and Index"

3. **Monitor Progress**:
   - Watch progress bar
   - See status for each file
   - Review total documents indexed

4. **View All APIs**:
   - Navigate to "Indexed APIs" section
   - See both APIs listed
   - Review endpoint counts

**Expected Result**: Multiple APIs indexed in one operation

### Workflow 9: Export and Backup (UI)

**Steps**:

1. **Navigate to "⚙️ Settings"** tab
2. **Export All Data**:
   - Click "Export Database"
   - Choose format: "JSON"
   - Click "Download Export"
   - Save file locally

3. **Export Specific API**:
   - Select API: "JSONPlaceholder API"
   - Click "Export Selected API"
   - Choose format: "YAML"
   - Download file

4. **View Export Stats**:
   - See document count
   - See file size
   - Review export timestamp

**Expected Result**: Complete backup of indexed data

### Workflow 10: Session Management (UI)

**Steps**:

1. **Navigate to "👤 Session Manager"** tab
2. **Create Session**:
   - Enter session name: "Product Testing"
   - Click "Create Session"
   - See session ID assigned

3. **Use Session**:
   - Navigate to "🔍 API Search"
   - Search with session active
   - All queries saved to session

4. **View Session History**:
   - Return to "👤 Session Manager"
   - Click "View History" for "Product Testing"
   - See all queries and results

5. **Export Session**:
   - Click "Export Session"
   - Download JSON file with full history

6. **Delete Session**:
   - Click "Delete Session"
   - Confirm deletion

**Expected Result**: Organized testing sessions with full history

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

**UI Test**:

1. Upload `test_data/graphql/countries.graphql`
2. Select format: "GraphQL"
3. Click "Parse and Index"
4. Search for "continent data"
5. See GraphQL types and queries

### Feature 2: Postman Collection Parsing

**CLI Test**:

```bash
# Parse Postman collection
python api_assistant_cli.py parse file test_data/postman/reqres_collection.json --format postman --add

# Search collection
python api_assistant_cli.py search query "list users" --limit 3

# Expected: Postman requests with descriptions
```

**UI Test**:

1. Upload `test_data/postman/reqres_collection.json`
2. Select format: "Postman Collection"
3. Click "Parse and Index"
4. Search for "authentication"
5. See login and register requests

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

**UI Test**:

1. Index both JSONPlaceholder and DummyJSON APIs
2. Search: "retrieve items"
3. See mixed results from both APIs
4. Filter by specific API using dropdown

### Feature 4: Query History and Recommendations

**CLI Test**:

```bash
# Enable session
python api_assistant_cli.py session create --name "test_session"

# Perform multiple searches
python api_assistant_cli.py search query "create user" --session test_session
python api_assistant_cli.py search query "update user" --session test_session
python api_assistant_cli.py search query "delete user" --session test_session

# View history
python api_assistant_cli.py session history --name "test_session"

# Get recommendations
python api_assistant_cli.py recommend --based-on-history --session test_session
```

**UI Test**:

1. Create session in UI
2. Perform 5+ different searches
3. Navigate to "History" tab
4. See query history with timestamps
5. Click "Get Recommendations"
6. See suggested related queries

### Feature 5: Performance Benchmarking

**CLI Test**:

```bash
# Benchmark search performance
python api_assistant_cli.py benchmark search \
  --queries "get users,create post,update user,delete item" \
  --iterations 10

# Expected output:
# Benchmark Results:
# Average query time: 45ms
# Min: 32ms
# Max: 68ms
# Median: 43ms

# Benchmark with different strategies
python api_assistant_cli.py benchmark compare \
  --query "user authentication" \
  --strategies "vector,bm25,hybrid,hybrid+rerank"
```

**UI Test**:

1. Navigate to "⚡ Performance" tab
2. Enter test query: "get all posts"
3. Click "Run Benchmark"
4. See comparison chart:
   - Vector search time
   - BM25 search time
   - Hybrid search time
   - Hybrid + Re-rank time
5. Review relevance scores

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

### Most Common UI Actions

1. **Upload & Index**: Document Manager → Upload → Parse and Index
2. **Search**: API Search → Enter query → Enable hybrid + rerank → Search
3. **Generate Diagram**: Diagram Generator → Select type → Generate
4. **Generate Code**: Code Generator → Select endpoint → Select language → Generate
5. **Chat**: Chat Assistant → Ask questions naturally
6. **Export**: Settings → Export Database → Download

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
