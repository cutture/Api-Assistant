"""
RAG (Retrieval-Augmented Generation) Agent for answering queries.

This agent retrieves relevant API documentation from the vector store
and generates comprehensive answers with proper source citations.
"""

from typing import Optional

import structlog

from src.agents.base_agent import BaseAgent
from src.agents.state import (
    AgentState,
    AgentType,
    IntentAnalysis,
    RetrievedDocument,
    SourceCitation,
    add_to_processing_path,
    set_error,
)
from src.core.llm_client import LLMClient
from src.core.vector_store import VectorStore, get_vector_store

logger = structlog.get_logger(__name__)


class RAGAgent(BaseAgent):
    """
    Retrieval-Augmented Generation agent for answering API-related queries.

    This agent enhances basic RAG with:
    - Multi-query expansion for better recall
    - Context relevance filtering
    - Source citation tracking
    - Metadata-based filtering (by HTTP method, endpoint, tags)
    - Comprehensive answer generation with references

    Example:
        ```python
        rag_agent = RAGAgent()
        state = create_initial_state("How do I authenticate?")
        state["intent_analysis"] = {...}
        result = rag_agent(state)

        # Access retrieved documents and response
        docs = result["retrieved_documents"]
        response = result["response"]
        citations = result["sources"]
        ```
    """

    # System prompt for answer generation
    ANSWER_GENERATION_PROMPT = """You are an expert API documentation assistant.

Your task is to answer the user's question using ONLY the provided API documentation context.

Guidelines:
- Provide clear, accurate answers based on the context
- If the context doesn't contain enough information, say so honestly
- Include specific details like endpoint paths, HTTP methods, parameters, and response formats
- Use code examples when helpful
- Cite sources by mentioning specific endpoints or sections
- Be concise but thorough
- Use markdown formatting for better readability

Context from API Documentation:
{context}

User Question: {query}

Provide a comprehensive answer based on the context above:"""

    # Prompt for query expansion
    QUERY_EXPANSION_PROMPT = """Generate 2-3 alternative phrasings of this API-related query that would help find relevant documentation.

Original Query: {query}

Generate variations that:
- Use different technical terms or synonyms
- Approach the question from different angles
- Include related concepts

Respond with one variation per line, no numbering or bullets:"""

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        llm_client: Optional[LLMClient] = None,
        top_k: int = 5,
        min_relevance_score: float = 0.3,
    ):
        """
        Initialize the RAG Agent.

        Args:
            vector_store: Vector store instance (creates default if not provided).
            llm_client: LLM client instance (creates default if not provided).
            top_k: Maximum number of documents to retrieve per query.
            min_relevance_score: Minimum relevance score (0-1) for filtering results.
        """
        super().__init__()
        self._vector_store = vector_store or get_vector_store()
        self._llm_client = llm_client or LLMClient()
        self.top_k = top_k
        self.min_relevance_score = min_relevance_score

    @property
    def name(self) -> str:
        """Return the agent name."""
        return "rag_agent"

    @property
    def agent_type(self) -> AgentType:
        """Return the agent type."""
        return AgentType.RAG_AGENT

    @property
    def description(self) -> str:
        """Return the agent description."""
        return "Retrieves API documentation and generates comprehensive answers with citations"

    def process(self, state: AgentState) -> AgentState:
        """
        Retrieve relevant documents and generate answer.

        Args:
            state: Current agent state with 'query' and optional 'intent_analysis'.

        Returns:
            Updated state with retrieved_documents, response, and sources.
        """
        query = state.get("query", "")
        if not query:
            self._logger.warning("No query provided to RAG agent")
            return set_error(
                state,
                agent=self.name,
                error_type="missing_input",
                message="No query provided for retrieval",
                recoverable=False,
            )

        self._logger.info("Processing RAG query", query=query[:100])

        try:
            # Extract intent analysis if available
            intent_analysis = None
            if state.get("intent_analysis"):
                intent_analysis = IntentAnalysis(**state["intent_analysis"])

            # Step 1: Retrieve relevant documents
            retrieved_docs = self._retrieve_documents(query, intent_analysis)

            if not retrieved_docs:
                self._logger.warning("No relevant documents found")
                return {
                    **state,
                    "retrieved_documents": [],
                    "response": "I couldn't find relevant information in the API documentation to answer your question. Please try rephrasing or ask about specific endpoints.",
                    "sources": [],
                }

            # Step 2: Generate answer from retrieved context
            response = self._generate_answer(query, retrieved_docs)

            # Step 3: Create source citations
            citations = self._create_citations(retrieved_docs)

            # Update state
            updated_state = {
                **state,
                "retrieved_documents": [doc.model_dump() for doc in retrieved_docs],
                "response": response,
                "sources": [citation.model_dump() for citation in citations],
                "context_text": self._format_context(retrieved_docs),
            }

            self._logger.info(
                "RAG processing complete",
                docs_retrieved=len(retrieved_docs),
                citations_created=len(citations),
            )

            return updated_state

        except Exception as e:
            self._logger.error("RAG processing failed", error=str(e))
            return set_error(
                state,
                agent=self.name,
                error_type="retrieval_error",
                message=f"Failed to retrieve and generate answer: {str(e)}",
                recoverable=True,
            )

    def _retrieve_documents(
        self,
        query: str,
        intent_analysis: Optional[IntentAnalysis] = None,
    ) -> list[RetrievedDocument]:
        """
        Retrieve relevant documents using multi-query expansion.

        Args:
            query: The user's query.
            intent_analysis: Optional intent analysis for filtering.

        Returns:
            List of retrieved documents with relevance scores.
        """
        # Generate query variations for better recall
        queries = self._expand_query(query, intent_analysis)
        self._logger.debug("Query expansion", original=query, variations=queries)

        # Retrieve documents for each query variation
        all_results = {}  # Use dict to deduplicate by doc_id

        for search_query in queries:
            # Build metadata filter if needed
            where_filter = self._build_metadata_filter(intent_analysis)

            # Search vector store
            results = self._vector_store.search(
                query=search_query,
                n_results=self.top_k,
                where=where_filter,
            )

            # Add to results (keeping highest score for duplicates)
            for result in results:
                doc_id = result["id"]
                score = result["score"]

                if doc_id not in all_results or score > all_results[doc_id]["score"]:
                    all_results[doc_id] = result

        # Filter by relevance score
        filtered_results = [
            result for result in all_results.values()
            if result["score"] >= self.min_relevance_score
        ]

        # Sort by score (highest first)
        filtered_results.sort(key=lambda x: x["score"], reverse=True)

        # Limit to top_k
        filtered_results = filtered_results[:self.top_k]

        # Convert to RetrievedDocument objects
        retrieved_docs = [
            RetrievedDocument(
                content=result["content"],
                metadata=result["metadata"],
                score=result["score"],
                doc_id=result["id"],
            )
            for result in filtered_results
        ]

        self._logger.info(
            "Documents retrieved",
            total_found=len(all_results),
            after_filtering=len(retrieved_docs),
        )

        return retrieved_docs

    def _expand_query(
        self,
        query: str,
        intent_analysis: Optional[IntentAnalysis] = None,
    ) -> list[str]:
        """
        Expand query into multiple variations for better recall.

        Args:
            query: The original query.
            intent_analysis: Optional intent analysis for context.

        Returns:
            List of query variations (includes original).
        """
        queries = [query]  # Always include original query

        # Add keyword-based variations
        if intent_analysis and intent_analysis.keywords:
            # Create a variation using extracted keywords
            keyword_query = " ".join(intent_analysis.keywords[:5])
            if keyword_query != query:
                queries.append(keyword_query)

        # Try LLM-based expansion (with fallback)
        try:
            expansion_prompt = self.QUERY_EXPANSION_PROMPT.format(query=query)
            response = self._llm_client.generate(
                prompt=expansion_prompt,
                temperature=0.7,
                max_tokens=200,
            )

            # Parse variations (one per line)
            variations = [
                line.strip()
                for line in response.strip().split("\n")
                if line.strip() and line.strip() != query
            ]

            # Add up to 2 variations
            queries.extend(variations[:2])

        except Exception as e:
            self._logger.warning("Query expansion failed, using original only", error=str(e))

        # Remove duplicates while preserving order
        seen = set()
        unique_queries = []
        for q in queries:
            q_lower = q.lower()
            if q_lower not in seen:
                seen.add(q_lower)
                unique_queries.append(q)

        return unique_queries[:3]  # Max 3 query variations

    def _build_metadata_filter(
        self,
        intent_analysis: Optional[IntentAnalysis] = None,
    ) -> Optional[dict]:
        """
        Build metadata filter for vector store search.

        Args:
            intent_analysis: Optional intent analysis for context.

        Returns:
            Metadata filter dict or None.
        """
        # For now, return None (no filtering)
        # In the future, could filter by:
        # - HTTP method (GET, POST, etc.)
        # - Endpoint tags
        # - Authentication requirements
        # - Specific endpoints if mentioned in keywords

        return None

    def _format_context(self, documents: list[RetrievedDocument]) -> str:
        """
        Format retrieved documents into context string.

        Args:
            documents: List of retrieved documents.

        Returns:
            Formatted context string.
        """
        if not documents:
            return ""

        context_parts = []
        for i, doc in enumerate(documents, 1):
            # Add metadata context if available
            metadata_str = ""
            if doc.metadata:
                parts = []
                if "endpoint" in doc.metadata:
                    parts.append(f"Endpoint: {doc.metadata['endpoint']}")
                if "method" in doc.metadata:
                    parts.append(f"Method: {doc.metadata['method']}")
                if "operation_id" in doc.metadata:
                    parts.append(f"Operation: {doc.metadata['operation_id']}")

                if parts:
                    metadata_str = f" [{', '.join(parts)}]"

            context_parts.append(f"[Source {i}]{metadata_str}\n{doc.content}\n")

        return "\n---\n\n".join(context_parts)

    def _generate_answer(
        self,
        query: str,
        documents: list[RetrievedDocument],
    ) -> str:
        """
        Generate answer using LLM with retrieved context.

        Args:
            query: The user's query.
            documents: Retrieved documents for context.

        Returns:
            Generated answer text.
        """
        # Format context
        context = self._format_context(documents)

        # Generate answer
        prompt = self.ANSWER_GENERATION_PROMPT.format(
            context=context,
            query=query,
        )

        response = self._llm_client.generate(
            prompt=prompt,
            temperature=0.3,  # Lower temperature for more focused answers
            max_tokens=2048,
        )

        return response.strip()

    def _create_citations(
        self,
        documents: list[RetrievedDocument],
    ) -> list[SourceCitation]:
        """
        Create source citations from retrieved documents.

        Args:
            documents: Retrieved documents.

        Returns:
            List of source citations.
        """
        citations = []

        for doc in documents:
            # Extract citation info from metadata
            endpoint_path = doc.metadata.get("endpoint", "")
            method = doc.metadata.get("method", "")

            # Create description
            if "operation_id" in doc.metadata:
                description = doc.metadata["operation_id"]
            elif "summary" in doc.metadata:
                description = doc.metadata["summary"]
            elif endpoint_path:
                description = f"Documentation for {endpoint_path}"
            else:
                description = "API Documentation"

            citation = SourceCitation(
                endpoint_path=endpoint_path,
                method=method,
                description=description,
                relevance_score=doc.score,
            )

            citations.append(citation)

        return citations

    def search_by_metadata(
        self,
        query: str,
        method: Optional[str] = None,
        endpoint: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> list[RetrievedDocument]:
        """
        Search with specific metadata filters.

        Args:
            query: The search query.
            method: Filter by HTTP method (GET, POST, etc.).
            endpoint: Filter by endpoint path.
            tags: Filter by tags.

        Returns:
            List of retrieved documents.
        """
        # Build where filter
        where = {}
        if method:
            where["method"] = method
        if endpoint:
            where["endpoint"] = endpoint
        if tags:
            # ChromaDB uses $in for array contains
            where["tags"] = {"$in": tags}

        # Search
        results = self._vector_store.search(
            query=query,
            n_results=self.top_k,
            where=where if where else None,
        )

        # Convert to RetrievedDocument objects
        return [
            RetrievedDocument(
                content=result["content"],
                metadata=result["metadata"],
                score=result["score"],
                doc_id=result["id"],
            )
            for result in results
            if result["score"] >= self.min_relevance_score
        ]
