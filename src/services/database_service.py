"""
Database Query Service.

Provides SQL and NoSQL query generation, validation, and explanation.
Supports PostgreSQL, MySQL, SQLite, and MongoDB.
"""

import re
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Any
from functools import lru_cache

logger = logging.getLogger(__name__)


class DatabaseType(str, Enum):
    """Supported database types."""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    MONGODB = "mongodb"


class QueryType(str, Enum):
    """Types of database queries."""
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    CREATE = "create"
    ALTER = "alter"
    DROP = "drop"
    AGGREGATE = "aggregate"  # MongoDB
    FIND = "find"  # MongoDB
    INDEX = "index"


class QueryRisk(str, Enum):
    """Risk level of a query."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class QueryValidationResult:
    """Result of query validation."""
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    risk_level: QueryRisk = QueryRisk.LOW
    query_type: Optional[QueryType] = None
    affected_tables: list[str] = field(default_factory=list)
    has_where_clause: bool = False
    is_parameterized: bool = False


@dataclass
class QueryExplanation:
    """Explanation of what a query does."""
    summary: str
    query_type: QueryType
    database_type: DatabaseType
    tables_involved: list[str]
    columns_involved: list[str]
    conditions: list[str]
    operations: list[str]
    performance_hints: list[str]
    security_notes: list[str]


@dataclass
class GeneratedQuery:
    """A generated database query."""
    query: str
    database_type: DatabaseType
    query_type: QueryType
    parameters: dict[str, Any] = field(default_factory=dict)
    explanation: Optional[QueryExplanation] = None
    validation: Optional[QueryValidationResult] = None
    sample_data: Optional[list[dict]] = None


class DatabaseService:
    """Service for database query generation, validation, and explanation."""

    # SQL keywords for parsing
    SQL_KEYWORDS = {
        'select', 'from', 'where', 'join', 'left', 'right', 'inner', 'outer',
        'on', 'and', 'or', 'not', 'in', 'like', 'between', 'is', 'null',
        'order', 'by', 'group', 'having', 'limit', 'offset', 'insert', 'into',
        'values', 'update', 'set', 'delete', 'create', 'table', 'alter', 'drop',
        'index', 'unique', 'primary', 'key', 'foreign', 'references', 'cascade',
        'union', 'all', 'distinct', 'as', 'count', 'sum', 'avg', 'min', 'max'
    }

    # Dangerous patterns that increase risk
    DANGEROUS_PATTERNS = [
        (r'\bDROP\s+(TABLE|DATABASE|INDEX)\b', QueryRisk.CRITICAL, "DROP statement detected"),
        (r'\bTRUNCATE\s+TABLE\b', QueryRisk.CRITICAL, "TRUNCATE statement detected"),
        (r'\bDELETE\s+FROM\s+\w+\s*(?:;|$)', QueryRisk.HIGH, "DELETE without WHERE clause"),
        (r'\bUPDATE\s+\w+\s+SET\s+.*(?:;|$)(?!.*WHERE)', QueryRisk.HIGH, "UPDATE without WHERE clause"),
        (r'--', QueryRisk.MEDIUM, "SQL comment detected (potential injection)"),
        (r'/\*', QueryRisk.MEDIUM, "Block comment detected"),
        (r';\s*\w', QueryRisk.HIGH, "Multiple statements detected"),
        (r'\bEXEC\b|\bEXECUTE\b', QueryRisk.HIGH, "EXEC statement detected"),
        (r'\bxp_\w+', QueryRisk.CRITICAL, "Extended stored procedure detected"),
        (r'\bSLEEP\s*\(', QueryRisk.HIGH, "SLEEP function detected"),
        (r'\bBENCHMARK\s*\(', QueryRisk.HIGH, "BENCHMARK function detected"),
        (r'\bLOAD_FILE\s*\(', QueryRisk.CRITICAL, "LOAD_FILE function detected"),
        (r'\bINTO\s+OUTFILE\b', QueryRisk.CRITICAL, "INTO OUTFILE detected"),
    ]

    # MongoDB dangerous operations
    MONGODB_DANGEROUS = [
        (r'\$where', QueryRisk.HIGH, "$where operator can execute arbitrary JavaScript"),
        (r'\.drop\(', QueryRisk.CRITICAL, "drop() method detected"),
        (r'\.remove\(\s*\{\s*\}', QueryRisk.HIGH, "remove({}) deletes all documents"),
        (r'\.deleteMany\(\s*\{\s*\}', QueryRisk.HIGH, "deleteMany({}) deletes all documents"),
    ]

    def __init__(self):
        """Initialize the database service."""
        self._type_mappings = {
            DatabaseType.POSTGRESQL: self._get_postgres_types(),
            DatabaseType.MYSQL: self._get_mysql_types(),
            DatabaseType.SQLITE: self._get_sqlite_types(),
            DatabaseType.MONGODB: self._get_mongodb_types(),
        }

    def _get_postgres_types(self) -> dict[str, str]:
        """Get PostgreSQL type mappings."""
        return {
            'string': 'VARCHAR(255)',
            'text': 'TEXT',
            'integer': 'INTEGER',
            'bigint': 'BIGINT',
            'float': 'REAL',
            'double': 'DOUBLE PRECISION',
            'decimal': 'DECIMAL',
            'boolean': 'BOOLEAN',
            'date': 'DATE',
            'datetime': 'TIMESTAMP',
            'timestamp': 'TIMESTAMP WITH TIME ZONE',
            'json': 'JSONB',
            'uuid': 'UUID',
            'binary': 'BYTEA',
            'array': 'ARRAY',
        }

    def _get_mysql_types(self) -> dict[str, str]:
        """Get MySQL type mappings."""
        return {
            'string': 'VARCHAR(255)',
            'text': 'TEXT',
            'integer': 'INT',
            'bigint': 'BIGINT',
            'float': 'FLOAT',
            'double': 'DOUBLE',
            'decimal': 'DECIMAL',
            'boolean': 'TINYINT(1)',
            'date': 'DATE',
            'datetime': 'DATETIME',
            'timestamp': 'TIMESTAMP',
            'json': 'JSON',
            'uuid': 'CHAR(36)',
            'binary': 'BLOB',
        }

    def _get_sqlite_types(self) -> dict[str, str]:
        """Get SQLite type mappings."""
        return {
            'string': 'TEXT',
            'text': 'TEXT',
            'integer': 'INTEGER',
            'bigint': 'INTEGER',
            'float': 'REAL',
            'double': 'REAL',
            'decimal': 'REAL',
            'boolean': 'INTEGER',
            'date': 'TEXT',
            'datetime': 'TEXT',
            'timestamp': 'TEXT',
            'json': 'TEXT',
            'uuid': 'TEXT',
            'binary': 'BLOB',
        }

    def _get_mongodb_types(self) -> dict[str, str]:
        """Get MongoDB type mappings."""
        return {
            'string': 'String',
            'text': 'String',
            'integer': 'Int32',
            'bigint': 'Int64',
            'float': 'Double',
            'double': 'Double',
            'decimal': 'Decimal128',
            'boolean': 'Boolean',
            'date': 'Date',
            'datetime': 'Date',
            'timestamp': 'Timestamp',
            'json': 'Object',
            'uuid': 'UUID',
            'binary': 'BinData',
            'array': 'Array',
            'objectid': 'ObjectId',
        }

    def validate_query(
        self,
        query: str,
        database_type: DatabaseType = DatabaseType.POSTGRESQL
    ) -> QueryValidationResult:
        """
        Validate a database query for syntax and security issues.

        Args:
            query: The query to validate
            database_type: The target database type

        Returns:
            QueryValidationResult with validation details
        """
        result = QueryValidationResult(is_valid=True)
        query_upper = query.upper().strip()

        # Detect query type
        result.query_type = self._detect_query_type(query_upper, database_type)

        # Check for dangerous patterns
        if database_type == DatabaseType.MONGODB:
            patterns = self.MONGODB_DANGEROUS
        else:
            patterns = self.DANGEROUS_PATTERNS

        max_risk = QueryRisk.LOW
        for pattern, risk, message in patterns:
            if re.search(pattern, query, re.IGNORECASE):
                result.warnings.append(message)
                if self._risk_level(risk) > self._risk_level(max_risk):
                    max_risk = risk

        result.risk_level = max_risk

        # SQL-specific validation
        if database_type != DatabaseType.MONGODB:
            # Check for WHERE clause in UPDATE/DELETE
            if result.query_type in [QueryType.UPDATE, QueryType.DELETE]:
                result.has_where_clause = 'WHERE' in query_upper
                if not result.has_where_clause:
                    result.warnings.append(
                        f"{result.query_type.value.upper()} without WHERE clause affects all rows"
                    )

            # Check for parameterized queries
            result.is_parameterized = bool(
                re.search(r'(\$\d+|%s|\?|:\w+)', query)
            )
            if not result.is_parameterized and result.query_type in [
                QueryType.INSERT, QueryType.UPDATE, QueryType.DELETE
            ]:
                result.warnings.append(
                    "Consider using parameterized queries to prevent SQL injection"
                )

            # Extract table names
            result.affected_tables = self._extract_tables(query)

            # Basic syntax validation
            syntax_errors = self._validate_sql_syntax(query, database_type)
            result.errors.extend(syntax_errors)

        else:
            # MongoDB validation
            syntax_errors = self._validate_mongodb_syntax(query)
            result.errors.extend(syntax_errors)

        result.is_valid = len(result.errors) == 0

        return result

    def _risk_level(self, risk: QueryRisk) -> int:
        """Convert risk to numeric level for comparison."""
        levels = {
            QueryRisk.LOW: 0,
            QueryRisk.MEDIUM: 1,
            QueryRisk.HIGH: 2,
            QueryRisk.CRITICAL: 3,
        }
        return levels.get(risk, 0)

    def _detect_query_type(
        self,
        query_upper: str,
        database_type: DatabaseType
    ) -> QueryType:
        """Detect the type of query."""
        if database_type == DatabaseType.MONGODB:
            if '.find(' in query_upper.lower() or 'find(' in query_upper.lower():
                return QueryType.FIND
            if '.aggregate(' in query_upper.lower():
                return QueryType.AGGREGATE
            if '.insert' in query_upper.lower():
                return QueryType.INSERT
            if '.update' in query_upper.lower():
                return QueryType.UPDATE
            if '.delete' in query_upper.lower() or '.remove(' in query_upper.lower():
                return QueryType.DELETE
            if '.createIndex(' in query_upper.lower():
                return QueryType.INDEX
            return QueryType.FIND

        # SQL detection
        if query_upper.startswith('SELECT'):
            return QueryType.SELECT
        if query_upper.startswith('INSERT'):
            return QueryType.INSERT
        if query_upper.startswith('UPDATE'):
            return QueryType.UPDATE
        if query_upper.startswith('DELETE'):
            return QueryType.DELETE
        if query_upper.startswith('CREATE'):
            return QueryType.CREATE
        if query_upper.startswith('ALTER'):
            return QueryType.ALTER
        if query_upper.startswith('DROP'):
            return QueryType.DROP

        return QueryType.SELECT

    def _extract_tables(self, query: str) -> list[str]:
        """Extract table names from SQL query."""
        tables = []

        # FROM clause
        from_match = re.search(
            r'\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            query,
            re.IGNORECASE
        )
        if from_match:
            tables.append(from_match.group(1))

        # JOIN clauses
        join_matches = re.findall(
            r'\bJOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            query,
            re.IGNORECASE
        )
        tables.extend(join_matches)

        # INSERT INTO
        insert_match = re.search(
            r'\bINSERT\s+INTO\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            query,
            re.IGNORECASE
        )
        if insert_match:
            tables.append(insert_match.group(1))

        # UPDATE
        update_match = re.search(
            r'\bUPDATE\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            query,
            re.IGNORECASE
        )
        if update_match:
            tables.append(update_match.group(1))

        # DELETE FROM
        delete_match = re.search(
            r'\bDELETE\s+FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            query,
            re.IGNORECASE
        )
        if delete_match:
            tables.append(delete_match.group(1))

        return list(set(tables))

    def _validate_sql_syntax(
        self,
        query: str,
        database_type: DatabaseType
    ) -> list[str]:
        """Basic SQL syntax validation."""
        errors = []
        query_stripped = query.strip()

        # Check for empty query
        if not query_stripped:
            errors.append("Query is empty")
            return errors

        # Check for unmatched parentheses
        if query_stripped.count('(') != query_stripped.count(')'):
            errors.append("Unmatched parentheses")

        # Check for unmatched quotes
        single_quotes = query_stripped.count("'") - query_stripped.count("\\'")
        if single_quotes % 2 != 0:
            errors.append("Unmatched single quotes")

        # Check for semicolon at end (optional but recommended)
        if not query_stripped.endswith(';'):
            pass  # Not an error, just a style choice

        return errors

    def _validate_mongodb_syntax(self, query: str) -> list[str]:
        """Basic MongoDB syntax validation."""
        errors = []
        query_stripped = query.strip()

        if not query_stripped:
            errors.append("Query is empty")
            return errors

        # Check for valid JSON-like structure in find queries
        if '.find(' in query_stripped:
            # Check parentheses balance
            if query_stripped.count('(') != query_stripped.count(')'):
                errors.append("Unmatched parentheses")

            # Check braces balance
            if query_stripped.count('{') != query_stripped.count('}'):
                errors.append("Unmatched curly braces")

            # Check brackets balance
            if query_stripped.count('[') != query_stripped.count(']'):
                errors.append("Unmatched square brackets")

        return errors

    def explain_query(
        self,
        query: str,
        database_type: DatabaseType = DatabaseType.POSTGRESQL
    ) -> QueryExplanation:
        """
        Generate a human-readable explanation of what a query does.

        Args:
            query: The query to explain
            database_type: The target database type

        Returns:
            QueryExplanation with detailed breakdown
        """
        query_type = self._detect_query_type(query.upper(), database_type)
        tables = self._extract_tables(query) if database_type != DatabaseType.MONGODB else []

        explanation = QueryExplanation(
            summary="",
            query_type=query_type,
            database_type=database_type,
            tables_involved=tables,
            columns_involved=[],
            conditions=[],
            operations=[],
            performance_hints=[],
            security_notes=[],
        )

        if database_type == DatabaseType.MONGODB:
            self._explain_mongodb(query, explanation)
        else:
            self._explain_sql(query, query_type, explanation)

        return explanation

    def _explain_sql(
        self,
        query: str,
        query_type: QueryType,
        explanation: QueryExplanation
    ) -> None:
        """Generate explanation for SQL query."""
        query_upper = query.upper()

        # Extract columns
        if query_type == QueryType.SELECT:
            select_match = re.search(
                r'SELECT\s+(.*?)\s+FROM',
                query,
                re.IGNORECASE | re.DOTALL
            )
            if select_match:
                cols = select_match.group(1)
                if cols.strip() == '*':
                    explanation.columns_involved = ['* (all columns)']
                else:
                    explanation.columns_involved = [
                        c.strip() for c in cols.split(',')
                    ]

        # Extract WHERE conditions
        where_match = re.search(
            r'WHERE\s+(.*?)(?:ORDER|GROUP|LIMIT|$)',
            query,
            re.IGNORECASE | re.DOTALL
        )
        if where_match:
            explanation.conditions = [where_match.group(1).strip()]
            explanation.operations.append("Filtering with WHERE clause")

        # Check for JOINs
        if 'JOIN' in query_upper:
            join_count = query_upper.count('JOIN')
            explanation.operations.append(f"Joining {join_count + 1} tables")

        # Check for aggregations
        agg_funcs = ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX']
        for func in agg_funcs:
            if func in query_upper:
                explanation.operations.append(f"Using {func} aggregation")

        # Check for GROUP BY
        if 'GROUP BY' in query_upper:
            explanation.operations.append("Grouping results")

        # Check for ORDER BY
        if 'ORDER BY' in query_upper:
            explanation.operations.append("Sorting results")

        # Check for LIMIT
        if 'LIMIT' in query_upper:
            explanation.operations.append("Limiting result count")

        # Generate summary
        if query_type == QueryType.SELECT:
            explanation.summary = f"Retrieves data from {', '.join(explanation.tables_involved) or 'table(s)'}"
        elif query_type == QueryType.INSERT:
            explanation.summary = f"Inserts new record(s) into {', '.join(explanation.tables_involved) or 'table'}"
        elif query_type == QueryType.UPDATE:
            explanation.summary = f"Updates record(s) in {', '.join(explanation.tables_involved) or 'table'}"
        elif query_type == QueryType.DELETE:
            explanation.summary = f"Deletes record(s) from {', '.join(explanation.tables_involved) or 'table'}"
        elif query_type == QueryType.CREATE:
            explanation.summary = "Creates a new database object"
        elif query_type == QueryType.DROP:
            explanation.summary = "Drops (deletes) a database object"
        else:
            explanation.summary = f"Executes {query_type.value} operation"

        # Performance hints
        if 'SELECT *' in query_upper:
            explanation.performance_hints.append(
                "Consider selecting specific columns instead of * for better performance"
            )
        if 'JOIN' in query_upper and 'INDEX' not in query_upper:
            explanation.performance_hints.append(
                "Ensure joined columns are indexed for better performance"
            )
        if 'LIKE' in query_upper and "LIKE '%" in query_upper:
            explanation.performance_hints.append(
                "Leading wildcard in LIKE prevents index usage"
            )
        if query_type in [QueryType.UPDATE, QueryType.DELETE] and 'WHERE' not in query_upper:
            explanation.performance_hints.append(
                "No WHERE clause - this affects ALL rows"
            )

        # Security notes
        validation = self.validate_query(query)
        explanation.security_notes = validation.warnings

    def _explain_mongodb(self, query: str, explanation: QueryExplanation) -> None:
        """Generate explanation for MongoDB query."""
        query_lower = query.lower()

        if '.find(' in query_lower:
            explanation.summary = "Finds documents matching the specified criteria"
            explanation.operations.append("Document retrieval")

            if '.sort(' in query_lower:
                explanation.operations.append("Sorting results")
            if '.limit(' in query_lower:
                explanation.operations.append("Limiting results")
            if '.skip(' in query_lower:
                explanation.operations.append("Skipping documents (pagination)")

        elif '.aggregate(' in query_lower:
            explanation.summary = "Performs aggregation pipeline operations"
            explanation.operations.append("Aggregation pipeline")

            # Common pipeline stages
            if '$match' in query_lower:
                explanation.operations.append("$match: Filtering documents")
            if '$group' in query_lower:
                explanation.operations.append("$group: Grouping documents")
            if '$sort' in query_lower:
                explanation.operations.append("$sort: Sorting documents")
            if '$project' in query_lower:
                explanation.operations.append("$project: Reshaping documents")
            if '$lookup' in query_lower:
                explanation.operations.append("$lookup: Joining collections")

        elif '.insertOne(' in query_lower or '.insertMany(' in query_lower:
            explanation.summary = "Inserts document(s) into the collection"
            explanation.operations.append("Document insertion")

        elif '.updateOne(' in query_lower or '.updateMany(' in query_lower:
            explanation.summary = "Updates document(s) in the collection"
            explanation.operations.append("Document update")

        elif '.deleteOne(' in query_lower or '.deleteMany(' in query_lower:
            explanation.summary = "Deletes document(s) from the collection"
            explanation.operations.append("Document deletion")

        elif '.createIndex(' in query_lower:
            explanation.summary = "Creates an index on the collection"
            explanation.operations.append("Index creation")

        # Performance hints for MongoDB
        if '.find({})' in query_lower or '.find()' in query_lower:
            explanation.performance_hints.append(
                "Empty filter returns all documents - consider adding criteria"
            )
        if '$regex' in query_lower:
            explanation.performance_hints.append(
                "Regex queries may not use indexes efficiently"
            )

    def generate_select_query(
        self,
        table: str,
        columns: list[str] | None = None,
        conditions: dict[str, Any] | None = None,
        order_by: str | None = None,
        order_direction: str = "ASC",
        limit: int | None = None,
        offset: int | None = None,
        database_type: DatabaseType = DatabaseType.POSTGRESQL
    ) -> GeneratedQuery:
        """
        Generate a SELECT query.

        Args:
            table: Table name
            columns: List of columns (None for *)
            conditions: WHERE conditions as dict
            order_by: Column to order by
            order_direction: ASC or DESC
            limit: Maximum rows to return
            offset: Number of rows to skip
            database_type: Target database

        Returns:
            GeneratedQuery with the generated SQL
        """
        cols = ', '.join(columns) if columns else '*'
        query = f"SELECT {cols}\nFROM {table}"

        params = {}
        if conditions:
            where_parts = []
            for i, (col, val) in enumerate(conditions.items()):
                param_name = f"p{i}"
                if database_type == DatabaseType.POSTGRESQL:
                    where_parts.append(f"{col} = ${i + 1}")
                elif database_type == DatabaseType.MYSQL:
                    where_parts.append(f"{col} = %s")
                else:
                    where_parts.append(f"{col} = ?")
                params[param_name] = val
            query += f"\nWHERE {' AND '.join(where_parts)}"

        if order_by:
            query += f"\nORDER BY {order_by} {order_direction}"

        if limit is not None:
            query += f"\nLIMIT {limit}"

        if offset is not None:
            query += f"\nOFFSET {offset}"

        query += ";"

        generated = GeneratedQuery(
            query=query,
            database_type=database_type,
            query_type=QueryType.SELECT,
            parameters=params,
        )
        generated.validation = self.validate_query(query, database_type)
        generated.explanation = self.explain_query(query, database_type)

        return generated

    def generate_insert_query(
        self,
        table: str,
        data: dict[str, Any],
        database_type: DatabaseType = DatabaseType.POSTGRESQL,
        returning: str | None = None
    ) -> GeneratedQuery:
        """
        Generate an INSERT query.

        Args:
            table: Table name
            data: Column-value pairs to insert
            database_type: Target database
            returning: Column to return (PostgreSQL only)

        Returns:
            GeneratedQuery with the generated SQL
        """
        columns = list(data.keys())
        cols_str = ', '.join(columns)

        if database_type == DatabaseType.POSTGRESQL:
            placeholders = ', '.join(f"${i + 1}" for i in range(len(columns)))
        elif database_type == DatabaseType.MYSQL:
            placeholders = ', '.join('%s' for _ in columns)
        else:
            placeholders = ', '.join('?' for _ in columns)

        query = f"INSERT INTO {table} ({cols_str})\nVALUES ({placeholders})"

        if returning and database_type == DatabaseType.POSTGRESQL:
            query += f"\nRETURNING {returning}"

        query += ";"

        params = {f"p{i}": v for i, v in enumerate(data.values())}

        generated = GeneratedQuery(
            query=query,
            database_type=database_type,
            query_type=QueryType.INSERT,
            parameters=params,
        )
        generated.validation = self.validate_query(query, database_type)
        generated.explanation = self.explain_query(query, database_type)

        return generated

    def generate_update_query(
        self,
        table: str,
        data: dict[str, Any],
        conditions: dict[str, Any],
        database_type: DatabaseType = DatabaseType.POSTGRESQL
    ) -> GeneratedQuery:
        """
        Generate an UPDATE query.

        Args:
            table: Table name
            data: Column-value pairs to update
            conditions: WHERE conditions
            database_type: Target database

        Returns:
            GeneratedQuery with the generated SQL
        """
        params = {}
        param_idx = 0

        # SET clause
        set_parts = []
        for col, val in data.items():
            if database_type == DatabaseType.POSTGRESQL:
                set_parts.append(f"{col} = ${param_idx + 1}")
            elif database_type == DatabaseType.MYSQL:
                set_parts.append(f"{col} = %s")
            else:
                set_parts.append(f"{col} = ?")
            params[f"p{param_idx}"] = val
            param_idx += 1

        # WHERE clause
        where_parts = []
        for col, val in conditions.items():
            if database_type == DatabaseType.POSTGRESQL:
                where_parts.append(f"{col} = ${param_idx + 1}")
            elif database_type == DatabaseType.MYSQL:
                where_parts.append(f"{col} = %s")
            else:
                where_parts.append(f"{col} = ?")
            params[f"p{param_idx}"] = val
            param_idx += 1

        query = f"UPDATE {table}\nSET {', '.join(set_parts)}\nWHERE {' AND '.join(where_parts)};"

        generated = GeneratedQuery(
            query=query,
            database_type=database_type,
            query_type=QueryType.UPDATE,
            parameters=params,
        )
        generated.validation = self.validate_query(query, database_type)
        generated.explanation = self.explain_query(query, database_type)

        return generated

    def generate_delete_query(
        self,
        table: str,
        conditions: dict[str, Any],
        database_type: DatabaseType = DatabaseType.POSTGRESQL
    ) -> GeneratedQuery:
        """
        Generate a DELETE query.

        Args:
            table: Table name
            conditions: WHERE conditions
            database_type: Target database

        Returns:
            GeneratedQuery with the generated SQL
        """
        params = {}
        where_parts = []

        for i, (col, val) in enumerate(conditions.items()):
            if database_type == DatabaseType.POSTGRESQL:
                where_parts.append(f"{col} = ${i + 1}")
            elif database_type == DatabaseType.MYSQL:
                where_parts.append(f"{col} = %s")
            else:
                where_parts.append(f"{col} = ?")
            params[f"p{i}"] = val

        query = f"DELETE FROM {table}\nWHERE {' AND '.join(where_parts)};"

        generated = GeneratedQuery(
            query=query,
            database_type=database_type,
            query_type=QueryType.DELETE,
            parameters=params,
        )
        generated.validation = self.validate_query(query, database_type)
        generated.explanation = self.explain_query(query, database_type)

        return generated

    def generate_create_table_query(
        self,
        table: str,
        columns: dict[str, dict],
        database_type: DatabaseType = DatabaseType.POSTGRESQL
    ) -> GeneratedQuery:
        """
        Generate a CREATE TABLE query.

        Args:
            table: Table name
            columns: Dict of column definitions
                {
                    "id": {"type": "integer", "primary_key": True},
                    "name": {"type": "string", "nullable": False},
                    "email": {"type": "string", "unique": True},
                }
            database_type: Target database

        Returns:
            GeneratedQuery with the generated SQL
        """
        type_map = self._type_mappings.get(database_type, {})
        col_defs = []
        primary_keys = []

        for col_name, col_spec in columns.items():
            col_type = type_map.get(col_spec.get('type', 'string'), 'TEXT')
            parts = [col_name, col_type]

            if col_spec.get('primary_key'):
                primary_keys.append(col_name)
                if database_type == DatabaseType.POSTGRESQL and col_type == 'INTEGER':
                    parts[1] = 'SERIAL'
                elif database_type == DatabaseType.MYSQL and col_type == 'INT':
                    parts.append('AUTO_INCREMENT')
                elif database_type == DatabaseType.SQLITE:
                    parts[1] = 'INTEGER'

            if not col_spec.get('nullable', True) and not col_spec.get('primary_key'):
                parts.append('NOT NULL')

            if col_spec.get('unique'):
                parts.append('UNIQUE')

            if 'default' in col_spec:
                default_val = col_spec['default']
                if isinstance(default_val, str):
                    parts.append(f"DEFAULT '{default_val}'")
                elif isinstance(default_val, bool):
                    parts.append(f"DEFAULT {str(default_val).upper()}")
                else:
                    parts.append(f"DEFAULT {default_val}")

            col_defs.append(' '.join(parts))

        # Add primary key constraint
        if primary_keys:
            if len(primary_keys) == 1 and database_type == DatabaseType.SQLITE:
                # SQLite handles single primary key inline
                for i, col_def in enumerate(col_defs):
                    if col_def.startswith(primary_keys[0]):
                        col_defs[i] += ' PRIMARY KEY'
            else:
                col_defs.append(f"PRIMARY KEY ({', '.join(primary_keys)})")

        query = f"CREATE TABLE {table} (\n    " + ",\n    ".join(col_defs) + "\n);"

        generated = GeneratedQuery(
            query=query,
            database_type=database_type,
            query_type=QueryType.CREATE,
            parameters={},
        )
        generated.validation = self.validate_query(query, database_type)
        generated.explanation = self.explain_query(query, database_type)

        return generated

    def generate_mongodb_find(
        self,
        collection: str,
        filter_query: dict | None = None,
        projection: dict | None = None,
        sort: dict | None = None,
        limit: int | None = None,
        skip: int | None = None
    ) -> GeneratedQuery:
        """
        Generate a MongoDB find query.

        Args:
            collection: Collection name
            filter_query: Filter criteria
            projection: Fields to include/exclude
            sort: Sort specification
            limit: Maximum documents
            skip: Documents to skip

        Returns:
            GeneratedQuery with the MongoDB query
        """
        import json

        parts = [f"db.{collection}.find("]

        # Filter
        filter_str = json.dumps(filter_query or {}, indent=2)
        parts.append(f"  {filter_str}")

        # Projection
        if projection:
            proj_str = json.dumps(projection, indent=2)
            parts.append(f",\n  {proj_str}")

        parts.append(")")

        # Chain methods
        if sort:
            sort_str = json.dumps(sort)
            parts.append(f".sort({sort_str})")

        if skip is not None:
            parts.append(f".skip({skip})")

        if limit is not None:
            parts.append(f".limit({limit})")

        query = "".join(parts)

        generated = GeneratedQuery(
            query=query,
            database_type=DatabaseType.MONGODB,
            query_type=QueryType.FIND,
            parameters=filter_query or {},
        )
        generated.validation = self.validate_query(query, DatabaseType.MONGODB)
        generated.explanation = self.explain_query(query, DatabaseType.MONGODB)

        return generated

    def generate_mongodb_aggregate(
        self,
        collection: str,
        pipeline: list[dict]
    ) -> GeneratedQuery:
        """
        Generate a MongoDB aggregation pipeline.

        Args:
            collection: Collection name
            pipeline: Aggregation pipeline stages

        Returns:
            GeneratedQuery with the MongoDB aggregation
        """
        import json

        pipeline_str = json.dumps(pipeline, indent=2)
        query = f"db.{collection}.aggregate({pipeline_str})"

        generated = GeneratedQuery(
            query=query,
            database_type=DatabaseType.MONGODB,
            query_type=QueryType.AGGREGATE,
            parameters={"pipeline": pipeline},
        )
        generated.validation = self.validate_query(query, DatabaseType.MONGODB)
        generated.explanation = self.explain_query(query, DatabaseType.MONGODB)

        return generated

    def natural_language_to_query(
        self,
        description: str,
        table_schema: dict | None = None,
        database_type: DatabaseType = DatabaseType.POSTGRESQL
    ) -> GeneratedQuery:
        """
        Convert natural language description to a database query.

        This is a simplified implementation. In production, this would
        use an LLM for more accurate conversion.

        Args:
            description: Natural language query description
            table_schema: Optional schema information
            database_type: Target database

        Returns:
            GeneratedQuery with the generated query
        """
        desc_lower = description.lower()

        # Simple pattern matching for common queries
        # In production, this would use an LLM

        # SELECT patterns
        if any(word in desc_lower for word in ['get', 'find', 'show', 'list', 'select', 'retrieve']):
            # Extract table name (simplified)
            words = description.split()
            table = "items"  # Default

            for word in ['from', 'in', 'table']:
                if word in desc_lower:
                    idx = words.index(word) if word in words else -1
                    if idx >= 0 and idx + 1 < len(words):
                        table = words[idx + 1].strip('.,')

            # Check for conditions
            conditions = {}
            if 'where' in desc_lower or 'with' in desc_lower:
                # Simplified condition extraction
                pass

            # Check for limit
            limit = None
            if 'first' in desc_lower or 'top' in desc_lower:
                for word in words:
                    if word.isdigit():
                        limit = int(word)
                        break

            return self.generate_select_query(
                table=table,
                limit=limit,
                database_type=database_type
            )

        # INSERT patterns
        if any(word in desc_lower for word in ['insert', 'add', 'create', 'new']):
            table = "items"
            data = {"column1": "value1"}  # Placeholder
            return self.generate_insert_query(table, data, database_type)

        # UPDATE patterns
        if any(word in desc_lower for word in ['update', 'change', 'modify', 'set']):
            table = "items"
            data = {"column1": "new_value"}
            conditions = {"id": 1}
            return self.generate_update_query(table, data, conditions, database_type)

        # DELETE patterns
        if any(word in desc_lower for word in ['delete', 'remove', 'drop']):
            table = "items"
            conditions = {"id": 1}
            return self.generate_delete_query(table, conditions, database_type)

        # Default: return a SELECT *
        return self.generate_select_query(
            table="table_name",
            database_type=database_type
        )


# Singleton instance
_database_service: DatabaseService | None = None


def get_database_service() -> DatabaseService:
    """Get or create the database service singleton."""
    global _database_service
    if _database_service is None:
        _database_service = DatabaseService()
    return _database_service
