"""
Query Analyzer Agent for intent classification.

This agent analyzes user queries to determine their intent and route them
to the appropriate downstream agents.
"""

import json
import re
from typing import Optional

import structlog

from src.agents.base_agent import BaseAgent
from src.agents.state import (
    AgentState,
    AgentType,
    IntentAnalysis,
    QueryIntent,
    add_to_processing_path,
    set_error,
)
from src.core.llm_client import LLMClient

logger = structlog.get_logger(__name__)


class QueryAnalyzer(BaseAgent):
    """
    Agent that analyzes user queries to determine intent and routing.

    This agent uses an LLM to classify the query into one of the predefined
    intent categories, extract keywords, and determine whether code generation
    or RAG retrieval is needed.

    Intent Categories:
        - GENERAL_QUESTION: General questions about API functionality
        - CODE_GENERATION: Requests to generate integration code
        - ENDPOINT_LOOKUP: Looking for specific endpoints
        - SCHEMA_EXPLANATION: Questions about data structures
        - AUTHENTICATION: Questions about API auth
        - DOCUMENTATION_GAP: Requests to identify missing docs

    Example:
        ```python
        analyzer = QueryAnalyzer()
        state = create_initial_state("How do I authenticate?")
        result = analyzer(state)

        # Access intent analysis
        intent = IntentAnalysis(**result["intent_analysis"])
        print(intent.primary_intent)  # QueryIntent.AUTHENTICATION
        print(intent.confidence)       # 0.95
        ```
    """

    # System prompt for intent classification
    INTENT_CLASSIFICATION_PROMPT = """You are an expert at analyzing user queries about APIs.

Your task is to classify the user's query into one of these intent categories:

1. **general_question** - General questions about API functionality, overview, or concepts
   Examples: "What does this API do?", "Tell me about the available endpoints"

2. **code_generation** - Requests to generate integration code
   Examples: "Generate Python code to call this endpoint", "Show me how to use the POST /users endpoint"

3. **endpoint_lookup** - Looking for specific endpoints by path, method, or functionality
   Examples: "Which endpoint creates a user?", "Find the endpoint for deleting orders"

4. **schema_explanation** - Questions about request/response schemas and data structures
   Examples: "What fields does the User object have?", "Explain the response format for GET /users"

5. **authentication** - Questions about API authentication and authorization
   Examples: "How do I authenticate?", "What are the auth requirements?", "Do I need an API key?"

6. **documentation_gap** - Requests to identify missing or incomplete documentation
   Examples: "What's missing in the docs?", "Find undocumented endpoints", "Check for incomplete descriptions"

Analyze the query and respond ONLY with a valid JSON object in this exact format:
{
  "primary_intent": "<one of the intents above>",
  "confidence": <number between 0 and 1>,
  "secondary_intents": ["<other possible intents>"],
  "keywords": ["<key terms from the query>"],
  "requires_code": <true/false>,
  "requires_retrieval": <true/false>
}

Guidelines:
- confidence: 0.9+ for very clear intent, 0.7-0.9 for clear, 0.5-0.7 for somewhat clear, <0.5 for unclear
- secondary_intents: List other possible interpretations (max 2)
- keywords: Extract 3-5 key terms that would be useful for searching
- requires_code: true if the user wants code examples/generation
- requires_retrieval: true if we need to search the API documentation (almost always true)

Respond ONLY with valid JSON, no other text."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Initialize the Query Analyzer agent.

        Args:
            llm_client: Optional LLM client (creates default if not provided).
        """
        super().__init__()
        self._llm_client = llm_client or LLMClient()

    @property
    def name(self) -> str:
        """Return the agent name."""
        return "query_analyzer"

    @property
    def agent_type(self) -> AgentType:
        """Return the agent type."""
        return AgentType.QUERY_ANALYZER

    @property
    def description(self) -> str:
        """Return the agent description."""
        return "Analyzes user queries to determine intent and routing requirements"

    def process(self, state: AgentState) -> AgentState:
        """
        Analyze the user query and update state with intent analysis.

        Args:
            state: Current agent state with 'query' field.

        Returns:
            Updated state with 'intent_analysis' populated.
        """
        query = state.get("query", "")

        if not query:
            self._logger.warning("No query provided to analyze")
            return set_error(
                state,
                agent=self.name,
                error_type="missing_input",
                message="No query provided for intent analysis",
                recoverable=False,
            )

        self._logger.info("Analyzing query intent", query=query[:100])

        try:
            # Get intent classification from LLM
            intent_analysis = self._classify_intent(query)

            # Log the analysis result
            self._logger.info(
                "Intent classified",
                intent=intent_analysis.primary_intent.value,
                confidence=intent_analysis.confidence,
                requires_code=intent_analysis.requires_code,
            )

            # Update state with intent analysis (serialized)
            updated_state = {
                **state,
                "intent_analysis": intent_analysis.model_dump(),
                "next_agent": self._determine_next_agent(intent_analysis),
            }

            return updated_state

        except Exception as e:
            self._logger.error("Intent analysis failed", error=str(e))
            return set_error(
                state,
                agent=self.name,
                error_type="classification_error",
                message=f"Failed to classify query intent: {str(e)}",
                recoverable=True,
            )

    def _classify_intent(self, query: str) -> IntentAnalysis:
        """
        Use LLM to classify the query intent.

        Args:
            query: The user's query string.

        Returns:
            IntentAnalysis with classification results.

        Raises:
            ValueError: If LLM response is invalid.
        """
        # Call LLM for classification
        response = self._llm_client.generate(
            prompt=f"Query to analyze: {query}",
            system_prompt=self.INTENT_CLASSIFICATION_PROMPT,
            temperature=0.3,  # Lower temperature for more consistent classification
            max_tokens=500,
        )

        # Parse JSON response
        try:
            # Extract JSON from response (handle cases where LLM adds extra text)
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON object found in LLM response")

            result = json.loads(json_match.group())

            # Validate and create IntentAnalysis
            primary_intent = QueryIntent(result["primary_intent"])
            confidence = float(result["confidence"])

            # Parse secondary intents
            secondary_intents = []
            for intent_str in result.get("secondary_intents", []):
                try:
                    secondary_intents.append(QueryIntent(intent_str))
                except ValueError:
                    self._logger.warning("Invalid secondary intent", intent=intent_str)

            # Create IntentAnalysis with automatic confidence level
            return IntentAnalysis.from_confidence(
                intent=primary_intent,
                score=confidence,
                secondary_intents=secondary_intents,
                keywords=result.get("keywords", []),
                requires_code=result.get("requires_code", False),
                requires_retrieval=result.get("requires_retrieval", True),
            )

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            self._logger.error("Failed to parse LLM response", error=str(e), response=response[:200])

            # Fallback: Use simple keyword matching
            return self._fallback_classification(query)

    def _fallback_classification(self, query: str) -> IntentAnalysis:
        """
        Fallback classification using simple keyword matching.

        Used when LLM classification fails.

        Args:
            query: The user's query string.

        Returns:
            IntentAnalysis with basic classification.
        """
        query_lower = query.lower()

        # Keyword patterns for each intent
        patterns = {
            QueryIntent.CODE_GENERATION: [
                "generate", "code", "example", "show me how", "write", "create code",
                "python", "javascript", "curl", "snippet"
            ],
            QueryIntent.AUTHENTICATION: [
                "auth", "authenticate", "login", "api key", "token", "credential",
                "authorization", "bearer", "oauth"
            ],
            QueryIntent.ENDPOINT_LOOKUP: [
                "endpoint", "which endpoint", "find endpoint", "what endpoint",
                "path", "route", "url for"
            ],
            QueryIntent.SCHEMA_EXPLANATION: [
                "schema", "fields", "response format", "request body", "data structure",
                "what fields", "object has", "response look like"
            ],
            QueryIntent.DOCUMENTATION_GAP: [
                "missing", "undocumented", "incomplete", "gap", "what's missing",
                "not documented", "documentation issue"
            ],
        }

        # Score each intent
        scores = {}
        for intent, keywords in patterns.items():
            score = sum(1 for kw in keywords if kw in query_lower)
            if score > 0:
                scores[intent] = score

        # Determine primary intent
        if scores:
            primary_intent = max(scores, key=scores.get)
            # Normalize confidence (0.5-0.7 for fallback)
            max_score = max(scores.values())
            confidence = 0.5 + (0.2 * (max_score / len(patterns[primary_intent])))
            confidence = min(confidence, 0.7)  # Cap at 0.7 for fallback
        else:
            primary_intent = QueryIntent.GENERAL_QUESTION
            confidence = 0.5

        # Extract simple keywords (split on spaces, remove common words)
        stop_words = {"the", "a", "an", "is", "are", "how", "do", "i", "to", "what", "in", "for"}
        keywords = [
            word.strip("?.,!")
            for word in query_lower.split()
            if len(word) > 3 and word not in stop_words
        ][:5]

        # Determine if code is needed
        requires_code = any(kw in query_lower for kw in ["generate", "code", "example", "show me"])

        self._logger.info(
            "Using fallback classification",
            intent=primary_intent.value,
            confidence=confidence,
        )

        return IntentAnalysis.from_confidence(
            intent=primary_intent,
            score=confidence,
            keywords=keywords,
            requires_code=requires_code,
            requires_retrieval=True,
        )

    def _determine_next_agent(self, intent: IntentAnalysis) -> str:
        """
        Determine which agent should process next based on intent.

        Args:
            intent: The classified intent analysis.

        Returns:
            Name of the next agent to route to.
        """
        # Map intents to agents
        routing = {
            QueryIntent.CODE_GENERATION: "code_generator",
            QueryIntent.DOCUMENTATION_GAP: "doc_analyzer",
            QueryIntent.GENERAL_QUESTION: "rag_agent",
            QueryIntent.ENDPOINT_LOOKUP: "rag_agent",
            QueryIntent.SCHEMA_EXPLANATION: "rag_agent",
            QueryIntent.AUTHENTICATION: "rag_agent",
        }

        next_agent = routing.get(intent.primary_intent, "rag_agent")

        self._logger.debug(
            "Determined next agent",
            intent=intent.primary_intent.value,
            next_agent=next_agent,
        )

        return next_agent
