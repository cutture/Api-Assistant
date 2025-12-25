"""
Unit tests for Documentation Analyzer Agent.
"""

import pytest

from src.agents.doc_analyzer import (
    DocumentationAnalyzer,
    DocumentationGap,
    GapSeverity,
    GapType,
)
from src.agents.state import AgentType, create_initial_state


class TestDocumentationGap:
    """Test DocumentationGap class."""

    def test_gap_creation(self):
        """Test creating a documentation gap."""
        gap = DocumentationGap(
            gap_type=GapType.MISSING_DESCRIPTION,
            severity=GapSeverity.HIGH,
            endpoint="/users",
            method="GET",
            description="No description provided",
            suggestion="Add a description",
        )

        assert gap.gap_type == GapType.MISSING_DESCRIPTION
        assert gap.severity == GapSeverity.HIGH
        assert gap.endpoint == "/users"
        assert gap.method == "GET"

    def test_gap_to_dict(self):
        """Test converting gap to dictionary."""
        gap = DocumentationGap(
            gap_type=GapType.MISSING_EXAMPLES,
            severity=GapSeverity.MEDIUM,
            endpoint="/posts",
            method="POST",
            description="No examples",
            suggestion="Add examples",
        )

        gap_dict = gap.to_dict()

        assert gap_dict["gap_type"] == "missing_examples"
        assert gap_dict["severity"] == "medium"
        assert gap_dict["endpoint"] == "/posts"
        assert gap_dict["method"] == "POST"

    def test_gap_repr(self):
        """Test gap string representation."""
        gap = DocumentationGap(
            gap_type=GapType.MISSING_AUTH_INFO,
            severity=GapSeverity.CRITICAL,
            endpoint="/admin",
            method="DELETE",
            description="Auth missing",
            suggestion="Add auth info",
        )

        repr_str = repr(gap)

        assert "critical" in repr_str
        assert "missing_auth_info" in repr_str
        assert "DELETE" in repr_str
        assert "/admin" in repr_str


class TestDocumentationAnalyzer:
    """Test suite for Documentation Analyzer Agent."""

    @pytest.fixture
    def analyzer(self):
        """Create DocumentationAnalyzer instance."""
        return DocumentationAnalyzer()

    def test_agent_properties(self, analyzer):
        """Test agent properties."""
        assert analyzer.name == "doc_analyzer"
        assert analyzer.agent_type == AgentType.DOC_ANALYZER
        assert "documentation" in analyzer.description.lower()

    def test_process_with_no_documents(self, analyzer):
        """Test processing with no documents returns error."""
        state = create_initial_state("Find gaps")

        result = analyzer.process(state)

        assert result.get("error") is not None
        assert result["error"]["agent"] == "doc_analyzer"
        assert result["error"]["error_type"] == "missing_input"

    def test_process_with_well_documented_endpoint(self, analyzer):
        """Test processing with comprehensive documentation."""
        state = create_initial_state("Analyze docs")
        state["retrieved_documents"] = [
            {
                "content": "GET /users - Returns a list of all users. "
                "Parameters: limit (integer) - Maximum number of users to return. "
                "Authentication: Bearer token required. "
                "Example: GET /users?limit=10 "
                "Response: 200 OK with JSON array of user objects. "
                "Error codes: 401 Unauthorized, 500 Internal Server Error.",
                "metadata": {"endpoint": "/users", "method": "GET"},
                "score": 0.9,
                "doc_id": "doc1",
            }
        ]

        result = analyzer.process(state)

        assert result.get("error") is None
        gaps = result["documentation_gaps"]
        # Should have few or no gaps
        assert len(gaps) <= 2  # Might flag some minor issues

    def test_process_with_missing_description(self, analyzer):
        """Test detection of missing description."""
        state = create_initial_state("Analyze docs")
        state["retrieved_documents"] = [
            {
                "content": "/users",  # Very short, no real description
                "metadata": {"endpoint": "/users", "method": "GET"},
                "score": 0.9,
                "doc_id": "doc1",
            }
        ]

        result = analyzer.process(state)

        gaps = result["documentation_gaps"]
        # Should detect missing description
        assert len(gaps) > 0
        assert any(
            gap["gap_type"] == "missing_description" for gap in gaps
        )

    def test_process_with_missing_parameters(self, analyzer):
        """Test detection of missing parameters."""
        state = create_initial_state("Analyze docs")
        state["retrieved_documents"] = [
            {
                "content": "POST /users - Creates a new user",
                "metadata": {"endpoint": "/users", "method": "POST"},
                "score": 0.9,
                "doc_id": "doc1",
            }
        ]

        result = analyzer.process(state)

        gaps = result["documentation_gaps"]
        # Should detect missing parameters
        assert any(
            gap["gap_type"] == "missing_parameters" for gap in gaps
        )

    def test_process_with_missing_examples(self, analyzer):
        """Test detection of missing examples."""
        state = create_initial_state("Analyze docs")
        state["retrieved_documents"] = [
            {
                "content": "GET /users - Returns users list with parameters: limit, offset",
                "metadata": {"endpoint": "/users", "method": "GET"},
                "score": 0.9,
                "doc_id": "doc1",
            }
        ]

        result = analyzer.process(state)

        gaps = result["documentation_gaps"]
        # Should detect missing examples
        assert any(
            gap["gap_type"] == "missing_examples" for gap in gaps
        )

    def test_process_with_missing_auth_info(self, analyzer):
        """Test detection of missing authentication info."""
        state = create_initial_state("Analyze docs")
        state["retrieved_documents"] = [
            {
                "content": "DELETE /users/{id} - Deletes a user account. Requires user ID parameter.",
                "metadata": {"endpoint": "/users/{id}", "method": "DELETE"},
                "score": 0.9,
                "doc_id": "doc1",
            }
        ]

        result = analyzer.process(state)

        gaps = result["documentation_gaps"]
        # Should detect missing auth (critical for DELETE)
        critical_gaps = [gap for gap in gaps if gap["severity"] == "critical"]
        assert len(critical_gaps) > 0

    def test_process_with_missing_error_codes(self, analyzer):
        """Test detection of missing error codes."""
        state = create_initial_state("Analyze docs")
        state["retrieved_documents"] = [
            {
                "content": "GET /users - Returns list of users with authentication required",
                "metadata": {"endpoint": "/users", "method": "GET"},
                "score": 0.9,
                "doc_id": "doc1",
            }
        ]

        result = analyzer.process(state)

        gaps = result["documentation_gaps"]
        # Should detect missing error codes
        assert any(
            gap["gap_type"] == "missing_error_codes" for gap in gaps
        )

    def test_process_with_missing_response_format(self, analyzer):
        """Test detection of missing response format."""
        state = create_initial_state("Analyze docs")
        state["retrieved_documents"] = [
            {
                "content": "GET /users - Gets users",
                "metadata": {"endpoint": "/users", "method": "GET"},
                "score": 0.9,
                "doc_id": "doc1",
            }
        ]

        result = analyzer.process(state)

        gaps = result["documentation_gaps"]
        # Should detect missing response format
        assert any(
            gap["gap_type"] == "missing_response_format" for gap in gaps
        )

    def test_quality_score_calculation(self, analyzer):
        """Test documentation quality score calculation."""
        # Perfect documentation
        gaps_perfect = []
        score_perfect = analyzer._calculate_quality_score(gaps_perfect, 1)
        assert score_perfect == 100.0

        # Poor documentation with critical issues
        gaps_poor = [
            DocumentationGap(
                GapType.MISSING_AUTH_INFO,
                GapSeverity.CRITICAL,
                "/test",
                "POST",
                "desc",
                "sug",
            )
            for _ in range(5)
        ]
        score_poor = analyzer._calculate_quality_score(gaps_poor, 1)
        assert score_poor < 50.0

    def test_quality_score_with_mixed_severity(self, analyzer):
        """Test quality score with mixed severity gaps."""
        gaps = [
            DocumentationGap(
                GapType.MISSING_AUTH_INFO,
                GapSeverity.CRITICAL,
                "/test",
                "POST",
                "d",
                "s",
            ),
            DocumentationGap(
                GapType.MISSING_DESCRIPTION,
                GapSeverity.HIGH,
                "/test",
                "GET",
                "d",
                "s",
            ),
            DocumentationGap(
                GapType.MISSING_EXAMPLES,
                GapSeverity.MEDIUM,
                "/test",
                "PUT",
                "d",
                "s",
            ),
        ]

        score = analyzer._calculate_quality_score(gaps, 3)

        # Should be between 0 and 100
        assert 0 <= score <= 100
        # With issues, should not be perfect
        assert score < 100

    def test_summary_generation_no_gaps(self, analyzer):
        """Test summary generation with no gaps."""
        summary = analyzer._generate_summary([], 100.0)

        assert "Excellent" in summary
        assert "100" in summary
        assert "No significant gaps" in summary

    def test_summary_generation_with_gaps(self, analyzer):
        """Test summary generation with gaps."""
        gaps = [
            DocumentationGap(
                GapType.MISSING_AUTH_INFO,
                GapSeverity.CRITICAL,
                "/admin",
                "DELETE",
                "Auth missing",
                "Add auth",
            ),
            DocumentationGap(
                GapType.MISSING_EXAMPLES,
                GapSeverity.MEDIUM,
                "/users",
                "GET",
                "No examples",
                "Add examples",
            ),
        ]

        summary = analyzer._generate_summary(gaps, 70.0)

        assert "70" in summary
        assert "2" in summary or "two" in summary.lower()
        assert "Critical" in summary or "critical" in summary
        assert "/admin" in summary

    def test_get_gaps_by_severity(self, analyzer):
        """Test filtering gaps by severity."""
        gaps = [
            DocumentationGap(
                GapType.MISSING_AUTH_INFO,
                GapSeverity.CRITICAL,
                "/test1",
                "POST",
                "d",
                "s",
            ),
            DocumentationGap(
                GapType.MISSING_EXAMPLES,
                GapSeverity.MEDIUM,
                "/test2",
                "GET",
                "d",
                "s",
            ),
            DocumentationGap(
                GapType.MISSING_DESCRIPTION,
                GapSeverity.CRITICAL,
                "/test3",
                "PUT",
                "d",
                "s",
            ),
        ]

        critical = analyzer.get_gaps_by_severity(gaps, GapSeverity.CRITICAL)
        medium = analyzer.get_gaps_by_severity(gaps, GapSeverity.MEDIUM)

        assert len(critical) == 2
        assert len(medium) == 1

    def test_get_gaps_by_type(self, analyzer):
        """Test filtering gaps by type."""
        gaps = [
            DocumentationGap(
                GapType.MISSING_AUTH_INFO,
                GapSeverity.CRITICAL,
                "/test1",
                "POST",
                "d",
                "s",
            ),
            DocumentationGap(
                GapType.MISSING_EXAMPLES,
                GapSeverity.MEDIUM,
                "/test2",
                "GET",
                "d",
                "s",
            ),
            DocumentationGap(
                GapType.MISSING_AUTH_INFO,
                GapSeverity.HIGH,
                "/test3",
                "PUT",
                "d",
                "s",
            ),
        ]

        auth_gaps = analyzer.get_gaps_by_type(gaps, GapType.MISSING_AUTH_INFO)
        example_gaps = analyzer.get_gaps_by_type(gaps, GapType.MISSING_EXAMPLES)

        assert len(auth_gaps) == 2
        assert len(example_gaps) == 1

    def test_get_gaps_by_endpoint(self, analyzer):
        """Test filtering gaps by endpoint."""
        gaps = [
            DocumentationGap(
                GapType.MISSING_AUTH_INFO,
                GapSeverity.CRITICAL,
                "/users",
                "POST",
                "d",
                "s",
            ),
            DocumentationGap(
                GapType.MISSING_EXAMPLES,
                GapSeverity.MEDIUM,
                "/posts",
                "GET",
                "d",
                "s",
            ),
            DocumentationGap(
                GapType.MISSING_DESCRIPTION,
                GapSeverity.HIGH,
                "/users",
                "PUT",
                "d",
                "s",
            ),
        ]

        user_gaps = analyzer.get_gaps_by_endpoint(gaps, "/users")
        post_gaps = analyzer.get_gaps_by_endpoint(gaps, "/posts")

        assert len(user_gaps) == 2
        assert len(post_gaps) == 1

    def test_min_description_length_configuration(self):
        """Test configurable minimum description length."""
        analyzer1 = DocumentationAnalyzer(min_description_length=10)
        analyzer2 = DocumentationAnalyzer(min_description_length=50)

        assert analyzer1.min_description_length == 10
        assert analyzer2.min_description_length == 50

    def test_require_examples_configuration(self):
        """Test configurable example requirement."""
        analyzer1 = DocumentationAnalyzer(require_examples=True)
        analyzer2 = DocumentationAnalyzer(require_examples=False)

        assert analyzer1.require_examples is True
        assert analyzer2.require_examples is False

    def test_is_description_missing(self, analyzer):
        """Test description missing detection."""
        assert analyzer._is_description_missing("")
        assert analyzer._is_description_missing("   ")
        assert analyzer._is_description_missing("/users")
        assert not analyzer._is_description_missing("This is a proper description of the endpoint")

    def test_is_description_too_short(self, analyzer):
        """Test short description detection."""
        assert analyzer._is_description_too_short("Short")
        assert analyzer._is_description_too_short("Just a bit")
        assert not analyzer._is_description_too_short("This is a comprehensive description that meets the minimum length")

    def test_has_missing_parameters_for_post(self, analyzer):
        """Test parameter detection for POST."""
        assert analyzer._has_missing_parameters("Creates a user", "POST")
        assert not analyzer._has_missing_parameters("Creates a user with parameters: name, email", "POST")

    def test_is_example_missing(self, analyzer):
        """Test example detection."""
        assert analyzer._is_example_missing("Simple description")
        assert not analyzer._is_example_missing("Description with example: GET /users?limit=10")
        assert not analyzer._is_example_missing("Sample request: ```json\n{}\n```")

    def test_has_missing_error_codes(self, analyzer):
        """Test error code detection."""
        assert analyzer._has_missing_error_codes("Returns user data")
        assert not analyzer._has_missing_error_codes("Returns 200 OK or 404 Not Found")
        assert not analyzer._has_missing_error_codes("Error codes: 400, 401, 500")

    def test_is_auth_info_missing(self, analyzer):
        """Test auth info detection."""
        content_with_auth = "Requires Bearer token authentication"
        content_without_auth = "Returns user data from the database table"

        assert not analyzer._is_auth_info_missing(content_with_auth)
        assert analyzer._is_auth_info_missing(content_without_auth)

    def test_is_response_format_missing(self, analyzer):
        """Test response format detection."""
        assert analyzer._is_response_format_missing("Simple endpoint")
        assert not analyzer._is_response_format_missing("Returns JSON with user schema")
        assert not analyzer._is_response_format_missing("Response: { id, name, email }")

    def test_processing_path_updated(self, analyzer):
        """Test that processing path is updated."""
        state = create_initial_state("test")
        state["retrieved_documents"] = [
            {"content": "test", "metadata": {"endpoint": "/test", "method": "GET"}, "score": 0.9, "doc_id": "doc1"}
        ]

        state = analyzer(state)  # Use __call__

        assert "doc_analyzer" in state["processing_path"]
        assert state["current_agent"] == "doc_analyzer"

    def test_metadata_includes_quality_metrics(self, analyzer):
        """Test that metadata includes quality metrics."""
        state = create_initial_state("test")
        state["retrieved_documents"] = [
            {"content": "short", "metadata": {"endpoint": "/test", "method": "GET"}, "score": 0.9, "doc_id": "doc1"}
        ]

        result = analyzer.process(state)

        metadata = result.get("metadata", {})
        assert "documentation_quality_score" in metadata
        assert "total_gaps" in metadata
        assert "critical_gaps" in metadata
        assert "high_gaps" in metadata

    def test_multiple_endpoints_analysis(self, analyzer):
        """Test analyzing multiple endpoints."""
        state = create_initial_state("test")
        state["retrieved_documents"] = [
            {"content": "GET /users - short", "metadata": {"endpoint": "/users", "method": "GET"}, "score": 0.9, "doc_id": "doc1"},
            {"content": "POST /users - brief", "metadata": {"endpoint": "/users", "method": "POST"}, "score": 0.9, "doc_id": "doc2"},
            {"content": "GET /posts - quick", "metadata": {"endpoint": "/posts", "method": "GET"}, "score": 0.9, "doc_id": "doc3"},
        ]

        result = analyzer.process(state)

        gaps = result["documentation_gaps"]
        # Should have gaps for multiple endpoints
        endpoints = set(gap["endpoint"] for gap in gaps)
        assert len(endpoints) >= 2

    def test_gap_severity_ordering(self, analyzer):
        """Test that summary shows most severe gaps first."""
        gaps = [
            DocumentationGap(GapType.MISSING_EXAMPLES, GapSeverity.LOW, "/test1", "GET", "d", "s"),
            DocumentationGap(GapType.MISSING_AUTH_INFO, GapSeverity.CRITICAL, "/test2", "POST", "d", "s"),
            DocumentationGap(GapType.MISSING_DESCRIPTION, GapSeverity.MEDIUM, "/test3", "PUT", "d", "s"),
        ]

        summary = analyzer._generate_summary(gaps, 60.0)

        # Critical gap should appear before others in summary
        critical_pos = summary.find("/test2")
        low_pos = summary.find("/test1")

        assert critical_pos < low_pos  # Critical should come first
