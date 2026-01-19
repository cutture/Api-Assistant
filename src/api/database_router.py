"""
Database Query API Router.

Provides endpoints for SQL and NoSQL query generation, validation, and explanation.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any

from src.services.database_service import (
    DatabaseService,
    DatabaseType,
    QueryType,
    QueryRisk,
    get_database_service,
)

router = APIRouter(prefix="/database", tags=["database"])


# Request/Response Models

class ValidateQueryRequest(BaseModel):
    """Request to validate a database query."""
    query: str = Field(..., description="The query to validate")
    database_type: str = Field(
        default="postgresql",
        description="Database type: postgresql, mysql, sqlite, mongodb"
    )


class ValidationResponse(BaseModel):
    """Validation result response."""
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    risk_level: str
    query_type: str | None
    affected_tables: list[str]
    has_where_clause: bool
    is_parameterized: bool


class ExplainQueryRequest(BaseModel):
    """Request to explain a database query."""
    query: str = Field(..., description="The query to explain")
    database_type: str = Field(
        default="postgresql",
        description="Database type: postgresql, mysql, sqlite, mongodb"
    )


class ExplanationResponse(BaseModel):
    """Query explanation response."""
    summary: str
    query_type: str
    database_type: str
    tables_involved: list[str]
    columns_involved: list[str]
    conditions: list[str]
    operations: list[str]
    performance_hints: list[str]
    security_notes: list[str]


class GenerateSelectRequest(BaseModel):
    """Request to generate a SELECT query."""
    table: str = Field(..., description="Table name")
    columns: list[str] | None = Field(None, description="Columns to select (None for *)")
    conditions: dict[str, Any] | None = Field(None, description="WHERE conditions")
    order_by: str | None = Field(None, description="Column to order by")
    order_direction: str = Field("ASC", description="ASC or DESC")
    limit: int | None = Field(None, description="Maximum rows")
    offset: int | None = Field(None, description="Rows to skip")
    database_type: str = Field(default="postgresql")


class GenerateInsertRequest(BaseModel):
    """Request to generate an INSERT query."""
    table: str = Field(..., description="Table name")
    data: dict[str, Any] = Field(..., description="Column-value pairs")
    database_type: str = Field(default="postgresql")
    returning: str | None = Field(None, description="Column to return (PostgreSQL)")


class GenerateUpdateRequest(BaseModel):
    """Request to generate an UPDATE query."""
    table: str = Field(..., description="Table name")
    data: dict[str, Any] = Field(..., description="Column-value pairs to update")
    conditions: dict[str, Any] = Field(..., description="WHERE conditions")
    database_type: str = Field(default="postgresql")


class GenerateDeleteRequest(BaseModel):
    """Request to generate a DELETE query."""
    table: str = Field(..., description="Table name")
    conditions: dict[str, Any] = Field(..., description="WHERE conditions")
    database_type: str = Field(default="postgresql")


class GenerateCreateTableRequest(BaseModel):
    """Request to generate a CREATE TABLE query."""
    table: str = Field(..., description="Table name")
    columns: dict[str, dict] = Field(
        ...,
        description="Column definitions",
        examples=[{
            "id": {"type": "integer", "primary_key": True},
            "name": {"type": "string", "nullable": False},
            "email": {"type": "string", "unique": True}
        }]
    )
    database_type: str = Field(default="postgresql")


class GenerateMongoFindRequest(BaseModel):
    """Request to generate a MongoDB find query."""
    collection: str = Field(..., description="Collection name")
    filter_query: dict | None = Field(None, description="Filter criteria")
    projection: dict | None = Field(None, description="Fields to include/exclude")
    sort: dict | None = Field(None, description="Sort specification")
    limit: int | None = Field(None, description="Maximum documents")
    skip: int | None = Field(None, description="Documents to skip")


class GenerateMongoAggregateRequest(BaseModel):
    """Request to generate a MongoDB aggregation pipeline."""
    collection: str = Field(..., description="Collection name")
    pipeline: list[dict] = Field(..., description="Aggregation pipeline stages")


class NaturalLanguageRequest(BaseModel):
    """Request to convert natural language to query."""
    description: str = Field(..., description="Natural language query description")
    table_schema: dict | None = Field(None, description="Optional schema information")
    database_type: str = Field(default="postgresql")


class GeneratedQueryResponse(BaseModel):
    """Generated query response."""
    query: str
    database_type: str
    query_type: str
    parameters: dict[str, Any]
    validation: ValidationResponse | None
    explanation: ExplanationResponse | None


def _parse_database_type(db_type: str) -> DatabaseType:
    """Parse database type string to enum."""
    try:
        return DatabaseType(db_type.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid database type: {db_type}. "
                   f"Supported: postgresql, mysql, sqlite, mongodb"
        )


def _validation_to_response(validation) -> ValidationResponse:
    """Convert validation result to response model."""
    return ValidationResponse(
        is_valid=validation.is_valid,
        errors=validation.errors,
        warnings=validation.warnings,
        risk_level=validation.risk_level.value,
        query_type=validation.query_type.value if validation.query_type else None,
        affected_tables=validation.affected_tables,
        has_where_clause=validation.has_where_clause,
        is_parameterized=validation.is_parameterized,
    )


def _explanation_to_response(explanation) -> ExplanationResponse:
    """Convert explanation to response model."""
    return ExplanationResponse(
        summary=explanation.summary,
        query_type=explanation.query_type.value,
        database_type=explanation.database_type.value,
        tables_involved=explanation.tables_involved,
        columns_involved=explanation.columns_involved,
        conditions=explanation.conditions,
        operations=explanation.operations,
        performance_hints=explanation.performance_hints,
        security_notes=explanation.security_notes,
    )


def _generated_to_response(generated) -> GeneratedQueryResponse:
    """Convert generated query to response model."""
    return GeneratedQueryResponse(
        query=generated.query,
        database_type=generated.database_type.value,
        query_type=generated.query_type.value,
        parameters=generated.parameters,
        validation=_validation_to_response(generated.validation) if generated.validation else None,
        explanation=_explanation_to_response(generated.explanation) if generated.explanation else None,
    )


# Endpoints

@router.post("/validate", response_model=ValidationResponse)
async def validate_query(request: ValidateQueryRequest):
    """
    Validate a database query for syntax and security issues.

    Checks for:
    - Dangerous patterns (DROP, TRUNCATE, etc.)
    - Missing WHERE clauses in UPDATE/DELETE
    - SQL injection patterns
    - Parameterized query usage
    """
    service = get_database_service()
    db_type = _parse_database_type(request.database_type)

    result = service.validate_query(request.query, db_type)
    return _validation_to_response(result)


@router.post("/explain", response_model=ExplanationResponse)
async def explain_query(request: ExplainQueryRequest):
    """
    Generate a human-readable explanation of what a query does.

    Returns:
    - Summary of the operation
    - Tables and columns involved
    - Conditions applied
    - Performance hints
    - Security notes
    """
    service = get_database_service()
    db_type = _parse_database_type(request.database_type)

    result = service.explain_query(request.query, db_type)
    return _explanation_to_response(result)


@router.post("/generate/select", response_model=GeneratedQueryResponse)
async def generate_select(request: GenerateSelectRequest):
    """
    Generate a SELECT query with automatic parameterization.

    Supports:
    - Column selection
    - WHERE conditions
    - ORDER BY
    - LIMIT/OFFSET
    """
    service = get_database_service()
    db_type = _parse_database_type(request.database_type)

    result = service.generate_select_query(
        table=request.table,
        columns=request.columns,
        conditions=request.conditions,
        order_by=request.order_by,
        order_direction=request.order_direction,
        limit=request.limit,
        offset=request.offset,
        database_type=db_type,
    )
    return _generated_to_response(result)


@router.post("/generate/insert", response_model=GeneratedQueryResponse)
async def generate_insert(request: GenerateInsertRequest):
    """
    Generate an INSERT query with automatic parameterization.

    Supports:
    - Multiple column-value pairs
    - RETURNING clause (PostgreSQL)
    """
    service = get_database_service()
    db_type = _parse_database_type(request.database_type)

    result = service.generate_insert_query(
        table=request.table,
        data=request.data,
        database_type=db_type,
        returning=request.returning,
    )
    return _generated_to_response(result)


@router.post("/generate/update", response_model=GeneratedQueryResponse)
async def generate_update(request: GenerateUpdateRequest):
    """
    Generate an UPDATE query with automatic parameterization.

    Always requires conditions to prevent accidental full-table updates.
    """
    service = get_database_service()
    db_type = _parse_database_type(request.database_type)

    if not request.conditions:
        raise HTTPException(
            status_code=400,
            detail="Conditions are required for UPDATE queries to prevent accidental data loss"
        )

    result = service.generate_update_query(
        table=request.table,
        data=request.data,
        conditions=request.conditions,
        database_type=db_type,
    )
    return _generated_to_response(result)


@router.post("/generate/delete", response_model=GeneratedQueryResponse)
async def generate_delete(request: GenerateDeleteRequest):
    """
    Generate a DELETE query with automatic parameterization.

    Always requires conditions to prevent accidental full-table deletes.
    """
    service = get_database_service()
    db_type = _parse_database_type(request.database_type)

    if not request.conditions:
        raise HTTPException(
            status_code=400,
            detail="Conditions are required for DELETE queries to prevent accidental data loss"
        )

    result = service.generate_delete_query(
        table=request.table,
        conditions=request.conditions,
        database_type=db_type,
    )
    return _generated_to_response(result)


@router.post("/generate/create-table", response_model=GeneratedQueryResponse)
async def generate_create_table(request: GenerateCreateTableRequest):
    """
    Generate a CREATE TABLE query.

    Column definition format:
    ```json
    {
      "id": {"type": "integer", "primary_key": true},
      "name": {"type": "string", "nullable": false},
      "email": {"type": "string", "unique": true},
      "created_at": {"type": "timestamp", "default": "CURRENT_TIMESTAMP"}
    }
    ```

    Supported types: string, text, integer, bigint, float, double, decimal,
    boolean, date, datetime, timestamp, json, uuid, binary
    """
    service = get_database_service()
    db_type = _parse_database_type(request.database_type)

    result = service.generate_create_table_query(
        table=request.table,
        columns=request.columns,
        database_type=db_type,
    )
    return _generated_to_response(result)


@router.post("/generate/mongodb/find", response_model=GeneratedQueryResponse)
async def generate_mongodb_find(request: GenerateMongoFindRequest):
    """
    Generate a MongoDB find query.

    Supports:
    - Filter criteria
    - Field projection
    - Sorting
    - Pagination (skip/limit)
    """
    service = get_database_service()

    result = service.generate_mongodb_find(
        collection=request.collection,
        filter_query=request.filter_query,
        projection=request.projection,
        sort=request.sort,
        limit=request.limit,
        skip=request.skip,
    )
    return _generated_to_response(result)


@router.post("/generate/mongodb/aggregate", response_model=GeneratedQueryResponse)
async def generate_mongodb_aggregate(request: GenerateMongoAggregateRequest):
    """
    Generate a MongoDB aggregation pipeline.

    Common stages:
    - $match: Filter documents
    - $group: Group and aggregate
    - $sort: Sort results
    - $project: Reshape documents
    - $lookup: Join collections
    """
    service = get_database_service()

    result = service.generate_mongodb_aggregate(
        collection=request.collection,
        pipeline=request.pipeline,
    )
    return _generated_to_response(result)


@router.post("/generate/natural-language", response_model=GeneratedQueryResponse)
async def generate_from_natural_language(request: NaturalLanguageRequest):
    """
    Convert natural language description to a database query.

    Examples:
    - "Get all users from the users table"
    - "Find the first 10 orders sorted by date"
    - "Insert a new product with name and price"

    Note: For complex queries, consider using the specific generation endpoints.
    """
    service = get_database_service()
    db_type = _parse_database_type(request.database_type)

    result = service.natural_language_to_query(
        description=request.description,
        table_schema=request.table_schema,
        database_type=db_type,
    )
    return _generated_to_response(result)


@router.get("/types")
async def get_supported_types():
    """
    Get supported database types and their features.
    """
    return {
        "databases": [
            {
                "id": "postgresql",
                "name": "PostgreSQL",
                "features": ["RETURNING", "JSONB", "Arrays", "UUID", "Full-text search"],
                "parameterization": "$1, $2, ...",
            },
            {
                "id": "mysql",
                "name": "MySQL",
                "features": ["AUTO_INCREMENT", "JSON", "Full-text search"],
                "parameterization": "%s",
            },
            {
                "id": "sqlite",
                "name": "SQLite",
                "features": ["Embedded", "Single-file", "JSON1 extension"],
                "parameterization": "?",
            },
            {
                "id": "mongodb",
                "name": "MongoDB",
                "features": ["Document store", "Aggregation pipeline", "Flexible schema"],
                "parameterization": "Object notation",
            },
        ],
        "column_types": [
            "string", "text", "integer", "bigint", "float", "double",
            "decimal", "boolean", "date", "datetime", "timestamp",
            "json", "uuid", "binary", "array"
        ]
    }


@router.get("/risk-levels")
async def get_risk_levels():
    """
    Get information about query risk levels.
    """
    return {
        "levels": [
            {
                "level": "low",
                "description": "Safe query with no dangerous operations",
                "color": "green",
            },
            {
                "level": "medium",
                "description": "Query contains patterns that should be reviewed",
                "color": "yellow",
            },
            {
                "level": "high",
                "description": "Query may cause data loss or security issues",
                "color": "orange",
            },
            {
                "level": "critical",
                "description": "Query contains extremely dangerous operations",
                "color": "red",
            },
        ],
        "dangerous_patterns": [
            "DROP TABLE/DATABASE",
            "TRUNCATE TABLE",
            "DELETE/UPDATE without WHERE",
            "Multiple statements (;)",
            "SQL comments (--)",
            "File operations (LOAD_FILE, INTO OUTFILE)",
        ]
    }
