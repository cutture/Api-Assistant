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
    groq_reasoning_model: str = Field(default="llama-3.3-70b-versatile")  # For QueryAnalyzer, DocAnalyzer
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

    # ----- Web Search (Fallback) -----
    enable_web_search: bool = Field(default=True)  # Enable web search fallback
    web_search_min_relevance: float = Field(default=0.5)  # Min relevance score before fallback
    web_search_max_results: int = Field(default=5)  # Max web search results to fetch

    # ----- Security -----
    secret_key: str = Field(
        default="",
        description="Secret key for session encryption (REQUIRED in production)"
    )
    allowed_origins: str = Field(
        default="http://localhost:3000,http://localhost:3001",
        description="Comma-separated list of allowed CORS origins"
    )
    api_keys: str = Field(
        default="",
        description="Comma-separated list of valid API keys for authentication"
    )
    require_auth: bool = Field(
        default=False,
        description="Require API key authentication for all endpoints"
    )

    # ----- JWT Authentication -----
    jwt_secret_key: str = Field(
        default="",
        description="Secret key for JWT signing (defaults to secret_key if not set)"
    )
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=30)
    jwt_refresh_token_expire_days: int = Field(default=7)

    # ----- OAuth - Google -----
    google_client_id: str = Field(
        default="",
        description="Google OAuth Client ID"
    )
    google_client_secret: str = Field(
        default="",
        description="Google OAuth Client Secret"
    )

    # ----- Email Verification -----
    smtp_host: str = Field(default="smtp.gmail.com")
    smtp_port: int = Field(default=587)
    smtp_user: str = Field(default="")
    smtp_password: str = Field(default="")
    email_from: str = Field(default="noreply@api-assistant.com")
    verification_token_expire_hours: int = Field(default=24)

    # ----- Password Requirements -----
    password_min_length: int = Field(default=8)
    password_require_uppercase: bool = Field(default=True)
    password_require_lowercase: bool = Field(default=True)
    password_require_digit: bool = Field(default=True)
    password_require_special: bool = Field(default=True)

    @property
    def allowed_extensions_list(self) -> list[str]:
        """Get allowed extensions as a list."""
        return [ext.strip() for ext in self.allowed_extensions.split(",")]

    @property
    def cors_origins(self) -> list[str]:
        """Parse allowed CORS origins into list."""
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def api_keys_list(self) -> list[str]:
        """Parse API keys into list."""
        return [key.strip() for key in self.api_keys.split(",") if key.strip()]

    @property
    def max_upload_size_bytes(self) -> int:
        """Get max upload size in bytes."""
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def effective_jwt_secret(self) -> str:
        """Get JWT secret key, falling back to secret_key if not set."""
        return self.jwt_secret_key or self.secret_key

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
