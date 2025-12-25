"""
Supervisor Agent - Orchestrates all agents using LangGraph StateGraph.

This module implements the main orchestrator that routes queries through
the appropriate agent pipeline based on intent classification.

Graph Structure:
    START → QueryAnalyzer → Router
                              ├─→ RAGAgent → END
                              ├─→ RAGAgent → CodeGenerator → END
                              ├─→ DocumentationAnalyzer → END
                              └─→ DirectResponse → END
"""

from typing import Literal, Optional

import structlog
from langgraph.graph import END, START, StateGraph

from src.agents.base_agent import BaseAgent
from src.agents.code_agent import CodeGenerator
from src.agents.doc_analyzer import DocumentationAnalyzer
from src.agents.query_analyzer import QueryAnalyzer
from src.agents.rag_agent import RAGAgent
from src.agents.state import AgentState, QueryIntent, create_initial_state

logger = structlog.get_logger(__name__)


class SupervisorAgent:
    """
    Supervisor agent that orchestrates all specialized agents.

    The supervisor uses LangGraph to route queries through the appropriate
    agent pipeline based on the classified intent. It supports both simple
    routing (single agent) and complex chaining (multiple agents).

    Architecture:
        1. Query Analysis - Classify user intent
        2. Routing - Select appropriate agent(s) based on intent
        3. Execution - Run selected agent(s) in sequence
        4. Aggregation - Combine results into final response

    Example:
        >>> supervisor = SupervisorAgent(
        ...     query_analyzer=analyzer,
        ...     rag_agent=rag,
        ...     code_generator=code_gen,
        ...     doc_analyzer=doc_analyzer
        ... )
        >>> result = supervisor.process("How do I authenticate?")
        >>> print(result["response"])
    """

    def __init__(
        self,
        query_analyzer: QueryAnalyzer,
        rag_agent: RAGAgent,
        code_generator: CodeGenerator,
        doc_analyzer: DocumentationAnalyzer,
    ):
        """
        Initialize the supervisor with all required agents.

        Args:
            query_analyzer: Agent that classifies user intent
            rag_agent: Agent that retrieves and synthesizes documentation
            code_generator: Agent that generates integration code
            doc_analyzer: Agent that identifies documentation gaps
        """
        self.query_analyzer = query_analyzer
        self.rag_agent = rag_agent
        self.code_generator = code_generator
        self.doc_analyzer = doc_analyzer

        # Build the LangGraph StateGraph
        self.graph = self._build_graph()

        logger.info("supervisor_initialized", agents=["query_analyzer", "rag_agent", "code_generator", "doc_analyzer"])

    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph StateGraph for agent orchestration.

        Returns:
            Compiled StateGraph ready for execution
        """
        # Create graph with AgentState
        workflow = StateGraph(AgentState)

        # Add nodes for each agent
        workflow.add_node("query_analyzer", self._run_query_analyzer)
        workflow.add_node("rag_agent", self._run_rag_agent)
        workflow.add_node("code_generator", self._run_code_generator)
        workflow.add_node("doc_analyzer", self._run_doc_analyzer)
        workflow.add_node("direct_response", self._run_direct_response)

        # Set entry point
        workflow.add_edge(START, "query_analyzer")

        # Add conditional routing after query analysis
        workflow.add_conditional_edges(
            "query_analyzer",
            self._route_after_analysis,
            {
                "rag_agent": "rag_agent",
                "rag_to_code": "rag_agent",
                "doc_analyzer": "doc_analyzer",
                "direct_response": "direct_response",
            },
        )

        # RAG agent routing (might chain to code generator)
        workflow.add_conditional_edges(
            "rag_agent",
            self._route_after_rag,
            {
                "code_generator": "code_generator",
                "end": END,
            },
        )

        # Terminal nodes
        workflow.add_edge("code_generator", END)
        workflow.add_edge("doc_analyzer", END)
        workflow.add_edge("direct_response", END)

        # Compile the graph
        return workflow.compile()

    def _run_query_analyzer(self, state: AgentState) -> AgentState:
        """
        Execute the query analyzer agent.

        Args:
            state: Current agent state

        Returns:
            Updated state with intent analysis
        """
        logger.info("executing_query_analyzer", query=state.get("query", "")[:50])
        try:
            result = self.query_analyzer(state)
            logger.info(
                "query_analyzer_complete",
                intent=result.get("intent_analysis", {}).get("primary_intent"),
                confidence=result.get("intent_analysis", {}).get("confidence"),
            )
            return result
        except Exception as e:
            logger.error("query_analyzer_failed", error=str(e))
            # Set error in state but continue
            state["error"] = {
                "agent": "query_analyzer",
                "message": str(e),
                "recoverable": True,
            }
            return state

    def _run_rag_agent(self, state: AgentState) -> AgentState:
        """
        Execute the RAG agent.

        Args:
            state: Current agent state

        Returns:
            Updated state with retrieved documents and response
        """
        logger.info("executing_rag_agent")
        try:
            result = self.rag_agent(state)
            logger.info(
                "rag_agent_complete",
                num_docs=len(result.get("retrieved_documents", [])),
                has_response=bool(result.get("response")),
            )
            return result
        except Exception as e:
            logger.error("rag_agent_failed", error=str(e))
            state["error"] = {
                "agent": "rag_agent",
                "message": str(e),
                "recoverable": True,
            }
            # Provide fallback response
            state["response"] = "I encountered an issue retrieving documentation. Please try rephrasing your question."
            return state

    def _run_code_generator(self, state: AgentState) -> AgentState:
        """
        Execute the code generator agent.

        Args:
            state: Current agent state

        Returns:
            Updated state with generated code
        """
        logger.info("executing_code_generator")
        try:
            result = self.code_generator(state)
            logger.info(
                "code_generator_complete",
                has_code=bool(result.get("code_snippets")),
            )
            return result
        except Exception as e:
            logger.error("code_generator_failed", error=str(e))
            state["error"] = {
                "agent": "code_generator",
                "message": str(e),
                "recoverable": True,
            }
            # Keep RAG response if code generation fails
            if not state.get("response"):
                state["response"] = "I found relevant documentation but couldn't generate code. Here's what I found..."
            return state

    def _run_doc_analyzer(self, state: AgentState) -> AgentState:
        """
        Execute the documentation analyzer agent.

        Args:
            state: Current agent state

        Returns:
            Updated state with documentation gaps
        """
        logger.info("executing_doc_analyzer")
        try:
            result = self.doc_analyzer(state)
            logger.info(
                "doc_analyzer_complete",
                num_gaps=len(result.get("documentation_gaps", [])),
            )
            return result
        except Exception as e:
            logger.error("doc_analyzer_failed", error=str(e))
            state["error"] = {
                "agent": "doc_analyzer",
                "message": str(e),
                "recoverable": True,
            }
            state["response"] = "I couldn't complete the documentation analysis. Please try again."
            return state

    def _run_direct_response(self, state: AgentState) -> AgentState:
        """
        Provide a direct response for simple queries.

        This is used for queries that don't require agent processing,
        such as greetings or very simple questions.

        Args:
            state: Current agent state

        Returns:
            Updated state with direct response
        """
        logger.info("executing_direct_response")

        query = state.get("query", "").lower()
        intent_analysis = state.get("intent_analysis", {})

        # Simple pattern matching for common queries
        if any(greeting in query for greeting in ["hello", "hi", "hey"]):
            state["response"] = "Hello! I'm your API Integration Assistant. I can help you understand API documentation, generate integration code, and identify documentation gaps. What would you like to know?"
        elif any(word in query for word in ["help", "what can you do"]):
            state["response"] = """I can help you with:
1. **General Questions** - Answer questions about API documentation
2. **Code Generation** - Generate Python code to integrate with APIs
3. **Endpoint Lookup** - Find specific API endpoints and their usage
4. **Schema Explanation** - Explain API data structures and models
5. **Authentication** - Help with API authentication methods
6. **Documentation Gaps** - Identify missing or incomplete documentation

What would you like to explore?"""
        else:
            # Fallback for other simple queries
            state["response"] = f"I understand you're asking about: {state.get('query')}. However, I need more context to provide a helpful answer. Could you please provide more details or upload an API specification?"

        state["current_agent"] = "direct_response"
        if "processing_path" not in state:
            state["processing_path"] = []
        state["processing_path"].append("direct_response")

        return state

    def _route_after_analysis(self, state: AgentState) -> str:
        """
        Route to appropriate agent(s) after query analysis.

        Routing Logic:
            - code_generation → rag_to_code (RAG then Code)
            - documentation_gap → doc_analyzer
            - general_question, endpoint_lookup, schema_explanation, authentication → rag_agent
            - Unknown/low confidence → direct_response

        Args:
            state: Current agent state with intent_analysis

        Returns:
            Next node name to execute
        """
        intent_analysis = state.get("intent_analysis")

        if not intent_analysis:
            logger.warning("no_intent_analysis", routing_to="direct_response")
            return "direct_response"

        primary_intent = intent_analysis.get("primary_intent")
        confidence = intent_analysis.get("confidence", 0.0)

        logger.info(
            "routing_decision",
            intent=primary_intent,
            confidence=confidence,
        )

        # Low confidence queries go to direct response
        if confidence < 0.3:
            logger.info("low_confidence_query", routing_to="direct_response")
            return "direct_response"

        # Route based on intent
        if primary_intent == QueryIntent.CODE_GENERATION.value:
            # Code generation requires RAG first, then code gen
            logger.info("routing_to_rag_to_code_chain")
            return "rag_to_code"

        elif primary_intent == QueryIntent.DOCUMENTATION_GAP.value:
            logger.info("routing_to_doc_analyzer")
            return "doc_analyzer"

        elif primary_intent in [
            QueryIntent.GENERAL_QUESTION.value,
            QueryIntent.ENDPOINT_LOOKUP.value,
            QueryIntent.SCHEMA_EXPLANATION.value,
            QueryIntent.AUTHENTICATION.value,
        ]:
            logger.info("routing_to_rag_agent")
            return "rag_agent"

        else:
            # Unknown intent
            logger.warning("unknown_intent", intent=primary_intent, routing_to="direct_response")
            return "direct_response"

    def _route_after_rag(self, state: AgentState) -> str:
        """
        Route after RAG agent execution.

        If this was a code generation request (rag_to_code flow),
        continue to code generator. Otherwise, end the workflow.

        Args:
            state: Current agent state

        Returns:
            Next node name ("code_generator" or "end")
        """
        intent_analysis = state.get("intent_analysis", {})
        primary_intent = intent_analysis.get("primary_intent")

        # Check if this was a code generation request
        if primary_intent == QueryIntent.CODE_GENERATION.value:
            # Check if RAG retrieved useful documents
            retrieved_docs = state.get("retrieved_documents", [])
            if retrieved_docs:
                logger.info("chaining_to_code_generator", num_docs=len(retrieved_docs))
                return "code_generator"
            else:
                logger.warning("no_docs_for_code_generation", routing_to="end")
                # Add a message to response
                if state.get("response"):
                    state["response"] += "\n\nI couldn't find relevant documentation to generate code from."
                return "end"

        # All other intents end after RAG
        logger.info("rag_workflow_complete", routing_to="end")
        return "end"

    def process(self, query: str) -> AgentState:
        """
        Process a user query through the agent pipeline.

        This is the main entry point for query processing. It creates
        initial state and invokes the LangGraph workflow.

        Args:
            query: User query string

        Returns:
            Final agent state with results

        Example:
            >>> supervisor = SupervisorAgent(...)
            >>> result = supervisor.process("How do I create a user?")
            >>> print(result["response"])
            >>> if result.get("code_snippets"):
            ...     print(result["code_snippets"][0]["code"])
        """
        logger.info("processing_query", query=query[:100])

        # Create initial state
        initial_state = create_initial_state(query)

        try:
            # Execute the graph
            final_state = self.graph.invoke(initial_state)

            logger.info(
                "processing_complete",
                processing_path=final_state.get("processing_path", []),
                has_response=bool(final_state.get("response")),
                has_error=bool(final_state.get("error")),
            )

            return final_state

        except Exception as e:
            logger.error("supervisor_execution_failed", error=str(e), exc_info=True)

            # Return error state
            error_state = initial_state.copy()
            error_state["error"] = {
                "agent": "supervisor",
                "message": f"Failed to process query: {str(e)}",
                "recoverable": False,
            }
            error_state["response"] = "I encountered an unexpected error while processing your query. Please try again or rephrase your question."

            return error_state

    def process_streaming(self, query: str):
        """
        Process a query with streaming updates.

        This method yields state updates as they occur, allowing
        for real-time UI updates showing agent progress.

        Args:
            query: User query string

        Yields:
            AgentState updates at each step

        Example:
            >>> for state_update in supervisor.process_streaming("Generate code"):
            ...     print(f"Agent: {state_update['current_agent']}")
            ...     if state_update.get("response"):
            ...         print(state_update["response"])
        """
        logger.info("processing_query_streaming", query=query[:100])

        initial_state = create_initial_state(query)

        try:
            # Stream updates from the graph
            for state_update in self.graph.stream(initial_state):
                logger.debug("state_update", current_agent=state_update.get("current_agent"))
                yield state_update

        except Exception as e:
            logger.error("supervisor_streaming_failed", error=str(e), exc_info=True)

            error_state = initial_state.copy()
            error_state["error"] = {
                "agent": "supervisor",
                "message": f"Failed to process query: {str(e)}",
                "recoverable": False,
            }
            error_state["response"] = "I encountered an unexpected error. Please try again."

            yield error_state

    def get_graph_visualization(self) -> str:
        """
        Get a Mermaid diagram visualization of the graph structure.

        Returns:
            Mermaid diagram string

        Example:
            >>> print(supervisor.get_graph_visualization())
        """
        try:
            # LangGraph supports graph visualization
            return self.graph.get_graph().draw_mermaid()
        except Exception as e:
            logger.error("visualization_failed", error=str(e))
            return "Graph visualization not available"


def create_supervisor(
    llm_client=None,
    vector_store=None,
) -> SupervisorAgent:
    """
    Factory function to create a fully configured SupervisorAgent.

    This is a convenience function that instantiates all required agents
    with specialized LLM clients based on the configured provider.

    When using Groq:
    - QueryAnalyzer: Uses reasoning model (DeepSeek R1)
    - RAGAgent: Uses general model (Llama 3.3 70B)
    - CodeGenerator: Uses code model (Llama 3.3 70B)
    - DocumentationAnalyzer: Uses reasoning model (DeepSeek R1)

    When using Ollama:
    - All agents use the same configured Ollama model

    Args:
        llm_client: Optional LLM client (deprecated, use LLM_PROVIDER env var)
        vector_store: Vector store for RAG agent

    Returns:
        Configured SupervisorAgent ready to use

    Example:
        >>> from src.services.vector_store import get_vector_store
        >>>
        >>> vector_store = get_vector_store()
        >>> supervisor = create_supervisor(vector_store=vector_store)
        >>> result = supervisor.process("How do I authenticate?")
    """
    from src.core.llm_client import (
        create_code_client,
        create_general_client,
        create_reasoning_client,
    )

    # Initialize all agents with specialized LLM clients
    query_analyzer = QueryAnalyzer(llm_client=create_reasoning_client())
    rag_agent = RAGAgent(vector_store=vector_store, llm_client=create_general_client())
    code_generator = CodeGenerator(llm_client=create_code_client())
    doc_analyzer = DocumentationAnalyzer(llm_client=create_reasoning_client())

    # Create and return supervisor
    supervisor = SupervisorAgent(
        query_analyzer=query_analyzer,
        rag_agent=rag_agent,
        code_generator=code_generator,
        doc_analyzer=doc_analyzer,
    )

    logger.info("supervisor_factory_complete")
    return supervisor
