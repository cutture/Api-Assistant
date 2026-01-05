"""
Tests for Mermaid Diagram Generator.

Tests generation of:
- Sequence diagrams
- ER diagrams
- Authentication flow diagrams
- API overview diagrams

Author: API Assistant Team
Date: 2025-12-27
"""

import pytest
from src.diagrams import MermaidGenerator, SequenceDiagram, ERDiagram, FlowDiagram
from src.parsers import (
    GraphQLParser,
    GraphQLSchema,
    GraphQLType,
    GraphQLTypeKind,
    PostmanParser,
    ParsedEndpoint,
    ParsedDocument,
    ParsedParameter,
    ParsedResponse,
)


class TestSequenceDiagram:
    """Test SequenceDiagram class."""

    def test_create_sequence_diagram(self):
        """Test creating a sequence diagram."""
        diagram = SequenceDiagram(
            title="User Login",
            participants=["Client", "API", "Database"],
            interactions=[
                {"from": "Client", "to": "API", "arrow": "->>", "message": "POST /login"},
                {"from": "API", "to": "Database", "arrow": "->>", "message": "Verify credentials"},
                {"from": "Database", "to": "API", "arrow": "-->>", "message": "User found"},
                {"from": "API", "to": "Client", "arrow": "-->>", "message": "200 OK"},
            ],
        )

        mermaid = diagram.to_mermaid()
        assert "sequenceDiagram" in mermaid
        assert "title User Login" in mermaid
        assert "participant Client" in mermaid
        assert "participant API" in mermaid
        assert "participant Database" in mermaid
        assert "Client->>API: POST /login" in mermaid
        assert "API->>Database: Verify credentials" in mermaid

    def test_sequence_diagram_from_endpoint(self):
        """Test generating sequence diagram from ParsedEndpoint."""
        endpoint = ParsedEndpoint(
            path="/api/users",
            method="GET",
            summary="Get user list",
            parameters=[
                ParsedParameter(name="limit", location="query", required=True),
            ],
            responses=[
                ParsedResponse(status_code="200", description="Success"),
                ParsedResponse(status_code="401", description="Unauthorized"),
            ],
            security=[{"bearer": []}],
        )

        diagram = MermaidGenerator.generate_sequence_diagram_from_endpoint(endpoint)

        assert diagram.title == "GET /api/users"
        assert "Client" in diagram.participants
        assert "API" in diagram.participants
        mermaid = diagram.to_mermaid()
        assert "sequenceDiagram" in mermaid
        assert "Validate authentication" in mermaid

    def test_sequence_diagram_from_postman(self):
        """Test generating sequence diagram from Postman request."""
        from src.parsers.postman_parser import PostmanRequest, PostmanAuth

        request = PostmanRequest(
            name="Get Users",
            method="GET",
            url="https://api.example.com/users",
            auth=PostmanAuth(type="bearer", details={"token": "secret"}),
        )

        diagram = MermaidGenerator.generate_sequence_diagram_from_postman(request)

        assert diagram.title == "Get Users"
        assert "Client" in diagram.participants
        assert "API" in diagram.participants
        mermaid = diagram.to_mermaid()
        assert "sequenceDiagram" in mermaid
        assert "GET https://api.example.com/users" in mermaid
        assert "Verify bearer" in mermaid


class TestERDiagram:
    """Test ERDiagram class."""

    def test_create_er_diagram(self):
        """Test creating an ER diagram."""
        diagram = ERDiagram(
            title="Blog Schema",
            entities={
                "User": [
                    {"type": "ID", "name": "id", "key": "PK"},
                    {"type": "String", "name": "name", "key": ""},
                    {"type": "String", "name": "email", "key": ""},
                ],
                "Post": [
                    {"type": "ID", "name": "id", "key": "PK"},
                    {"type": "String", "name": "title", "key": ""},
                    {"type": "ID", "name": "authorId", "key": "FK"},
                ],
            },
            relationships=[
                {"from": "User", "to": "Post", "relationship": "||--o{", "label": "writes"},
            ],
        )

        mermaid = diagram.to_mermaid()
        assert "erDiagram" in mermaid
        assert "User {" in mermaid
        assert "ID id PK" in mermaid
        assert "String name" in mermaid
        assert "Post {" in mermaid
        assert "User ||--o{ Post : writes" in mermaid

    def test_er_diagram_from_graphql(self):
        """Test generating ER diagram from GraphQL schema."""
        schema_text = """
        type User {
            id: ID!
            name: String!
            posts: [Post!]!
        }

        type Post {
            id: ID!
            title: String!
            author: User!
        }

        type Query {
            user(id: ID!): User
        }
        """

        parser = GraphQLParser()
        schema = parser.parse(schema_text)

        diagram = MermaidGenerator.generate_er_diagram_from_graphql(schema)

        assert "User" in diagram.entities
        assert "Post" in diagram.entities
        assert len(diagram.relationships) > 0

        mermaid = diagram.to_mermaid()
        assert "erDiagram" in mermaid
        assert "User {" in mermaid
        assert "Post {" in mermaid

    def test_er_diagram_with_type_filter(self):
        """Test generating ER diagram with type filter."""
        schema_text = """
        type User {
            id: ID!
            name: String!
        }

        type Post {
            id: ID!
            title: String!
        }

        type Comment {
            id: ID!
            text: String!
        }

        type Query {
            users: [User]
        }
        """

        parser = GraphQLParser()
        schema = parser.parse(schema_text)

        # Filter to only User and Post
        diagram = MermaidGenerator.generate_er_diagram_from_graphql(
            schema, include_types={"User", "Post"}
        )

        assert "User" in diagram.entities
        assert "Post" in diagram.entities
        assert "Comment" not in diagram.entities


class TestFlowDiagram:
    """Test FlowDiagram class."""

    def test_create_flow_diagram(self):
        """Test creating a flow diagram."""
        diagram = FlowDiagram(
            title="User Registration",
            direction="TD",
            nodes={
                "start": {"label": "Start", "shape": "stadium"},
                "check": {"label": "Email Valid?", "shape": "diamond"},
                "create": {"label": "Create User", "shape": "rectangle"},
                "end": {"label": "End", "shape": "stadium"},
            },
            edges=[
                {"from": "start", "to": "check"},
                {"from": "check", "to": "create", "label": "Yes", "arrow": "-->"},
                {"from": "check", "to": "end", "label": "No", "arrow": "-->"},
                {"from": "create", "to": "end"},
            ],
        )

        mermaid = diagram.to_mermaid()
        assert "flowchart TD" in mermaid
        assert "start([Start])" in mermaid
        assert "check{{Email Valid?}}" in mermaid
        assert "create[Create User]" in mermaid
        assert "check -->|Yes| create" in mermaid


class TestAuthFlowDiagrams:
    """Test authentication flow diagram generation."""

    def test_bearer_auth_flow(self):
        """Test Bearer authentication flow."""
        diagram = MermaidGenerator.generate_auth_flow("bearer")

        assert diagram.title == "BEARER Authentication Flow"
        assert "start" in diagram.nodes
        assert "check" in diagram.nodes
        assert "validate" in diagram.nodes
        assert len(diagram.edges) > 0

        mermaid = diagram.to_mermaid()
        assert "flowchart TD" in mermaid
        assert "Has Bearer Token?" in mermaid
        assert "401 Unauthorized" in mermaid

    def test_oauth2_auth_flow(self):
        """Test OAuth2 authentication flow."""
        diagram = MermaidGenerator.generate_auth_flow("oauth2")

        assert diagram.title == "OAUTH2 Authentication Flow"
        mermaid = diagram.to_mermaid()
        assert "flowchart TD" in mermaid
        assert "OAuth Provider" in mermaid
        assert "Access Token" in mermaid

    def test_apikey_auth_flow(self):
        """Test API Key authentication flow."""
        diagram = MermaidGenerator.generate_auth_flow("apikey")

        assert diagram.title == "APIKEY Authentication Flow"
        mermaid = diagram.to_mermaid()
        assert "flowchart TD" in mermaid
        assert "Has API Key?" in mermaid
        assert "Rate Limit" in mermaid
        assert "429 Too Many Requests" in mermaid

    def test_basic_auth_flow(self):
        """Test Basic authentication flow."""
        diagram = MermaidGenerator.generate_auth_flow("basic")

        assert diagram.title == "BASIC Authentication Flow"
        mermaid = diagram.to_mermaid()
        assert "flowchart TD" in mermaid
        assert "Decode Base64" in mermaid
        assert "Validate Credentials" in mermaid


class TestAPIOverviewDiagram:
    """Test API overview diagram generation."""

    def test_api_overview_from_parsed_document(self):
        """Test generating API overview from ParsedDocument."""
        doc = ParsedDocument(
            title="User API",
            version="1.0.0",
            endpoints=[
                ParsedEndpoint(path="/users", method="GET", tags=["Users"]),
                ParsedEndpoint(path="/users/{id}", method="GET", tags=["Users"]),
                ParsedEndpoint(path="/auth/login", method="POST", tags=["Auth"]),
            ],
        )

        diagram = MermaidGenerator.generate_api_overview_flow(doc)

        assert diagram.title == "User API API Flow"
        assert "client" in diagram.nodes
        assert "api" in diagram.nodes

        mermaid = diagram.to_mermaid()
        assert "flowchart LR" in mermaid
        assert "User API" in mermaid


class TestDiagramSaving:
    """Test saving diagrams to files."""

    def test_save_sequence_diagram(self, tmp_path):
        """Test saving sequence diagram to file."""
        diagram = SequenceDiagram(
            title="Test",
            participants=["A", "B"],
            interactions=[{"from": "A", "to": "B", "arrow": "->", "message": "hello"}],
        )

        output_file = tmp_path / "sequence.mmd"
        MermaidGenerator.save_diagram(diagram, str(output_file))

        assert output_file.exists()
        content = output_file.read_text()
        assert "sequenceDiagram" in content
        assert "A->B: hello" in content

    def test_save_er_diagram(self, tmp_path):
        """Test saving ER diagram to file."""
        diagram = ERDiagram(
            entities={
                "User": [{"type": "ID", "name": "id", "key": "PK"}],
            }
        )

        output_file = tmp_path / "er.mmd"
        MermaidGenerator.save_diagram(diagram, str(output_file))

        assert output_file.exists()
        content = output_file.read_text()
        assert "erDiagram" in content
        assert "User {" in content

    def test_save_flow_diagram(self, tmp_path):
        """Test saving flow diagram to file."""
        diagram = FlowDiagram(
            nodes={"a": {"label": "Start", "shape": "stadium"}},
            edges=[],
        )

        output_file = tmp_path / "flow.mmd"
        MermaidGenerator.save_diagram(diagram, str(output_file))

        assert output_file.exists()
        content = output_file.read_text()
        assert "flowchart" in content


class TestMermaidSyntax:
    """Test Mermaid syntax generation."""

    def test_sequence_diagram_arrows(self):
        """Test different arrow types in sequence diagrams."""
        diagram = SequenceDiagram(
            title="Arrows",
            participants=["A", "B"],
            interactions=[
                {"from": "A", "to": "B", "arrow": "->>", "message": "request"},
                {"from": "B", "to": "A", "arrow": "-->>", "message": "response"},
                {"from": "A", "to": "B", "arrow": "-x", "message": "failed"},
            ],
        )

        mermaid = diagram.to_mermaid()
        assert "A->>B: request" in mermaid
        assert "B-->>A: response" in mermaid
        assert "A-xB: failed" in mermaid

    def test_flowchart_node_shapes(self):
        """Test different node shapes in flowcharts."""
        diagram = FlowDiagram(
            nodes={
                "rect": {"label": "Rectangle", "shape": "rectangle"},
                "round": {"label": "Rounded", "shape": "rounded"},
                "diamond": {"label": "Decision", "shape": "diamond"},
                "circle": {"label": "Circle", "shape": "circle"},
            },
            edges=[],
        )

        mermaid = diagram.to_mermaid()
        assert "rect[Rectangle]" in mermaid
        assert "round(Rounded)" in mermaid
        assert "diamond{{Decision}}" in mermaid
        assert "circle((Circle))" in mermaid

    def test_er_diagram_relationships(self):
        """Test different relationship types in ER diagrams."""
        diagram = ERDiagram(
            entities={"A": [], "B": [], "C": []},
            relationships=[
                {"from": "A", "to": "B", "relationship": "||--o{", "label": "one-to-many"},
                {"from": "B", "to": "C", "relationship": "||--||", "label": "one-to-one"},
            ],
        )

        mermaid = diagram.to_mermaid()
        assert "A ||--o{ B : one-to-many" in mermaid
        assert "B ||--|| C : one-to-one" in mermaid


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
