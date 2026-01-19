"""
Enhanced Code Generator Agent for the Intelligent Coding Agent.

This agent generates code based on natural language prompts,
supporting multiple languages and integrating with the LLM router
for cost-effective generation.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

import structlog

from src.agents.base_agent import BaseAgent
from src.agents.state import AgentState, AgentType, set_error
from src.core.llm_client import LLMClient
from src.core.llm_router import LLMRouter, RouterResult, get_llm_router

logger = structlog.get_logger(__name__)


class SupportedLanguage(str, Enum):
    """Supported programming languages."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    GO = "go"
    CSHARP = "csharp"
    RUST = "rust"
    SQL = "sql"


@dataclass
class GeneratedCode:
    """Result of code generation."""
    code: str
    language: str
    filename: str
    description: str
    dependencies: list[str]
    entry_point: Optional[str] = None


@dataclass
class CodeGenerationResult:
    """Complete result of code generation request."""
    files: list[GeneratedCode]
    main_file: str
    language: str
    complexity_score: int
    llm_provider: str
    llm_model: str


class EnhancedCodeGenerator(BaseAgent):
    """
    Enhanced code generator that produces production-ready code.

    Features:
    - Multi-language support (Python, JS, TS, Java, Go, C#)
    - LLM router integration for cost optimization
    - Structured output with multiple files if needed
    - Dependency detection
    - Best practices enforcement
    """

    # System prompt for code generation
    CODE_GENERATION_SYSTEM_PROMPT = """You are an expert software engineer who writes clean, production-ready code.

Guidelines:
1. Write clean, well-documented code following best practices
2. Include proper error handling
3. Use type hints/annotations where applicable
4. Follow the language's standard style guide
5. Include necessary imports
6. Make the code modular and testable
7. Add docstrings/comments explaining complex logic

Output Format:
- Return ONLY the code, no explanations
- If multiple files are needed, separate them with:
  --- FILE: filename.ext ---
- Always include a main entry point when appropriate
"""

    # Language-specific prompts
    LANGUAGE_PROMPTS = {
        "python": """Write Python code following PEP 8 style guide.
Use type hints for function parameters and return values.
Use docstrings for functions and classes.
Prefer pathlib for file operations.
Use dataclasses or Pydantic for data structures.""",

        "javascript": """Write modern JavaScript (ES6+).
Use const/let, not var.
Use arrow functions where appropriate.
Include JSDoc comments for documentation.""",

        "typescript": """Write TypeScript with strict type checking.
Define interfaces/types for all data structures.
Use async/await for asynchronous code.
Include proper type annotations.""",

        "java": """Write Java 17+ code.
Follow standard Java naming conventions.
Include JavaDoc comments.
Use modern features like records where appropriate.""",

        "go": """Write idiomatic Go code.
Follow effective Go guidelines.
Handle errors explicitly.
Use proper package structure.""",

        "csharp": """Write C# 10+ code.
Use nullable reference types.
Follow .NET naming conventions.
Include XML documentation comments.""",
    }

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        router: Optional[LLMRouter] = None,
    ):
        """
        Initialize the enhanced code generator.

        Args:
            llm_client: Optional LLM client (will use router if not provided)
            router: LLM router for cost-optimized generation
        """
        super().__init__()
        self._llm_client = llm_client
        self._router = router or get_llm_router()

    @property
    def name(self) -> str:
        """Return the agent name."""
        return "enhanced_code_generator"

    @property
    def agent_type(self) -> AgentType:
        """Return the agent type."""
        return AgentType.CODE_GENERATOR

    @property
    def description(self) -> str:
        """Return the agent description."""
        return "Generates production-ready code from natural language prompts"

    def process(self, state: AgentState) -> AgentState:
        """
        Generate code based on the query in state.

        Args:
            state: Current agent state with query

        Returns:
            Updated state with generated code
        """
        query = state.get("query", "")
        context_docs = state.get("retrieved_documents", [])

        if not query:
            return set_error(
                state,
                agent=self.name,
                error_type="missing_input",
                message="No query provided for code generation",
                recoverable=False,
            )

        try:
            # Generate code
            result = self.generate(
                prompt=query,
                context=self._format_context(context_docs),
            )

            # Update state with results
            code_snippets = []
            for file in result.files:
                code_snippets.append({
                    "language": file.language,
                    "code": file.code,
                    "filename": file.filename,
                    "description": file.description,
                    "dependencies": file.dependencies,
                })

            updated_state = {
                **state,
                "code_snippets": code_snippets,
                "generated_code": result.files[0].code if result.files else "",
                "code_language": result.language,
                "complexity_score": result.complexity_score,
                "llm_provider": result.llm_provider,
                "llm_model": result.llm_model,
                "response": f"Generated {result.language} code ({len(result.files)} file(s))",
            }

            self._logger.info(
                "code_generation_complete",
                language=result.language,
                files=len(result.files),
                complexity=result.complexity_score,
                provider=result.llm_provider,
            )

            return updated_state

        except Exception as e:
            self._logger.error("code_generation_failed", error=str(e))
            return set_error(
                state,
                agent=self.name,
                error_type="generation_error",
                message=f"Failed to generate code: {str(e)}",
                recoverable=True,
            )

    def generate(
        self,
        prompt: str,
        language: Optional[str] = None,
        context: Optional[str] = None,
        preference: Optional[str] = None,
    ) -> CodeGenerationResult:
        """
        Generate code from a natural language prompt.

        Args:
            prompt: Natural language description of what to generate
            language: Target language (auto-detected if not provided)
            context: Additional context (e.g., existing code, docs)
            preference: LLM preference ("fast", "balanced", "quality")

        Returns:
            CodeGenerationResult with generated files
        """
        # Route to appropriate LLM
        route_result = self._router.route(prompt, preference=preference)

        # Detect language if not specified
        detected_language = language or self._detect_language(prompt)

        self._logger.info(
            "generating_code",
            language=detected_language,
            complexity=route_result.complexity.score,
            provider=route_result.provider,
            model=route_result.model,
        )

        # Get LLM client
        if self._llm_client:
            client = self._llm_client
        else:
            client = self._router.get_client(route_result)

        # Build the generation prompt
        full_prompt = self._build_prompt(prompt, detected_language, context)

        # Generate code
        response = client.generate(
            prompt=full_prompt,
            system_prompt=self.CODE_GENERATION_SYSTEM_PROMPT,
            temperature=0.3,  # Lower temperature for code
            max_tokens=4096,
        )

        # Parse the response
        files = self._parse_response(response, detected_language)

        # Extract dependencies
        for file in files:
            file.dependencies = self._extract_dependencies(file.code, file.language)

        return CodeGenerationResult(
            files=files,
            main_file=files[0].filename if files else "",
            language=detected_language,
            complexity_score=route_result.complexity.score,
            llm_provider=route_result.provider,
            llm_model=route_result.model,
        )

    def regenerate_with_feedback(
        self,
        original_code: str,
        error_message: str,
        language: str,
        attempt: int = 1,
    ) -> GeneratedCode:
        """
        Regenerate code based on error feedback.

        Args:
            original_code: The code that failed
            error_message: Error message from execution/validation
            language: Programming language
            attempt: Current attempt number

        Returns:
            GeneratedCode with fixed code
        """
        fix_prompt = f"""The following {language} code has an error. Please fix it.

ORIGINAL CODE:
```{language}
{original_code}
```

ERROR:
{error_message}

INSTRUCTIONS:
1. Analyze the error carefully
2. Fix ONLY what's necessary to resolve the error
3. Preserve the original functionality
4. Return the complete fixed code

Return ONLY the fixed code, no explanations:"""

        # Use quality preference for fixes
        route_result = self._router.route(fix_prompt, preference="quality")
        client = self._router.get_client(route_result)

        response = client.generate(
            prompt=fix_prompt,
            system_prompt="You are a debugging expert. Fix the code while preserving functionality.",
            temperature=0.2,
            max_tokens=4096,
        )

        # Clean up response
        fixed_code = self._clean_code_response(response, language)

        self._logger.info(
            "code_regenerated",
            attempt=attempt,
            language=language,
            provider=route_result.provider,
        )

        return GeneratedCode(
            code=fixed_code,
            language=language,
            filename=self._generate_filename(language),
            description=f"Fixed code (attempt {attempt})",
            dependencies=self._extract_dependencies(fixed_code, language),
        )

    def _detect_language(self, prompt: str) -> str:
        """Detect target programming language from prompt."""
        prompt_lower = prompt.lower()

        language_keywords = {
            "python": ["python", "py", "django", "flask", "fastapi"],
            "javascript": ["javascript", "js", "node", "react", "vue", "express"],
            "typescript": ["typescript", "ts", "angular", "next.js", "nest"],
            "java": ["java", "spring", "maven", "gradle"],
            "go": ["golang", "go "],
            "csharp": ["c#", "csharp", ".net", "asp.net"],
            "rust": ["rust", "cargo"],
            "sql": ["sql", "query", "database query"],
        }

        for lang, keywords in language_keywords.items():
            for keyword in keywords:
                if keyword in prompt_lower:
                    return lang

        # Default to Python
        return "python"

    def _build_prompt(
        self,
        user_prompt: str,
        language: str,
        context: Optional[str] = None,
    ) -> str:
        """Build the complete generation prompt."""
        parts = []

        # Language-specific instructions
        if language in self.LANGUAGE_PROMPTS:
            parts.append(self.LANGUAGE_PROMPTS[language])
            parts.append("")

        # Context if provided
        if context:
            parts.append("CONTEXT:")
            parts.append(context)
            parts.append("")

        # User request
        parts.append("REQUEST:")
        parts.append(user_prompt)
        parts.append("")
        parts.append(f"Generate {language} code that fulfills the above request:")

        return "\n".join(parts)

    def _parse_response(self, response: str, language: str) -> list[GeneratedCode]:
        """Parse LLM response into structured code files."""
        files = []

        # Clean up response
        response = response.strip()

        # Check for multiple files
        if "--- FILE:" in response:
            # Multi-file response
            file_sections = re.split(r'---\s*FILE:\s*', response)
            for section in file_sections:
                if not section.strip():
                    continue

                # Extract filename and code
                lines = section.strip().split("\n")
                if lines:
                    filename_line = lines[0].strip().rstrip("---").strip()
                    code = "\n".join(lines[1:])
                    code = self._clean_code_response(code, language)

                    if code:
                        files.append(GeneratedCode(
                            code=code,
                            language=language,
                            filename=filename_line,
                            description=f"Generated {filename_line}",
                            dependencies=[],
                        ))
        else:
            # Single file response
            code = self._clean_code_response(response, language)
            if code:
                files.append(GeneratedCode(
                    code=code,
                    language=language,
                    filename=self._generate_filename(language),
                    description="Generated code",
                    dependencies=[],
                ))

        return files

    def _clean_code_response(self, response: str, language: str) -> str:
        """Clean up code response from LLM."""
        code = response.strip()

        # Remove markdown code blocks
        if code.startswith("```"):
            lines = code.split("\n")
            # Remove first line (```language)
            if lines[0].startswith("```"):
                lines = lines[1:]
            # Remove last line if it's closing ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            code = "\n".join(lines)

        return code.strip()

    def _generate_filename(self, language: str) -> str:
        """Generate default filename for language."""
        extensions = {
            "python": "main.py",
            "javascript": "index.js",
            "typescript": "index.ts",
            "java": "Main.java",
            "go": "main.go",
            "csharp": "Program.cs",
            "rust": "main.rs",
            "sql": "query.sql",
        }
        return extensions.get(language, f"code.{language}")

    def _extract_dependencies(self, code: str, language: str) -> list[str]:
        """Extract dependencies from code."""
        dependencies = []

        if language == "python":
            # Extract imports
            import_pattern = r'^(?:from\s+(\w+)|import\s+(\w+))'
            for match in re.finditer(import_pattern, code, re.MULTILINE):
                pkg = match.group(1) or match.group(2)
                if pkg and pkg not in ["os", "sys", "json", "re", "typing", "dataclasses", "pathlib", "datetime", "collections", "functools", "itertools"]:
                    if pkg not in dependencies:
                        dependencies.append(pkg)

        elif language in ["javascript", "typescript"]:
            # Extract requires/imports
            require_pattern = r'require\([\'"](.+?)[\'"]\)'
            import_pattern = r'from\s+[\'"](.+?)[\'"]'
            for pattern in [require_pattern, import_pattern]:
                for match in re.finditer(pattern, code):
                    pkg = match.group(1)
                    if not pkg.startswith(".") and not pkg.startswith("/"):
                        base_pkg = pkg.split("/")[0]
                        if base_pkg not in dependencies:
                            dependencies.append(base_pkg)

        elif language == "java":
            # Extract imports
            import_pattern = r'^import\s+([\w.]+);'
            for match in re.finditer(import_pattern, code, re.MULTILINE):
                pkg = match.group(1).split(".")[0]
                if pkg not in ["java", "javax"] and pkg not in dependencies:
                    dependencies.append(pkg)

        elif language == "go":
            # Extract imports
            import_pattern = r'"(.+?)"'
            in_import = False
            for line in code.split("\n"):
                if "import" in line:
                    in_import = True
                if in_import:
                    for match in re.finditer(import_pattern, line):
                        pkg = match.group(1)
                        if not pkg.startswith("fmt") and not pkg.startswith("os"):
                            dependencies.append(pkg)
                    if ")" in line or ('"' in line and "import" in line):
                        in_import = False

        return dependencies

    def _format_context(self, docs: list[dict]) -> Optional[str]:
        """Format retrieved documents as context."""
        if not docs:
            return None

        context_parts = []
        for doc in docs[:3]:  # Use top 3 documents
            content = doc.get("content", "")
            if content:
                context_parts.append(content)

        return "\n\n".join(context_parts) if context_parts else None


# Convenience function
def create_code_generator() -> EnhancedCodeGenerator:
    """Create a new enhanced code generator instance."""
    return EnhancedCodeGenerator()
