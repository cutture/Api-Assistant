"""
Shared state definitions for LangGraph agent orchestration.

This module defines the state schema that is passed between agents
in the LangGraph pipeline. All agents read from and write to this
shared state object.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional, TypedDict

from pydantic import BaseModel, Field


class QueryIntent(str, Enum):
    """
    Classification of user query intent.
    
    Used by QueryAnalyzer agent to route queries to appropriate handlers.
    """
    
    GENERAL_QUESTION = "general_question"
    """General questions about API functionality, overview, or concepts."""
    
    CODE_GENERATION = "code_generation"
    """Requests to generate integration code for API endpoints."""
    
    ENDPOINT_LOOKUP = "endpoint_lookup"
    """Looking for specific endpoints by path, method, or functionality."""
    
    SCHEMA_EXPLANATION = "schema_explanation"
    """Questions about request/response schemas and data structures."""
    
    AUTHENTICATION = "authentication"
    """Questions about API authentication and authorization."""
    
    DOCUMENTATION_GAP = "documentation_gap"
    """Requests to identify missing or incomplete documentation."""


class AgentType(str, Enum):
    """Types of agents in the system."""
    
    QUERY_ANALYZER = "query_analyzer"
    RAG_AGENT = "rag_agent"
    CODE_GENERATOR = "code_generator"
    DOC_ANALYZER = "doc_analyzer"
    SUPERVISOR = "supervisor"


class ConfidenceLevel(str, Enum):
    """Confidence levels for agent outputs."""
    
    HIGH = "high"      # > 0.8
    MEDIUM = "medium"  # 0.5 - 0.8
    LOW = "low"        # < 0.5


class RetrievedDocument(BaseModel):
    """A document retrieved from the vector store."""
    
    content: str = Field(..., description="The text content of the document")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Associated metadata (path, method, tags, etc.)"
    )
    score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Relevance score (0-1)"
    )
    doc_id: str = Field(default="", description="Document ID in vector store")

    class Config:
        frozen = False


class SourceCitation(BaseModel):
    """A citation reference for response attribution."""
    
    endpoint_path: str = Field(default="", description="API endpoint path")
    method: str = Field(default="", description="HTTP method")
    description: str = Field(default="", description="Brief description of the source")
    relevance_score: float = Field(default=0.0, description="How relevant this source is")
    
    def to_display_string(self) -> str:
        """Format citation for display in UI."""
        if self.method and self.endpoint_path:
            return f"`{self.method} {self.endpoint_path}` - {self.description}"
        return self.description


class IntentAnalysis(BaseModel):
    """Result of query intent analysis."""
    
    primary_intent: QueryIntent = Field(
        default=QueryIntent.GENERAL_QUESTION,
        description="The primary classified intent"
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence score for the classification"
    )
    confidence_level: ConfidenceLevel = Field(
        default=ConfidenceLevel.LOW,
        description="Categorical confidence level"
    )
    secondary_intents: list[QueryIntent] = Field(
        default_factory=list,
        description="Other possible intents with lower confidence"
    )
    keywords: list[str] = Field(
        default_factory=list,
        description="Key terms extracted from the query"
    )
    requires_code: bool = Field(
        default=False,
        description="Whether the response should include code"
    )
    requires_retrieval: bool = Field(
        default=True,
        description="Whether RAG retrieval is needed"
    )

    @classmethod
    def from_confidence(cls, intent: QueryIntent, score: float, **kwargs) -> "IntentAnalysis":
        """Create IntentAnalysis with automatic confidence level calculation."""
        if score >= 0.8:
            level = ConfidenceLevel.HIGH
        elif score >= 0.5:
            level = ConfidenceLevel.MEDIUM
        else:
            level = ConfidenceLevel.LOW
        
        return cls(
            primary_intent=intent,
            confidence=score,
            confidence_level=level,
            **kwargs
        )


class AgentMessage(BaseModel):
    """A message in the conversation history."""
    
    role: str = Field(..., description="Message role: 'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now)
    agent: Optional[str] = Field(default=None, description="Which agent generated this message")
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentError(BaseModel):
    """Error information from agent processing."""
    
    agent: str = Field(..., description="Which agent encountered the error")
    error_type: str = Field(..., description="Type/category of error")
    message: str = Field(..., description="Human-readable error message")
    recoverable: bool = Field(default=True, description="Whether processing can continue")
    timestamp: datetime = Field(default_factory=datetime.now)
    details: dict[str, Any] = Field(default_factory=dict)


class AgentState(TypedDict, total=False):
    """
    Shared state for LangGraph agent orchestration.
    
    This TypedDict defines the structure of state that flows between
    agents in the processing pipeline. Each agent can read any field
    and update specific fields based on its responsibility.
    
    Usage with LangGraph:
        ```python
        from langgraph.graph import StateGraph
        
        graph = StateGraph(AgentState)
        graph.add_node("analyzer", query_analyzer)
        graph.add_node("rag", rag_agent)
        ...
        ```
    
    Attributes:
        query: The original user query (required).
        intent_analysis: Result of query classification.
        retrieved_documents: Documents from vector store.
        response: The generated response text.
        sources: Citations for the response.
        code_snippets: Generated code blocks.
        documentation_gaps: Identified documentation issues.
        messages: Conversation history.
        current_agent: Which agent is currently processing.
        processing_path: Sequence of agents that processed the query.
        error: Any error that occurred during processing.
        metadata: Additional routing and processing information.
    """
    
    # === Input ===
    query: str
    """The original user query."""
    
    # === Analysis ===
    intent_analysis: Optional[dict]  # Serialized IntentAnalysis
    """Result of query intent classification."""
    
    # === Retrieval ===
    retrieved_documents: list[dict]  # Serialized RetrievedDocument list
    """Documents retrieved from vector store."""
    
    context_text: str
    """Assembled context string from retrieved documents."""
    
    # === Generation ===
    response: str
    """The generated response text."""
    
    sources: list[dict]  # Serialized SourceCitation list
    """Citations for response attribution."""
    
    code_snippets: list[dict]
    """Generated code blocks with language and content."""
    
    # === Documentation Analysis ===
    documentation_gaps: list[dict]
    """Identified documentation issues and suggestions."""
    
    # === Conversation ===
    messages: list[dict]  # Serialized AgentMessage list
    """Full conversation history."""
    
    # === Routing & Control ===
    current_agent: str
    """Which agent is currently processing."""
    
    next_agent: Optional[str]
    """Suggested next agent (for routing)."""
    
    processing_path: list[str]
    """Sequence of agents that have processed the query."""
    
    should_continue: bool
    """Whether processing should continue to next agent."""
    
    # === Error Handling ===
    error: Optional[dict]  # Serialized AgentError
    """Error information if something went wrong."""
    
    # === Metadata ===
    metadata: dict
    """Additional information for routing and processing."""


def create_initial_state(query: str, messages: Optional[list[dict]] = None) -> AgentState:
    """
    Create a fresh AgentState with a new query.
    
    Args:
        query: The user's query to process.
        messages: Optional conversation history.
    
    Returns:
        AgentState initialized with defaults.
    
    Example:
        ```python
        state = create_initial_state("How do I authenticate?")
        result = graph.invoke(state)
        ```
    """
    return AgentState(
        query=query,
        intent_analysis=None,
        retrieved_documents=[],
        context_text="",
        response="",
        sources=[],
        code_snippets=[],
        documentation_gaps=[],
        messages=messages or [],
        current_agent="",
        next_agent=None,
        processing_path=[],
        should_continue=True,
        error=None,
        metadata={
            "start_time": datetime.now().isoformat(),
            "query_length": len(query),
        },
    )


def add_to_processing_path(state: AgentState, agent_name: str) -> AgentState:
    """
    Record an agent in the processing path.
    
    Args:
        state: Current agent state.
        agent_name: Name of the agent that processed.
    
    Returns:
        Updated state with agent added to path.
    """
    path = state.get("processing_path", [])
    return {
        **state,
        "current_agent": agent_name,
        "processing_path": path + [agent_name],
    }


def set_error(state: AgentState, agent: str, error_type: str, message: str, recoverable: bool = True) -> AgentState:
    """
    Set error information in state.
    
    Args:
        state: Current agent state.
        agent: Which agent encountered the error.
        error_type: Category of error.
        message: Human-readable error description.
        recoverable: Whether processing can continue.
    
    Returns:
        Updated state with error information.
    """
    error = AgentError(
        agent=agent,
        error_type=error_type,
        message=message,
        recoverable=recoverable,
    )
    return {
        **state,
        "error": error.model_dump(),
        "should_continue": recoverable,
    }
