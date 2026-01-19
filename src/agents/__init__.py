"""
LangGraph agents for Intelligent Coding Agent.

This package contains specialized agents for query processing:
- QueryAnalyzer: Classifies user intent and routes queries
- RAG Agent: Retrieves and synthesizes documentation
- Code Generator: Generates integration code from templates
- Orchestrator: Supervises and coordinates agent workflows
"""

from src.agents.base_agent import AgentRegistry, BaseAgent, PassThroughAgent
from src.agents.code_agent import CodeGenerator
from src.agents.query_analyzer import QueryAnalyzer
from src.agents.rag_agent import RAGAgent
from src.agents.state import (
    AgentError,
    AgentMessage,
    AgentState,
    AgentType,
    ConfidenceLevel,
    IntentAnalysis,
    QueryIntent,
    RetrievedDocument,
    SourceCitation,
    add_to_processing_path,
    create_initial_state,
    set_error,
)
from src.agents.supervisor import SupervisorAgent, create_supervisor

__all__ = [
    # State management
    "AgentState",
    "AgentType",
    "QueryIntent",
    "ConfidenceLevel",
    "IntentAnalysis",
    "RetrievedDocument",
    "SourceCitation",
    "AgentMessage",
    "AgentError",
    "create_initial_state",
    "add_to_processing_path",
    "set_error",
    # Base agents
    "BaseAgent",
    "PassThroughAgent",
    "AgentRegistry",
    # Specialized agents
    "QueryAnalyzer",
    "RAGAgent",
    "CodeGenerator",
    # Orchestration
    "SupervisorAgent",
    "create_supervisor",
]
