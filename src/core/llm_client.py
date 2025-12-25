"""
LLM Client abstraction for interacting with language models.
Supports Ollama (local) and Groq (cloud) providers.
"""

from typing import AsyncGenerator, Generator, Literal, Optional

import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import settings

logger = structlog.get_logger(__name__)


class LLMClient:
    """
    Unified LLM client supporting local (Ollama) and cloud (Groq) models.

    Features:
    - Configurable provider (ollama or groq)
    - Streaming support
    - Retry with exponential backoff
    - Conversation history management
    """

    def __init__(
        self,
        provider: Optional[Literal["ollama", "groq"]] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        Initialize the LLM client.

        Args:
            provider: LLM provider ("ollama" or "groq"). Defaults to settings.llm_provider.
            model: Model name to use. If None, uses provider-specific default from settings.
            base_url: Ollama base URL (only for Ollama provider).
        """
        self.provider = provider or settings.llm_provider
        self.base_url = base_url or settings.ollama_base_url

        # Set model based on provider
        if model:
            self.model = model
        else:
            if self.provider == "groq":
                self.model = settings.groq_general_model
            else:
                self.model = settings.ollama_model

        self._ollama_client = None
        self._groq_client = None

        logger.info(
            "llm_client_initialized",
            provider=self.provider,
            model=self.model,
        )

    @property
    def ollama_client(self):
        """Get or create the Ollama client."""
        if self._ollama_client is None:
            import ollama
            self._ollama_client = ollama.Client(host=self.base_url)
        return self._ollama_client

    @property
    def groq_client(self):
        """Get or create the Groq client."""
        if self._groq_client is None:
            try:
                from groq import Groq
                if not settings.groq_api_key:
                    raise ValueError("GROQ_API_KEY not set in environment")
                self._groq_client = Groq(api_key=settings.groq_api_key)
            except ImportError:
                logger.error("Groq package not installed. Run: pip install groq")
                raise
        return self._groq_client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """
        Generate a response from the LLM.

        Args:
            prompt: User prompt.
            system_prompt: Optional system prompt for context.
            temperature: Sampling temperature (0-2).
            max_tokens: Maximum tokens in response.

        Returns:
            Generated text response.
        """
        logger.debug(
            "Generating LLM response",
            provider=self.provider,
            model=self.model,
            prompt_length=len(prompt),
        )

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            if self.provider == "groq":
                return self._generate_with_groq(messages, temperature, max_tokens)
            else:
                return self._generate_with_ollama(messages, temperature, max_tokens)

        except Exception as e:
            logger.error("LLM generation failed", error=str(e), provider=self.provider)
            raise

    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Generator[str, None, None]:
        """
        Generate a streaming response from the LLM.

        Args:
            prompt: User prompt.
            system_prompt: Optional system prompt for context.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in response.

        Yields:
            Text chunks as they are generated.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            if self.provider == "groq":
                yield from self._generate_stream_with_groq(messages, temperature, max_tokens)
            else:
                yield from self._generate_stream_with_ollama(messages, temperature, max_tokens)

        except Exception as e:
            logger.error("LLM streaming failed", error=str(e), provider=self.provider)
            raise

    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """
        Chat with conversation history.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in response.

        Returns:
            Assistant's response.
        """
        try:
            if self.provider == "groq":
                return self._generate_with_groq(messages, temperature, max_tokens)
            else:
                return self._generate_with_ollama(messages, temperature, max_tokens)

        except Exception as e:
            logger.error("Chat failed", error=str(e), provider=self.provider)
            raise

    def chat_stream(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Generator[str, None, None]:
        """
        Streaming chat with conversation history.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in response.

        Yields:
            Text chunks as they are generated.
        """
        try:
            if self.provider == "groq":
                yield from self._generate_stream_with_groq(messages, temperature, max_tokens)
            else:
                yield from self._generate_stream_with_ollama(messages, temperature, max_tokens)

        except Exception as e:
            logger.error("Chat streaming failed", error=str(e), provider=self.provider)
            raise

    def _generate_with_ollama(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """
        Generate using Ollama local API.

        Args:
            messages: Conversation messages.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens.

        Returns:
            Generated response.
        """
        response = self.ollama_client.chat(
            model=self.model,
            messages=messages,
            options={
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        )
        content = response["message"]["content"]
        logger.debug("Ollama response generated", response_length=len(content))
        return content

    def _generate_stream_with_ollama(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> Generator[str, None, None]:
        """
        Generate streaming response using Ollama.

        Args:
            messages: Conversation messages.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens.

        Yields:
            Text chunks.
        """
        stream = self.ollama_client.chat(
            model=self.model,
            messages=messages,
            stream=True,
            options={
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        )

        for chunk in stream:
            if "message" in chunk and "content" in chunk["message"]:
                yield chunk["message"]["content"]

    def _generate_with_groq(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """
        Generate using Groq cloud API.

        Args:
            messages: Conversation messages.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens.

        Returns:
            Generated response.
        """
        response = self.groq_client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content
        logger.debug("Groq response generated", response_length=len(content))
        return content

    def _generate_stream_with_groq(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> Generator[str, None, None]:
        """
        Generate streaming response using Groq.

        Args:
            messages: Conversation messages.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens.

        Yields:
            Text chunks.
        """
        stream = self.groq_client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def get_model_info(self) -> dict:
        """Get information about the current model."""
        try:
            if self.provider == "ollama":
                info = self.ollama_client.show(self.model)
                return {
                    "provider": "ollama",
                    "name": self.model,
                    "parameters": info.get("parameters", "unknown"),
                    "size": info.get("size", "unknown"),
                    "family": info.get("details", {}).get("family", "unknown"),
                }
            else:
                return {
                    "provider": "groq",
                    "name": self.model,
                }
        except Exception as e:
            logger.warning("Could not get model info", error=str(e))
            return {"provider": self.provider, "name": self.model, "error": str(e)}


# Convenience functions
def get_llm_client(agent_type: Optional[str] = None) -> LLMClient:
    """
    Get an LLM client instance configured for the current provider.

    Args:
        agent_type: Type of agent ("reasoning", "code", "general").
                   Used to select appropriate model when provider is Groq.

    Returns:
        Configured LLMClient instance.
    """
    provider = settings.llm_provider

    if provider == "groq":
        # Map agent type to appropriate Groq model
        if agent_type == "reasoning":
            model = settings.groq_reasoning_model
        elif agent_type == "code":
            model = settings.groq_code_model
        else:
            model = settings.groq_general_model

        return LLMClient(provider="groq", model=model)
    else:
        # Ollama uses the same model for all agents
        return LLMClient(provider="ollama", model=settings.ollama_model)


def create_reasoning_client() -> LLMClient:
    """Create LLM client for reasoning/planning agents (QueryAnalyzer, DocAnalyzer)."""
    return get_llm_client(agent_type="reasoning")


def create_code_client() -> LLMClient:
    """Create LLM client for code generation agent."""
    return get_llm_client(agent_type="code")


def create_general_client() -> LLMClient:
    """Create LLM client for general agents (RAGAgent)."""
    return get_llm_client(agent_type="general")
