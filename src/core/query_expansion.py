"""
Query Expansion Module

Provides query expansion strategies to improve search recall by generating
additional query variations, related terms, and reformulations.

Query expansion helps overcome vocabulary mismatch between user queries
and document content by:
- Adding synonyms and related terms
- Generating query variations using LLM
- Creating multiple perspectives of the same query
- Pseudo-relevance feedback from top results

Author: API Assistant Team
Date: 2025-12-27
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ExpandedQuery:
    """Represents an expanded query with metadata."""

    original_query: str
    expanded_terms: List[str]
    query_variations: List[str]
    expansion_method: str
    confidence: float = 1.0

    def get_all_terms(self) -> List[str]:
        """Get all unique terms from original and expanded."""
        terms = set()
        terms.add(self.original_query)
        terms.update(self.expanded_terms)
        return list(terms)

    def get_all_queries(self) -> List[str]:
        """Get all query variations including original."""
        queries = [self.original_query]
        queries.extend(self.query_variations)
        return queries


class QueryExpander:
    """
    Query expansion system with multiple strategies.

    Supports:
    - Synonym expansion: Add related terms and synonyms
    - LLM-based expansion: Use LLM to generate query variations
    - Term expansion: Add domain-specific related terms
    - Multi-query: Generate multiple query perspectives
    """

    # Domain-specific term expansions for API/tech documentation
    DOMAIN_EXPANSIONS = {
        "auth": ["authentication", "authorization", "login", "signin", "oauth", "jwt"],
        "authentication": ["auth", "login", "signin", "verify", "credentials", "oauth", "jwt", "token"],
        "authorization": ["auth", "permissions", "access control", "roles", "oauth"],
        "oauth": ["oauth2", "authentication", "authorization", "token", "access token"],
        "jwt": ["json web token", "authentication", "token", "bearer token"],
        "token": ["access token", "bearer token", "jwt", "api key", "auth token"],
        "api": ["rest api", "endpoint", "web service", "http api", "rest"],
        "rest": ["rest api", "restful", "http api", "web service"],
        "endpoint": ["api endpoint", "route", "url", "path", "resource"],
        "request": ["http request", "api call", "query", "api request"],
        "response": ["http response", "api response", "result", "output"],
        "get": ["retrieve", "fetch", "read", "query"],
        "post": ["create", "add", "insert", "submit"],
        "put": ["update", "modify", "edit", "change"],
        "delete": ["remove", "destroy", "erase"],
        "error": ["exception", "failure", "bug", "issue", "problem"],
        "debug": ["troubleshoot", "diagnose", "investigate", "fix"],
        "config": ["configuration", "settings", "setup", "options"],
        "deploy": ["deployment", "release", "publish", "rollout"],
        "db": ["database", "data store", "persistence"],
        "cache": ["caching", "cache layer", "redis", "memcached"],
        "queue": ["message queue", "task queue", "job queue", "rabbitmq", "celery"],
        "async": ["asynchronous", "non-blocking", "concurrent", "parallel"],
        "sync": ["synchronous", "blocking", "sequential"],
    }

    # Common technical abbreviations
    ABBREVIATIONS = {
        "oauth": "oauth2",
        "jwt": "json web token",
        "api": "application programming interface",
        "rest": "representational state transfer",
        "http": "hypertext transfer protocol",
        "https": "hypertext transfer protocol secure",
        "url": "uniform resource locator",
        "json": "javascript object notation",
        "xml": "extensible markup language",
        "sql": "structured query language",
        "db": "database",
        "config": "configuration",
        "repo": "repository",
        "auth": "authentication",
        "admin": "administrator",
    }

    def __init__(
        self,
        llm_client: Optional[Any] = None,
        max_expansions: int = 5,
        enable_domain_expansions: bool = True,
        enable_abbreviations: bool = True,
    ):
        """
        Initialize query expander.

        Args:
            llm_client: Optional LLM client for LLM-based expansions
            max_expansions: Maximum number of expansion terms per query
            enable_domain_expansions: Enable domain-specific expansions
            enable_abbreviations: Enable abbreviation expansions
        """
        self.llm_client = llm_client
        self.max_expansions = max_expansions
        self.enable_domain_expansions = enable_domain_expansions
        self.enable_abbreviations = enable_abbreviations

    def expand_query(
        self,
        query: str,
        strategy: str = "auto",
        max_variations: int = 3,
    ) -> ExpandedQuery:
        """
        Expand a query using specified strategy.

        Args:
            query: Original query string
            strategy: Expansion strategy ("auto", "synonyms", "llm", "multi_query")
            max_variations: Maximum number of query variations to generate

        Returns:
            ExpandedQuery with expanded terms and variations
        """
        query = query.strip()

        if strategy == "auto":
            # Auto-detect best strategy based on query
            strategy = self._select_strategy(query)

        logger.debug(
            "Expanding query",
            query=query[:50],
            strategy=strategy,
            max_variations=max_variations,
        )

        if strategy == "synonyms":
            return self._expand_with_synonyms(query)
        elif strategy == "llm" and self.llm_client:
            return self._expand_with_llm(query, max_variations)
        elif strategy == "multi_query":
            return self._expand_multi_query(query, max_variations)
        elif strategy == "domain":
            return self._expand_with_domain_terms(query)
        else:
            # Fallback to domain expansion
            return self._expand_with_domain_terms(query)

    def _select_strategy(self, query: str) -> str:
        """Auto-select best expansion strategy for query."""
        query_lower = query.lower()

        # Check if query contains technical terms
        has_tech_terms = any(
            term in query_lower for term in self.DOMAIN_EXPANSIONS.keys()
        )

        # Check if query is a question
        is_question = any(
            query_lower.startswith(q) for q in ["how", "what", "where", "when", "why", "who"]
        )

        if is_question and self.llm_client:
            return "multi_query"  # Questions benefit from multi-query
        elif has_tech_terms:
            return "domain"  # Technical queries use domain expansions
        else:
            return "synonyms"  # Default to synonym expansion

    def _expand_with_synonyms(self, query: str) -> ExpandedQuery:
        """
        Expand query with synonyms and related terms.

        Uses domain-specific expansions and abbreviation handling.
        """
        expanded_terms = set()
        query_tokens = self._tokenize(query)

        # Add domain-specific expansions
        if self.enable_domain_expansions:
            for token in query_tokens:
                token_lower = token.lower()
                if token_lower in self.DOMAIN_EXPANSIONS:
                    expansions = self.DOMAIN_EXPANSIONS[token_lower]
                    expanded_terms.update(expansions[:self.max_expansions])

        # Add abbreviation expansions
        if self.enable_abbreviations:
            for token in query_tokens:
                token_lower = token.lower()
                if token_lower in self.ABBREVIATIONS:
                    expanded_terms.add(self.ABBREVIATIONS[token_lower])

        logger.debug(
            "Synonym expansion",
            original=query,
            expanded_count=len(expanded_terms),
        )

        return ExpandedQuery(
            original_query=query,
            expanded_terms=list(expanded_terms)[:self.max_expansions],
            query_variations=[],
            expansion_method="synonyms",
            confidence=0.9,
        )

    def _expand_with_domain_terms(self, query: str) -> ExpandedQuery:
        """Expand query with domain-specific technical terms."""
        return self._expand_with_synonyms(query)  # Same as synonym for now

    def _expand_with_llm(
        self,
        query: str,
        max_variations: int = 3,
    ) -> ExpandedQuery:
        """
        Expand query using LLM to generate variations.

        The LLM generates alternative phrasings that preserve intent.
        """
        if not self.llm_client:
            logger.warning("LLM client not available, falling back to synonym expansion")
            return self._expand_with_synonyms(query)

        try:
            prompt = f"""Given this search query about API documentation or technical concepts, generate {max_variations} alternative phrasings that preserve the original intent but use different wording.

Original query: "{query}"

Generate {max_variations} alternative queries, one per line, without numbering or bullets:"""

            response = self.llm_client.generate(
                prompt=prompt,
                max_tokens=150,
                temperature=0.7,
            )

            # Parse response into variations
            variations = []
            for line in response.strip().split("\n"):
                line = line.strip()
                # Remove numbering, bullets, quotes
                line = re.sub(r"^[\d\.\)\-\*]+\s*", "", line)
                line = line.strip('"\'')
                if line and line.lower() != query.lower():
                    variations.append(line)

            variations = variations[:max_variations]

            logger.info(
                "LLM query expansion",
                original=query,
                variations_count=len(variations),
            )

            return ExpandedQuery(
                original_query=query,
                expanded_terms=[],
                query_variations=variations,
                expansion_method="llm",
                confidence=0.85,
            )

        except Exception as e:
            logger.error("LLM expansion failed", error=str(e))
            return self._expand_with_synonyms(query)

    def _expand_multi_query(
        self,
        query: str,
        max_variations: int = 3,
    ) -> ExpandedQuery:
        """
        Generate multiple query variations for different perspectives.

        Particularly useful for question-based queries.
        """
        if self.llm_client:
            return self._expand_with_llm(query, max_variations)

        # Fallback: manual variations for common patterns
        variations = []
        query_lower = query.lower()

        # Transform questions into statements
        if query_lower.startswith("how to "):
            # "how to X" -> "X guide", "X tutorial"
            topic = query[7:]
            variations.append(f"{topic} guide")
            variations.append(f"{topic} tutorial")
            variations.append(f"{topic} documentation")
        elif query_lower.startswith("what is "):
            # "what is X" -> "X definition", "X explanation"
            topic = query[8:]
            variations.append(f"{topic} definition")
            variations.append(f"{topic} explanation")
            variations.append(f"{topic} overview")
        elif query_lower.startswith("why "):
            # "why X" -> "X reason", "X explanation"
            topic = query[4:]
            variations.append(f"{topic} reason")
            variations.append(f"{topic} explanation")

        variations = variations[:max_variations]

        logger.debug(
            "Multi-query expansion",
            original=query,
            variations_count=len(variations),
        )

        return ExpandedQuery(
            original_query=query,
            expanded_terms=[],
            query_variations=variations,
            expansion_method="multi_query",
            confidence=0.8,
        )

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Simple tokenization: split on whitespace and punctuation."""
        # Split on whitespace and common punctuation
        tokens = re.findall(r'\w+', text)
        return [t for t in tokens if len(t) > 1]  # Filter very short tokens

    def expand_and_format(self, query: str, strategy: str = "auto") -> str:
        """
        Expand query and format as a search string.

        Returns a formatted string with expanded terms that can be used
        directly in search.
        """
        expanded = self.expand_query(query, strategy=strategy)

        # Combine original and expanded terms
        all_terms = [query]
        all_terms.extend(expanded.expanded_terms)

        # Create formatted string (terms connected with OR-like semantics)
        formatted = " ".join(all_terms[:self.max_expansions + 1])

        logger.debug(
            "Formatted expanded query",
            original=query,
            formatted=formatted[:100],
        )

        return formatted


# Convenience functions
_default_expander: Optional[QueryExpander] = None


def get_query_expander(
    llm_client: Optional[Any] = None,
    max_expansions: int = 5,
) -> QueryExpander:
    """
    Get or create a query expander instance.

    Args:
        llm_client: Optional LLM client for advanced expansions
        max_expansions: Maximum expansion terms

    Returns:
        QueryExpander instance
    """
    global _default_expander

    if _default_expander is None:
        _default_expander = QueryExpander(
            llm_client=llm_client,
            max_expansions=max_expansions,
        )

    return _default_expander


def expand_query(
    query: str,
    strategy: str = "auto",
    llm_client: Optional[Any] = None,
) -> ExpandedQuery:
    """
    Quick helper to expand a query.

    Args:
        query: Query to expand
        strategy: Expansion strategy
        llm_client: Optional LLM client

    Returns:
        ExpandedQuery
    """
    expander = QueryExpander(llm_client=llm_client)
    return expander.expand_query(query, strategy=strategy)


__all__ = [
    "QueryExpander",
    "ExpandedQuery",
    "get_query_expander",
    "expand_query",
]
