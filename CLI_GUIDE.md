# API Assistant CLI Guide

Command-line interface for parsing API specifications, managing vector store collections, and searching API documentation.

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Make CLI executable (optional)
chmod +x api_assistant_cli.py
```

## Quick Start

```bash
# Show help
python api_assistant_cli.py --help

# Show supported formats
python api_assistant_cli.py info formats

# Parse a GraphQL schema
python api_assistant_cli.py parse file schema.graphql

# Parse and add to vector store
python api_assistant_cli.py parse file schema.graphql --add

# Parse multiple files in batch
python api_assistant_cli.py parse batch schema1.graphql schema2.json

# Search the vector store
python api_assistant_cli.py search "user authentication"
```

## Commands

### Parse Commands

Parse API specifications in multiple formats (GraphQL, Postman, OpenAPI).

#### `parse file`

Parse a single API specification file.

```bash
# Basic parsing
python api_assistant_cli.py parse file API_SPEC_FILE

# With format hint
python api_assistant_cli.py parse file collection.json --format postman

# Save parsed output to JSON
python api_assistant_cli.py parse file schema.graphql --output result.json

# Add documents to vector store
python api_assistant_cli.py parse file schema.graphql --add

# Show generated documents
python api_assistant_cli.py parse file schema.graphql --show-docs
```

**Options:**
- `--format, -f`: Format hint (openapi, graphql, postman)
- `--output, -o`: Save parsed data to JSON file
- `--add, -a`: Add documents to vector store
- `--show-docs, -d`: Show generated documents

**Examples:**

```bash
# Parse GraphQL schema
python api_assistant_cli.py parse file examples/schema.graphql

# Parse Postman collection with output
python api_assistant_cli.py parse file collection.json -o parsed.json

# Parse OpenAPI spec and add to store
python api_assistant_cli.py parse file openapi.yaml --add
```

#### `parse batch`

Parse multiple API specification files in batch.

```bash
# Parse multiple files
python api_assistant_cli.py parse batch FILE1 FILE2 FILE3 ...

# With options
python api_assistant_cli.py parse batch \
  schema1.graphql \
  schema2.graphql \
  collection.json \
  --add \
  --output-dir ./results
```

**Options:**
- `--add/--no-add`: Add documents to vector store (default: true)
- `--output-dir, -o`: Save individual results to directory
- `--summary/--no-summary`: Show summary table (default: true)

**Examples:**

```bash
# Parse all GraphQL files
python api_assistant_cli.py parse batch *.graphql

# Parse mixed formats
python api_assistant_cli.py parse batch \
  api/schema.graphql \
  api/collection.json \
  api/openapi.yaml

# Parse without adding to store
python api_assistant_cli.py parse batch *.graphql --no-add
```

### Search Commands

Search the vector store for API documentation.

#### `search query`

Search for API documentation by query text.

```bash
# Basic search
python api_assistant_cli.py search "QUERY_TEXT"

# With options
python api_assistant_cli.py search "user authentication" \
  --limit 10 \
  --source graphql \
  --method GET
```

**Options:**
- `--limit, -n`: Number of results (default: 5)
- `--source, -s`: Filter by source (openapi, graphql, postman)
- `--method, -m`: Filter by HTTP method (GET, POST, etc.)
- `--content/--no-content`: Show document content (default: true)

**Examples:**

```bash
# Search for authentication
python api_assistant_cli.py search "authentication"

# Search with filters
python api_assistant_cli.py search "user" --source graphql --limit 10

# Search POST endpoints only
python api_assistant_cli.py search "create" --method POST

# Search without showing content
python api_assistant_cli.py search "api" --no-content
```

### Collection Commands

Manage vector store collections.

#### `collection info`

Show information about the current collection.

```bash
python api_assistant_cli.py collection info
```

Shows:
- Collection name
- Total documents
- Embedding model

#### `collection clear`

Clear all documents from the collection.

```bash
# With confirmation prompt
python api_assistant_cli.py collection clear

# Skip confirmation
python api_assistant_cli.py collection clear --yes
```

**⚠️ Warning:** This operation cannot be undone!

### Info Commands

Get information about supported formats and features.

#### `info formats`

Show supported API specification formats.

```bash
python api_assistant_cli.py info formats
```

Shows details about:
- OpenAPI (Swagger) 2.0, 3.x
- GraphQL Schema Definition Language
- Postman Collections v2.0, v2.1

#### `info version`

Show API Assistant version.

```bash
python api_assistant_cli.py info version
```

### Export Commands

Export data from the vector store.

#### `export documents`

Export all documents to JSON file.

```bash
# Export all documents
python api_assistant_cli.py export documents output.json

# Export with limit
python api_assistant_cli.py export documents output.json --limit 100
```

**Options:**
- `--limit, -n`: Limit number of documents

## Usage Examples

### Example 1: Parse and Add GraphQL Schema

```bash
# Parse GraphQL schema and add to vector store
python api_assistant_cli.py parse file examples/schema.graphql --add

# Search for queries
python api_assistant_cli.py search "user queries"
```

### Example 2: Batch Process API Specifications

```bash
# Parse all API specs in directory
python api_assistant_cli.py parse batch \
  specs/*.graphql \
  specs/*.json \
  --add \
  --output-dir ./parsed_results
```

### Example 3: Export and Backup

```bash
# Export all documents
python api_assistant_cli.py export documents backup_$(date +%Y%m%d).json

# View collection info
python api_assistant_cli.py collection info
```

### Example 4: CI/CD Integration

```bash
#!/bin/bash
# Parse API specs in CI pipeline

# Parse all specs
python api_assistant_cli.py parse batch api/**/*.graphql api/**/*.json --add

# Run validations
python api_assistant_cli.py search "authentication" --limit 1

# Export results
python api_assistant_cli.py export documents api_docs.json
```

### Example 5: Format Detection

```bash
# Let CLI auto-detect format
python api_assistant_cli.py parse file unknown_spec.json

# Explicitly specify format
python api_assistant_cli.py parse file spec.json --format openapi
```

## Global Options

Available for all commands:

- `--verbose, -v`: Verbose output
- `--help`: Show help message

## Output Formats

### Parse Output

```json
{
  "source_file": "schema.graphql",
  "format": "graphql",
  "stats": {
    "total_types": 10,
    "total_queries": 5,
    "total_mutations": 3
  },
  "documents": [
    {
      "content": "GraphQL Type: User...",
      "metadata": {
        "source": "graphql",
        "type": "type_definition",
        "name": "User"
      }
    }
  ]
}
```

### Search Output

Pretty-formatted results with:
- Document content
- Relevance score
- Metadata (method, name, source)

## Exit Codes

- `0`: Success
- `1`: Error (file not found, parsing failed, etc.)

## Shell Completion

Install shell completion for faster command entry:

```bash
# Install for current shell
python api_assistant_cli.py --install-completion

# Show completion script
python api_assistant_cli.py --show-completion
```

## Tips

1. **Use batch processing** for multiple files to improve performance
2. **Add to vector store** during parsing to enable search
3. **Use format hints** for faster parsing when format is known
4. **Export regularly** to backup your vector store
5. **Use filters** in search to narrow down results

## Common Workflows

### Setup New Project

```bash
# 1. Parse all API specs
python api_assistant_cli.py parse batch api/**/* --add

# 2. Verify collection
python api_assistant_cli.py collection info

# 3. Test search
python api_assistant_cli.py search "test query"
```

### Update API Documentation

```bash
# 1. Parse new/updated specs
python api_assistant_cli.py parse file updated_schema.graphql --add

# 2. Search to verify
python api_assistant_cli.py search "new feature"
```

### Migrate/Backup

```bash
# Export current data
python api_assistant_cli.py export documents backup.json

# Clear collection (if needed)
python api_assistant_cli.py collection clear --yes

# Re-import (future feature)
# python api_assistant_cli.py import documents backup.json
```

## Troubleshooting

### CLI hangs on startup

- Check if heavy dependencies (embeddings) are being loaded
- Try simpler commands first (`info formats`)

### File not found

- Use absolute paths or verify working directory
- Check file permissions

### Parsing fails

- Verify file format is supported
- Try with `--format` hint
- Check file is valid (JSON, GraphQL syntax)

### Search returns no results

- Verify documents were added with `--add`
- Check collection info
- Try broader search queries

## Support

For issues and feature requests:
- GitHub: https://github.com/anthropics/api-assistant
- Documentation: See `docs/` directory

---

**Version**: 1.0.0
**Updated**: 2025-12-27
**Phase 4, Day 28**: CLI Tool
