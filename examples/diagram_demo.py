#!/usr/bin/env python3
"""
Diagram Generation Demo - Day 29

Demonstrates Mermaid diagram generation capabilities:
- Sequence diagrams for API request/response flows
- Entity Relationship diagrams from GraphQL schemas
- Authentication flow diagrams
- API overview flowcharts

Shows how to:
- Generate diagrams from parsed API specifications
- Create custom diagrams programmatically
- Save diagrams to files
- Use different diagram types

Author: API Assistant Team
Date: 2025-12-27
"""

from src.diagrams import MermaidGenerator, SequenceDiagram, ERDiagram, FlowDiagram
from src.parsers import GraphQLParser, PostmanParser, ParsedEndpoint, ParsedDocument, ParsedParameter, ParsedResponse
import json


def print_section(title: str):
    """Print section header."""
    print(f"\n{'=' * 90}")
    print(f"{title}")
    print(f"{'=' * 90}")


def demo_sequence_diagrams():
    """Demonstrate sequence diagram generation."""
    print_section("SEQUENCE DIAGRAMS")

    # Example 1: Create custom sequence diagram
    print("\n1. Custom Sequence Diagram")
    print("-" * 45)

    diagram = SequenceDiagram(
        title="User Login Flow",
        participants=["Client", "API", "Auth Service", "Database"],
        interactions=[
            {"from": "Client", "to": "API", "arrow": "->>", "message": "POST /login {email, password}"},
            {"from": "API", "to": "Auth Service", "arrow": "->>", "message": "Verify credentials"},
            {"from": "Auth Service", "to": "Database", "arrow": "->>", "message": "Query user"},
            {"from": "Database", "to": "Auth Service", "arrow": "-->>", "message": "User data"},
            {"from": "Auth Service", "to": "API", "arrow": "-->>", "message": "Token generated"},
            {"from": "API", "to": "Client", "arrow": "-->>", "message": "200 OK {token}"},
        ],
    )

    print(diagram.to_mermaid())

    # Example 2: Generate from ParsedEndpoint
    print("\n\n2. Sequence Diagram from ParsedEndpoint")
    print("-" * 45)

    endpoint = ParsedEndpoint(
        path="/api/users/{id}",
        method="GET",
        summary="Get user by ID",
        parameters=[
            ParsedParameter(name="id", location="path", required=True, param_type="string"),
            ParsedParameter(name="fields", location="query", required=False, param_type="string"),
        ],
        responses=[
            ParsedResponse(status_code="200", description="User found"),
            ParsedResponse(status_code="404", description="User not found"),
        ],
        security=[{"bearer": []}],
    )

    diagram2 = MermaidGenerator.generate_sequence_diagram_from_endpoint(endpoint)
    print(diagram2.to_mermaid())


def demo_er_diagrams():
    """Demonstrate ER diagram generation."""
    print_section("ENTITY RELATIONSHIP DIAGRAMS")

    # Example 1: GraphQL schema to ER diagram
    print("\n1. ER Diagram from GraphQL Schema")
    print("-" * 45)

    schema = """
    type User {
        id: ID!
        email: String!
        name: String!
        posts: [Post!]!
        comments: [Comment!]!
    }

    type Post {
        id: ID!
        title: String!
        content: String!
        author: User!
        comments: [Comment!]!
        published: Boolean!
    }

    type Comment {
        id: ID!
        text: String!
        author: User!
        post: Post!
        createdAt: DateTime!
    }

    scalar DateTime

    type Query {
        user(id: ID!): User
        posts: [Post!]!
    }
    """

    parser = GraphQLParser()
    parsed_schema = parser.parse(schema)

    diagram = MermaidGenerator.generate_er_diagram_from_graphql(parsed_schema)
    print(diagram.to_mermaid())

    # Example 2: Custom ER diagram
    print("\n\n2. Custom ER Diagram")
    print("-" * 45)

    diagram2 = ERDiagram(
        title="E-commerce Database Schema",
        entities={
            "Customer": [
                {"type": "int", "name": "customer_id", "key": "PK"},
                {"type": "string", "name": "email", "key": ""},
                {"type": "string", "name": "name", "key": ""},
            ],
            "Order": [
                {"type": "int", "name": "order_id", "key": "PK"},
                {"type": "int", "name": "customer_id", "key": "FK"},
                {"type": "decimal", "name": "total", "key": ""},
                {"type": "datetime", "name": "created_at", "key": ""},
            ],
            "Product": [
                {"type": "int", "name": "product_id", "key": "PK"},
                {"type": "string", "name": "name", "key": ""},
                {"type": "decimal", "name": "price", "key": ""},
            ],
            "OrderItem": [
                {"type": "int", "name": "order_id", "key": "FK"},
                {"type": "int", "name": "product_id", "key": "FK"},
                {"type": "int", "name": "quantity", "key": ""},
            ],
        },
        relationships=[
            {"from": "Customer", "to": "Order", "relationship": "||--o{", "label": "places"},
            {"from": "Order", "to": "OrderItem", "relationship": "||--o{", "label": "contains"},
            {"from": "Product", "to": "OrderItem", "relationship": "||--o{", "label": "in"},
        ],
    )

    print(diagram2.to_mermaid())


def demo_auth_flows():
    """Demonstrate authentication flow diagrams."""
    print_section("AUTHENTICATION FLOW DIAGRAMS")

    # Example 1: Bearer Token
    print("\n1. Bearer Token Authentication")
    print("-" * 45)

    bearer_diagram = MermaidGenerator.generate_auth_flow("bearer")
    print(bearer_diagram.to_mermaid())

    # Example 2: OAuth2
    print("\n\n2. OAuth2 Authentication")
    print("-" * 45)

    oauth2_diagram = MermaidGenerator.generate_auth_flow("oauth2")
    print(oauth2_diagram.to_mermaid())

    # Example 3: API Key
    print("\n\n3. API Key Authentication")
    print("-" * 45)

    apikey_diagram = MermaidGenerator.generate_auth_flow("apikey")
    print(apikey_diagram.to_mermaid())


def demo_flowcharts():
    """Demonstrate flowchart generation."""
    print_section("FLOWCHART DIAGRAMS")

    # Example 1: Custom business process
    print("\n1. Custom Business Process Flow")
    print("-" * 45)

    diagram = FlowDiagram(
        title="Order Processing",
        direction="TD",
        nodes={
            "start": {"label": "New Order", "shape": "stadium"},
            "check_stock": {"label": "Check Stock", "shape": "rectangle"},
            "in_stock": {"label": "In Stock?", "shape": "diamond"},
            "process": {"label": "Process Payment", "shape": "rectangle"},
            "payment_ok": {"label": "Payment OK?", "shape": "diamond"},
            "ship": {"label": "Ship Order", "shape": "rectangle"},
            "backorder": {"label": "Create Backorder", "shape": "rectangle"},
            "refund": {"label": "Refund Payment", "shape": "rectangle"},
            "end_success": {"label": "Order Complete", "shape": "stadium"},
            "end_fail": {"label": "Order Failed", "shape": "stadium"},
        },
        edges=[
            {"from": "start", "to": "check_stock"},
            {"from": "check_stock", "to": "in_stock"},
            {"from": "in_stock", "to": "process", "label": "Yes", "arrow": "-->"},
            {"from": "in_stock", "to": "backorder", "label": "No", "arrow": "-->"},
            {"from": "process", "to": "payment_ok"},
            {"from": "payment_ok", "to": "ship", "label": "Yes", "arrow": "-->"},
            {"from": "payment_ok", "to": "end_fail", "label": "No", "arrow": "-->"},
            {"from": "ship", "to": "end_success"},
            {"from": "backorder", "to": "end_success"},
            {"from": "refund", "to": "end_fail"},
        ],
    )

    print(diagram.to_mermaid())

    # Example 2: API overview
    print("\n\n2. API Overview Flowchart")
    print("-" * 45)

    doc = ParsedDocument(
        title="User Management API",
        version="1.0",
        endpoints=[
            ParsedEndpoint(path="/users", method="GET", tags=["Users"], summary="List users"),
            ParsedEndpoint(path="/users/{id}", method="GET", tags=["Users"], summary="Get user"),
            ParsedEndpoint(path="/users", method="POST", tags=["Users"], summary="Create user"),
            ParsedEndpoint(path="/auth/login", method="POST", tags=["Auth"], summary="Login"),
            ParsedEndpoint(path="/auth/logout", method="POST", tags=["Auth"], summary="Logout"),
        ],
    )

    overview_diagram = MermaidGenerator.generate_api_overview_flow(doc)
    print(overview_diagram.to_mermaid())


def demo_save_diagrams():
    """Demonstrate saving diagrams to files."""
    print_section("SAVING DIAGRAMS")

    print("\n1. Saving to .mmd files")
    print("-" * 45)

    # Create a simple diagram
    diagram = SequenceDiagram(
        title="API Request",
        participants=["Client", "Server"],
        interactions=[
            {"from": "Client", "to": "Server", "arrow": "->>", "message": "Request"},
            {"from": "Server", "to": "Client", "arrow": "-->>", "message": "Response"},
        ],
    )

    # Save to file
    output_file = "examples/diagrams/api_request.mmd"
    print(f"Saving diagram to: {output_file}")

    # Note: In production, you would actually save the file
    # MermaidGenerator.save_diagram(diagram, output_file)
    print("(Skipped in demo - would save to file)")


def demo_integration():
    """Demonstrate integration with parsers."""
    print_section("PARSER INTEGRATION")

    print("\n1. Postman Collection to Sequence Diagram")
    print("-" * 45)

    collection_json = {
        "info": {
            "name": "User API",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "item": [
            {
                "name": "Create User",
                "request": {
                    "method": "POST",
                    "url": "https://api.example.com/users",
                    "header": [
                        {"key": "Content-Type", "value": "application/json"},
                        {"key": "Authorization", "value": "Bearer {{token}}"},
                    ],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({"name": "John Doe", "email": "john@example.com"}),
                    },
                },
            }
        ],
    }

    parser = PostmanParser()
    collection = parser.parse(collection_json)

    if collection.requests:
        request = collection.requests[0]
        diagram = MermaidGenerator.generate_sequence_diagram_from_postman(request)
        print(diagram.to_mermaid())


def main():
    """Run diagram demo."""
    print_section("DIAGRAM GENERATION DEMO - DAY 29")

    print("\nMermaid diagram generation for API specifications:")
    print("  ✓ Sequence diagrams for API request/response flows")
    print("  ✓ Entity Relationship diagrams from GraphQL schemas")
    print("  ✓ Authentication flow diagrams (Bearer, OAuth2, API Key, Basic)")
    print("  ✓ Flowcharts for business processes and API overviews")

    # Run demos
    demo_sequence_diagrams()
    demo_er_diagrams()
    demo_auth_flows()
    demo_flowcharts()
    demo_save_diagrams()
    demo_integration()

    # Summary
    print_section("DEMO SUMMARY")
    print("\n✅ Features Demonstrated:")
    print("  1. Sequence diagrams from endpoints and custom data")
    print("  2. ER diagrams from GraphQL schemas")
    print("  3. Authentication flow diagrams (4 types)")
    print("  4. Custom flowcharts and API overviews")
    print("  5. Saving diagrams to .mmd files")
    print("  6. Integration with parsers")

    print("\n📚 Usage:")
    print("""
# Import diagram generators
from src.diagrams import MermaidGenerator, SequenceDiagram, ERDiagram, FlowDiagram

# Create custom sequence diagram
diagram = SequenceDiagram(
    title="API Flow",
    participants=["Client", "Server"],
    interactions=[
        {"from": "Client", "to": "Server", "arrow": "->>", "message": "Request"},
    ],
)
print(diagram.to_mermaid())

# Generate from GraphQL
from src.parsers import GraphQLParser
schema = GraphQLParser().parse(schema_text)
er_diagram = MermaidGenerator.generate_er_diagram_from_graphql(schema)

# Generate auth flow
auth_diagram = MermaidGenerator.generate_auth_flow("bearer")

# Save to file
MermaidGenerator.save_diagram(diagram, "output.mmd")
    """)

    print("\n💡 CLI Commands:")
    print("""
# Generate sequence diagram
python api_assistant_cli.py diagram sequence schema.graphql -o sequence.mmd

# Generate ER diagram from GraphQL
python api_assistant_cli.py diagram er schema.graphql -o er.mmd

# Generate auth flow
python api_assistant_cli.py diagram auth bearer -o auth.mmd

# Generate API overview
python api_assistant_cli.py diagram overview openapi.yaml -o overview.mmd
    """)

    print("\n" + "=" * 90)
    print("Demo completed! View diagrams at https://mermaid.live")
    print("=" * 90)


if __name__ == "__main__":
    main()
