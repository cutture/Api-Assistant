"""
GraphQL Schema Parser for API Assistant.

Parses GraphQL schema files (.graphql, .gql) and extracts:
- Types (Object, Input, Enum, Scalar, Interface, Union)
- Queries, Mutations, Subscriptions
- Fields with types and arguments
- Descriptions and documentation
- Directives

Author: API Assistant Team
Date: 2025-12-27
"""

import re
import structlog
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = structlog.get_logger(__name__)


class GraphQLTypeKind(Enum):
    """GraphQL type kinds."""

    OBJECT = "object"
    INPUT_OBJECT = "input_object"
    ENUM = "enum"
    SCALAR = "scalar"
    INTERFACE = "interface"
    UNION = "union"


@dataclass
class GraphQLField:
    """GraphQL field definition."""

    name: str
    type: str
    description: Optional[str] = None
    arguments: Dict[str, str] = field(default_factory=dict)
    is_required: bool = False
    is_list: bool = False
    deprecated: bool = False
    deprecation_reason: Optional[str] = None


@dataclass
class GraphQLType:
    """GraphQL type definition."""

    name: str
    kind: GraphQLTypeKind
    description: Optional[str] = None
    fields: List[GraphQLField] = field(default_factory=list)
    enum_values: List[str] = field(default_factory=list)
    interfaces: List[str] = field(default_factory=list)
    union_types: List[str] = field(default_factory=list)


@dataclass
class GraphQLOperation:
    """GraphQL operation (query, mutation, subscription)."""

    name: str
    operation_type: str  # "query", "mutation", "subscription"
    return_type: str
    description: Optional[str] = None
    arguments: Dict[str, str] = field(default_factory=dict)
    deprecated: bool = False


@dataclass
class GraphQLSchema:
    """Parsed GraphQL schema."""

    types: List[GraphQLType] = field(default_factory=list)
    queries: List[GraphQLOperation] = field(default_factory=list)
    mutations: List[GraphQLOperation] = field(default_factory=list)
    subscriptions: List[GraphQLOperation] = field(default_factory=list)
    directives: List[Dict[str, Any]] = field(default_factory=list)


class GraphQLParser:
    """Parser for GraphQL schema files."""

    def __init__(self):
        """Initialize GraphQL parser."""
        self.schema = GraphQLSchema()

    def parse(self, schema_content: str) -> GraphQLSchema:
        """
        Parse GraphQL schema content.

        Args:
            schema_content: GraphQL schema as string

        Returns:
            Parsed GraphQLSchema
        """
        logger.info("Parsing GraphQL schema")

        # Clean schema content
        content = self._clean_schema(schema_content)

        # Extract different elements
        self._parse_types(content)
        self._parse_operations(content)
        self._parse_directives(content)

        logger.info(
            "GraphQL schema parsed",
            types=len(self.schema.types),
            queries=len(self.schema.queries),
            mutations=len(self.schema.mutations),
            subscriptions=len(self.schema.subscriptions),
        )

        return self.schema

    def _clean_schema(self, content: str) -> str:
        """Remove comments and normalize whitespace."""
        # Remove single-line comments
        content = re.sub(r'#[^\n]*', '', content)

        # Remove multi-line comments (if any)
        content = re.sub(r'""".*?"""', '', content, flags=re.DOTALL)

        return content

    def _extract_description(self, content: str, before_position: int) -> Optional[str]:
        """Extract description from before a definition."""
        # Look for """ description """ before the definition
        lines = content[:before_position].split('\n')
        description_lines = []

        # Search backwards for description
        for line in reversed(lines):
            stripped = line.strip()
            if stripped.startswith('"""'):
                # Found start of description
                description_lines.reverse()
                return '\n'.join(description_lines).strip()
            elif description_lines or stripped:
                description_lines.append(stripped)
            if len(description_lines) > 20:  # Limit description length
                break

        return None

    def _parse_type_annotation(self, type_str: str) -> tuple[str, bool, bool]:
        """
        Parse GraphQL type annotation.

        Returns:
            Tuple of (base_type, is_required, is_list)
        """
        type_str = type_str.strip()
        is_required = type_str.endswith('!')
        is_list = '[' in type_str

        # Remove modifiers
        base_type = type_str.replace('!', '').replace('[', '').replace(']', '').strip()

        return base_type, is_required, is_list

    def _parse_fields(self, block: str) -> List[GraphQLField]:
        """Parse fields from a type block."""
        fields = []

        # Match field definitions: fieldName(args): Type
        field_pattern = r'(\w+)(\([^)]*\))?\s*:\s*([^\n]+)'
        matches = re.finditer(field_pattern, block)

        for match in matches:
            field_name = match.group(1)
            args_str = match.group(2) or ''
            type_str = match.group(3).strip()

            # Parse arguments
            arguments = {}
            if args_str:
                arg_pattern = r'(\w+)\s*:\s*([^,\)]+)'
                for arg_match in re.finditer(arg_pattern, args_str):
                    arg_name = arg_match.group(1)
                    arg_type = arg_match.group(2).strip()
                    arguments[arg_name] = arg_type

            # Parse type
            base_type, is_required, is_list = self._parse_type_annotation(type_str)

            # Check for deprecated directive
            deprecated = '@deprecated' in block
            deprecation_reason = None
            if deprecated:
                reason_match = re.search(
                    r'@deprecated\s*\(reason:\s*"([^"]+)"\)', block
                )
                if reason_match:
                    deprecation_reason = reason_match.group(1)

            field = GraphQLField(
                name=field_name,
                type=base_type,
                arguments=arguments,
                is_required=is_required,
                is_list=is_list,
                deprecated=deprecated,
                deprecation_reason=deprecation_reason,
            )

            fields.append(field)

        return fields

    def _parse_types(self, content: str):
        """Parse all type definitions."""
        # Parse object types
        self._parse_object_types(content, 'type', GraphQLTypeKind.OBJECT)

        # Parse input types
        self._parse_object_types(content, 'input', GraphQLTypeKind.INPUT_OBJECT)

        # Parse enums
        self._parse_enum_types(content)

        # Parse interfaces
        self._parse_object_types(content, 'interface', GraphQLTypeKind.INTERFACE)

        # Parse unions
        self._parse_union_types(content)

        # Parse scalars
        self._parse_scalar_types(content)

    def _parse_object_types(
        self, content: str, keyword: str, kind: GraphQLTypeKind
    ):
        """Parse object, input, or interface types."""
        pattern = rf'{keyword}\s+(\w+)(\s+implements\s+([^\{{]+))?\s*\{{([^}}]+)\}}'
        matches = re.finditer(pattern, content, re.DOTALL)

        for match in matches:
            type_name = match.group(1)
            implements = match.group(3)
            block = match.group(4)

            # Skip Query, Mutation, Subscription (handled separately)
            if type_name in ['Query', 'Mutation', 'Subscription']:
                continue

            # Parse interfaces
            interfaces = []
            if implements:
                interfaces = [i.strip() for i in implements.split(',')]

            # Parse fields
            fields = self._parse_fields(block)

            # Extract description
            description = self._extract_description(content, match.start())

            graphql_type = GraphQLType(
                name=type_name,
                kind=kind,
                description=description,
                fields=fields,
                interfaces=interfaces,
            )

            self.schema.types.append(graphql_type)

    def _parse_enum_types(self, content: str):
        """Parse enum types."""
        pattern = r'enum\s+(\w+)\s*\{([^}]+)\}'
        matches = re.finditer(pattern, content)

        for match in matches:
            enum_name = match.group(1)
            values_block = match.group(2)

            # Extract enum values
            values = re.findall(r'\b(\w+)\b', values_block)

            description = self._extract_description(content, match.start())

            graphql_type = GraphQLType(
                name=enum_name,
                kind=GraphQLTypeKind.ENUM,
                description=description,
                enum_values=values,
            )

            self.schema.types.append(graphql_type)

    def _parse_union_types(self, content: str):
        """Parse union types."""
        pattern = r'union\s+(\w+)\s*=\s*([^\n]+)'
        matches = re.finditer(pattern, content)

        for match in matches:
            union_name = match.group(1)
            types_str = match.group(2)

            # Extract union member types
            union_types = [t.strip() for t in types_str.split('|')]

            description = self._extract_description(content, match.start())

            graphql_type = GraphQLType(
                name=union_name,
                kind=GraphQLTypeKind.UNION,
                description=description,
                union_types=union_types,
            )

            self.schema.types.append(graphql_type)

    def _parse_scalar_types(self, content: str):
        """Parse custom scalar types."""
        pattern = r'scalar\s+(\w+)'
        matches = re.finditer(pattern, content)

        for match in matches:
            scalar_name = match.group(1)

            description = self._extract_description(content, match.start())

            graphql_type = GraphQLType(
                name=scalar_name,
                kind=GraphQLTypeKind.SCALAR,
                description=description,
            )

            self.schema.types.append(graphql_type)

    def _parse_operations(self, content: str):
        """Parse Query, Mutation, and Subscription types."""
        self._parse_operation_type(content, 'Query', 'query')
        self._parse_operation_type(content, 'Mutation', 'mutation')
        self._parse_operation_type(content, 'Subscription', 'subscription')

    def _parse_operation_type(
        self, content: str, type_name: str, operation_type: str
    ):
        """Parse a specific operation type."""
        pattern = rf'type\s+{type_name}\s*\{{([^}}]+)\}}'
        match = re.search(pattern, content, re.DOTALL)

        if not match:
            return

        block = match.group(1)
        fields = self._parse_fields(block)

        # Convert fields to operations
        for field in fields:
            operation = GraphQLOperation(
                name=field.name,
                operation_type=operation_type,
                return_type=field.type,
                description=field.description,
                arguments=field.arguments,
                deprecated=field.deprecated,
            )

            if operation_type == 'query':
                self.schema.queries.append(operation)
            elif operation_type == 'mutation':
                self.schema.mutations.append(operation)
            elif operation_type == 'subscription':
                self.schema.subscriptions.append(operation)

    def _parse_directives(self, content: str):
        """Parse directive definitions."""
        pattern = r'directive\s+@(\w+)(\([^)]*\))?\s+on\s+([^\n]+)'
        matches = re.finditer(pattern, content)

        for match in matches:
            directive_name = match.group(1)
            args_str = match.group(2) or ''
            locations = match.group(3)

            directive = {
                'name': directive_name,
                'arguments': args_str,
                'locations': [loc.strip() for loc in locations.split('|')],
            }

            self.schema.directives.append(directive)

    def to_documents(self) -> List[Dict[str, Any]]:
        """
        Convert GraphQL schema to vector store documents.

        Returns:
            List of documents ready for vector store indexing
        """
        documents = []

        # Add type documents
        for gql_type in self.schema.types:
            content = self._format_type_content(gql_type)
            metadata = {
                'source': 'graphql',
                'type': 'type_definition',
                'name': gql_type.name,
                'kind': gql_type.kind.value,
            }
            documents.append({'content': content, 'metadata': metadata})

            # Add individual field documents for better granularity
            for field in gql_type.fields:
                field_content = self._format_field_content(gql_type.name, field)
                field_metadata = {
                    'source': 'graphql',
                    'type': 'field',
                    'parent_type': gql_type.name,
                    'field_name': field.name,
                    'field_type': field.type,
                }
                documents.append({'content': field_content, 'metadata': field_metadata})

        # Add query documents
        for query in self.schema.queries:
            content = self._format_operation_content(query)
            metadata = {
                'source': 'graphql',
                'type': 'query',
                'name': query.name,
                'return_type': query.return_type,
            }
            documents.append({'content': content, 'metadata': metadata})

        # Add mutation documents
        for mutation in self.schema.mutations:
            content = self._format_operation_content(mutation)
            metadata = {
                'source': 'graphql',
                'type': 'mutation',
                'name': mutation.name,
                'return_type': mutation.return_type,
            }
            documents.append({'content': content, 'metadata': metadata})

        # Add subscription documents
        for subscription in self.schema.subscriptions:
            content = self._format_operation_content(subscription)
            metadata = {
                'source': 'graphql',
                'type': 'subscription',
                'name': subscription.name,
                'return_type': subscription.return_type,
            }
            documents.append({'content': content, 'metadata': metadata})

        logger.info("Converted GraphQL schema to documents", count=len(documents))
        return documents

    def _format_type_content(self, gql_type: GraphQLType) -> str:
        """Format type as content string."""
        lines = []

        # Header
        if gql_type.kind == GraphQLTypeKind.ENUM:
            lines.append(f"GraphQL Enum: {gql_type.name}")
        elif gql_type.kind == GraphQLTypeKind.UNION:
            lines.append(f"GraphQL Union: {gql_type.name}")
        elif gql_type.kind == GraphQLTypeKind.SCALAR:
            lines.append(f"GraphQL Scalar: {gql_type.name}")
        elif gql_type.kind == GraphQLTypeKind.INPUT_OBJECT:
            lines.append(f"GraphQL Input: {gql_type.name}")
        elif gql_type.kind == GraphQLTypeKind.INTERFACE:
            lines.append(f"GraphQL Interface: {gql_type.name}")
        else:
            lines.append(f"GraphQL Type: {gql_type.name}")

        # Description
        if gql_type.description:
            lines.append(f"\nDescription: {gql_type.description}")

        # Fields
        if gql_type.fields:
            lines.append("\nFields:")
            for field in gql_type.fields:
                field_line = f"  - {field.name}: {field.type}"
                if field.is_list:
                    field_line += " (list)"
                if field.is_required:
                    field_line += " (required)"
                if field.arguments:
                    args_str = ', '.join(
                        f"{k}: {v}" for k, v in field.arguments.items()
                    )
                    field_line += f" - Arguments: {args_str}"
                lines.append(field_line)

        # Enum values
        if gql_type.enum_values:
            lines.append("\nValues:")
            for value in gql_type.enum_values:
                lines.append(f"  - {value}")

        # Union types
        if gql_type.union_types:
            lines.append("\nTypes:")
            for union_type in gql_type.union_types:
                lines.append(f"  - {union_type}")

        # Interfaces
        if gql_type.interfaces:
            lines.append(f"\nImplements: {', '.join(gql_type.interfaces)}")

        return '\n'.join(lines)

    def _format_field_content(self, type_name: str, field: GraphQLField) -> str:
        """Format field as content string."""
        lines = [f"GraphQL Field: {type_name}.{field.name}"]

        if field.description:
            lines.append(f"\nDescription: {field.description}")

        type_str = field.type
        if field.is_list:
            type_str = f"[{type_str}]"
        if field.is_required:
            type_str += "!"

        lines.append(f"\nType: {type_str}")

        if field.arguments:
            lines.append("\nArguments:")
            for arg_name, arg_type in field.arguments.items():
                lines.append(f"  - {arg_name}: {arg_type}")

        if field.deprecated:
            lines.append("\n⚠️ Deprecated")
            if field.deprecation_reason:
                lines.append(f"Reason: {field.deprecation_reason}")

        return '\n'.join(lines)

    def _format_operation_content(self, operation: GraphQLOperation) -> str:
        """Format operation as content string."""
        op_type = operation.operation_type.capitalize()
        lines = [f"GraphQL {op_type}: {operation.name}"]

        if operation.description:
            lines.append(f"\nDescription: {operation.description}")

        lines.append(f"\nReturns: {operation.return_type}")

        if operation.arguments:
            lines.append("\nArguments:")
            for arg_name, arg_type in operation.arguments.items():
                lines.append(f"  - {arg_name}: {arg_type}")

        if operation.deprecated:
            lines.append("\n⚠️ Deprecated")

        # Add usage example
        args_str = ", ".join(
            f"{k}: ${k}" for k in operation.arguments.keys()
        )
        lines.append(f"\nExample:")
        lines.append(f"{operation.operation_type} {{")
        lines.append(f"  {operation.name}({args_str}) {{")
        lines.append(f"    # fields")
        lines.append(f"  }}")
        lines.append(f"}}")

        return '\n'.join(lines)


def parse_graphql_schema(schema_content: str) -> List[Dict[str, Any]]:
    """
    Parse GraphQL schema and return documents.

    Convenience function for parsing GraphQL schemas.

    Args:
        schema_content: GraphQL schema as string

    Returns:
        List of documents for vector store
    """
    parser = GraphQLParser()
    parser.parse(schema_content)
    return parser.to_documents()


__all__ = [
    "GraphQLParser",
    "GraphQLSchema",
    "GraphQLType",
    "GraphQLField",
    "GraphQLOperation",
    "GraphQLTypeKind",
    "parse_graphql_schema",
]
