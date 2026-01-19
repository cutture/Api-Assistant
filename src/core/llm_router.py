"""
LLM Router - Task-based routing to appropriate LLM providers.

Routes tasks to the most cost-effective LLM based on complexity:
- Simple (score < 3): Ollama local (free)
- Medium (score 3-6): Groq (fast, cheap cloud)
- Complex (score > 6): Premium models (future: Claude/GPT-4)

Complexity scoring factors:
- Lines of code needed: +1 per 50 lines
- Number of files: +1 per file
- External dependencies: +1 per dependency
- API integrations: +2 per API
- Database operations: +2
- Authentication logic: +2
- Multi-language: +3
- UI components: +2
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Literal, Optional

import structlog

from src.config import settings
from src.core.llm_client import LLMClient

logger = structlog.get_logger(__name__)


class ComplexityTier(str, Enum):
    """Complexity tier for routing."""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


@dataclass
class ComplexityAnalysis:
    """Result of complexity analysis."""
    score: int
    tier: ComplexityTier
    factors: dict[str, int]
    estimated_lines: int
    estimated_files: int
    languages: list[str]
    reasoning: str


@dataclass
class RouterResult:
    """Result of LLM routing decision."""
    provider: Literal["ollama", "groq"]
    model: str
    complexity: ComplexityAnalysis
    fallback_chain: list[tuple[str, str]]  # List of (provider, model) fallbacks


class LLMRouter:
    """
    Routes code generation tasks to appropriate LLM based on complexity.

    Features:
    - Complexity-based routing
    - Cost optimization (local first)
    - Fallback chain for reliability
    - Language detection
    """

    # Keywords that indicate higher complexity
    COMPLEXITY_KEYWORDS = {
        "authentication": 2,
        "auth": 2,
        "oauth": 3,
        "jwt": 2,
        "api": 2,
        "rest": 1,
        "graphql": 2,
        "database": 2,
        "sql": 2,
        "mongodb": 2,
        "postgresql": 2,
        "mysql": 2,
        "redis": 2,
        "websocket": 3,
        "realtime": 2,
        "streaming": 2,
        "microservice": 3,
        "docker": 2,
        "kubernetes": 3,
        "ci/cd": 2,
        "testing": 1,
        "unit test": 1,
        "integration test": 2,
        "react": 2,
        "vue": 2,
        "angular": 2,
        "frontend": 2,
        "backend": 2,
        "fullstack": 4,
        "machine learning": 4,
        "ml": 3,
        "ai": 3,
        "neural network": 4,
        "encryption": 2,
        "security": 2,
        "payment": 3,
        "stripe": 2,
        "email": 1,
        "file upload": 2,
        "image processing": 3,
        "video": 3,
        "pdf": 2,
        "excel": 2,
        "csv": 1,
        "scraping": 2,
        "crawler": 3,
        "async": 2,
        "concurrent": 2,
        "parallel": 2,
        "distributed": 3,
        "cache": 2,
        "queue": 2,
        "worker": 2,
        "scheduler": 2,
        "cron": 1,
    }

    # Language indicators
    LANGUAGE_KEYWORDS = {
        "python": ["python", "django", "flask", "fastapi", "pandas", "numpy", "pytorch", "tensorflow"],
        "javascript": ["javascript", "js", "node", "express", "react", "vue", "angular", "npm"],
        "typescript": ["typescript", "ts", "tsx", "nest.js", "next.js"],
        "java": ["java", "spring", "maven", "gradle", "kotlin"],
        "go": ["golang", "go ", "gin", "echo"],
        "rust": ["rust", "cargo", "tokio"],
        "csharp": ["c#", "csharp", ".net", "dotnet", "asp.net"],
        "sql": ["sql", "query", "select", "insert", "update", "delete"],
    }

    def __init__(self):
        """Initialize the LLM router."""
        self.ollama_model = settings.ollama_model
        self.groq_model = settings.groq_code_model
        logger.info(
            "llm_router_initialized",
            ollama_model=self.ollama_model,
            groq_model=self.groq_model,
        )

    def analyze_complexity(self, prompt: str) -> ComplexityAnalysis:
        """
        Analyze the complexity of a code generation request.

        Args:
            prompt: The user's code generation request

        Returns:
            ComplexityAnalysis with score, tier, and breakdown
        """
        prompt_lower = prompt.lower()
        factors = {}

        # Keyword-based scoring
        keyword_score = 0
        for keyword, weight in self.COMPLEXITY_KEYWORDS.items():
            if keyword in prompt_lower:
                keyword_score += weight
                factors[f"keyword_{keyword}"] = weight

        # Estimate lines of code
        estimated_lines = self._estimate_lines(prompt_lower)
        line_score = estimated_lines // 50
        if line_score > 0:
            factors["estimated_lines"] = line_score

        # Estimate number of files
        estimated_files = self._estimate_files(prompt_lower)
        file_score = estimated_files
        if file_score > 0:
            factors["estimated_files"] = file_score

        # Multi-language penalty
        languages = self._detect_languages(prompt_lower)
        if len(languages) > 1:
            multi_lang_score = 3
            factors["multi_language"] = multi_lang_score
        else:
            multi_lang_score = 0

        # Calculate total score
        total_score = keyword_score + line_score + file_score + multi_lang_score

        # Determine tier
        if total_score < 3:
            tier = ComplexityTier.SIMPLE
        elif total_score <= 6:
            tier = ComplexityTier.MEDIUM
        else:
            tier = ComplexityTier.COMPLEX

        # Generate reasoning
        reasoning = self._generate_reasoning(total_score, tier, factors, languages)

        return ComplexityAnalysis(
            score=total_score,
            tier=tier,
            factors=factors,
            estimated_lines=estimated_lines,
            estimated_files=estimated_files,
            languages=languages or ["python"],  # Default to Python
            reasoning=reasoning,
        )

    def route(
        self,
        prompt: str,
        preference: Optional[Literal["fast", "balanced", "quality"]] = None,
        force_provider: Optional[Literal["ollama", "groq"]] = None,
    ) -> RouterResult:
        """
        Route a code generation request to the appropriate LLM.

        Args:
            prompt: The code generation request
            preference: User preference for routing
                - "fast": Prefer local Ollama
                - "balanced": Use complexity-based routing (default)
                - "quality": Prefer cloud models
            force_provider: Override routing and use specific provider

        Returns:
            RouterResult with selected provider and fallback chain
        """
        complexity = self.analyze_complexity(prompt)

        logger.info(
            "llm_routing_decision",
            complexity_score=complexity.score,
            complexity_tier=complexity.tier.value,
            preference=preference,
            force_provider=force_provider,
        )

        # Handle forced provider
        if force_provider:
            provider = force_provider
            model = self.ollama_model if provider == "ollama" else self.groq_model
            fallback_chain = self._get_fallback_chain(provider)
            return RouterResult(
                provider=provider,
                model=model,
                complexity=complexity,
                fallback_chain=fallback_chain,
            )

        # Route based on preference and complexity
        if preference == "fast":
            # Always use Ollama if available
            provider = "ollama"
            model = self.ollama_model
        elif preference == "quality":
            # Always use best available (Groq for now)
            provider = "groq"
            model = self.groq_model
        else:
            # Balanced: use complexity-based routing
            if complexity.tier == ComplexityTier.SIMPLE:
                # Simple tasks: use Ollama (free, fast for simple)
                provider = "ollama"
                model = self.ollama_model
            elif complexity.tier == ComplexityTier.MEDIUM:
                # Medium tasks: use Groq (better quality)
                provider = "groq"
                model = self.groq_model
            else:
                # Complex tasks: use Groq (future: Claude/GPT-4)
                provider = "groq"
                model = self.groq_model

        # Build fallback chain
        fallback_chain = self._get_fallback_chain(provider)

        return RouterResult(
            provider=provider,
            model=model,
            complexity=complexity,
            fallback_chain=fallback_chain,
        )

    def get_client(self, route_result: RouterResult) -> LLMClient:
        """
        Get an LLM client based on routing result.

        Args:
            route_result: Result from route() method

        Returns:
            Configured LLMClient instance
        """
        return LLMClient(
            provider=route_result.provider,
            model=route_result.model,
        )

    def _estimate_lines(self, prompt: str) -> int:
        """Estimate lines of code needed based on prompt."""
        # Simple heuristic based on task description
        indicators = {
            "simple": 20,
            "basic": 30,
            "small": 30,
            "quick": 20,
            "function": 30,
            "class": 50,
            "module": 100,
            "service": 150,
            "api": 100,
            "full": 200,
            "complete": 150,
            "comprehensive": 200,
            "application": 300,
            "app": 200,
            "system": 300,
            "project": 400,
        }

        max_estimate = 50  # Default
        for indicator, lines in indicators.items():
            if indicator in prompt:
                max_estimate = max(max_estimate, lines)

        return max_estimate

    def _estimate_files(self, prompt: str) -> int:
        """Estimate number of files needed based on prompt."""
        # Look for multi-file indicators
        indicators = {
            "file": 1,
            "module": 2,
            "package": 3,
            "project": 5,
            "application": 4,
            "microservice": 5,
            "separate": 2,
            "multiple": 3,
        }

        max_files = 1  # Default single file
        for indicator, files in indicators.items():
            if indicator in prompt:
                max_files = max(max_files, files)

        return max_files

    def _detect_languages(self, prompt: str) -> list[str]:
        """Detect programming languages mentioned in prompt."""
        detected = []

        for lang, keywords in self.LANGUAGE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in prompt:
                    if lang not in detected:
                        detected.append(lang)
                    break

        return detected

    def _generate_reasoning(
        self,
        score: int,
        tier: ComplexityTier,
        factors: dict[str, int],
        languages: list[str],
    ) -> str:
        """Generate human-readable reasoning for complexity assessment."""
        parts = []

        # Tier explanation
        tier_explanations = {
            ComplexityTier.SIMPLE: "This is a simple task suitable for fast local generation.",
            ComplexityTier.MEDIUM: "This is a moderately complex task requiring a capable model.",
            ComplexityTier.COMPLEX: "This is a complex task requiring a high-quality model.",
        }
        parts.append(tier_explanations[tier])

        # Key factors
        if factors:
            key_factors = sorted(factors.items(), key=lambda x: x[1], reverse=True)[:3]
            factor_str = ", ".join(f"{k.replace('keyword_', '')}" for k, v in key_factors)
            parts.append(f"Key factors: {factor_str}.")

        # Languages
        if languages:
            parts.append(f"Languages: {', '.join(languages)}.")

        return " ".join(parts)

    def _get_fallback_chain(self, primary_provider: str) -> list[tuple[str, str]]:
        """Get fallback chain for a provider."""
        if primary_provider == "ollama":
            # Ollama -> Groq fallback
            return [
                ("groq", self.groq_model),
            ]
        else:
            # Groq -> Ollama fallback (if Groq fails)
            return [
                ("ollama", self.ollama_model),
            ]


# Singleton instance
_router: Optional[LLMRouter] = None


def get_llm_router() -> LLMRouter:
    """Get the global LLM router instance."""
    global _router
    if _router is None:
        _router = LLMRouter()
    return _router
