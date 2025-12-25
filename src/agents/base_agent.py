"""
Base agent interface for API Integration Assistant.

This module defines the abstract base class that all agents must implement.
It provides common functionality like logging, error handling, and state
management utilities.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

import structlog

from src.agents.state import (
    AgentState,
    AgentType,
    QueryIntent,
    add_to_processing_path,
    set_error,
)


logger = structlog.get_logger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the system.
    
    Each agent is responsible for a specific task in the query processing
    pipeline. Agents read from the shared AgentState and update relevant
    fields based on their processing.
    
    Subclasses must implement:
        - `name` property: Unique identifier for the agent
        - `agent_type` property: The AgentType enum value
        - `process()` method: Main processing logic
    
    Example:
        ```python
        class MyAgent(BaseAgent):
            @property
            def name(self) -> str:
                return "my_agent"
            
            @property
            def agent_type(self) -> AgentType:
                return AgentType.RAG_AGENT
            
            def process(self, state: AgentState) -> AgentState:
                # Process and return updated state
                return state
        ```
    """

    def __init__(self):
        """Initialize the base agent with logging."""
        self._logger = structlog.get_logger(self.__class__.__name__)

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Unique name identifier for this agent.
        
        Used in routing, logging, and tracking the processing path.
        Should be lowercase with underscores (snake_case).
        """
        pass

    @property
    @abstractmethod
    def agent_type(self) -> AgentType:
        """
        The type category of this agent.
        
        Used for routing decisions and capability matching.
        """
        pass

    @property
    def description(self) -> str:
        """
        Human-readable description of what this agent does.
        
        Override in subclasses to provide specific description.
        """
        return f"{self.name} agent"

    @abstractmethod
    def process(self, state: AgentState) -> AgentState:
        """
        Process the current state and return updated state.
        
        This is the main entry point for agent logic. The agent should:
        1. Read relevant fields from state
        2. Perform its processing
        3. Update appropriate state fields
        4. Return the modified state
        
        Args:
            state: The current shared agent state.
        
        Returns:
            Updated AgentState with this agent's contributions.
        
        Raises:
            Should not raise exceptions - use set_error() instead.
        """
        pass

    def __call__(self, state: AgentState) -> AgentState:
        """
        Make the agent callable for LangGraph integration.
        
        This wrapper provides:
        - Automatic processing path tracking
        - Error handling with state updates
        - Logging of agent execution
        
        Args:
            state: The current shared agent state.
        
        Returns:
            Updated AgentState after processing.
        """
        self._logger.info(
            "agent_started",
            agent=self.name,
            query_preview=state.get("query", "")[:50],
        )
        
        try:
            # Add this agent to the processing path
            state = add_to_processing_path(state, self.name)
            
            # Run the agent's processing logic
            result = self.process(state)
            
            self._logger.info(
                "agent_completed",
                agent=self.name,
                has_response=bool(result.get("response")),
                has_error=bool(result.get("error")),
            )
            
            return result
            
        except Exception as e:
            self._logger.error(
                "agent_error",
                agent=self.name,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            
            return set_error(
                state=state,
                agent=self.name,
                error_type=type(e).__name__,
                message=str(e),
                recoverable=True,
            )

    def can_handle(self, intent: QueryIntent) -> bool:
        """
        Check if this agent can handle the given intent.
        
        Override in subclasses to define which intents the agent handles.
        Default implementation returns False for all intents.
        
        Args:
            intent: The classified query intent.
        
        Returns:
            True if this agent should handle the intent.
        """
        return False

    def validate_state(self, state: AgentState) -> tuple[bool, Optional[str]]:
        """
        Validate that the state has required fields for this agent.
        
        Override in subclasses to add specific validation.
        
        Args:
            state: The current agent state.
        
        Returns:
            Tuple of (is_valid, error_message).
        """
        if not state.get("query"):
            return False, "Query is required"
        return True, None

    def log_debug(self, message: str, **kwargs: Any) -> None:
        """Log a debug message with agent context."""
        self._logger.debug(message, agent=self.name, **kwargs)

    def log_info(self, message: str, **kwargs: Any) -> None:
        """Log an info message with agent context."""
        self._logger.info(message, agent=self.name, **kwargs)

    def log_warning(self, message: str, **kwargs: Any) -> None:
        """Log a warning message with agent context."""
        self._logger.warning(message, agent=self.name, **kwargs)

    def log_error(self, message: str, **kwargs: Any) -> None:
        """Log an error message with agent context."""
        self._logger.error(message, agent=self.name, **kwargs)


class PassThroughAgent(BaseAgent):
    """
    A simple agent that passes state through unchanged.
    
    Useful for testing the pipeline or as a placeholder.
    """

    @property
    def name(self) -> str:
        return "pass_through"

    @property
    def agent_type(self) -> AgentType:
        return AgentType.SUPERVISOR

    @property
    def description(self) -> str:
        return "Passes state through without modification"

    def process(self, state: AgentState) -> AgentState:
        """Simply return the state unchanged."""
        self.log_debug("passing_through", query=state.get("query", ""))
        return state


class AgentRegistry:
    """
    Registry for managing available agents.
    
    Provides a central place to register and retrieve agents by name or type.
    
    Example:
        ```python
        registry = AgentRegistry()
        registry.register(MyAgent())
        
        agent = registry.get_by_name("my_agent")
        agents = registry.get_by_type(AgentType.RAG_AGENT)
        ```
    """

    def __init__(self):
        """Initialize an empty registry."""
        self._agents: dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        """
        Register an agent in the registry.
        
        Args:
            agent: The agent instance to register.
        
        Raises:
            ValueError: If an agent with the same name is already registered.
        """
        if agent.name in self._agents:
            raise ValueError(f"Agent '{agent.name}' is already registered")
        
        self._agents[agent.name] = agent
        logger.info("agent_registered", name=agent.name, type=agent.agent_type.value)

    def unregister(self, name: str) -> Optional[BaseAgent]:
        """
        Remove an agent from the registry.
        
        Args:
            name: The name of the agent to remove.
        
        Returns:
            The removed agent, or None if not found.
        """
        return self._agents.pop(name, None)

    def get_by_name(self, name: str) -> Optional[BaseAgent]:
        """
        Get an agent by its name.
        
        Args:
            name: The unique name of the agent.
        
        Returns:
            The agent instance, or None if not found.
        """
        return self._agents.get(name)

    def get_by_type(self, agent_type: AgentType) -> list[BaseAgent]:
        """
        Get all agents of a specific type.
        
        Args:
            agent_type: The type of agents to retrieve.
        
        Returns:
            List of agents matching the type.
        """
        return [
            agent for agent in self._agents.values()
            if agent.agent_type == agent_type
        ]

    def get_for_intent(self, intent: QueryIntent) -> list[BaseAgent]:
        """
        Get all agents that can handle a specific intent.
        
        Args:
            intent: The query intent to handle.
        
        Returns:
            List of agents that can handle the intent.
        """
        return [
            agent for agent in self._agents.values()
            if agent.can_handle(intent)
        ]

    def list_all(self) -> list[BaseAgent]:
        """Get all registered agents."""
        return list(self._agents.values())

    def list_names(self) -> list[str]:
        """Get names of all registered agents."""
        return list(self._agents.keys())

    def __len__(self) -> int:
        """Return the number of registered agents."""
        return len(self._agents)

    def __contains__(self, name: str) -> bool:
        """Check if an agent with the given name is registered."""
        return name in self._agents


# Global registry instance
_registry: Optional[AgentRegistry] = None


def get_agent_registry() -> AgentRegistry:
    """
    Get the global agent registry instance.
    
    Creates the registry on first call (singleton pattern).
    
    Returns:
        The global AgentRegistry instance.
    """
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry


def register_agent(agent: BaseAgent) -> None:
    """
    Register an agent in the global registry.
    
    Convenience function for `get_agent_registry().register(agent)`.
    
    Args:
        agent: The agent to register.
    """
    get_agent_registry().register(agent)


def get_agent(name: str) -> Optional[BaseAgent]:
    """
    Get an agent from the global registry by name.
    
    Convenience function for `get_agent_registry().get_by_name(name)`.
    
    Args:
        name: The name of the agent.
    
    Returns:
        The agent instance, or None if not found.
    """
    return get_agent_registry().get_by_name(name)
