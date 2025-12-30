# Sample API Specification Files

This folder contains example API specification files that you can use to test the API Assistant upload functionality.

## Available Samples

### 1. OpenAPI Sample (`sample-openapi.json`)
A complete OpenAPI 3.0 specification for a simple User Management API.

**Features:**
- CRUD operations for users
- Query parameters with pagination
- Request/response schemas
- Multiple HTTP methods (GET, POST, PUT, DELETE)
- Proper error responses

**How to use:**
1. Go to the Documents section in the UI
2. Click "Upload Documents" tab
3. Upload `sample-openapi.json`
4. The system will automatically detect it as OpenAPI format
5. You should see ~5 documents indexed (1 summary + 4 endpoints)

## Expected File Formats

### OpenAPI
Files must contain either:
- `"openapi": "3.0.0"` (or any 3.x version)
- `"swagger": "2.0"`

### Postman Collection
Files must contain:
- `"info"` object with collection metadata
- `"item"` array with API requests

### GraphQL
Files must contain GraphQL schema syntax:
```graphql
type Query {
  users: [User!]!
}

type User {
  id: ID!
  name: String!
}
```

## Creating Your Own Samples

### OpenAPI Template
```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "My API",
    "version": "1.0.0"
  },
  "paths": {
    "/endpoint": {
      "get": {
        "summary": "Description",
        "responses": {
          "200": {
            "description": "Success"
          }
        }
      }
    }
  }
}
```

### Postman Collection Template
```json
{
  "info": {
    "name": "My Collection",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Get Users",
      "request": {
        "method": "GET",
        "url": "https://api.example.com/users"
      }
    }
  ]
}
```

## Troubleshooting

### "Unsupported or unknown API specification format" Error

This error means your file doesn't match any of the expected formats. Check:

1. **For JSON files:**
   - Does it have `"openapi"` or `"swagger"` field? (OpenAPI)
   - Does it have both `"info"` and `"item"` fields? (Postman)
   - Is the JSON valid? Use a JSON validator

2. **For GraphQL files:**
   - Does it use `.graphql` or `.gql` extension?
   - Does it contain type definitions (`type`, `input`, `enum`, etc.)?

3. **Common mistakes:**
   - Uploading a regular JSON file (not an API spec)
   - Missing required fields
   - Invalid JSON syntax
   - Wrong file encoding (use UTF-8)

### File Uploads Successfully But No Results

If the file uploads but you don't see search results:
1. Check the upload response - look for "skipped_count"
2. Documents might be duplicates (same content already indexed)
3. Try a different search query
4. Check the API logs for errors

## Testing the Upload

To verify the upload worked:
1. Upload a sample file
2. Go to the Search tab
3. Search for keywords from your API (e.g., "users", "GET", "create")
4. You should see results matching your API endpoints
