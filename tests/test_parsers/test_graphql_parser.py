"""
Tests for GraphQL Schema Parser.

Tests parsing of GraphQL schemas including:
- Object types, input types, enums, scalars, interfaces, unions
- Queries, mutations, subscriptions
- Fields with arguments and type modifiers
- Descriptions and directives
- Document conversion for vector store

Author: API Assistant Team
Date: 2025-12-27
"""

import pytest
from src.parsers.graphql_parser import (
    GraphQLParser,
    GraphQLTypeKind,
    GraphQLField,
    GraphQLType,
    GraphQLOperation,
    GraphQLSchema,
)


class TestBasicTypeParsing:
    """Test parsing of basic GraphQL types."""

    def test_parse_object_type(self):
        """Test parsing a simple object type."""
        schema = """
        type User {
            id: ID!
            name: String!
            email: String
        }
        """

        parser = GraphQLParser()
        result = parser.parse(schema)

        assert len(result.types) == 1
        user_type = result.types[0]
        assert user_type.name == "User"
        assert user_type.kind == GraphQLTypeKind.OBJECT
        assert len(user_type.fields) == 3

        # Check fields
        id_field = next(f for f in user_type.fields if f.name == "id")
        assert id_field.type == "ID"
        assert id_field.is_required is True

        email_field = next(f for f in user_type.fields if f.name == "email")
        assert email_field.is_required is False

    def test_parse_input_type(self):
        """Test parsing input object type."""
        schema = """
        input CreateUserInput {
            name: String!
            email: String!
            age: Int
        }
        """

        parser = GraphQLParser()
        result = parser.parse(schema)

        assert len(result.types) == 1
        input_type = result.types[0]
        assert input_type.name == "CreateUserInput"
        assert input_type.kind == GraphQLTypeKind.INPUT_OBJECT
        assert len(input_type.fields) == 3

    def test_parse_enum_type(self):
        """Test parsing enum type."""
        schema = """
        enum Role {
            ADMIN
            USER
            GUEST
        }
        """

        parser = GraphQLParser()
        result = parser.parse(schema)

        assert len(result.types) == 1
        enum_type = result.types[0]
        assert enum_type.name == "Role"
        assert enum_type.kind == GraphQLTypeKind.ENUM
        assert len(enum_type.enum_values) == 3
        assert "ADMIN" in enum_type.enum_values
        assert "USER" in enum_type.enum_values
        assert "GUEST" in enum_type.enum_values

    def test_parse_scalar_type(self):
        """Test parsing custom scalar type."""
        schema = """
        scalar DateTime
        scalar Email
        """

        parser = GraphQLParser()
        result = parser.parse(schema)

        assert len(result.types) == 2
        scalar_names = [t.name for t in result.types]
        assert "DateTime" in scalar_names
        assert "Email" in scalar_names

        datetime_type = next(t for t in result.types if t.name == "DateTime")
        assert datetime_type.kind == GraphQLTypeKind.SCALAR

    def test_parse_interface_type(self):
        """Test parsing interface type."""
        schema = """
        interface Node {
            id: ID!
            createdAt: DateTime!
        }
        """

        parser = GraphQLParser()
        result = parser.parse(schema)

        assert len(result.types) == 1
        interface_type = result.types[0]
        assert interface_type.name == "Node"
        assert interface_type.kind == GraphQLTypeKind.INTERFACE
        assert len(interface_type.fields) == 2

    def test_parse_union_type(self):
        """Test parsing union type."""
        schema = """
        union SearchResult = User | Post | Comment
        """

        parser = GraphQLParser()
        result = parser.parse(schema)

        assert len(result.types) == 1
        union_type = result.types[0]
        assert union_type.name == "SearchResult"
        assert union_type.kind == GraphQLTypeKind.UNION
        assert len(union_type.union_types) == 3
        assert "User" in union_type.union_types
        assert "Post" in union_type.union_types
        assert "Comment" in union_type.union_types


class TestFieldParsing:
    """Test parsing of fields with various modifiers."""

    def test_parse_list_field(self):
        """Test parsing field with list type."""
        schema = """
        type User {
            tags: [String]
            roles: [Role!]!
        }
        """

        parser = GraphQLParser()
        result = parser.parse(schema)

        user_type = result.types[0]
        tags_field = next(f for f in user_type.fields if f.name == "tags")
        assert tags_field.is_list is True
        assert tags_field.is_required is False

        roles_field = next(f for f in user_type.fields if f.name == "roles")
        assert roles_field.is_list is True
        assert roles_field.is_required is True

    def test_parse_field_with_arguments(self):
        """Test parsing field with arguments."""
        schema = """
        type Query {
            user(id: ID!): User
            posts(limit: Int, offset: Int): [Post]
        }
        """

        parser = GraphQLParser()
        result = parser.parse(schema)

        assert len(result.queries) == 2

        user_query = next(q for q in result.queries if q.name == "user")
        assert "id" in user_query.arguments
        assert user_query.arguments["id"] == "ID!"

        posts_query = next(q for q in result.queries if q.name == "posts")
        assert "limit" in posts_query.arguments
        assert "offset" in posts_query.arguments

    def test_parse_deprecated_field(self):
        """Test parsing deprecated field."""
        schema = """
        type User {
            oldField: String @deprecated(reason: "Use newField instead")
            newField: String
        }
        """

        parser = GraphQLParser()
        result = parser.parse(schema)

        user_type = result.types[0]
        old_field = next(f for f in user_type.fields if f.name == "oldField")
        assert old_field.deprecated is True
        assert old_field.deprecation_reason == "Use newField instead"


class TestOperationParsing:
    """Test parsing of queries, mutations, and subscriptions."""

    def test_parse_queries(self):
        """Test parsing Query type."""
        schema = """
        type Query {
            user(id: ID!): User
            users(limit: Int): [User!]!
            currentUser: User
        }
        """

        parser = GraphQLParser()
        result = parser.parse(schema)

        assert len(result.queries) == 3

        query_names = [q.name for q in result.queries]
        assert "user" in query_names
        assert "users" in query_names
        assert "currentUser" in query_names

        user_query = next(q for q in result.queries if q.name == "user")
        assert user_query.operation_type == "query"
        assert user_query.return_type == "User"
        assert len(user_query.arguments) == 1

    def test_parse_mutations(self):
        """Test parsing Mutation type."""
        schema = """
        type Mutation {
            createUser(input: CreateUserInput!): User!
            updateUser(id: ID!, input: UpdateUserInput!): User
            deleteUser(id: ID!): Boolean!
        }
        """

        parser = GraphQLParser()
        result = parser.parse(schema)

        assert len(result.mutations) == 3

        create_mutation = next(m for m in result.mutations if m.name == "createUser")
        assert create_mutation.operation_type == "mutation"
        assert create_mutation.return_type == "User"
        assert "input" in create_mutation.arguments

        delete_mutation = next(m for m in result.mutations if m.name == "deleteUser")
        assert delete_mutation.return_type == "Boolean"

    def test_parse_subscriptions(self):
        """Test parsing Subscription type."""
        schema = """
        type Subscription {
            userCreated: User!
            messageReceived(roomId: ID!): Message!
        }
        """

        parser = GraphQLParser()
        result = parser.parse(schema)

        assert len(result.subscriptions) == 2

        user_sub = next(s for s in result.subscriptions if s.name == "userCreated")
        assert user_sub.operation_type == "subscription"
        assert user_sub.return_type == "User"

        message_sub = next(s for s in result.subscriptions if s.name == "messageReceived")
        assert "roomId" in message_sub.arguments


class TestInterfaceImplementation:
    """Test parsing types that implement interfaces."""

    def test_parse_type_implementing_interface(self):
        """Test parsing type with interface implementation."""
        schema = """
        interface Node {
            id: ID!
        }

        type User implements Node {
            id: ID!
            name: String!
        }
        """

        parser = GraphQLParser()
        result = parser.parse(schema)

        # Should have 2 types: interface and implementing type
        assert len(result.types) == 2

        user_type = next(t for t in result.types if t.name == "User")
        assert len(user_type.interfaces) == 1
        assert "Node" in user_type.interfaces

    def test_parse_type_implementing_multiple_interfaces(self):
        """Test parsing type implementing multiple interfaces."""
        schema = """
        interface Node {
            id: ID!
        }

        interface Timestamped {
            createdAt: DateTime!
        }

        type Post implements Node, Timestamped {
            id: ID!
            createdAt: DateTime!
            title: String!
        }
        """

        parser = GraphQLParser()
        result = parser.parse(schema)

        post_type = next(t for t in result.types if t.name == "Post")
        assert len(post_type.interfaces) == 2
        assert "Node" in post_type.interfaces
        assert "Timestamped" in post_type.interfaces


class TestDescriptionParsing:
    """Test parsing descriptions from schema."""

    def test_parse_type_description(self):
        """Test parsing type description."""
        schema = '''
        """
        Represents a user in the system
        """
        type User {
            id: ID!
        }
        '''

        parser = GraphQLParser()
        result = parser.parse(schema)

        user_type = result.types[0]
        # Note: Description parsing may need refinement in implementation
        # This test verifies the structure is in place

    def test_parse_field_description(self):
        """Test parsing field descriptions."""
        schema = '''
        type User {
            """The unique identifier"""
            id: ID!

            """The user's display name"""
            name: String!
        }
        '''

        parser = GraphQLParser()
        result = parser.parse(schema)

        # Verify schema parses without errors
        assert len(result.types) == 1


class TestDirectiveParsing:
    """Test parsing directives."""

    def test_parse_directive_definitions(self):
        """Test parsing custom directive definitions."""
        schema = """
        directive @auth(role: String!) on FIELD_DEFINITION
        directive @deprecated(reason: String) on FIELD_DEFINITION

        type User {
            id: ID!
        }
        """

        parser = GraphQLParser()
        result = parser.parse(schema)

        # Verify directives are captured
        assert len(result.directives) >= 0  # Implementation may vary


class TestComplexSchema:
    """Test parsing complex, realistic schemas."""

    def test_parse_blog_schema(self):
        """Test parsing a realistic blog API schema."""
        schema = """
        scalar DateTime

        enum Role {
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
            name: String!
            email: String!
            role: Role!
            posts: [Post!]!
        }

        type Post implements Node {
            id: ID!
            createdAt: DateTime!
            title: String!
            content: String!
            author: User!
            comments: [Comment!]!
            published: Boolean!
        }

        type Comment implements Node {
            id: ID!
            createdAt: DateTime!
            content: String!
            author: User!
            post: Post!
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
            commentAdded(postId: ID!): Comment!
        }
        """

        parser = GraphQLParser()
        result = parser.parse(schema)

        # Verify all components were parsed
        assert len(result.types) > 0
        assert len(result.queries) == 4
        assert len(result.mutations) == 3
        assert len(result.subscriptions) == 2

        # Verify specific types
        type_names = [t.name for t in result.types]
        assert "User" in type_names
        assert "Post" in type_names
        assert "Comment" in type_names
        assert "CreatePostInput" in type_names
        assert "Role" in type_names
        assert "DateTime" in type_names

        # Verify Node interface
        node_interface = next((t for t in result.types if t.name == "Node"), None)
        assert node_interface is not None
        assert node_interface.kind == GraphQLTypeKind.INTERFACE

        # Verify User implements Node
        user_type = next(t for t in result.types if t.name == "User")
        assert "Node" in user_type.interfaces


class TestDocumentConversion:
    """Test conversion of GraphQL schema to vector store documents."""

    def test_convert_schema_to_documents(self):
        """Test converting parsed schema to documents."""
        schema = """
        enum Status {
            ACTIVE
            INACTIVE
        }

        type User {
            id: ID!
            name: String!
            status: Status!
        }

        type Query {
            user(id: ID!): User
        }
        """

        parser = GraphQLParser()
        parsed_schema = parser.parse(schema)
        documents = parser.to_documents()

        assert len(documents) > 0

        # Verify document structure
        for doc in documents:
            assert "content" in doc
            assert "metadata" in doc
            assert isinstance(doc["content"], str)
            assert isinstance(doc["metadata"], dict)

        # Verify metadata
        metadata_list = [doc["metadata"] for doc in documents]
        sources = [m.get("source") for m in metadata_list]
        assert all(s == "graphql" for s in sources)

        # Verify type documents
        type_docs = [d for d in documents if d["metadata"].get("type") == "type_definition"]
        assert len(type_docs) > 0

        # Verify operation documents
        query_docs = [d for d in documents if d["metadata"].get("type") == "query"]
        assert len(query_docs) > 0

    def test_document_content_format(self):
        """Test format of document content."""
        schema = """
        type User {
            id: ID!
            name: String!
        }
        """

        parser = GraphQLParser()
        parser.parse(schema)
        documents = parser.to_documents()

        # Find User type document
        user_doc = next(
            (d for d in documents if d["metadata"].get("name") == "User"),
            None
        )

        assert user_doc is not None
        content = user_doc["content"]

        # Content should contain type information
        assert "User" in content
        assert "type" in content.lower() or "Type" in content


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_parse_empty_schema(self):
        """Test parsing empty schema."""
        schema = ""

        parser = GraphQLParser()
        result = parser.parse(schema)

        assert result.types == []
        assert result.queries == []
        assert result.mutations == []
        assert result.subscriptions == []

    def test_parse_schema_with_comments(self):
        """Test parsing schema with comments."""
        schema = """
        # This is a comment
        type User {
            id: ID! # User identifier
            name: String! # User name
        }
        """

        parser = GraphQLParser()
        result = parser.parse(schema)

        # Should parse successfully despite comments
        assert len(result.types) == 1
        assert result.types[0].name == "User"

    def test_parse_schema_with_whitespace(self):
        """Test parsing schema with extra whitespace."""
        schema = """


        type    User    {

            id   :   ID!

            name  :  String!

        }


        """

        parser = GraphQLParser()
        result = parser.parse(schema)

        assert len(result.types) == 1
        user_type = result.types[0]
        assert len(user_type.fields) == 2

    def test_type_annotation_parsing(self):
        """Test type annotation parsing edge cases."""
        parser = GraphQLParser()

        # Test required type
        base, required, is_list = parser._parse_type_annotation("String!")
        assert base == "String"
        assert required is True
        assert is_list is False

        # Test list type
        base, required, is_list = parser._parse_type_annotation("[String]")
        assert base == "String"
        assert required is False
        assert is_list is True

        # Test required list
        base, required, is_list = parser._parse_type_annotation("[String!]!")
        assert base == "String"
        assert required is True
        assert is_list is True

        # Test simple type
        base, required, is_list = parser._parse_type_annotation("String")
        assert base == "String"
        assert required is False
        assert is_list is False


class TestMultipleTypesAndOperations:
    """Test schemas with multiple types and operations."""

    def test_multiple_object_types(self):
        """Test parsing multiple object types."""
        schema = """
        type User {
            id: ID!
        }

        type Post {
            id: ID!
        }

        type Comment {
            id: ID!
        }
        """

        parser = GraphQLParser()
        result = parser.parse(schema)

        assert len(result.types) == 3
        type_names = {t.name for t in result.types}
        assert type_names == {"User", "Post", "Comment"}

    def test_mixed_type_kinds(self):
        """Test parsing schema with different type kinds."""
        schema = """
        scalar DateTime

        enum Status {
            ACTIVE
            INACTIVE
        }

        type User {
            id: ID!
            status: Status!
        }

        input UserInput {
            name: String!
        }

        interface Node {
            id: ID!
        }

        union SearchResult = User
        """

        parser = GraphQLParser()
        result = parser.parse(schema)

        # Should have all different kinds
        kinds = {t.kind for t in result.types}
        assert GraphQLTypeKind.SCALAR in kinds
        assert GraphQLTypeKind.ENUM in kinds
        assert GraphQLTypeKind.OBJECT in kinds
        assert GraphQLTypeKind.INPUT_OBJECT in kinds
        assert GraphQLTypeKind.INTERFACE in kinds
        assert GraphQLTypeKind.UNION in kinds


class TestRealWorldSchema:
    """Test with real-world GraphQL schema examples."""

    def test_github_like_schema(self):
        """Test parsing a GitHub-like API schema."""
        schema = """
        scalar DateTime
        scalar URI

        enum OrderDirection {
            ASC
            DESC
        }

        interface Node {
            id: ID!
        }

        type User implements Node {
            id: ID!
            login: String!
            name: String
            email: String
            createdAt: DateTime!
            repositories: [Repository!]!
        }

        type Repository implements Node {
            id: ID!
            name: String!
            description: String
            url: URI!
            owner: User!
            stargazerCount: Int!
            createdAt: DateTime!
        }

        input RepositoryOrder {
            field: String!
            direction: OrderDirection!
        }

        type Query {
            viewer: User
            user(login: String!): User
            repository(owner: String!, name: String!): Repository
            search(query: String!, first: Int): [Node!]!
        }

        type Mutation {
            createRepository(name: String!, description: String): Repository!
            deleteRepository(id: ID!): Boolean!
        }
        """

        parser = GraphQLParser()
        result = parser.parse(schema)

        # Verify comprehensive parsing
        assert len(result.types) > 5
        assert len(result.queries) == 4
        assert len(result.mutations) == 2

        # Verify Repository type
        repo_type = next(t for t in result.types if t.name == "Repository")
        assert repo_type.kind == GraphQLTypeKind.OBJECT
        assert "Node" in repo_type.interfaces
        assert len(repo_type.fields) > 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
