"""
Gap Analysis Agent for detecting missing information.

This agent analyzes the current state and context to identify gaps
in information needed to fulfill the user's request. It determines
whether we have sufficient context or need to ask the user for more details.
"""

from typing import Optional

import structlog

from src.agents.base_agent import BaseAgent
from src.agents.state import (
    AgentState,
    AgentType,
    IntentAnalysis,
    set_error,
)
from src.core.llm_client import LLMClient, create_reasoning_client

logger = structlog.get_logger(__name__)


class GapAnalysisAgent(BaseAgent):
    """
    Gap Analysis agent for identifying missing information.

    This agent examines the query, intent, and available context to determine
    if we have enough information to proceed or if we need to ask the user
    for clarification or additional details.

    Example:
        ```python
        gap_agent = GapAnalysisAgent()
        state = {
            "query": "Generate code to create a user",
            "intent_analysis": {...},
            "retrieved_documents": [...],
        }
        result = gap_agent(state)

        if result.get("missing_info"):
            # Ask user for clarification
            questions = result["questions_for_user"]
        ```
    """

    # System prompt for gap analysis
    GAP_ANALYSIS_PROMPT = """You are an expert at analyzing whether we have sufficient information to fulfill a request.

Analyze the following:

**User Request**: {query}

**Intent**: {intent}

**Available Context**:
{context_summary}

**Task**: Determine if we have enough information to fulfill this request.

Consider:
1. For CODE GENERATION:
   - Do we know which endpoint to use?
   - Do we know the HTTP method?
   - Do we have parameter details?
   - Do we know the authentication method?
   - Do we have request/response formats?

2. For DOCUMENTATION QUERIES:
   - Do we have relevant API documentation?
   - Is the context specific enough?

3. For GENERAL QUERIES:
   - Is the question clear and answerable?

Respond in JSON format:
{{
    "has_sufficient_info": true/false,
    "confidence": 0.0-1.0,
    "missing_aspects": ["aspect1", "aspect2", ...],
    "questions_for_user": ["question1?", "question2?", ...],
    "reasoning": "Brief explanation"
}}

If has_sufficient_info is true, questions_for_user should be empty.
If false, provide 1-3 specific questions to ask the user.
"""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Initialize the Gap Analysis Agent.

        Args:
            llm_client: LLM client instance (creates reasoning client if not provided).
        """
        super().__init__()
        self._llm_client = llm_client or create_reasoning_client()

    @property
    def name(self) -> str:
        """Return the agent name."""
        return "gap_analysis_agent"

    @property
    def agent_type(self) -> AgentType:
        """Return the agent type."""
        return AgentType.CUSTOM

    @property
    def description(self) -> str:
        """Return the agent description."""
        return "Analyzes context to identify missing information and generate clarifying questions"

    def process(self, state: AgentState) -> AgentState:
        """
        Analyze context for information gaps.

        Args:
            state: Current agent state with query, intent, and context.

        Returns:
            Updated state with gap analysis results.
        """
        query = state.get("query", "")
        if not query:
            self._logger.warning("No query provided to gap analysis agent")
            return state

        self._logger.info("Analyzing information gaps", query=query[:100])

        try:
            # Extract intent analysis
            intent_analysis = None
            intent_str = "Unknown"
            if state.get("intent_analysis"):
                intent_analysis = IntentAnalysis(**state["intent_analysis"])
                intent_str = intent_analysis.primary_intent

            # Summarize available context
            context_summary = self._summarize_context(state)

            # Perform gap analysis
            gap_analysis = self._analyze_gaps(query, intent_str, context_summary)

            # Update state
            updated_state = {
                **state,
                "gap_analysis": gap_analysis,
                "has_sufficient_info": gap_analysis.get("has_sufficient_info", True),
                "missing_info": not gap_analysis.get("has_sufficient_info", True),
                "questions_for_user": gap_analysis.get("questions_for_user", []),
            }

            self._logger.info(
                "Gap analysis complete",
                has_sufficient_info=gap_analysis.get("has_sufficient_info"),
                num_questions=len(gap_analysis.get("questions_for_user", [])),
            )

            return updated_state

        except Exception as e:
            self._logger.error("Gap analysis failed", error=str(e))
            # Default to having sufficient info (don't block on errors)
            return {
                **state,
                "has_sufficient_info": True,
                "missing_info": False,
                "gap_analysis": {
                    "has_sufficient_info": True,
                    "confidence": 0.5,
                    "reasoning": f"Gap analysis failed: {str(e)}",
                },
            }

    def _summarize_context(self, state: AgentState) -> str:
        """
        Summarize available context from state.

        Args:
            state: Current agent state.

        Returns:
            Summary of available context.
        """
        parts = []

        # Retrieved documents
        retrieved_docs = state.get("retrieved_documents", [])
        if retrieved_docs:
            parts.append(f"- {len(retrieved_docs)} relevant documents retrieved")
            # Sample first document
            if retrieved_docs[0].get("metadata"):
                metadata = retrieved_docs[0]["metadata"]
                if metadata.get("endpoint"):
                    parts.append(f"  - Example endpoint: {metadata['endpoint']}")
                if metadata.get("source") == "web_search":
                    parts.append("  - Includes web search results")
        else:
            parts.append("- No documents retrieved yet")

        # Context text
        context_text = state.get("context_text", "")
        if context_text:
            preview = context_text[:200].replace("\n", " ")
            parts.append(f"- Context preview: {preview}...")

        # Conversation history
        conversation_history = state.get("conversation_history", [])
        if conversation_history:
            parts.append(f"- {len(conversation_history)} messages in conversation history")

        # Web search results
        if any(
            doc.get("metadata", {}).get("source") == "web_search"
            for doc in retrieved_docs
        ):
            parts.append("- Web search fallback was used")

        return "\n".join(parts) if parts else "No context available"

    def _analyze_gaps(
        self, query: str, intent: str, context_summary: str
    ) -> dict:
        """
        Use LLM to analyze information gaps.

        Args:
            query: User's query.
            intent: Detected intent.
            context_summary: Summary of available context.

        Returns:
            Gap analysis results.
        """
        prompt = self.GAP_ANALYSIS_PROMPT.format(
            query=query,
            intent=intent,
            context_summary=context_summary,
        )

        try:
            response = self._llm_client.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=500,
            )

            # Parse JSON response
            import json
            import re

            # Extract JSON from markdown code blocks if present
            json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON object directly
                json_match = re.search(r"\{.*\}", response, re.DOTALL)
                json_str = json_match.group(0) if json_match else response

            gap_analysis = json.loads(json_str)

            # Validate required fields
            if "has_sufficient_info" not in gap_analysis:
                gap_analysis["has_sufficient_info"] = True

            return gap_analysis

        except Exception as e:
            self._logger.error("Failed to parse gap analysis", error=str(e))
            # Default to having sufficient info
            return {
                "has_sufficient_info": True,
                "confidence": 0.5,
                "reasoning": "Failed to analyze gaps, proceeding with available context",
            }
