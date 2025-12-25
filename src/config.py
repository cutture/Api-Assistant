"""
Configuration management for API Integration Assistant.
Uses Pydantic Settings for type-safe environment variable handling.
"""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ----- Application -----
    app_name: str = Field(default="API Integration Assistant")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    # ----- LLM Provider -----
    llm_provider: str = Field(default="ollama")  # "ollama" or "groq"

    # ----- Ollama (Local LLM) -----
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="deepseek-coder:6.7b")

    # ----- Groq (Cloud LLM) -----
    groq_api_key: Optional[str] = Field(default=None)
    groq_reasoning_model: str = Field(default="deepseek-r1-distill-llama-70b")  # For QueryAnalyzer, DocAnalyzer
    groq_code_model: str = Field(default="llama-3.3-70b-versatile")  # For CodeGenerator
    groq_general_model: str = Field(default="llama-3.3-70b-versatile")  # For RAGAgent

    # ----- Embeddings -----
    embedding_model: str = Field(default="all-MiniLM-L6-v2")

    # ----- ChromaDB -----
    chroma_persist_dir: str = Field(default="./data/chroma_db")
    chroma_collection_name: str = Field(default="api_docs")

    # ----- Upload Settings -----
    max_upload_size_mb: int = Field(default=10)
    allowed_extensions: str = Field(default="json,yaml,yml,md,txt")

    @property
    def allowed_extensions_list(self) -> list[str]:
        """Get allowed extensions as a list."""
        return [ext.strip() for ext in self.allowed_extensions.split(",")]

    @property
    def max_upload_size_bytes(self) -> int:
        """Get max upload size in bytes."""
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def chroma_persist_path(self) -> Path:
        """Get ChromaDB persist directory as Path object."""
        return Path(self.chroma_persist_dir)


# Global settings instance (singleton pattern)
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance (lazy initialization)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# Convenience export
settings = get_settings()
