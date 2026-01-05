"""
Documentation Analyzer Agent for detecting API documentation gaps.

This agent analyzes API documentation to identify missing information,
incomplete descriptions, and areas that need improvement.
"""

from enum import Enum
from typing import Any, Optional

import structlog

from src.agents.base_agent import BaseAgent
from src.agents.state import (
    AgentState,
    AgentType,
    RetrievedDocument,
    add_to_processing_path,
    set_error,
)
from src.core.llm_client import LLMClient

logger = structlog.get_logger(__name__)


class GapSeverity(str, Enum):
    """Severity levels for documentation gaps."""

    CRITICAL = "critical"  # Missing essential information
    HIGH = "high"          # Important information missing
    MEDIUM = "medium"      # Nice to have information missing
    LOW = "low"            # Minor improvements


class GapType(str, Enum):
    """Types of documentation gaps."""

    MISSING_DESCRIPTION = "missing_description"
    MISSING_PARAMETERS = "missing_parameters"
    MISSING_EXAMPLES = "missing_examples"
    MISSING_ERROR_CODES = "missing_error_codes"
    MISSING_AUTH_INFO = "missing_auth_info"
    INCOMPLETE_SCHEMA = "incomplete_schema"
    MISSING_RESPONSE_FORMAT = "missing_response_format"
    UNCLEAR_USAGE = "unclear_usage"


class DocumentationGap:
    """Represents a documentation gap or issue."""

    def __init__(
        self,
        gap_type: GapType,
        severity: GapSeverity,
        endpoint: str,
        method: str,
        description: str,
        suggestion: str,
    ):
        """
        Initialize a documentation gap.

        Args:
            gap_type: Type of gap.
            severity: Severity level.
            endpoint: API endpoint path.
            method: HTTP method.
            description: Description of the issue.
            suggestion: Suggested improvement.
        """
        self.gap_type = gap_type
        self.severity = severity
        self.endpoint = endpoint
        self.method = method
        self.description = description
        self.suggestion = suggestion

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "gap_type": self.gap_type.value,
            "severity": self.severity.value,
            "endpoint": self.endpoint,
            "method": self.method,
            "description": self.description,
            "suggestion": self.suggestion,
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"DocumentationGap({self.severity.value}: {self.gap_type.value} in {self.method} {self.endpoint})"


class DocumentationAnalyzer(BaseAgent):
    """
    Agent that analyzes API documentation for gaps and issues.

    This agent:
    - Identifies missing or incomplete documentation
    - Detects undocumented parameters and responses
    - Finds endpoints without examples
    - Checks for missing authentication information
    - Generates improvement suggestions
    - Calculates documentation quality score

    Example:
        ```python
        analyzer = DocumentationAnalyzer()
        state = create_initial_state("Find documentation gaps")
        state["retrieved_documents"] = [...]  # From RAG agent
        result = analyzer(state)

        # Access gaps
        gaps = result["documentation_gaps"]
        print(f"Found {len(gaps)} issues")
        ```
    """

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        min_description_length: int = 20,
        require_examples: bool = True,
    ):
        """
        Initialize the Documentation Analyzer agent.

        Args:
            llm_client: LLM client for analysis.
            min_description_length: Minimum acceptable description length.
            require_examples: Whether examples are required.
        """
        super().__init__()
        self._llm_client = llm_client or LLMClient()
        self.min_description_length = min_description_length
        self.require_examples = require_examples

    @property
    def name(self) -> str:
        """Return the agent name."""
        return "doc_analyzer"

    @property
    def agent_type(self) -> AgentType:
        """Return the agent type."""
        return AgentType.DOC_ANALYZER

    @property
    def description(self) -> str:
        """Return the agent description."""
        return "Analyzes API documentation to identify gaps and suggest improvements"

    def process(self, state: AgentState) -> AgentState:
        """
        Analyze documentation for gaps and issues.

        Args:
            state: Current agent state with query and retrieved_documents.

        Returns:
            Updated state with documentation_gaps populated.
        """
        query = state.get("query", "")
        retrieved_docs = state.get("retrieved_documents", [])

        if not retrieved_docs:
            self._logger.warning("No documents to analyze")
            return set_error(
                state,
                agent=self.name,
                error_type="missing_input",
                message="No API documentation found to analyze",
                recoverable=False,
            )

        self._logger.info("Analyzing documentation", doc_count=len(retrieved_docs))

        try:
            # Analyze documents for gaps
            gaps = self._analyze_documents(retrieved_docs)

            # Calculate quality score
            quality_score = self._calculate_quality_score(gaps, len(retrieved_docs))

            # Generate summary
            summary = self._generate_summary(gaps, quality_score)

            # Update state
            updated_state = {
                **state,
                "documentation_gaps": [gap.to_dict() for gap in gaps],
                "response": summary,
                "metadata": {
                    **state.get("metadata", {}),
                    "documentation_quality_score": quality_score,
                    "total_gaps": len(gaps),
                    "critical_gaps": len([g for g in gaps if g.severity == GapSeverity.CRITICAL]),
                    "high_gaps": len([g for g in gaps if g.severity == GapSeverity.HIGH]),
                },
            }

            self._logger.info(
                "Documentation analysis complete",
                total_gaps=len(gaps),
                quality_score=quality_score,
            )

            return updated_state

        except Exception as e:
            self._logger.error("Documentation analysis failed", error=str(e))
            return set_error(
                state,
                agent=self.name,
                error_type="analysis_error",
                message=f"Failed to analyze documentation: {str(e)}",
                recoverable=True,
            )

    def _analyze_documents(self, retrieved_docs: list[dict]) -> list[DocumentationGap]:
        """
        Analyze documents for gaps and issues.

        Args:
            retrieved_docs: Retrieved documents to analyze.

        Returns:
            List of identified gaps.
        """
        gaps = []

        for doc_dict in retrieved_docs:
            doc = RetrievedDocument(**doc_dict)
            metadata = doc.metadata
            content = doc.content

            endpoint = metadata.get("endpoint", "")
            method = metadata.get("method", "")

            # Skip if no endpoint info
            if not endpoint:
                continue

            # Check for missing description
            if self._is_description_missing(content):
                gaps.append(
                    DocumentationGap(
                        gap_type=GapType.MISSING_DESCRIPTION,
                        severity=GapSeverity.HIGH,
                        endpoint=endpoint,
                        method=method,
                        description="Endpoint lacks a clear description",
                        suggestion=f"Add a detailed description explaining what {method} {endpoint} does",
                    )
                )

            # Check for short/unclear description
            elif self._is_description_too_short(content):
                gaps.append(
                    DocumentationGap(
                        gap_type=GapType.MISSING_DESCRIPTION,
                        severity=GapSeverity.MEDIUM,
                        endpoint=endpoint,
                        method=method,
                        description="Endpoint description is too brief",
                        suggestion=f"Expand the description for {method} {endpoint} to be more detailed",
                    )
                )

            # Check for missing parameters
            if self._has_missing_parameters(content, method):
                gaps.append(
                    DocumentationGap(
                        gap_type=GapType.MISSING_PARAMETERS,
                        severity=GapSeverity.HIGH,
                        endpoint=endpoint,
                        method=method,
                        description="Parameters are not documented",
                        suggestion=f"Document all parameters for {method} {endpoint} including types and descriptions",
                    )
                )

            # Check for missing examples
            if self.require_examples and self._is_example_missing(content):
                gaps.append(
                    DocumentationGap(
                        gap_type=GapType.MISSING_EXAMPLES,
                        severity=GapSeverity.MEDIUM,
                        endpoint=endpoint,
                        method=method,
                        description="No usage examples provided",
                        suggestion=f"Add example request/response for {method} {endpoint}",
                    )
                )

            # Check for missing error codes
            if self._has_missing_error_codes(content):
                gaps.append(
                    DocumentationGap(
                        gap_type=GapType.MISSING_ERROR_CODES,
                        severity=GapSeverity.MEDIUM,
                        endpoint=endpoint,
                        method=method,
                        description="Error codes are not documented",
                        suggestion=f"Document possible error codes and responses for {method} {endpoint}",
                    )
                )

            # Check for missing auth info
            if self._is_auth_info_missing(content):
                gaps.append(
                    DocumentationGap(
                        gap_type=GapType.MISSING_AUTH_INFO,
                        severity=GapSeverity.CRITICAL,
                        endpoint=endpoint,
                        method=method,
                        description="Authentication requirements not documented",
                        suggestion=f"Document authentication requirements for {method} {endpoint}",
                    )
                )

            # Check for missing response format
            if self._is_response_format_missing(content):
                gaps.append(
                    DocumentationGap(
                        gap_type=GapType.MISSING_RESPONSE_FORMAT,
                        severity=GapSeverity.HIGH,
                        endpoint=endpoint,
                        method=method,
                        description="Response format is not documented",
                        suggestion=f"Document the response format and schema for {method} {endpoint}",
                    )
                )

        return gaps

    def _is_description_missing(self, content: str) -> bool:
        """Check if description is missing."""
        content_lower = content.lower()
        # Very short content likely means no description
        return len(content.strip()) < 10

    def _is_description_too_short(self, content: str) -> bool:
        """Check if description is too short."""
        return len(content.strip()) < self.min_description_length

    def _has_missing_parameters(self, content: str, method: str) -> bool:
        """Check if parameters are missing for methods that typically need them."""
        content_lower = content.lower()

        # Methods that often have parameters
        if method.upper() in ["POST", "PUT", "PATCH", "GET"]:
            # Check for parameter keywords
            has_param_info = any(
                keyword in content_lower
                for keyword in ["parameter", "param", "query", "body", "field"]
            )
            return not has_param_info

        return False

    def _is_example_missing(self, content: str) -> bool:
        """Check if examples are missing."""
        content_lower = content.lower()
        has_example = any(
            keyword in content_lower for keyword in ["example", "sample", "```", "response:", "request:"]
        )
        return not has_example

    def _has_missing_error_codes(self, content: str) -> bool:
        """Check if error codes are missing."""
        content_lower = content.lower()
        has_errors = any(
            keyword in content_lower for keyword in ["error", "status code", "400", "401", "404", "500"]
        )
        return not has_errors

    def _is_auth_info_missing(self, content: str) -> bool:
        """Check if authentication info is missing."""
        content_lower = content.lower()

        # Check if there's any auth-related information
        has_auth = any(
            keyword in content_lower
            for keyword in ["auth", "token", "api key", "bearer", "authorization", "credential"]
        )

        # If no auth info AND content is substantial, it might be missing
        return not has_auth and len(content.strip()) > 10

    def _is_response_format_missing(self, content: str) -> bool:
        """Check if response format is missing."""
        content_lower = content.lower()
        has_response = any(
            keyword in content_lower for keyword in ["response", "returns", "output", "json", "schema"]
        )
        return not has_response

    def _calculate_quality_score(self, gaps: list[DocumentationGap], total_docs: int) -> float:
        """
        Calculate documentation quality score (0-100).

        Args:
            gaps: List of identified gaps.
            total_docs: Total number of documents analyzed.

        Returns:
            Quality score from 0 (poor) to 100 (excellent).
        """
        if total_docs == 0:
            return 0.0

        # Weight gaps by severity
        severity_weights = {
            GapSeverity.CRITICAL: 10,
            GapSeverity.HIGH: 5,
            GapSeverity.MEDIUM: 2,
            GapSeverity.LOW: 1,
        }

        # Calculate total penalty
        total_penalty = sum(severity_weights[gap.severity] for gap in gaps)

        # Max possible penalty (if all docs had all critical issues)
        max_penalty_per_doc = 30  # Approximate max
        max_penalty = total_docs * max_penalty_per_doc

        # Calculate score
        if max_penalty == 0:
            score = 100.0
        else:
            score = max(0, 100 - (total_penalty / max_penalty * 100))

        return round(score, 1)

    def _generate_summary(self, gaps: list[DocumentationGap], quality_score: float) -> str:
        """
        Generate summary of documentation analysis.

        Args:
            gaps: List of identified gaps.
            quality_score: Overall quality score.

        Returns:
            Summary text.
        """
        if not gaps:
            return f"✅ Documentation Quality: Excellent ({quality_score}/100)\n\nNo significant gaps found. The API documentation is comprehensive and well-maintained."

        # Count by severity
        critical = len([g for g in gaps if g.severity == GapSeverity.CRITICAL])
        high = len([g for g in gaps if g.severity == GapSeverity.HIGH])
        medium = len([g for g in gaps if g.severity == GapSeverity.MEDIUM])
        low = len([g for g in gaps if g.severity == GapSeverity.LOW])

        # Determine quality level
        if quality_score >= 80:
            quality_level = "Good"
            emoji = "👍"
        elif quality_score >= 60:
            quality_level = "Fair"
            emoji = "⚠️"
        else:
            quality_level = "Needs Improvement"
            emoji = "❌"

        summary = f"{emoji} Documentation Quality: {quality_level} ({quality_score}/100)\n\n"
        summary += f"Found {len(gaps)} documentation gap(s):\n"

        if critical > 0:
            summary += f"  • {critical} Critical issue(s)\n"
        if high > 0:
            summary += f"  • {high} High priority issue(s)\n"
        if medium > 0:
            summary += f"  • {medium} Medium priority issue(s)\n"
        if low > 0:
            summary += f"  • {low} Low priority issue(s)\n"

        summary += "\nTop Issues:\n"
        # Show top 5 most severe gaps
        sorted_gaps = sorted(
            gaps,
            key=lambda g: (
                ["critical", "high", "medium", "low"].index(g.severity.value),
                g.gap_type.value,
            ),
        )

        for gap in sorted_gaps[:5]:
            summary += f"\n• [{gap.severity.value.upper()}] {gap.method} {gap.endpoint}\n"
            summary += f"  {gap.description}\n"
            summary += f"  💡 {gap.suggestion}\n"

        if len(gaps) > 5:
            summary += f"\n... and {len(gaps) - 5} more issue(s)"

        return summary

    def get_gaps_by_severity(self, gaps: list[DocumentationGap], severity: GapSeverity) -> list[DocumentationGap]:
        """
        Filter gaps by severity level.

        Args:
            gaps: List of all gaps.
            severity: Severity level to filter by.

        Returns:
            Filtered list of gaps.
        """
        return [gap for gap in gaps if gap.severity == severity]

    def get_gaps_by_type(self, gaps: list[DocumentationGap], gap_type: GapType) -> list[DocumentationGap]:
        """
        Filter gaps by type.

        Args:
            gaps: List of all gaps.
            gap_type: Gap type to filter by.

        Returns:
            Filtered list of gaps.
        """
        return [gap for gap in gaps if gap.gap_type == gap_type]

    def get_gaps_by_endpoint(self, gaps: list[DocumentationGap], endpoint: str) -> list[DocumentationGap]:
        """
        Filter gaps by endpoint.

        Args:
            gaps: List of all gaps.
            endpoint: Endpoint path to filter by.

        Returns:
            Filtered list of gaps.
        """
        return [gap for gap in gaps if gap.endpoint == endpoint]
