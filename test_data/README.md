# Test Data Directory

This directory contains sample API specifications and test data for the API Integration Assistant.

## Directory Structure

```
test_data/
├── openapi/          # OpenAPI/Swagger specifications
│   ├── jsonplaceholder.yaml
│   └── dummyjson.yaml
├── graphql/          # GraphQL schemas
│   └── countries.graphql
├── postman/          # Postman collections
│   └── reqres_collection.json
├── diagrams/         # Generated Mermaid diagrams (output)
├── clients/          # Generated client code (output)
├── exports/          # Exported data (output)
└── sessions/         # Session exports (output)
```

## Sample APIs Included

### 1. JSONPlaceholder API (OpenAPI)
**File**: `openapi/jsonplaceholder.yaml`

A fake REST API for testing and prototyping with:
- **6 endpoints** for posts, users, and comments
- **CRUD operations** for posts
- **Nested schemas** (User, Address, Company)

**Usage**:
```bash
python api_assistant_cli.py parse file test_data/openapi/jsonplaceholder.yaml --add
```

### 2. DummyJSON Products API (OpenAPI)
**File**: `openapi/dummyjson.yaml`

Product catalog API with:
- **4 endpoints** for product management
- **Search and filter** capabilities
- **Pagination** support

**Usage**:
```bash
python api_assistant_cli.py parse file test_data/openapi/dummyjson.yaml --add
```

### 3. Countries GraphQL API
**File**: `graphql/countries.graphql`

GraphQL schema for geographical data:
- **Query types** for countries, continents, and languages
- **Filter inputs** for advanced querying
- **Nested relationships** between entities

**Usage**:
```bash
python api_assistant_cli.py parse file test_data/graphql/countries.graphql --format graphql --add
```

### 4. ReqRes API Collection (Postman)
**File**: `postman/reqres_collection.json`

Postman collection for user management:
- **7 requests** including authentication
- **User CRUD** operations
- **Login and registration** endpoints

**Usage**:
```bash
python api_assistant_cli.py parse file test_data/postman/reqres_collection.json --format postman --add
```

## Quick Start

### 1. Index All Sample APIs

```bash
# Create a batch file
echo "test_data/openapi/jsonplaceholder.yaml" > batch_files.txt
echo "test_data/openapi/dummyjson.yaml" >> batch_files.txt

# Batch index
python api_assistant_cli.py batch parse --file-list batch_files.txt --add
```

### 2. Test Search

```bash
# Search across all indexed APIs
python api_assistant_cli.py search query "get all posts" --hybrid --rerank --limit 5
```

### 3. Generate Diagrams

```bash
# Create diagrams directory if it doesn't exist
mkdir -p test_data/diagrams

# Generate sequence diagram
python api_assistant_cli.py diagram generate sequence \
  --endpoint "/posts" \
  --method GET \
  --output test_data/diagrams/posts_sequence.mmd
```

### 4. Generate Client Code

```bash
# Create clients directory if it doesn't exist
mkdir -p test_data/clients

# Generate Python client
python api_assistant_cli.py generate code \
  --endpoint "/posts" \
  --method GET \
  --language python \
  --output test_data/clients/get_posts.py
```

## Output Directories

These directories are created automatically when you generate output:

- **diagrams/**: Mermaid diagram files (.mmd)
- **clients/**: Generated client code (.py, .js, .sh)
- **exports/**: Database exports (.json, .yaml, .md)
- **sessions/**: Session history exports (.json)

## Adding Your Own Test Data

You can add your own API specifications to test:

1. **OpenAPI/Swagger**: Place `.yaml` or `.json` files in `openapi/`
2. **GraphQL**: Place `.graphql` or `.gql` files in `graphql/`
3. **Postman**: Place `.json` collection files in `postman/`

Then index them:

```bash
python api_assistant_cli.py parse file test_data/your_category/your_api.yaml --add
```

## Real Public APIs

These sample files are based on real public APIs:

- **JSONPlaceholder**: https://jsonplaceholder.typicode.com
- **DummyJSON**: https://dummyjson.com
- **Countries GraphQL**: https://countries.trevorblades.com
- **ReqRes**: https://reqres.in

You can test the actual APIs alongside the indexed specifications!

## Cleaning Up

To clear all indexed data and start fresh:

```bash
python api_assistant_cli.py database clear --confirm
```

To remove generated files:

```bash
rm -rf test_data/diagrams/* test_data/clients/* test_data/exports/* test_data/sessions/*
```

## See Also

- **TESTING_GUIDE.md**: Comprehensive testing workflows
- **README.md**: Main project documentation
- **docs/**: Additional documentation

---

**Happy Testing!** 🚀
