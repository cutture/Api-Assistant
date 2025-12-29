"""
Mermaid Diagram Generator for API Assistant.

Generates Mermaid diagrams for API specifications:
- Sequence diagrams for API request/response flows
- Entity relationship diagrams from GraphQL schemas
- Flowcharts for authentication flows
- Class diagrams for type hierarchies

Author: API Assistant Team
Date: 2025-12-27
"""

import re
import structlog
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from enum import Enum

from src.parsers import (
    GraphQLSchema,
    GraphQLType,
    GraphQLTypeKind,
    PostmanCollection,
    PostmanRequest,
    ParsedEndpoint,
    ParsedDocument,
)

logger = structlog.get_logger(__name__)


class DiagramType(Enum):
    """Types of Mermaid diagrams."""

    SEQUENCE = "sequence"
    ER = "er"
    FLOWCHART = "flowchart"
    CLASS = "class"


@dataclass
class SequenceDiagram:
    """Sequence diagram for API request/response flow."""

    title: str
    participants: List[str] = field(default_factory=list)
    interactions: List[Dict[str, str]] = field(default_factory=list)

    def to_mermaid(self) -> str:
        """Convert to Mermaid syntax."""
        lines = ["sequenceDiagram"]

        if self.title:
            lines.append(f"    title {self.title}")

        # Add participants
        for participant in self.participants:
            lines.append(f"    participant {participant}")

        # Add interactions
        for interaction in self.interactions:
            actor_from = interaction.get("from", "")
            actor_to = interaction.get("to", "")
            message = interaction.get("message", "")
            arrow = interaction.get("arrow", "->")  # ->, -->>, -x, --x

            lines.append(f"    {actor_from}{arrow}{actor_to}: {message}")

        return "\n".join(lines)


@dataclass
class ERDiagram:
    """Entity relationship diagram."""

    title: Optional[str] = None
    entities: Dict[str, List[Dict[str, str]]] = field(default_factory=dict)
    relationships: List[Dict[str, str]] = field(default_factory=list)

    def to_mermaid(self) -> str:
        """Convert to Mermaid syntax."""
        lines = ["erDiagram"]

        if self.title:
            lines.append(f"    %% {self.title}")

        # Add entities with attributes
        for entity_name, attributes in self.entities.items():
            lines.append(f"    {entity_name} {{")
            for attr in attributes:
                attr_type = attr.get("type", "string")
                attr_name = attr.get("name", "")
                attr_key = attr.get("key", "")

                key_marker = ""
                if attr_key == "PK":
                    key_marker = " PK"
                elif attr_key == "FK":
                    key_marker = " FK"

                lines.append(f"        {attr_type} {attr_name}{key_marker}")
            lines.append("    }")

        # Add relationships
        for rel in self.relationships:
            from_entity = rel.get("from", "")
            to_entity = rel.get("to", "")
            relationship = rel.get("relationship", "||--o{")  # one-to-many
            label = rel.get("label", "")

            if label:
                lines.append(f"    {from_entity} {relationship} {to_entity} : {label}")
            else:
                lines.append(f"    {from_entity} {relationship} {to_entity}")

        return "\n".join(lines)


@dataclass
class FlowDiagram:
    """Flowchart diagram for processes."""

    title: Optional[str] = None
    direction: str = "TD"  # TD, LR, BT, RL
    nodes: Dict[str, Dict[str, str]] = field(default_factory=dict)
    edges: List[Dict[str, str]] = field(default_factory=list)

    def to_mermaid(self) -> str:
        """Convert to Mermaid syntax."""
        lines = [f"flowchart {self.direction}"]

        if self.title:
            lines.append(f"    %% {self.title}")

        # Add nodes
        for node_id, node_data in self.nodes.items():
            label = node_data.get("label", node_id)
            shape = node_data.get("shape", "rectangle")

            # Escape special characters in labels by wrapping in quotes if needed
            # Check if label contains special characters that need quoting
            special_chars = ['(', ')', '[', ']', '{', '}', '#', ':', ';', '|', '&']
            needs_quotes = any(char in label for char in special_chars)

            if needs_quotes:
                # Use double quotes and escape any quotes in the label
                label = f'"{label.replace(chr(34), chr(34) + chr(34))}"'

            # Different shapes
            if shape == "rectangle":
                lines.append(f"    {node_id}[{label}]")
            elif shape == "rounded":
                lines.append(f"    {node_id}({label})")
            elif shape == "stadium":
                lines.append(f"    {node_id}([{label}])")
            elif shape == "diamond":
                lines.append(f"    {node_id}{{{{{label}}}}}")
            elif shape == "circle":
                lines.append(f"    {node_id}(({label}))")
            elif shape == "hexagon":
                lines.append(f"    {node_id}{{{{{{{label}}}}}}}")
            else:
                lines.append(f"    {node_id}[{label}]")

        # Add edges
        for edge in self.edges:
            from_node = edge.get("from", "")
            to_node = edge.get("to", "")
            label = edge.get("label", "")
            arrow = edge.get("arrow", "-->")  # -->, -.->

            if label:
                lines.append(f"    {from_node} {arrow}|{label}| {to_node}")
            else:
                lines.append(f"    {from_node} {arrow} {to_node}")

        return "\n".join(lines)


class MermaidGenerator:
    """Generate Mermaid diagrams from API specifications."""

    @staticmethod
    def generate_sequence_diagram_from_endpoint(
        endpoint: ParsedEndpoint,
    ) -> SequenceDiagram:
        """
        Generate sequence diagram from OpenAPI endpoint.

        Args:
            endpoint: Parsed API endpoint

        Returns:
            SequenceDiagram instance
        """
        diagram = SequenceDiagram(
            title=f"{endpoint.method.upper()} {endpoint.path}",
            participants=["Client", "API", "Backend"],
        )

        # Request flow
        request_msg = f"{endpoint.method.upper()} {endpoint.path}"
        if endpoint.summary:
            request_msg = endpoint.summary

        diagram.interactions.append({
            "from": "Client",
            "to": "API",
            "arrow": "->>",
            "message": request_msg,
        })

        # Add authentication if required
        if endpoint.security:
            diagram.interactions.append({
                "from": "API",
                "to": "API",
                "arrow": "->",
                "message": "Validate authentication",
            })

        # Add parameters validation
        if endpoint.parameters:
            param_names = [p.name for p in endpoint.parameters if p.required]
            if param_names:
                diagram.interactions.append({
                    "from": "API",
                    "to": "API",
                    "arrow": "->",
                    "message": f"Validate params: {', '.join(param_names[:3])}",
                })

        # Backend processing
        diagram.interactions.append({
            "from": "API",
            "to": "Backend",
            "arrow": "->>",
            "message": "Process request",
        })

        # Response
        if endpoint.responses:
            success_response = next(
                (r for r in endpoint.responses if r.status_code.startswith("2")),
                None
            )
            if success_response:
                diagram.interactions.append({
                    "from": "Backend",
                    "to": "API",
                    "arrow": "-->>",
                    "message": f"{success_response.status_code} {success_response.description}",
                })

            # Error response
            error_response = next(
                (r for r in endpoint.responses if r.status_code.startswith("4")),
                None
            )
            if error_response:
                diagram.interactions.append({
                    "from": "API",
                    "to": "Client",
                    "arrow": "-->>",
                    "message": f"Error: {error_response.status_code}",
                })

        diagram.interactions.append({
            "from": "API",
            "to": "Client",
            "arrow": "-->>",
            "message": "Response",
        })

        return diagram

    @staticmethod
    def generate_sequence_diagram_from_postman(
        request: PostmanRequest,
    ) -> SequenceDiagram:
        """
        Generate sequence diagram from Postman request.

        Args:
            request: Postman request

        Returns:
            SequenceDiagram instance
        """
        diagram = SequenceDiagram(
            title=request.name,
            participants=["Client", "API"],
        )

        # Request
        msg = f"{request.method} {request.url}"
        diagram.interactions.append({
            "from": "Client",
            "to": "API",
            "arrow": "->>",
            "message": msg,
        })

        # Authentication
        if request.auth:
            diagram.interactions.append({
                "from": "API",
                "to": "API",
                "arrow": "->",
                "message": f"Verify {request.auth.type}",
            })

        # Response
        diagram.interactions.append({
            "from": "API",
            "to": "Client",
            "arrow": "-->>",
            "message": "Response",
        })

        return diagram

    @staticmethod
    def generate_er_diagram_from_graphql(
        schema: GraphQLSchema,
        include_types: Optional[Set[str]] = None,
    ) -> ERDiagram:
        """
        Generate ER diagram from GraphQL schema.

        Args:
            schema: Parsed GraphQL schema
            include_types: Optional set of type names to include

        Returns:
            ERDiagram instance
        """
        diagram = ERDiagram(title="GraphQL Schema Entities")

        # Filter object types only
        object_types = [
            t for t in schema.types
            if t.kind == GraphQLTypeKind.OBJECT
        ]

        if include_types:
            object_types = [t for t in object_types if t.name in include_types]

        # Add entities
        for gql_type in object_types:
            attributes = []

            for field in gql_type.fields:
                # Determine if it's a key
                key = ""
                if field.name == "id" or field.name.endswith("Id"):
                    key = "PK" if field.name == "id" else "FK"

                # Get base type - Mermaid ER doesn't support brackets at start
                # Use suffix notation instead: Type[] for arrays
                field_type = field.type
                if field.is_list:
                    field_type = f"{field_type}[]"  # Array notation at end

                attributes.append({
                    "type": field_type,
                    "name": field.name,
                    "key": key,
                })

            diagram.entities[gql_type.name] = attributes

        # Add relationships based on fields
        for gql_type in object_types:
            for field in gql_type.fields:
                # Check if field references another type
                if field.type in [t.name for t in object_types]:
                    relationship = "||--o|" if field.is_required else "||--o{"
                    if field.is_list:
                        relationship = "||--o{"

                    diagram.relationships.append({
                        "from": gql_type.name,
                        "to": field.type,
                        "relationship": relationship,
                        "label": field.name,
                    })

        return diagram

    @staticmethod
    def generate_auth_flow(
        auth_type: str,
        endpoints: Optional[List[str]] = None,
    ) -> FlowDiagram:
        """
        Generate authentication flow diagram.

        Args:
            auth_type: Type of authentication (bearer, apikey, oauth2, basic)
            endpoints: Optional list of endpoints that use this auth

        Returns:
            FlowDiagram instance
        """
        diagram = FlowDiagram(
            title=f"{auth_type.upper()} Authentication Flow",
            direction="TD",
        )

        if auth_type.lower() == "bearer":
            diagram.nodes = {
                "start": {"label": "Client Request", "shape": "stadium"},
                "check": {"label": "Has Bearer Token?", "shape": "diamond"},
                "validate": {"label": "Validate Token", "shape": "rectangle"},
                "valid": {"label": "Token Valid?", "shape": "diamond"},
                "process": {"label": "Process Request", "shape": "rectangle"},
                "success": {"label": "Return Response", "shape": "stadium"},
                "error401": {"label": "401 Unauthorized", "shape": "stadium"},
                "error403": {"label": "403 Forbidden", "shape": "stadium"},
            }

            diagram.edges = [
                {"from": "start", "to": "check"},
                {"from": "check", "to": "error401", "label": "No", "arrow": "-->"},
                {"from": "check", "to": "validate", "label": "Yes", "arrow": "-->"},
                {"from": "validate", "to": "valid"},
                {"from": "valid", "to": "process", "label": "Valid", "arrow": "-->"},
                {"from": "valid", "to": "error403", "label": "Invalid", "arrow": "-->"},
                {"from": "process", "to": "success"},
            ]

        elif auth_type.lower() == "oauth2":
            diagram.nodes = {
                "start": {"label": "Client Request", "shape": "stadium"},
                "redirect": {"label": "Redirect to OAuth Provider", "shape": "rectangle"},
                "auth": {"label": "User Authenticates", "shape": "rectangle"},
                "code": {"label": "Receive Auth Code", "shape": "rectangle"},
                "exchange": {"label": "Exchange Code for Token", "shape": "rectangle"},
                "token": {"label": "Store Access Token", "shape": "rectangle"},
                "api": {"label": "Make API Request", "shape": "rectangle"},
                "success": {"label": "Return Response", "shape": "stadium"},
            }

            diagram.edges = [
                {"from": "start", "to": "redirect"},
                {"from": "redirect", "to": "auth"},
                {"from": "auth", "to": "code"},
                {"from": "code", "to": "exchange"},
                {"from": "exchange", "to": "token"},
                {"from": "token", "to": "api"},
                {"from": "api", "to": "success"},
            ]

        elif auth_type.lower() == "apikey":
            diagram.nodes = {
                "start": {"label": "Client Request", "shape": "stadium"},
                "check": {"label": "Has API Key?", "shape": "diamond"},
                "validate": {"label": "Validate API Key", "shape": "rectangle"},
                "valid": {"label": "Key Valid?", "shape": "diamond"},
                "ratelimit": {"label": "Check Rate Limit", "shape": "rectangle"},
                "process": {"label": "Process Request", "shape": "rectangle"},
                "success": {"label": "Return Response", "shape": "stadium"},
                "error401": {"label": "401 Unauthorized", "shape": "stadium"},
                "error403": {"label": "403 Forbidden", "shape": "stadium"},
                "error429": {"label": "429 Too Many Requests", "shape": "stadium"},
            }

            diagram.edges = [
                {"from": "start", "to": "check"},
                {"from": "check", "to": "error401", "label": "No", "arrow": "-->"},
                {"from": "check", "to": "validate", "label": "Yes", "arrow": "-->"},
                {"from": "validate", "to": "valid"},
                {"from": "valid", "to": "error403", "label": "Invalid", "arrow": "-->"},
                {"from": "valid", "to": "ratelimit", "label": "Valid", "arrow": "-->"},
                {"from": "ratelimit", "to": "error429", "label": "Exceeded", "arrow": "-->"},
                {"from": "ratelimit", "to": "process", "label": "OK", "arrow": "-->"},
                {"from": "process", "to": "success"},
            ]

        elif auth_type.lower() == "basic":
            diagram.nodes = {
                "start": {"label": "Client Request", "shape": "stadium"},
                "check": {"label": "Has Credentials?", "shape": "diamond"},
                "decode": {"label": "Decode Base64", "shape": "rectangle"},
                "validate": {"label": "Validate Credentials", "shape": "rectangle"},
                "valid": {"label": "Valid?", "shape": "diamond"},
                "process": {"label": "Process Request", "shape": "rectangle"},
                "success": {"label": "Return Response", "shape": "stadium"},
                "error401": {"label": "401 Unauthorized", "shape": "stadium"},
            }

            diagram.edges = [
                {"from": "start", "to": "check"},
                {"from": "check", "to": "error401", "label": "No", "arrow": "-->"},
                {"from": "check", "to": "decode", "label": "Yes", "arrow": "-->"},
                {"from": "decode", "to": "validate"},
                {"from": "validate", "to": "valid"},
                {"from": "valid", "to": "error401", "label": "Invalid", "arrow": "-->"},
                {"from": "valid", "to": "process", "label": "Valid", "arrow": "-->"},
                {"from": "process", "to": "success"},
            ]

        return diagram

    @staticmethod
    def generate_api_overview_flow(
        parsed_doc: ParsedDocument,
    ) -> FlowDiagram:
        """
        Generate API overview flowchart from parsed document.

        Args:
            parsed_doc: Parsed API document

        Returns:
            FlowDiagram instance
        """
        diagram = FlowDiagram(
            title=f"{parsed_doc.title} API Flow",
            direction="LR",
        )

        diagram.nodes["client"] = {"label": "Client", "shape": "stadium"}
        diagram.nodes["api"] = {"label": parsed_doc.title, "shape": "rectangle"}

        # Group endpoints by tags
        tags_endpoints: Dict[str, List[ParsedEndpoint]] = {}
        for endpoint in parsed_doc.endpoints:
            tag = endpoint.tags[0] if endpoint.tags else "Other"
            if tag not in tags_endpoints:
                tags_endpoints[tag] = []
            tags_endpoints[tag].append(endpoint)

        # Add tag nodes
        for i, (tag, endpoints) in enumerate(tags_endpoints.items()):
            node_id = f"tag_{i}"
            count = len(endpoints)
            diagram.nodes[node_id] = {
                "label": f"{tag} ({count} endpoints)",
                "shape": "rounded"
            }
            diagram.edges.append({
                "from": "api",
                "to": node_id,
            })

        # Connect client to API
        diagram.edges.insert(0, {
            "from": "client",
            "to": "api",
        })

        return diagram

    @staticmethod
    def save_diagram(diagram, file_path: str):
        """
        Save diagram to file.

        Args:
            diagram: Diagram instance (SequenceDiagram, ERDiagram, FlowDiagram)
            file_path: Path to save file
        """
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(diagram.to_mermaid())

        logger.info("Diagram saved", file_path=file_path)
