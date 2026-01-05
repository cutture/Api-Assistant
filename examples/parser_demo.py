#!/usr/bin/env python3
"""
Parser Demo - Day 27

Demonstrates the API Assistant parser capabilities for multiple formats:
- GraphQL Schema parsing
- Postman Collection parsing
- OpenAPI/Swagger parsing
- Unified format handler (auto-detection)

Shows how to:
- Parse different API specification formats
- Auto-detect format type
- Convert specifications to vector store documents
- Extract metadata and statistics

Author: API Assistant Team
Date: 2025-12-27
"""

import json
from typing import Dict, List, Any

# Import all parsers
from src.parsers import (
    GraphQLParser,
    PostmanParser,
    OpenAPIParser,
    UnifiedFormatHandler,
    APIFormat,
)


def print_section(title: str):
    """Print section header."""
    print(f"\n{'=' * 90}")
    print(f"{title}")
    print(f"{'=' * 90}")


def print_stats(stats: Dict[str, Any], format_type: str):
    """Print parsing statistics."""
    print(f"\nParsing Statistics ({format_type}):")
    print("-" * 45)
    for key, value in stats.items():
        print(f"  {key}: {value}")


def demo_graphql_parser():
    """Demonstrate GraphQL parser."""
    print_section("GRAPHQL SCHEMA PARSER")

    # Sample GraphQL schema
    schema = """
    scalar DateTime

    enum UserRole {
        ADMIN
        EDITOR
        VIEWER
    }

    interface Node {
        id: ID!
        createdAt: DateTime!
    }

    type User implements Node {
        id: ID!
        createdAt: DateTime!
        email: String!
        name: String!
        role: UserRole!
        posts: [Post!]!
    }

    type Post implements Node {
        id: ID!
        createdAt: DateTime!
        title: String!
        content: String!
        author: User!
        published: Boolean!
    }

    input CreatePostInput {
        title: String!
        content: String!
        published: Boolean
    }

    type Query {
        user(id: ID!): User
        users(limit: Int, offset: Int): [User!]!
        post(id: ID!): Post
        posts(published: Boolean): [Post!]!
    }

    type Mutation {
        createPost(input: CreatePostInput!): Post!
        updatePost(id: ID!, input: CreatePostInput!): Post
        deletePost(id: ID!): Boolean!
    }

    type Subscription {
        postCreated: Post!
    }
    """

    # Parse schema
    parser = GraphQLParser()
    parsed_schema = parser.parse(schema)

    print("\n✓ GraphQL Schema Parsed Successfully")
    print(f"\nTypes: {len(parsed_schema.types)}")
    for gql_type in parsed_schema.types:
        print(f"  - {gql_type.name} ({gql_type.kind.value})")

    print(f"\nQueries: {len(parsed_schema.queries)}")
    for query in parsed_schema.queries:
        args = f"({', '.join(query.arguments.keys())})" if query.arguments else "()"
        print(f"  - {query.name}{args}: {query.return_type}")

    print(f"\nMutations: {len(parsed_schema.mutations)}")
    for mutation in parsed_schema.mutations:
        args = f"({', '.join(mutation.arguments.keys())})" if mutation.arguments else "()"
        print(f"  - {mutation.name}{args}: {mutation.return_type}")

    print(f"\nSubscriptions: {len(parsed_schema.subscriptions)}")
    for subscription in parsed_schema.subscriptions:
        print(f"  - {subscription.name}: {subscription.return_type}")

    # Convert to documents
    documents = parser.to_documents()
    print(f"\n✓ Generated {len(documents)} documents for vector store")

    # Show sample document
    if documents:
        print("\nSample Document:")
        print("-" * 45)
        sample = documents[0]
        print(f"Content (truncated): {sample['content'][:200]}...")
        print(f"Metadata: {json.dumps(sample['metadata'], indent=2)}")


def demo_postman_parser():
    """Demonstrate Postman parser."""
    print_section("POSTMAN COLLECTION PARSER")

    # Sample Postman collection
    collection = {
        "info": {
            "name": "E-commerce API",
            "description": "Complete e-commerce platform API",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "variable": [
            {"key": "baseUrl", "value": "https://api.ecommerce.com"},
            {"key": "apiVersion", "value": "v1"},
        ],
        "auth": {
            "type": "bearer",
            "bearer": [
                {"key": "token", "value": "{{authToken}}"}
            ],
        },
        "item": [
            {
                "name": "Products",
                "item": [
                    {
                        "name": "List Products",
                        "request": {
                            "method": "GET",
                            "url": "{{baseUrl}}/{{apiVersion}}/products",
                            "header": [
                                {"key": "Accept", "value": "application/json"}
                            ],
                        },
                    },
                    {
                        "name": "Create Product",
                        "request": {
                            "method": "POST",
                            "url": "{{baseUrl}}/{{apiVersion}}/products",
                            "header": [
                                {"key": "Content-Type", "value": "application/json"}
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "name": "New Product",
                                    "price": 29.99,
                                    "category": "Electronics"
                                }),
                            },
                        },
                    },
                ],
            },
            {
                "name": "Orders",
                "item": [
                    {
                        "name": "Get Orders",
                        "request": {
                            "method": "GET",
                            "url": "{{baseUrl}}/{{apiVersion}}/orders",
                        },
                    },
                    {
                        "name": "Create Order",
                        "request": {
                            "method": "POST",
                            "url": "{{baseUrl}}/{{apiVersion}}/orders",
                        },
                    },
                ],
            },
        ],
    }

    # Parse collection
    parser = PostmanParser()
    parsed_collection = parser.parse(collection)

    print("\n✓ Postman Collection Parsed Successfully")
    print(f"\nCollection: {parsed_collection.name}")
    print(f"Description: {parsed_collection.description}")
    print(f"Version: {parsed_collection.version}")

    print(f"\nVariables: {len(parsed_collection.variables)}")
    for var in parsed_collection.variables:
        print(f"  - {var.key} = {var.value}")

    print(f"\nAuthentication: {parsed_collection.auth.type if parsed_collection.auth else 'None'}")

    print(f"\nRequests: {len(parsed_collection.requests)}")
    for request in parsed_collection.requests:
        folder = " > ".join(request.folder_path) if request.folder_path else "Root"
        print(f"  - [{folder}] {request.method} {request.name}")

    # Group by method
    get_requests = parser.get_requests_by_method("GET")
    post_requests = parser.get_requests_by_method("POST")
    print(f"\nBy Method:")
    print(f"  GET: {len(get_requests)} requests")
    print(f"  POST: {len(post_requests)} requests")

    # Convert to documents
    documents = parser.to_documents()
    print(f"\n✓ Generated {len(documents)} documents for vector store")

    # Show sample document
    if len(documents) > 1:
        print("\nSample Request Document:")
        print("-" * 45)
        # Get first request document (skip collection info)
        request_doc = next(d for d in documents if d["metadata"]["type"] == "request")
        print(f"Content (truncated):\n{request_doc['content'][:300]}...")
        print(f"\nMetadata: {json.dumps(request_doc['metadata'], indent=2)}")


def demo_unified_handler():
    """Demonstrate unified format handler with auto-detection."""
    print_section("UNIFIED FORMAT HANDLER (AUTO-DETECTION)")

    # Test different formats
    test_specs = [
        {
            "name": "GraphQL Schema",
            "content": """
                type Query {
                    hello: String!
                }
                type User {
                    id: ID!
                    name: String!
                }
            """,
        },
        {
            "name": "Postman Collection",
            "content": json.dumps({
                "info": {"name": "Test API", "schema": "v2.1.0"},
                "item": [
                    {
                        "name": "Test Request",
                        "request": {"method": "GET", "url": "https://api.test.com"},
                    }
                ],
            }),
        },
        {
            "name": "OpenAPI 3.0",
            "content": json.dumps({
                "openapi": "3.0.0",
                "info": {"title": "Test API", "version": "1.0.0"},
                "paths": {
                    "/users": {
                        "get": {
                            "summary": "List users",
                            "responses": {"200": {"description": "Success"}},
                        }
                    }
                },
            }),
        },
    ]

    handler = UnifiedFormatHandler()

    print("\nSupported Formats:")
    for fmt in UnifiedFormatHandler.get_supported_formats():
        print(f"  - {fmt}")

    print("\n" + "-" * 90)

    for spec in test_specs:
        print(f"\n{spec['name']}:")
        print("-" * 45)

        try:
            result = handler.parse(spec["content"])

            print(f"✓ Detected Format: {result['format']}")
            print_stats(result["stats"], result["format"])
            print(f"Documents Generated: {len(result['documents'])}")

        except Exception as e:
            print(f"✗ Error: {e}")


def demo_format_info():
    """Demonstrate format information retrieval."""
    print_section("FORMAT INFORMATION")

    format_info = UnifiedFormatHandler.get_format_info()

    for format_name, info in format_info.items():
        print(f"\n{info['name']}:")
        print("-" * 45)
        print(f"  Versions: {', '.join(info['versions'])}")
        print(f"  Extensions: {', '.join(info['extensions'])}")
        print(f"  Description: {info['description']}")


def main():
    """Run parser demo."""
    print_section("PARSER DEMO - DAY 27")

    print("\nAPI Assistant now supports parsing multiple API specification formats:")
    print("  ✓ GraphQL Schema Definition Language (.graphql, .gql)")
    print("  ✓ Postman Collections v2.0 and v2.1 (.json)")
    print("  ✓ OpenAPI (Swagger) 2.0 and 3.x (.json, .yaml)")
    print("  ✓ Unified auto-detection and parsing interface")

    # Run demos
    demo_graphql_parser()
    demo_postman_parser()
    demo_unified_handler()
    demo_format_info()

    # Summary
    print_section("DEMO SUMMARY")
    print("\n✅ Features Demonstrated:")
    print("  1. GraphQL schema parsing (types, queries, mutations, subscriptions)")
    print("  2. Postman collection parsing (requests, folders, variables, auth)")
    print("  3. Unified format handler with auto-detection")
    print("  4. Document conversion for vector store integration")
    print("  5. Metadata extraction and statistics")
    print("  6. Support for multiple API specification formats")

    print("\n📚 Usage:")
    print("""
# Import parsers
from src.parsers import (
    GraphQLParser,
    PostmanParser,
    UnifiedFormatHandler,
)

# Parse GraphQL
graphql_parser = GraphQLParser()
schema = graphql_parser.parse(graphql_content)
documents = graphql_parser.to_documents()

# Parse Postman
postman_parser = PostmanParser()
collection = postman_parser.parse(postman_json)
documents = postman_parser.to_documents()

# Auto-detect and parse any format
handler = UnifiedFormatHandler()
result = handler.parse(content)  # Auto-detects format
documents = result['documents']
    """)

    print("\n" + "=" * 90)
    print("Demo completed!")
    print("=" * 90)


if __name__ == "__main__":
    main()
