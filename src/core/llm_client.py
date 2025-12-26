"""
LLM Client abstraction for interacting with language models.
Supports Ollama (local) and Groq (cloud) providers with:
- Circuit breaker protection
- Retry with exponential backoff
- Request timeouts
- Comprehensive error handling
"""

import signal
from contextlib import contextmanager
from typing import AsyncGenerator, Generator, Literal, Optional

import structlog
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from src.config import settings
from src.core.circuit_breaker import llm_circuit_breaker
from src.core.exceptions import (
    LLMConnectionError,
    LLMTimeoutError,
    LLMResponseError,
    LLMCircuitBreakerOpen,
    is_retryable_error,
)

logger = structlog.get_logger(__name__)


# ============================================================================
# Timeout handling
# ============================================================================


class TimeoutError(Exception):
    """Raised when operation times out."""

    pass


@contextmanager
def timeout(seconds: int):
    """
    Context manager for operation timeout.

    Args:
        seconds: Timeout in seconds

    Raises:
        LLMTimeoutError: If operation exceeds timeout

    Example:
        ```python
        with timeout(30):
            result = llm_client.generate(prompt)
        ```
    """

    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")

    # Set the signal handler and alarm
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

    try:
        yield
    except TimeoutError as e:
        raise LLMTimeoutError(
            f"LLM request timed out after {seconds} seconds",
            details={"timeout_seconds": seconds},
        )
    finally:
        # Disable the alarm and restore old handler
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


# ============================================================================
# LLM Client
# ============================================================================


class LLMClient:
    """
    Unified LLM client supporting local (Ollama) and cloud (Groq) models.

    Features:
    - Configurable provider (ollama or groq)
    - Streaming support
    - Circuit breaker protection
    - Retry with exponential backoff
    - Request timeouts
    - Comprehensive error handling
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
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((LLMConnectionError, LLMTimeoutError)),
        before_sleep=before_sleep_log(logger, "warning"),
        reraise=True,
    )
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        timeout_seconds: int = 120,
    ) -> str:
        """
        Generate a response from the LLM with circuit breaker protection.

        Args:
            prompt: User prompt.
            system_prompt: Optional system prompt for context.
            temperature: Sampling temperature (0-2).
            max_tokens: Maximum tokens in response.
            timeout_seconds: Request timeout in seconds (default: 120).

        Returns:
            Generated text response.

        Raises:
            LLMCircuitBreakerOpen: If circuit breaker is open
            LLMTimeoutError: If request times out
            LLMConnectionError: If connection fails
            LLMResponseError: If response is invalid
        """
        logger.debug(
            "llm_generate_request",
            provider=self.provider,
            model=self.model,
            prompt_length=len(prompt),
            timeout=timeout_seconds,
        )

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            # Use circuit breaker to protect the call
            result = llm_circuit_breaker.call(
                self._generate_with_timeout,
                messages,
                temperature,
                max_tokens,
                timeout_seconds,
            )
            return result

        except LLMCircuitBreakerOpen:
            # Don't log as error - circuit breaker is doing its job
            logger.warning(
                "llm_circuit_breaker_blocking",
                provider=self.provider,
            )
            raise

        except (LLMTimeoutError, LLMConnectionError, LLMResponseError):
            # Re-raise our custom exceptions
            raise

        except Exception as e:
            # Convert unknown exceptions to our exception types
            error_msg = str(e).lower()

            if "timeout" in error_msg or "timed out" in error_msg:
                raise LLMTimeoutError(
                    f"LLM request timed out: {str(e)}",
                    details={"provider": self.provider, "model": self.model},
                ) from e
            elif (
                "connection" in error_msg
                or "network" in error_msg
                or "unreachable" in error_msg
            ):
                raise LLMConnectionError(
                    f"Failed to connect to LLM: {str(e)}",
                    details={"provider": self.provider, "model": self.model},
                ) from e
            else:
                raise LLMResponseError(
                    f"LLM generation failed: {str(e)}",
                    details={"provider": self.provider, "model": self.model},
                ) from e

    def _generate_with_timeout(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
        timeout_seconds: int,
    ) -> str:
        """
        Generate response with timeout protection.

        Args:
            messages: Conversation messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            timeout_seconds: Timeout in seconds

        Returns:
            Generated response

        Raises:
            LLMTimeoutError: If request times out
        """
        with timeout(timeout_seconds):
            if self.provider == "groq":
                return self._generate_with_groq(messages, temperature, max_tokens)
            else:
                return self._generate_with_ollama(messages, temperature, max_tokens)

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
