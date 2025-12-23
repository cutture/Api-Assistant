"""
LLM Client abstraction for interacting with language models.
Supports Ollama (local) with optional Groq (cloud) fallback.
"""

from typing import AsyncGenerator, Generator, Optional

import ollama
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import settings

logger = structlog.get_logger(__name__)


class LLMClient:
    """
    Unified LLM client supporting local (Ollama) and cloud (Groq) models.
    
    Features:
    - Automatic fallback to cloud if local fails
    - Streaming support
    - Retry with exponential backoff
    - Conversation history management
    """

    def __init__(
        self,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        use_cloud_fallback: bool = True,
    ):
        """
        Initialize the LLM client.

        Args:
            model: Model name to use (default from settings).
            base_url: Ollama base URL (default from settings).
            use_cloud_fallback: Whether to fallback to cloud if local fails.
        """
        self.model = model or settings.ollama_model
        self.base_url = base_url or settings.ollama_base_url
        self.use_cloud_fallback = use_cloud_fallback
        
        self._ollama_client: Optional[ollama.Client] = None

    @property
    def ollama_client(self) -> ollama.Client:
        """Get or create the Ollama client."""
        if self._ollama_client is None:
            self._ollama_client = ollama.Client(host=self.base_url)
        return self._ollama_client

    def _check_ollama_available(self) -> bool:
        """Check if Ollama is available and the model is loaded."""
        try:
            models = self.ollama_client.list()
            available_models = [m["name"] for m in models.get("models", [])]
            
            # Check if our model is available (handle tag variations)
            model_base = self.model.split(":")[0]
            return any(model_base in m for m in available_models)
        except Exception as e:
            logger.warning("Ollama not available", error=str(e))
            return False

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
            model=self.model,
            prompt_length=len(prompt),
        )

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.ollama_client.chat(
                model=self.model,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            )
            
            content = response["message"]["content"]
            logger.debug("LLM response generated", response_length=len(content))
            return content

        except Exception as e:
            logger.error("LLM generation failed", error=str(e))
            
            if self.use_cloud_fallback and settings.groq_api_key:
                logger.info("Falling back to cloud LLM")
                return self._generate_with_groq(messages, temperature, max_tokens)
            
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

        except Exception as e:
            logger.error("LLM streaming failed", error=str(e))
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
            response = self.ollama_client.chat(
                model=self.model,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            )
            return response["message"]["content"]

        except Exception as e:
            logger.error("Chat failed", error=str(e))
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

        except Exception as e:
            logger.error("Chat streaming failed", error=str(e))
            raise

    def _generate_with_groq(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """
        Fallback generation using Groq cloud API.

        Args:
            messages: Conversation messages.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens.

        Returns:
            Generated response.
        """
        try:
            from groq import Groq
            
            client = Groq(api_key=settings.groq_api_key)
            response = client.chat.completions.create(
                model=settings.groq_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content

        except ImportError:
            logger.error("Groq package not installed. Run: pip install groq")
            raise
        except Exception as e:
            logger.error("Groq generation failed", error=str(e))
            raise

    def get_model_info(self) -> dict:
        """Get information about the current model."""
        try:
            info = self.ollama_client.show(self.model)
            return {
                "name": self.model,
                "parameters": info.get("parameters", "unknown"),
                "size": info.get("size", "unknown"),
                "family": info.get("details", {}).get("family", "unknown"),
            }
        except Exception as e:
            logger.warning("Could not get model info", error=str(e))
            return {"name": self.model, "error": str(e)}


# Convenience function
def get_llm_client() -> LLMClient:
    """Get an LLM client instance with default settings."""
    return LLMClient()
