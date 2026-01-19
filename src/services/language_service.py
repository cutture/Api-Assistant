"""
Language Service.

Provides language-specific configurations, test generators, and lint rules
for multiple programming languages including Python, JavaScript, TypeScript,
Java, Go, and C#.
"""

import re
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Any
from functools import lru_cache

logger = logging.getLogger(__name__)


class Language(str, Enum):
    """Supported programming languages."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    GO = "go"
    CSHARP = "csharp"
    RUST = "rust"
    RUBY = "ruby"
    PHP = "php"
    KOTLIN = "kotlin"
    SWIFT = "swift"
    SQL = "sql"


@dataclass
class LanguageConfig:
    """Configuration for a programming language."""
    language: Language
    name: str
    file_extensions: list[str]
    comment_single: str
    comment_multi_start: str
    comment_multi_end: str
    string_delimiters: list[str]
    package_manager: str | None
    package_file: str | None
    test_framework: str
    test_file_pattern: str
    lint_tool: str | None
    format_tool: str | None
    compile_command: str | None
    run_command: str
    docker_image: str
    complexity_weight: float = 1.0


@dataclass
class TestTemplate:
    """Template for generating tests."""
    language: Language
    framework: str
    imports: str
    test_class_template: str
    test_method_template: str
    assertion_template: str
    setup_template: str | None = None
    teardown_template: str | None = None


@dataclass
class LintRule:
    """A lint rule for code quality checking."""
    id: str
    name: str
    description: str
    severity: str  # error, warning, info
    pattern: str  # Regex pattern
    message: str
    fix_suggestion: str | None = None


@dataclass
class GeneratedTest:
    """A generated test file."""
    language: Language
    framework: str
    filename: str
    content: str
    imports: list[str]
    test_count: int


class LanguageService:
    """Service for language-specific operations."""

    def __init__(self):
        """Initialize language configurations."""
        self._configs = self._initialize_configs()
        self._test_templates = self._initialize_test_templates()
        self._lint_rules = self._initialize_lint_rules()

    def _initialize_configs(self) -> dict[Language, LanguageConfig]:
        """Initialize language configurations."""
        return {
            Language.PYTHON: LanguageConfig(
                language=Language.PYTHON,
                name="Python",
                file_extensions=[".py", ".pyw", ".pyi"],
                comment_single="#",
                comment_multi_start='"""',
                comment_multi_end='"""',
                string_delimiters=['"', "'", '"""', "'''"],
                package_manager="pip",
                package_file="requirements.txt",
                test_framework="pytest",
                test_file_pattern="test_*.py",
                lint_tool="flake8",
                format_tool="black",
                compile_command=None,
                run_command="python {file}",
                docker_image="python:3.11-slim",
                complexity_weight=1.0,
            ),
            Language.JAVASCRIPT: LanguageConfig(
                language=Language.JAVASCRIPT,
                name="JavaScript",
                file_extensions=[".js", ".mjs", ".cjs"],
                comment_single="//",
                comment_multi_start="/*",
                comment_multi_end="*/",
                string_delimiters=['"', "'", "`"],
                package_manager="npm",
                package_file="package.json",
                test_framework="jest",
                test_file_pattern="*.test.js",
                lint_tool="eslint",
                format_tool="prettier",
                compile_command=None,
                run_command="node {file}",
                docker_image="node:20-slim",
                complexity_weight=1.0,
            ),
            Language.TYPESCRIPT: LanguageConfig(
                language=Language.TYPESCRIPT,
                name="TypeScript",
                file_extensions=[".ts", ".tsx", ".mts", ".cts"],
                comment_single="//",
                comment_multi_start="/*",
                comment_multi_end="*/",
                string_delimiters=['"', "'", "`"],
                package_manager="npm",
                package_file="package.json",
                test_framework="jest",
                test_file_pattern="*.test.ts",
                lint_tool="eslint",
                format_tool="prettier",
                compile_command="tsc {file}",
                run_command="ts-node {file}",
                docker_image="node:20-slim",
                complexity_weight=1.1,
            ),
            Language.JAVA: LanguageConfig(
                language=Language.JAVA,
                name="Java",
                file_extensions=[".java"],
                comment_single="//",
                comment_multi_start="/*",
                comment_multi_end="*/",
                string_delimiters=['"'],
                package_manager="maven",
                package_file="pom.xml",
                test_framework="junit5",
                test_file_pattern="*Test.java",
                lint_tool="checkstyle",
                format_tool="google-java-format",
                compile_command="javac {file}",
                run_command="java {class}",
                docker_image="eclipse-temurin:17-jdk-jammy",
                complexity_weight=1.2,
            ),
            Language.GO: LanguageConfig(
                language=Language.GO,
                name="Go",
                file_extensions=[".go"],
                comment_single="//",
                comment_multi_start="/*",
                comment_multi_end="*/",
                string_delimiters=['"', "`"],
                package_manager="go",
                package_file="go.mod",
                test_framework="testing",
                test_file_pattern="*_test.go",
                lint_tool="golangci-lint",
                format_tool="gofmt",
                compile_command="go build {file}",
                run_command="go run {file}",
                docker_image="golang:1.21-alpine",
                complexity_weight=1.1,
            ),
            Language.CSHARP: LanguageConfig(
                language=Language.CSHARP,
                name="C#",
                file_extensions=[".cs"],
                comment_single="//",
                comment_multi_start="/*",
                comment_multi_end="*/",
                string_delimiters=['"', '@"'],
                package_manager="nuget",
                package_file="*.csproj",
                test_framework="nunit",
                test_file_pattern="*Tests.cs",
                lint_tool="dotnet-format",
                format_tool="dotnet-format",
                compile_command="dotnet build",
                run_command="dotnet run",
                docker_image="mcr.microsoft.com/dotnet/sdk:8.0",
                complexity_weight=1.2,
            ),
            Language.RUST: LanguageConfig(
                language=Language.RUST,
                name="Rust",
                file_extensions=[".rs"],
                comment_single="//",
                comment_multi_start="/*",
                comment_multi_end="*/",
                string_delimiters=['"'],
                package_manager="cargo",
                package_file="Cargo.toml",
                test_framework="cargo-test",
                test_file_pattern="*_test.rs",
                lint_tool="clippy",
                format_tool="rustfmt",
                compile_command="cargo build",
                run_command="cargo run",
                docker_image="rust:1.74-slim",
                complexity_weight=1.3,
            ),
        }

    def _initialize_test_templates(self) -> dict[Language, TestTemplate]:
        """Initialize test generation templates."""
        return {
            Language.PYTHON: TestTemplate(
                language=Language.PYTHON,
                framework="pytest",
                imports="import pytest\nfrom {module} import {functions}",
                test_class_template="""
class Test{class_name}:
    \"\"\"Test suite for {class_name}.\"\"\"

{test_methods}
""",
                test_method_template="""
    def test_{method_name}(self):
        \"\"\"Test {method_name} function.\"\"\"
{assertions}
""",
                assertion_template="        assert {actual} == {expected}",
                setup_template="""
    @pytest.fixture(autouse=True)
    def setup(self):
        \"\"\"Set up test fixtures.\"\"\"
        {setup_code}
""",
            ),
            Language.JAVASCRIPT: TestTemplate(
                language=Language.JAVASCRIPT,
                framework="jest",
                imports="const {{ {functions} }} = require('./{module}');",
                test_class_template="""
describe('{class_name}', () => {{
{test_methods}
}});
""",
                test_method_template="""
  test('{method_name}', () => {{
{assertions}
  }});
""",
                assertion_template="    expect({actual}).toBe({expected});",
                setup_template="""
  beforeEach(() => {{
    {setup_code}
  }});
""",
            ),
            Language.TYPESCRIPT: TestTemplate(
                language=Language.TYPESCRIPT,
                framework="jest",
                imports="import {{ {functions} }} from './{module}';",
                test_class_template="""
describe('{class_name}', () => {{
{test_methods}
}});
""",
                test_method_template="""
  test('{method_name}', () => {{
{assertions}
  }});
""",
                assertion_template="    expect({actual}).toBe({expected});",
                setup_template="""
  beforeEach(() => {{
    {setup_code}
  }});
""",
            ),
            Language.JAVA: TestTemplate(
                language=Language.JAVA,
                framework="junit5",
                imports="""import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import static org.junit.jupiter.api.Assertions.*;

import {package}.{class_name};""",
                test_class_template="""
@DisplayName("{class_name} Tests")
public class {class_name}Test {{
{setup}
{test_methods}
}}
""",
                test_method_template="""
    @Test
    @DisplayName("{method_name}")
    void test{method_name_pascal}() {{
{assertions}
    }}
""",
                assertion_template="        assertEquals({expected}, {actual});",
                setup_template="""
    private {class_name} instance;

    @BeforeEach
    void setUp() {{
        instance = new {class_name}();
    }}
""",
            ),
            Language.GO: TestTemplate(
                language=Language.GO,
                framework="testing",
                imports="""package {package}

import (
    "testing"
)""",
                test_class_template="""
{test_methods}
""",
                test_method_template="""
func Test{method_name_pascal}(t *testing.T) {{
{assertions}
}}
""",
                assertion_template="""    if {actual} != {expected} {{
        t.Errorf("expected %v, got %v", {expected}, {actual})
    }}""",
                setup_template=None,
            ),
            Language.CSHARP: TestTemplate(
                language=Language.CSHARP,
                framework="nunit",
                imports="""using NUnit.Framework;
using {namespace};""",
                test_class_template="""
namespace {namespace}.Tests
{{
    [TestFixture]
    public class {class_name}Tests
    {{
{setup}
{test_methods}
    }}
}}
""",
                test_method_template="""
        [Test]
        public void {method_name_pascal}_ShouldWork()
        {{
{assertions}
        }}
""",
                assertion_template="            Assert.AreEqual({expected}, {actual});",
                setup_template="""
        private {class_name} _instance;

        [SetUp]
        public void Setup()
        {{
            _instance = new {class_name}();
        }}
""",
            ),
        }

    def _initialize_lint_rules(self) -> dict[Language, list[LintRule]]:
        """Initialize language-specific lint rules."""
        return {
            Language.PYTHON: [
                LintRule(
                    id="PY001",
                    name="unused-import",
                    description="Unused import detected",
                    severity="warning",
                    pattern=r"^import\s+(\w+)|^from\s+(\w+)\s+import",
                    message="Import '{name}' appears to be unused",
                    fix_suggestion="Remove the unused import",
                ),
                LintRule(
                    id="PY002",
                    name="bare-except",
                    description="Bare except clause",
                    severity="warning",
                    pattern=r"except\s*:",
                    message="Avoid bare except clauses, catch specific exceptions",
                    fix_suggestion="Specify exception type: except Exception:",
                ),
                LintRule(
                    id="PY003",
                    name="hardcoded-password",
                    description="Hardcoded password detected",
                    severity="error",
                    pattern=r"(password|passwd|pwd)\s*=\s*['\"][^'\"]+['\"]",
                    message="Hardcoded password detected",
                    fix_suggestion="Use environment variables or config files",
                ),
                LintRule(
                    id="PY004",
                    name="print-statement",
                    description="Print statement in production code",
                    severity="info",
                    pattern=r"\bprint\s*\(",
                    message="Consider using logging instead of print",
                    fix_suggestion="Use logging.info() or logging.debug()",
                ),
            ],
            Language.JAVASCRIPT: [
                LintRule(
                    id="JS001",
                    name="no-var",
                    description="Use of var instead of let/const",
                    severity="warning",
                    pattern=r"\bvar\s+\w+",
                    message="Use 'let' or 'const' instead of 'var'",
                    fix_suggestion="Replace 'var' with 'let' or 'const'",
                ),
                LintRule(
                    id="JS002",
                    name="no-console",
                    description="Console statement in production",
                    severity="warning",
                    pattern=r"console\.(log|warn|error|info)\s*\(",
                    message="Avoid console statements in production code",
                    fix_suggestion="Remove or use proper logging library",
                ),
                LintRule(
                    id="JS003",
                    name="no-eval",
                    description="Use of eval function",
                    severity="error",
                    pattern=r"\beval\s*\(",
                    message="Avoid using eval() - security risk",
                    fix_suggestion="Use safer alternatives like JSON.parse()",
                ),
                LintRule(
                    id="JS004",
                    name="eqeqeq",
                    description="Use of == instead of ===",
                    severity="warning",
                    pattern=r"[^!=]==[^=]",
                    message="Use strict equality (===) instead of ==",
                    fix_suggestion="Replace == with ===",
                ),
            ],
            Language.TYPESCRIPT: [
                LintRule(
                    id="TS001",
                    name="no-any",
                    description="Use of 'any' type",
                    severity="warning",
                    pattern=r":\s*any\b",
                    message="Avoid using 'any' type - use specific types",
                    fix_suggestion="Define proper type or use 'unknown'",
                ),
                LintRule(
                    id="TS002",
                    name="no-non-null-assertion",
                    description="Non-null assertion operator",
                    severity="info",
                    pattern=r"\w+!(?:\.|;|\))",
                    message="Avoid non-null assertion operator (!)",
                    fix_suggestion="Use proper null checking instead",
                ),
            ],
            Language.JAVA: [
                LintRule(
                    id="JV001",
                    name="system-out",
                    description="Use of System.out in production",
                    severity="warning",
                    pattern=r"System\.(out|err)\.(print|println)\s*\(",
                    message="Use proper logging instead of System.out",
                    fix_suggestion="Use Logger.info() or similar",
                ),
                LintRule(
                    id="JV002",
                    name="catch-exception",
                    description="Catching generic Exception",
                    severity="warning",
                    pattern=r"catch\s*\(\s*Exception\s+\w+\s*\)",
                    message="Avoid catching generic Exception",
                    fix_suggestion="Catch specific exception types",
                ),
                LintRule(
                    id="JV003",
                    name="empty-catch",
                    description="Empty catch block",
                    severity="error",
                    pattern=r"catch\s*\([^)]+\)\s*\{\s*\}",
                    message="Empty catch block - exceptions should be handled",
                    fix_suggestion="Handle or log the exception",
                ),
            ],
            Language.GO: [
                LintRule(
                    id="GO001",
                    name="error-not-checked",
                    description="Error return value not checked",
                    severity="error",
                    pattern=r"\w+\s*,\s*_\s*:?=",
                    message="Error value ignored - check errors",
                    fix_suggestion="Handle the error appropriately",
                ),
                LintRule(
                    id="GO002",
                    name="fmt-print",
                    description="Use of fmt.Print in production",
                    severity="warning",
                    pattern=r"fmt\.(Print|Println|Printf)\s*\(",
                    message="Consider using structured logging",
                    fix_suggestion="Use log package or structured logger",
                ),
            ],
            Language.CSHARP: [
                LintRule(
                    id="CS001",
                    name="console-write",
                    description="Use of Console.Write in production",
                    severity="warning",
                    pattern=r"Console\.(Write|WriteLine)\s*\(",
                    message="Use proper logging instead of Console.Write",
                    fix_suggestion="Use ILogger or similar",
                ),
                LintRule(
                    id="CS002",
                    name="catch-exception",
                    description="Catching generic Exception",
                    severity="warning",
                    pattern=r"catch\s*\(\s*Exception\s+\w+?\s*\)",
                    message="Avoid catching generic Exception",
                    fix_suggestion="Catch specific exception types",
                ),
                LintRule(
                    id="CS003",
                    name="async-void",
                    description="Async void method",
                    severity="warning",
                    pattern=r"async\s+void\s+\w+",
                    message="Avoid async void - use async Task",
                    fix_suggestion="Change return type to Task",
                ),
            ],
        }

    def get_config(self, language: Language | str) -> LanguageConfig | None:
        """Get configuration for a language."""
        if isinstance(language, str):
            try:
                language = Language(language.lower())
            except ValueError:
                return None
        return self._configs.get(language)

    def get_all_configs(self) -> list[LanguageConfig]:
        """Get all language configurations."""
        return list(self._configs.values())

    def detect_language(self, code: str, filename: str | None = None) -> Language | None:
        """
        Detect the programming language from code or filename.

        Args:
            code: Source code content
            filename: Optional filename for extension-based detection

        Returns:
            Detected Language or None
        """
        # Try extension-based detection first
        if filename:
            ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
            for config in self._configs.values():
                if ext in config.file_extensions:
                    return config.language

        # Content-based detection
        code_lower = code.lower()

        # Python indicators
        if any(indicator in code for indicator in [
            "def ", "import ", "from ", "class ",
            "if __name__", "print(", "self."
        ]):
            if "def " in code or "import " in code:
                return Language.PYTHON

        # Java indicators
        if any(indicator in code for indicator in [
            "public class ", "public static void main",
            "System.out", "import java."
        ]):
            return Language.JAVA

        # Go indicators
        if any(indicator in code for indicator in [
            "package main", "func main()", "import (",
            "fmt.", ":= "
        ]):
            return Language.GO

        # C# indicators
        if any(indicator in code for indicator in [
            "namespace ", "using System", "public class",
            "static void Main", "Console."
        ]):
            return Language.CSHARP

        # TypeScript indicators (before JS due to overlap)
        if any(indicator in code for indicator in [
            ": string", ": number", ": boolean",
            "interface ", ": void", "<T>"
        ]):
            return Language.TYPESCRIPT

        # JavaScript indicators
        if any(indicator in code for indicator in [
            "const ", "let ", "function ",
            "console.log", "require(", "module.exports"
        ]):
            return Language.JAVASCRIPT

        # Rust indicators
        if any(indicator in code for indicator in [
            "fn main()", "let mut ", "impl ",
            "pub fn ", "use std::", "&str"
        ]):
            return Language.RUST

        return None

    def generate_test(
        self,
        code: str,
        language: Language | str,
        class_name: str = "MyClass",
        method_names: list[str] | None = None
    ) -> GeneratedTest | None:
        """
        Generate test code for the given source code.

        Args:
            code: Source code to test
            language: Programming language
            class_name: Name of the class being tested
            method_names: List of method names to test

        Returns:
            GeneratedTest with test file content
        """
        if isinstance(language, str):
            try:
                language = Language(language.lower())
            except ValueError:
                return None

        template = self._test_templates.get(language)
        if not template:
            return None

        config = self._configs.get(language)
        if not config:
            return None

        # Extract method names if not provided
        if not method_names:
            method_names = self._extract_method_names(code, language)

        if not method_names:
            method_names = ["example"]

        # Generate test methods
        test_methods = []
        for method in method_names:
            method_pascal = self._to_pascal_case(method)
            test_method = template.test_method_template.format(
                method_name=method,
                method_name_pascal=method_pascal,
                assertions="        # TODO: Add assertions",
            )
            test_methods.append(test_method)

        # Generate setup if available
        setup_code = ""
        if template.setup_template:
            setup_code = template.setup_template.format(
                class_name=class_name,
                setup_code="pass" if language == Language.PYTHON else "",
            )

        # Generate test class
        test_content = template.test_class_template.format(
            class_name=class_name,
            test_methods="\n".join(test_methods),
            setup=setup_code,
        )

        # Generate imports
        imports = template.imports.format(
            module=class_name.lower(),
            functions=", ".join(method_names),
            package=class_name.lower(),
            namespace=class_name,
            class_name=class_name,
        )

        # Combine into final content
        final_content = f"{imports}\n{test_content}"

        # Determine filename
        if language == Language.PYTHON:
            filename = f"test_{class_name.lower()}.py"
        elif language in [Language.JAVASCRIPT, Language.TYPESCRIPT]:
            ext = ".test.ts" if language == Language.TYPESCRIPT else ".test.js"
            filename = f"{class_name.lower()}{ext}"
        elif language == Language.JAVA:
            filename = f"{class_name}Test.java"
        elif language == Language.GO:
            filename = f"{class_name.lower()}_test.go"
        elif language == Language.CSHARP:
            filename = f"{class_name}Tests.cs"
        else:
            filename = f"test_{class_name.lower()}"

        return GeneratedTest(
            language=language,
            framework=template.framework,
            filename=filename,
            content=final_content,
            imports=[imports],
            test_count=len(method_names),
        )

    def _extract_method_names(self, code: str, language: Language) -> list[str]:
        """Extract method/function names from code."""
        methods = []

        patterns = {
            Language.PYTHON: r"def\s+(\w+)\s*\(",
            Language.JAVASCRIPT: r"(?:function\s+(\w+)|(\w+)\s*=\s*(?:async\s+)?function|(\w+)\s*:\s*(?:async\s+)?function)",
            Language.TYPESCRIPT: r"(?:function\s+(\w+)|(\w+)\s*=\s*(?:async\s+)?function|(\w+)\s*\([^)]*\)\s*:\s*\w+)",
            Language.JAVA: r"(?:public|private|protected)\s+(?:static\s+)?\w+\s+(\w+)\s*\(",
            Language.GO: r"func\s+(?:\([^)]+\)\s+)?(\w+)\s*\(",
            Language.CSHARP: r"(?:public|private|protected|internal)\s+(?:static\s+)?(?:async\s+)?\w+\s+(\w+)\s*\(",
        }

        pattern = patterns.get(language)
        if pattern:
            matches = re.findall(pattern, code)
            for match in matches:
                if isinstance(match, tuple):
                    # Take first non-empty group
                    name = next((m for m in match if m), None)
                else:
                    name = match
                if name and not name.startswith("_") and name not in ["main", "Main"]:
                    methods.append(name)

        return methods[:10]  # Limit to 10 methods

    def _to_pascal_case(self, name: str) -> str:
        """Convert string to PascalCase."""
        words = re.split(r"[_\s-]", name)
        return "".join(word.capitalize() for word in words)

    def lint_code(
        self,
        code: str,
        language: Language | str
    ) -> list[dict]:
        """
        Run lint rules on code and return issues.

        Args:
            code: Source code to lint
            language: Programming language

        Returns:
            List of lint issues with severity, message, line, etc.
        """
        if isinstance(language, str):
            try:
                language = Language(language.lower())
            except ValueError:
                return []

        rules = self._lint_rules.get(language, [])
        issues = []
        lines = code.split("\n")

        for rule in rules:
            for line_num, line in enumerate(lines, 1):
                if re.search(rule.pattern, line, re.IGNORECASE):
                    issues.append({
                        "rule_id": rule.id,
                        "rule_name": rule.name,
                        "severity": rule.severity,
                        "message": rule.message,
                        "line": line_num,
                        "column": 1,
                        "fix_suggestion": rule.fix_suggestion,
                        "source": line.strip(),
                    })

        return issues

    def get_lint_rules(self, language: Language | str) -> list[LintRule]:
        """Get lint rules for a language."""
        if isinstance(language, str):
            try:
                language = Language(language.lower())
            except ValueError:
                return []
        return self._lint_rules.get(language, [])

    def calculate_complexity(
        self,
        code: str,
        language: Language | str
    ) -> dict[str, Any]:
        """
        Calculate code complexity metrics.

        Args:
            code: Source code to analyze
            language: Programming language

        Returns:
            Dictionary with complexity metrics
        """
        if isinstance(language, str):
            try:
                language = Language(language.lower())
            except ValueError:
                return {"error": "Unknown language"}

        config = self._configs.get(language)
        if not config:
            return {"error": "Unsupported language"}

        lines = code.split("\n")
        total_lines = len(lines)
        code_lines = sum(1 for line in lines if line.strip() and not self._is_comment(line, language))

        # Count control flow statements for cyclomatic complexity
        control_patterns = {
            Language.PYTHON: r"\b(if|elif|else|for|while|try|except|finally|with|and|or)\b",
            Language.JAVASCRIPT: r"\b(if|else|for|while|do|switch|case|try|catch|finally|\?\?|&&|\|\|)\b",
            Language.TYPESCRIPT: r"\b(if|else|for|while|do|switch|case|try|catch|finally|\?\?|&&|\|\|)\b",
            Language.JAVA: r"\b(if|else|for|while|do|switch|case|try|catch|finally|&&|\|\|)\b",
            Language.GO: r"\b(if|else|for|switch|case|select|defer|go)\b",
            Language.CSHARP: r"\b(if|else|for|foreach|while|do|switch|case|try|catch|finally|&&|\|\|)\b",
        }

        control_pattern = control_patterns.get(language, r"\b(if|else|for|while)\b")
        control_matches = re.findall(control_pattern, code)
        cyclomatic = len(control_matches) + 1

        # Count functions/methods
        function_patterns = {
            Language.PYTHON: r"def\s+\w+\s*\(",
            Language.JAVASCRIPT: r"function\s+\w+\s*\(|(\w+)\s*=\s*(?:async\s+)?function",
            Language.TYPESCRIPT: r"function\s+\w+\s*\(|(\w+)\s*=\s*(?:async\s+)?function",
            Language.JAVA: r"(?:public|private|protected)\s+(?:static\s+)?\w+\s+\w+\s*\(",
            Language.GO: r"func\s+",
            Language.CSHARP: r"(?:public|private|protected|internal)\s+(?:static\s+)?(?:async\s+)?\w+\s+\w+\s*\(",
        }

        func_pattern = function_patterns.get(language, r"function\s+\w+\s*\(")
        function_count = len(re.findall(func_pattern, code))

        # Count classes
        class_patterns = {
            Language.PYTHON: r"class\s+\w+",
            Language.JAVASCRIPT: r"class\s+\w+",
            Language.TYPESCRIPT: r"class\s+\w+|interface\s+\w+",
            Language.JAVA: r"(?:public\s+)?class\s+\w+|interface\s+\w+",
            Language.GO: r"type\s+\w+\s+struct",
            Language.CSHARP: r"(?:public\s+)?(?:class|interface|struct)\s+\w+",
        }

        class_pattern = class_patterns.get(language, r"class\s+\w+")
        class_count = len(re.findall(class_pattern, code))

        # Calculate nesting depth
        max_nesting = self._calculate_nesting_depth(code, language)

        # Apply language weight
        weighted_complexity = cyclomatic * config.complexity_weight

        return {
            "total_lines": total_lines,
            "code_lines": code_lines,
            "comment_lines": total_lines - code_lines,
            "function_count": function_count,
            "class_count": class_count,
            "cyclomatic_complexity": cyclomatic,
            "weighted_complexity": round(weighted_complexity, 2),
            "max_nesting_depth": max_nesting,
            "language": language.value,
            "complexity_weight": config.complexity_weight,
        }

    def _is_comment(self, line: str, language: Language) -> bool:
        """Check if a line is a comment."""
        stripped = line.strip()
        config = self._configs.get(language)
        if not config:
            return False

        if stripped.startswith(config.comment_single):
            return True
        if stripped.startswith(config.comment_multi_start):
            return True

        return False

    def _calculate_nesting_depth(self, code: str, language: Language) -> int:
        """Calculate maximum nesting depth."""
        max_depth = 0
        current_depth = 0

        # Simple brace/indent counting
        if language == Language.PYTHON:
            # Python uses indentation
            lines = code.split("\n")
            for line in lines:
                if line.strip():
                    indent = len(line) - len(line.lstrip())
                    depth = indent // 4  # Assume 4-space indentation
                    max_depth = max(max_depth, depth)
        else:
            # Count braces for C-style languages
            for char in code:
                if char == "{":
                    current_depth += 1
                    max_depth = max(max_depth, current_depth)
                elif char == "}":
                    current_depth = max(0, current_depth - 1)

        return max_depth


# Singleton instance
_language_service: LanguageService | None = None


def get_language_service() -> LanguageService:
    """Get or create the language service singleton."""
    global _language_service
    if _language_service is None:
        _language_service = LanguageService()
    return _language_service
