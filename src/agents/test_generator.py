"""
Test Generator Agent for the Intelligent Coding Agent.

This agent generates tests for code produced by the code generator,
enabling the validation loop to verify code correctness.
"""

import re
from dataclasses import dataclass
from typing import Optional

import structlog

from src.agents.base_agent import BaseAgent
from src.agents.state import AgentState, AgentType, set_error
from src.core.llm_client import LLMClient
from src.core.llm_router import get_llm_router

logger = structlog.get_logger(__name__)


@dataclass
class GeneratedTests:
    """Result of test generation."""
    test_code: str
    language: str
    framework: str
    filename: str
    test_count: int
    dependencies: list[str]


class TestGenerator(BaseAgent):
    """
    Agent that generates tests for provided code.

    Features:
    - Multi-language test generation
    - Framework selection based on language
    - Coverage-focused test cases
    - Edge case detection
    - Integration test support
    """

    # System prompt for test generation
    TEST_GENERATION_SYSTEM_PROMPT = """You are an expert software tester who writes comprehensive, high-quality tests.

Guidelines:
1. Write tests that cover main functionality
2. Include edge cases and error conditions
3. Use appropriate assertions
4. Make tests independent and repeatable
5. Follow testing best practices for the language
6. Include both unit tests and integration tests where appropriate

Output Format:
- Return ONLY the test code
- Include all necessary imports
- Make tests runnable with standard test runners
"""

    # Language-specific test frameworks and instructions
    TEST_FRAMEWORKS = {
        "python": {
            "framework": "pytest",
            "filename": "test_main.py",
            "instructions": """Write pytest tests.
Use pytest fixtures for setup/teardown.
Use parameterized tests for multiple inputs.
Include tests for:
- Happy path scenarios
- Edge cases (empty inputs, None values)
- Error handling
- Type validation""",
            "dependencies": ["pytest"],
            "example": """import pytest
from main import your_function

def test_basic_functionality():
    result = your_function("input")
    assert result == expected_output

def test_edge_case_empty():
    with pytest.raises(ValueError):
        your_function("")
""",
        },
        "javascript": {
            "framework": "jest",
            "filename": "main.test.js",
            "instructions": """Write Jest tests.
Use describe blocks to group related tests.
Use beforeEach/afterEach for setup/cleanup.
Include tests for async functions with async/await.""",
            "dependencies": ["jest"],
            "example": """const { yourFunction } = require('./main');

describe('yourFunction', () => {
  test('should handle basic input', () => {
    expect(yourFunction('input')).toBe('expected');
  });

  test('should throw on invalid input', () => {
    expect(() => yourFunction(null)).toThrow();
  });
});
""",
        },
        "typescript": {
            "framework": "jest",
            "filename": "main.test.ts",
            "instructions": """Write Jest tests with TypeScript.
Use type-safe assertions.
Test type constraints where applicable.""",
            "dependencies": ["jest", "@types/jest", "ts-jest"],
            "example": """import { yourFunction } from './main';

describe('yourFunction', () => {
  it('should return correct type', () => {
    const result = yourFunction('input');
    expect(typeof result).toBe('string');
  });
});
""",
        },
        "java": {
            "framework": "junit",
            "filename": "MainTest.java",
            "instructions": """Write JUnit 5 tests.
Use @BeforeEach and @AfterEach for setup/cleanup.
Use assertThrows for exception testing.
Use parameterized tests where appropriate.""",
            "dependencies": ["junit-jupiter"],
            "example": """import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class MainTest {
    @Test
    void testBasicFunctionality() {
        assertEquals(expected, actual);
    }
}
""",
        },
        "go": {
            "framework": "testing",
            "filename": "main_test.go",
            "instructions": """Write Go tests using the testing package.
Use table-driven tests for multiple cases.
Include benchmarks where performance matters.
Test error returns explicitly.""",
            "dependencies": [],  # Built-in
            "example": """package main

import "testing"

func TestYourFunction(t *testing.T) {
    tests := []struct {
        name     string
        input    string
        expected string
    }{
        {"basic", "input", "expected"},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got := YourFunction(tt.input)
            if got != tt.expected {
                t.Errorf("got %v, want %v", got, tt.expected)
            }
        })
    }
}
""",
        },
        "csharp": {
            "framework": "xunit",
            "filename": "MainTests.cs",
            "instructions": """Write xUnit tests.
Use [Fact] for single tests.
Use [Theory] with [InlineData] for parameterized tests.
Use Assert methods for validation.""",
            "dependencies": ["xunit"],
            "example": """using Xunit;

public class MainTests
{
    [Fact]
    public void TestBasicFunctionality()
    {
        var result = YourFunction("input");
        Assert.Equal(expected, result);
    }

    [Theory]
    [InlineData("input1", "output1")]
    [InlineData("input2", "output2")]
    public void TestMultipleCases(string input, string expected)
    {
        Assert.Equal(expected, YourFunction(input));
    }
}
""",
        },
    }

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Initialize the test generator.

        Args:
            llm_client: Optional LLM client for generation
        """
        super().__init__()
        self._llm_client = llm_client
        self._router = get_llm_router()

    @property
    def name(self) -> str:
        """Return the agent name."""
        return "test_generator"

    @property
    def agent_type(self) -> AgentType:
        """Return the agent type."""
        return AgentType.CUSTOM

    @property
    def description(self) -> str:
        """Return the agent description."""
        return "Generates comprehensive tests for code"

    def process(self, state: AgentState) -> AgentState:
        """
        Generate tests for code in state.

        Args:
            state: State containing generated_code and code_language

        Returns:
            Updated state with generated_tests
        """
        code = state.get("generated_code", "")
        language = state.get("code_language", "python")

        if not code:
            return set_error(
                state,
                agent=self.name,
                error_type="missing_input",
                message="No code provided for test generation",
                recoverable=False,
            )

        try:
            result = self.generate(code, language)

            updated_state = {
                **state,
                "generated_tests": result.test_code,
                "test_framework": result.framework,
                "test_filename": result.filename,
                "test_dependencies": result.dependencies,
                "test_count": result.test_count,
            }

            self._logger.info(
                "test_generation_complete",
                language=language,
                framework=result.framework,
                test_count=result.test_count,
            )

            return updated_state

        except Exception as e:
            self._logger.error("test_generation_failed", error=str(e))
            return set_error(
                state,
                agent=self.name,
                error_type="test_generation_error",
                message=f"Failed to generate tests: {str(e)}",
                recoverable=True,
            )

    def generate(
        self,
        code: str,
        language: str,
        additional_context: Optional[str] = None,
    ) -> GeneratedTests:
        """
        Generate tests for the provided code.

        Args:
            code: The code to generate tests for
            language: Programming language
            additional_context: Optional context about the code

        Returns:
            GeneratedTests with test code and metadata
        """
        # Get framework info
        framework_info = self.TEST_FRAMEWORKS.get(language, self.TEST_FRAMEWORKS["python"])

        # Build the generation prompt
        prompt = self._build_prompt(code, language, framework_info, additional_context)

        # Get LLM client (use quality preference for tests)
        route_result = self._router.route(prompt, preference="quality")
        client = self._llm_client or self._router.get_client(route_result)

        # Generate tests
        response = client.generate(
            prompt=prompt,
            system_prompt=self.TEST_GENERATION_SYSTEM_PROMPT,
            temperature=0.3,
            max_tokens=4096,
        )

        # Clean up response
        test_code = self._clean_test_response(response, language)

        # Count tests
        test_count = self._count_tests(test_code, language)

        self._logger.info(
            "tests_generated",
            language=language,
            framework=framework_info["framework"],
            test_count=test_count,
        )

        return GeneratedTests(
            test_code=test_code,
            language=language,
            framework=framework_info["framework"],
            filename=framework_info["filename"],
            test_count=test_count,
            dependencies=framework_info["dependencies"],
        )

    def _build_prompt(
        self,
        code: str,
        language: str,
        framework_info: dict,
        additional_context: Optional[str] = None,
    ) -> str:
        """Build the test generation prompt."""
        parts = [
            f"Generate comprehensive {framework_info['framework']} tests for the following {language} code.",
            "",
            framework_info["instructions"],
            "",
            "CODE TO TEST:",
            f"```{language}",
            code,
            "```",
            "",
        ]

        if additional_context:
            parts.extend([
                "ADDITIONAL CONTEXT:",
                additional_context,
                "",
            ])

        parts.extend([
            "EXAMPLE TEST FORMAT:",
            f"```{language}",
            framework_info["example"],
            "```",
            "",
            f"Generate complete {framework_info['framework']} tests. Return ONLY the test code:",
        ])

        return "\n".join(parts)

    def _clean_test_response(self, response: str, language: str) -> str:
        """Clean up test code response from LLM."""
        code = response.strip()

        # Remove markdown code blocks
        if code.startswith("```"):
            lines = code.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            code = "\n".join(lines)

        return code.strip()

    def _count_tests(self, test_code: str, language: str) -> int:
        """Count the number of tests in the test code."""
        count = 0

        if language == "python":
            # Count def test_ functions
            count = len(re.findall(r'def test_\w+', test_code))

        elif language in ["javascript", "typescript"]:
            # Count test/it blocks
            count = len(re.findall(r'(?:test|it)\s*\(', test_code))

        elif language == "java":
            # Count @Test annotations
            count = len(re.findall(r'@Test', test_code))

        elif language == "go":
            # Count func Test functions
            count = len(re.findall(r'func Test\w+', test_code))

        elif language == "csharp":
            # Count [Fact] and [Theory] attributes
            count = len(re.findall(r'\[(Fact|Theory)\]', test_code))

        return max(1, count)  # At least 1 if we generated something


# Convenience function
def create_test_generator() -> TestGenerator:
    """Create a new test generator instance."""
    return TestGenerator()
