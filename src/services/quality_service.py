"""
Code Quality Service for scoring code quality.

Provides functionality to calculate quality scores based on multiple factors:
- Code complexity (cyclomatic complexity, nesting depth)
- Test coverage estimation
- Lint/style compliance
- Security scan results
- Documentation coverage
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class QualityLevel(str, Enum):
    """Quality level classification."""
    EXCELLENT = "excellent"  # 90-100
    GOOD = "good"           # 70-89
    FAIR = "fair"           # 50-69
    POOR = "poor"           # 30-49
    CRITICAL = "critical"   # 0-29


@dataclass
class ComplexityMetrics:
    """Metrics related to code complexity."""
    lines_of_code: int = 0
    function_count: int = 0
    class_count: int = 0
    max_nesting_depth: int = 0
    avg_function_length: float = 0.0
    cyclomatic_complexity: int = 1

    def to_dict(self) -> dict:
        return {
            "lines_of_code": self.lines_of_code,
            "function_count": self.function_count,
            "class_count": self.class_count,
            "max_nesting_depth": self.max_nesting_depth,
            "avg_function_length": round(self.avg_function_length, 1),
            "cyclomatic_complexity": self.cyclomatic_complexity,
        }


@dataclass
class DocumentationMetrics:
    """Metrics related to documentation coverage."""
    has_module_docstring: bool = False
    function_docstrings: int = 0
    total_functions: int = 0
    class_docstrings: int = 0
    total_classes: int = 0
    inline_comments: int = 0

    @property
    def docstring_coverage(self) -> float:
        total = self.total_functions + self.total_classes
        if total == 0:
            return 100.0
        documented = self.function_docstrings + self.class_docstrings
        return (documented / total) * 100

    def to_dict(self) -> dict:
        return {
            "has_module_docstring": self.has_module_docstring,
            "function_docstrings": self.function_docstrings,
            "total_functions": self.total_functions,
            "class_docstrings": self.class_docstrings,
            "total_classes": self.total_classes,
            "inline_comments": self.inline_comments,
            "docstring_coverage": round(self.docstring_coverage, 1),
        }


@dataclass
class TestMetrics:
    """Metrics related to test coverage."""
    has_tests: bool = False
    test_count: int = 0
    assertion_count: int = 0
    estimated_coverage: float = 0.0  # Estimated based on test presence

    def to_dict(self) -> dict:
        return {
            "has_tests": self.has_tests,
            "test_count": self.test_count,
            "assertion_count": self.assertion_count,
            "estimated_coverage": round(self.estimated_coverage, 1),
        }


@dataclass
class QualityScore:
    """Complete quality score for code."""
    overall_score: int  # 0-100
    level: QualityLevel
    complexity_metrics: ComplexityMetrics
    documentation_metrics: DocumentationMetrics
    test_metrics: TestMetrics
    lint_score: int = 100  # 0-100
    security_score: int = 100  # 0-100
    breakdown: dict = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "overall_score": self.overall_score,
            "level": self.level.value,
            "complexity": self.complexity_metrics.to_dict(),
            "documentation": self.documentation_metrics.to_dict(),
            "tests": self.test_metrics.to_dict(),
            "lint_score": self.lint_score,
            "security_score": self.security_score,
            "breakdown": self.breakdown,
            "recommendations": self.recommendations,
        }


class QualityService:
    """Service for calculating code quality scores."""

    def __init__(self):
        # Weight configuration for overall score
        self.weights = {
            "complexity": 0.20,
            "documentation": 0.15,
            "tests": 0.25,
            "lint": 0.20,
            "security": 0.20,
        }

    def calculate_quality(
        self,
        code: str,
        language: str,
        tests: Optional[str] = None,
        lint_passed: Optional[bool] = None,
        lint_results: Optional[dict] = None,
        security_passed: Optional[bool] = None,
        security_results: Optional[dict] = None,
    ) -> QualityScore:
        """
        Calculate overall quality score for code.

        Args:
            code: The source code to analyze
            language: Programming language
            tests: Optional test code
            lint_passed: Whether lint check passed
            lint_results: Optional lint results with details
            security_passed: Whether security check passed
            security_results: Optional security results with details

        Returns:
            QualityScore with complete breakdown
        """
        # Calculate component scores
        complexity = self._analyze_complexity(code, language)
        documentation = self._analyze_documentation(code, language)
        test_metrics = self._analyze_tests(tests, language) if tests else TestMetrics()

        # Calculate lint score
        lint_score = self._calculate_lint_score(lint_passed, lint_results)

        # Calculate security score
        security_score = self._calculate_security_score(security_passed, security_results)

        # Calculate component scores (0-100)
        complexity_score = self._score_complexity(complexity)
        documentation_score = self._score_documentation(documentation)
        test_score = self._score_tests(test_metrics)

        # Calculate weighted overall score
        breakdown = {
            "complexity": complexity_score,
            "documentation": documentation_score,
            "tests": test_score,
            "lint": lint_score,
            "security": security_score,
        }

        overall_score = int(sum(
            breakdown[key] * self.weights[key]
            for key in self.weights
        ))

        # Determine quality level
        level = self._determine_level(overall_score)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            complexity, documentation, test_metrics,
            lint_passed, lint_results,
            security_passed, security_results,
            breakdown,
        )

        return QualityScore(
            overall_score=overall_score,
            level=level,
            complexity_metrics=complexity,
            documentation_metrics=documentation,
            test_metrics=test_metrics,
            lint_score=lint_score,
            security_score=security_score,
            breakdown=breakdown,
            recommendations=recommendations,
        )

    def _analyze_complexity(self, code: str, language: str) -> ComplexityMetrics:
        """Analyze code complexity metrics."""
        lines = code.split('\n')
        non_empty_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]

        metrics = ComplexityMetrics(
            lines_of_code=len(non_empty_lines),
        )

        # Count functions and classes based on language
        if language in ('python', 'py'):
            metrics.function_count = len(re.findall(r'^\s*def\s+\w+', code, re.MULTILINE))
            metrics.class_count = len(re.findall(r'^\s*class\s+\w+', code, re.MULTILINE))

            # Estimate cyclomatic complexity (simplified)
            metrics.cyclomatic_complexity = 1 + sum([
                len(re.findall(pattern, code))
                for pattern in [r'\bif\b', r'\belif\b', r'\bfor\b', r'\bwhile\b', r'\band\b', r'\bor\b', r'\bexcept\b']
            ])

            # Calculate nesting depth
            metrics.max_nesting_depth = self._calculate_nesting_depth(code, language)

        elif language in ('javascript', 'typescript', 'js', 'ts'):
            metrics.function_count = len(re.findall(r'(function\s+\w+|const\s+\w+\s*=\s*(?:async\s*)?\(|=>\s*{)', code))
            metrics.class_count = len(re.findall(r'\bclass\s+\w+', code))

            metrics.cyclomatic_complexity = 1 + sum([
                len(re.findall(pattern, code))
                for pattern in [r'\bif\b', r'\bfor\b', r'\bwhile\b', r'\bcase\b', r'\&\&', r'\|\|', r'\bcatch\b']
            ])

            metrics.max_nesting_depth = self._calculate_nesting_depth(code, language)

        elif language in ('java',):
            metrics.function_count = len(re.findall(r'(public|private|protected)\s+\w+\s+\w+\s*\([^)]*\)\s*{', code))
            metrics.class_count = len(re.findall(r'\bclass\s+\w+', code))
            metrics.cyclomatic_complexity = 1 + sum([
                len(re.findall(pattern, code))
                for pattern in [r'\bif\b', r'\bfor\b', r'\bwhile\b', r'\bcase\b', r'\&\&', r'\|\|', r'\bcatch\b']
            ])

        # Calculate average function length
        if metrics.function_count > 0:
            metrics.avg_function_length = metrics.lines_of_code / metrics.function_count

        return metrics

    def _calculate_nesting_depth(self, code: str, language: str) -> int:
        """Calculate maximum nesting depth."""
        max_depth = 0
        current_depth = 0

        if language in ('python', 'py'):
            # For Python, track indentation
            prev_indent = 0
            for line in code.split('\n'):
                if not line.strip():
                    continue
                indent = len(line) - len(line.lstrip())
                if indent > prev_indent:
                    current_depth += 1
                elif indent < prev_indent:
                    current_depth = max(0, current_depth - 1)
                max_depth = max(max_depth, current_depth)
                prev_indent = indent
        else:
            # For brace-based languages, count braces
            for char in code:
                if char == '{':
                    current_depth += 1
                    max_depth = max(max_depth, current_depth)
                elif char == '}':
                    current_depth = max(0, current_depth - 1)

        return max_depth

    def _analyze_documentation(self, code: str, language: str) -> DocumentationMetrics:
        """Analyze documentation coverage."""
        metrics = DocumentationMetrics()

        if language in ('python', 'py'):
            # Check for module docstring
            metrics.has_module_docstring = bool(re.match(r'^[\s]*["\']["\']["\']', code))

            # Count function docstrings
            functions = re.findall(r'def\s+\w+[^:]+:\s*\n(\s+["\']["\']["\'])?', code)
            metrics.total_functions = len(re.findall(r'^\s*def\s+\w+', code, re.MULTILINE))
            metrics.function_docstrings = sum(1 for f in functions if f)

            # Count class docstrings
            classes = re.findall(r'class\s+\w+[^:]*:\s*\n(\s+["\']["\']["\'])?', code)
            metrics.total_classes = len(re.findall(r'^\s*class\s+\w+', code, re.MULTILINE))
            metrics.class_docstrings = sum(1 for c in classes if c)

            # Count inline comments
            metrics.inline_comments = len(re.findall(r'#[^!].*$', code, re.MULTILINE))

        elif language in ('javascript', 'typescript', 'js', 'ts'):
            # Check for module-level JSDoc
            metrics.has_module_docstring = bool(re.search(r'^/\*\*', code, re.MULTILINE))

            # Count JSDoc comments before functions
            jsdocs = re.findall(r'/\*\*[\s\S]*?\*/\s*(function|const|class)', code)
            metrics.function_docstrings = len(jsdocs)
            metrics.total_functions = len(re.findall(r'(function\s+\w+|const\s+\w+\s*=\s*(?:async\s*)?\()', code))

            # Count inline comments
            metrics.inline_comments = len(re.findall(r'//.*$', code, re.MULTILINE))

        return metrics

    def _analyze_tests(self, tests: str, language: str) -> TestMetrics:
        """Analyze test code metrics."""
        if not tests:
            return TestMetrics()

        metrics = TestMetrics(has_tests=True)

        if language in ('python', 'py'):
            # Count test functions
            metrics.test_count = len(re.findall(r'def\s+test_\w+', tests))
            # Count assertions
            metrics.assertion_count = len(re.findall(r'assert\s+', tests))

        elif language in ('javascript', 'typescript', 'js', 'ts'):
            # Count test/it blocks
            metrics.test_count = len(re.findall(r'\b(test|it)\s*\(', tests))
            # Count expect assertions
            metrics.assertion_count = len(re.findall(r'expect\s*\(', tests))

        elif language in ('java',):
            # Count @Test annotations
            metrics.test_count = len(re.findall(r'@Test', tests))
            # Count assert calls
            metrics.assertion_count = len(re.findall(r'assert\w*\s*\(', tests))

        # Estimate coverage based on test density
        if metrics.test_count > 0:
            # Rough estimation: more tests = higher coverage
            metrics.estimated_coverage = min(100, metrics.test_count * 20)

        return metrics

    def _calculate_lint_score(
        self,
        lint_passed: Optional[bool],
        lint_results: Optional[dict],
    ) -> int:
        """Calculate lint score."""
        if lint_passed is None:
            return 80  # Default when not checked

        if lint_passed:
            return 100

        if lint_results:
            # Deduct points based on issue count and severity
            errors = lint_results.get('error_count', 0)
            warnings = lint_results.get('warning_count', 0)

            deductions = (errors * 10) + (warnings * 3)
            return max(0, 100 - deductions)

        return 50  # Default for failed lint without details

    def _calculate_security_score(
        self,
        security_passed: Optional[bool],
        security_results: Optional[dict],
    ) -> int:
        """Calculate security score."""
        if security_passed is None:
            return 80  # Default when not checked

        if security_passed:
            return 100

        if security_results:
            counts = security_results.get('counts', {})
            critical = counts.get('critical', 0)
            high = counts.get('high', 0)
            medium = counts.get('medium', 0)
            low = counts.get('low', 0)

            deductions = (critical * 30) + (high * 15) + (medium * 5) + (low * 1)
            return max(0, 100 - deductions)

        return 30  # Default for failed security without details

    def _score_complexity(self, metrics: ComplexityMetrics) -> int:
        """Score code complexity (higher is better, less complex)."""
        score = 100

        # Penalize high cyclomatic complexity
        if metrics.cyclomatic_complexity > 20:
            score -= 30
        elif metrics.cyclomatic_complexity > 10:
            score -= 15
        elif metrics.cyclomatic_complexity > 5:
            score -= 5

        # Penalize deep nesting
        if metrics.max_nesting_depth > 5:
            score -= 20
        elif metrics.max_nesting_depth > 3:
            score -= 10

        # Penalize very long functions
        if metrics.avg_function_length > 100:
            score -= 20
        elif metrics.avg_function_length > 50:
            score -= 10

        return max(0, score)

    def _score_documentation(self, metrics: DocumentationMetrics) -> int:
        """Score documentation coverage."""
        score = 0

        # Module docstring
        if metrics.has_module_docstring:
            score += 20

        # Docstring coverage
        score += int(metrics.docstring_coverage * 0.6)

        # Bonus for inline comments (up to 20 points)
        comment_bonus = min(20, metrics.inline_comments * 2)
        score += comment_bonus

        return min(100, score)

    def _score_tests(self, metrics: TestMetrics) -> int:
        """Score test coverage."""
        if not metrics.has_tests:
            return 0

        score = 30  # Base score for having tests

        # Add points for test count
        score += min(30, metrics.test_count * 5)

        # Add points for assertions
        score += min(20, metrics.assertion_count * 2)

        # Add estimated coverage
        score += int(metrics.estimated_coverage * 0.2)

        return min(100, score)

    def _determine_level(self, score: int) -> QualityLevel:
        """Determine quality level from score."""
        if score >= 90:
            return QualityLevel.EXCELLENT
        elif score >= 70:
            return QualityLevel.GOOD
        elif score >= 50:
            return QualityLevel.FAIR
        elif score >= 30:
            return QualityLevel.POOR
        else:
            return QualityLevel.CRITICAL

    def _generate_recommendations(
        self,
        complexity: ComplexityMetrics,
        documentation: DocumentationMetrics,
        tests: TestMetrics,
        lint_passed: Optional[bool],
        lint_results: Optional[dict],
        security_passed: Optional[bool],
        security_results: Optional[dict],
        breakdown: dict,
    ) -> list[str]:
        """Generate improvement recommendations."""
        recommendations = []

        # Complexity recommendations
        if breakdown['complexity'] < 70:
            if complexity.cyclomatic_complexity > 10:
                recommendations.append("Reduce cyclomatic complexity by breaking down complex functions")
            if complexity.max_nesting_depth > 3:
                recommendations.append("Reduce nesting depth using early returns or extracting functions")
            if complexity.avg_function_length > 50:
                recommendations.append("Consider splitting long functions into smaller ones")

        # Documentation recommendations
        if breakdown['documentation'] < 70:
            if not documentation.has_module_docstring:
                recommendations.append("Add a module-level docstring explaining the purpose")
            if documentation.docstring_coverage < 50:
                recommendations.append("Add docstrings to more functions and classes")

        # Test recommendations
        if breakdown['tests'] < 70:
            if not tests.has_tests:
                recommendations.append("Add unit tests to verify functionality")
            elif tests.test_count < 5:
                recommendations.append("Increase test coverage with more test cases")
            if tests.assertion_count < tests.test_count * 2:
                recommendations.append("Add more assertions to existing tests")

        # Lint recommendations
        if lint_passed is False:
            recommendations.append("Fix linting issues to improve code style")

        # Security recommendations
        if security_passed is False:
            if security_results:
                counts = security_results.get('counts', {})
                if counts.get('critical', 0) > 0 or counts.get('high', 0) > 0:
                    recommendations.append("Address high/critical security vulnerabilities immediately")
                else:
                    recommendations.append("Review and fix security warnings")

        return recommendations[:5]  # Limit to top 5 recommendations


# Singleton instance
_quality_service: Optional[QualityService] = None


def get_quality_service() -> QualityService:
    """Get or create the quality service singleton."""
    global _quality_service
    if _quality_service is None:
        _quality_service = QualityService()
    return _quality_service
