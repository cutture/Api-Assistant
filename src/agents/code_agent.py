"""
Code Generator Agent for creating API integration code.

This agent generates production-ready Python code for calling API endpoints
using various HTTP client libraries (requests, httpx, aiohttp).
"""

import ast
import re
from pathlib import Path
from typing import Any, Optional

import structlog
from jinja2 import Environment, FileSystemLoader, Template

from src.agents.base_agent import BaseAgent
from src.agents.state import (
    AgentState,
    AgentType,
    IntentAnalysis,
    RetrievedDocument,
    add_to_processing_path,
    set_error,
)
from src.core.llm_client import LLMClient

logger = structlog.get_logger(__name__)


class CodeLibrary:
    """Supported Python HTTP client libraries."""

    REQUESTS = "requests"
    HTTPX = "httpx"
    AIOHTTP = "aiohttp"


class CodeGenerator(BaseAgent):
    """
    Agent that generates API integration code from templates.

    This agent:
    - Extracts endpoint information from retrieved documents
    - Selects appropriate code template based on HTTP method and library
    - Injects parameters, authentication, and examples
    - Generates clean, production-ready code

    Supported Libraries:
        - requests: Synchronous HTTP library (most common)
        - httpx: Modern async HTTP library
        - aiohttp: Async HTTP library

    Example:
        ```python
        code_gen = CodeGenerator()
        state = create_initial_state("Generate code for POST /users")
        state["retrieved_documents"] = [...]  # From RAG agent
        result = code_gen(state)

        # Access generated code
        code_snippets = result["code_snippets"]
        print(code_snippets[0]["code"])
        ```
    """

    # System prompt for extracting endpoint details
    ENDPOINT_EXTRACTION_PROMPT = """Extract the API endpoint details from the provided context.

Context:
{context}

User Request:
{query}

Extract and return ONLY valid JSON with this exact structure:
{{
  "endpoint": "/path/to/endpoint",
  "method": "GET or POST or PUT or DELETE or PATCH",
  "description": "What this endpoint does",
  "operation_id": "operationId if available",
  "path_params": [
    {{"name": "param_name", "type": "string", "description": "what it is", "example": "'example_value'"}}
  ],
  "query_params": [
    {{"name": "param_name", "type": "string", "required": true, "description": "what it is", "default": "null", "example": "'example_value'"}}
  ],
  "request_body": {{
    "required": true,
    "example": {{"key": "value"}}
  }},
  "auth_type": "none or bearer or api_key",
  "auth_details": {{
    "header_name": "Authorization or X-API-Key"
  }}
}}

Notes:
- For path_params, type can be: "string", "integer", "number", "boolean"
- For query_params, include all optional and required parameters
- Examples should be valid Python literals with quotes if strings
- Set auth_type based on what you find in the context
- If no auth mentioned, use "none"

Respond ONLY with valid JSON, no other text:"""

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        default_library: str = CodeLibrary.REQUESTS,
        base_url: str = "https://api.example.com",
        validate_syntax: bool = True,
        add_retry: bool = False,
    ):
        """
        Initialize the Code Generator agent.

        Args:
            llm_client: LLM client for extracting endpoint details.
            default_library: Default HTTP library to use.
            base_url: Default API base URL.
            validate_syntax: Whether to validate generated code syntax.
            add_retry: Whether to add retry logic to generated code.
        """
        super().__init__()
        self._llm_client = llm_client or LLMClient()
        self.default_library = default_library
        self.base_url = base_url
        self.validate_syntax = validate_syntax
        self.add_retry = add_retry

        # Initialize Jinja2 environment
        template_dir = Path(__file__).parent / "templates"
        self._jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    @property
    def name(self) -> str:
        """Return the agent name."""
        return "code_generator"

    @property
    def agent_type(self) -> AgentType:
        """Return the agent type."""
        return AgentType.CODE_GENERATOR

    @property
    def description(self) -> str:
        """Return the agent description."""
        return "Generates production-ready Python code for API integration"

    def process(self, state: AgentState) -> AgentState:
        """
        Generate code for the requested endpoint.

        Args:
            state: Current agent state with query and retrieved_documents.

        Returns:
            Updated state with code_snippets populated.
        """
        query = state.get("query", "")
        retrieved_docs = state.get("retrieved_documents", [])

        if not query:
            self._logger.warning("No query provided to code generator")
            return set_error(
                state,
                agent=self.name,
                error_type="missing_input",
                message="No query provided for code generation",
                recoverable=False,
            )

        if not retrieved_docs:
            self._logger.warning("No retrieved documents for code generation")
            return set_error(
                state,
                agent=self.name,
                error_type="missing_context",
                message="No API documentation found. Cannot generate code without endpoint information.",
                recoverable=False,
            )

        self._logger.info("Generating code", query=query[:100])

        try:
            # Step 1: Extract endpoint details from context
            endpoint_details = self._extract_endpoint_details(query, retrieved_docs)

            # Step 2: Determine requested language(s) from query
            requested_languages = self._detect_requested_languages(query)

            # Step 3: Generate code for each requested language
            code_snippets = []
            for language in requested_languages:
                if language == "python":
                    # Use template-based generation for Python
                    library = self._determine_library(query)
                    code = self._generate_code(endpoint_details, library)

                    # Validate and enhance code
                    if self.validate_syntax:
                        validation_result = self._validate_code(code)
                        if not validation_result["valid"]:
                            self._logger.warning(
                                "Generated code has syntax errors",
                                errors=validation_result["errors"]
                            )

                    # Optionally add retry logic
                    if self.add_retry:
                        code = self._add_retry_decorator(code, endpoint_details.get("method", "GET"))

                    # Format code
                    code = self._format_code(code)

                    code_snippets.append({
                        "language": "python",
                        "library": library,
                        "code": code,
                        "endpoint": endpoint_details.get("endpoint", ""),
                        "method": endpoint_details.get("method", "GET"),
                        "description": endpoint_details.get("description", ""),
                    })
                else:
                    # Use LLM-based generation for other languages (JavaScript, etc.)
                    code = self._generate_code_llm(endpoint_details, language, query)

                    code_snippets.append({
                        "language": language,
                        "library": self._get_default_library_for_language(language),
                        "code": code,
                        "endpoint": endpoint_details.get("endpoint", ""),
                        "method": endpoint_details.get("method", "GET"),
                        "description": endpoint_details.get("description", ""),
                    })

            # Create response message
            languages_str = ", ".join([lang.title() for lang in requested_languages])
            response_msg = f"Generated code in {languages_str} for {endpoint_details.get('method')} {endpoint_details.get('endpoint')}"

            # Update state
            updated_state = {
                **state,
                "code_snippets": code_snippets,
                "response": response_msg,
            }

            self._logger.info(
                "Code generation complete",
                endpoint=endpoint_details.get("endpoint"),
                method=endpoint_details.get("method"),
                library=library,
            )

            return updated_state

        except Exception as e:
            self._logger.error("Code generation failed", error=str(e))
            return set_error(
                state,
                agent=self.name,
                error_type="generation_error",
                message=f"Failed to generate code: {str(e)}",
                recoverable=True,
            )

    def _extract_endpoint_details(
        self,
        query: str,
        retrieved_docs: list[dict],
    ) -> dict[str, Any]:
        """
        Extract endpoint details from retrieved documents using LLM.

        Args:
            query: User's query.
            retrieved_docs: Retrieved documents from RAG agent.

        Returns:
            Dictionary with endpoint details.
        """
        # Format context from retrieved documents
        context_parts = []
        for i, doc_dict in enumerate(retrieved_docs, 1):
            doc = RetrievedDocument(**doc_dict)
            context_parts.append(f"[Source {i}]\n{doc.content}")

        context = "\n\n".join(context_parts[:3])  # Use top 3 documents

        # Ask LLM to extract details
        prompt = self.ENDPOINT_EXTRACTION_PROMPT.format(
            context=context,
            query=query,
        )

        response = self._llm_client.generate(
            prompt=prompt,
            temperature=0.2,  # Low temperature for structured output
            max_tokens=1000,
        )

        # Parse JSON response
        import json
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if not json_match:
            raise ValueError("LLM did not return valid JSON")

        endpoint_details = json.loads(json_match.group())
        self._logger.debug("Extracted endpoint details", details=endpoint_details)

        return endpoint_details

    def _determine_library(self, query: str) -> str:
        """
        Determine which HTTP library to use based on query.

        Args:
            query: User's query.

        Returns:
            Library name (requests, httpx, or aiohttp).
        """
        query_lower = query.lower()

        if "httpx" in query_lower or "async" in query_lower:
            return CodeLibrary.HTTPX
        elif "aiohttp" in query_lower:
            return CodeLibrary.AIOHTTP
        else:
            return CodeLibrary.REQUESTS  # Default

    def _generate_code(
        self,
        endpoint_details: dict[str, Any],
        library: str,
    ) -> str:
        """
        Generate code using Jinja2 template.

        Args:
            endpoint_details: Extracted endpoint information.
            library: HTTP library to use.

        Returns:
            Generated code string.
        """
        method = endpoint_details.get("method", "GET").upper()

        # Select template based on method and library
        template_name = self._select_template(method, library)

        # Prepare template variables
        template_vars = self._prepare_template_vars(endpoint_details)

        # Load and render template
        template = self._jinja_env.get_template(template_name)
        code = template.render(**template_vars)

        return code

    def _select_template(self, method: str, library: str) -> str:
        """
        Select appropriate template file.

        Args:
            method: HTTP method (GET, POST, etc.).
            library: HTTP library name.

        Returns:
            Template filename.
        """
        if library == CodeLibrary.HTTPX:
            return "python/httpx_async.py.jinja2"
        elif library == CodeLibrary.REQUESTS:
            if method in ["POST", "PUT", "PATCH"]:
                return "python/requests_post.py.jinja2"
            else:
                return "python/requests_get.py.jinja2"
        else:
            # Default to requests
            return "python/requests_get.py.jinja2"

    def _prepare_template_vars(self, endpoint_details: dict[str, Any]) -> dict[str, Any]:
        """
        Prepare variables for template rendering.

        Args:
            endpoint_details: Extracted endpoint information.

        Returns:
            Dictionary of template variables.
        """
        endpoint = endpoint_details.get("endpoint", "/")
        method = endpoint_details.get("method", "GET").upper()
        description = endpoint_details.get("description", "API endpoint call")

        # Generate function name from endpoint and method
        function_name = self._generate_function_name(endpoint, method)

        # Prepare path parameters
        path_params = []
        for param in endpoint_details.get("path_params", []):
            path_params.append({
                "name": param["name"],
                "python_type": self._map_type_to_python(param.get("type", "string")),
                "description": param.get("description", ""),
                "example": param.get("example", "'value'"),
            })

        # Prepare query parameters
        query_params = []
        for param in endpoint_details.get("query_params", []):
            query_params.append({
                "name": param["name"],
                "python_type": self._map_type_to_python(param.get("type", "string")),
                "description": param.get("description", ""),
                "required": param.get("required", False),
                "default": param.get("default", "None"),
                "example": param.get("example", "'value'"),
            })

        # Build endpoint template (for path params)
        endpoint_template = endpoint
        for param in path_params:
            endpoint_template = endpoint_template.replace(
                f"{{{param['name']}}}",
                f"{{{param['name']}}}"  # Keep for f-string
            )

        # Authentication details
        auth_type = endpoint_details.get("auth_type", "none")
        auth_details = endpoint_details.get("auth_details", {})
        api_key_header = auth_details.get("header_name", "X-API-Key")

        # Request body example
        request_body = endpoint_details.get("request_body", {})
        request_body_example = request_body.get("example", {})

        return {
            "endpoint": endpoint,
            "endpoint_template": endpoint_template,
            "method": method,
            "function_name": function_name,
            "description": description,
            "operation_description": description,
            "base_url": self.base_url,
            "path_params": path_params,
            "query_params": query_params,
            "auth_type": auth_type,
            "api_key_header": api_key_header,
            "request_body_example": request_body_example,
        }

    def _generate_function_name(self, endpoint: str, method: str) -> str:
        """
        Generate a valid Python function name from endpoint and method.

        Args:
            endpoint: API endpoint path.
            method: HTTP method.

        Returns:
            Valid Python function name.
        """
        # Remove leading slash and replace slashes with underscores
        name_parts = endpoint.strip("/").replace("/", "_").replace("-", "_")

        # Remove path parameter braces
        name_parts = re.sub(r'\{|\}', '', name_parts)

        # Add method prefix
        method_lower = method.lower()
        if name_parts:
            function_name = f"{method_lower}_{name_parts}"
        else:
            function_name = method_lower

        # Ensure valid Python identifier
        function_name = re.sub(r'[^\w]', '_', function_name)

        return function_name

    def _map_type_to_python(self, api_type: str) -> str:
        """
        Map API parameter type to Python type hint.

        Args:
            api_type: API parameter type (string, integer, etc.).

        Returns:
            Python type hint string.
        """
        type_mapping = {
            "string": "str",
            "integer": "int",
            "number": "float",
            "boolean": "bool",
            "array": "list",
            "object": "dict",
        }

        return type_mapping.get(api_type.lower(), "str")

    def _validate_code(self, code: str) -> dict[str, Any]:
        """
        Validate Python code syntax using ast.parse().

        Args:
            code: Python code string to validate.

        Returns:
            Dictionary with 'valid' bool and 'errors' list.
        """
        try:
            ast.parse(code)
            self._logger.debug("Code validation passed")
            return {"valid": True, "errors": []}
        except SyntaxError as e:
            error_msg = f"Line {e.lineno}: {e.msg}"
            self._logger.warning("Code syntax validation failed", error=error_msg)
            return {"valid": False, "errors": [error_msg]}
        except Exception as e:
            error_msg = f"Validation error: {str(e)}"
            self._logger.warning("Code validation exception", error=error_msg)
            return {"valid": False, "errors": [error_msg]}

    def _format_code(self, code: str) -> str:
        """
        Format Python code for better readability.

        This performs basic formatting:
        - Ensures consistent blank lines
        - Removes trailing whitespace
        - Ensures proper spacing around operators

        Args:
            code: Python code string to format.

        Returns:
            Formatted code string.
        """
        # Remove trailing whitespace from each line
        lines = [line.rstrip() for line in code.split('\n')]

        # Remove multiple consecutive blank lines
        formatted_lines = []
        prev_blank = False
        for line in lines:
            is_blank = len(line.strip()) == 0
            if is_blank and prev_blank:
                continue  # Skip consecutive blank lines
            formatted_lines.append(line)
            prev_blank = is_blank

        # Join back together
        formatted_code = '\n'.join(formatted_lines)

        # Ensure file ends with single newline
        formatted_code = formatted_code.rstrip('\n') + '\n'

        return formatted_code

    def _add_retry_decorator(self, code: str, method: str) -> str:
        """
        Add retry logic decorator to the generated function.

        Args:
            code: Original Python code.
            method: HTTP method (GET, POST, etc.).

        Returns:
            Code with retry decorator added.
        """
        # Only add retry for idempotent methods
        if method.upper() not in ["GET", "HEAD", "OPTIONS", "PUT", "DELETE"]:
            return code

        # Find the function definition line
        lines = code.split('\n')
        function_def_idx = None
        function_indent = ""
        for i, line in enumerate(lines):
            if line.strip().startswith('def '):
                function_def_idx = i
                # Detect indentation level of the function
                function_indent = line[:len(line) - len(line.lstrip())]
                break

        if function_def_idx is None:
            return code  # Couldn't find function definition

        # Check if tenacity import already exists
        has_tenacity = any('from tenacity import' in line for line in lines[:function_def_idx])

        # Build retry decorator with same indentation as function
        retry_decorator = f"{function_indent}@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))"

        # Add import if needed
        if not has_tenacity:
            # Find where to insert import (after other imports)
            import_idx = 0
            for i, line in enumerate(lines):
                if line.strip().startswith('import ') or line.strip().startswith('from '):
                    import_idx = i + 1

            lines.insert(import_idx, "from tenacity import retry, stop_after_attempt, wait_exponential")
            function_def_idx += 1  # Adjust index after insertion

        # Add decorator before function
        lines.insert(function_def_idx, retry_decorator)

        return '\n'.join(lines)

    def generate_code_for_endpoint(
        self,
        endpoint: str,
        method: str,
        description: str = "",
        path_params: Optional[list[dict]] = None,
        query_params: Optional[list[dict]] = None,
        auth_type: str = "none",
        library: Optional[str] = None,
    ) -> str:
        """
        Generate code directly without using LLM extraction.

        This is a convenience method for when you already have the endpoint details.

        Args:
            endpoint: API endpoint path (e.g., "/users/{id}").
            method: HTTP method (GET, POST, etc.).
            description: Endpoint description.
            path_params: List of path parameter dicts.
            query_params: List of query parameter dicts.
            auth_type: Authentication type (none, bearer, api_key).
            library: HTTP library to use (defaults to self.default_library).

        Returns:
            Generated Python code string.

        Example:
            ```python
            code = generator.generate_code_for_endpoint(
                endpoint="/users/{user_id}",
                method="GET",
                description="Get user by ID",
                path_params=[{"name": "user_id", "type": "string"}],
                auth_type="bearer"
            )
            ```
        """
        endpoint_details = {
            "endpoint": endpoint,
            "method": method.upper(),
            "description": description or f"{method.upper()} {endpoint}",
            "operation_id": "",
            "path_params": path_params or [],
            "query_params": query_params or [],
            "request_body": {"required": False, "example": {}},
            "auth_type": auth_type,
            "auth_details": {"header_name": "X-API-Key" if auth_type == "api_key" else "Authorization"},
        }

        library = library or self.default_library
        code = self._generate_code(endpoint_details, library)

        # Apply validation and formatting
        if self.validate_syntax:
            validation_result = self._validate_code(code)
            if not validation_result["valid"]:
                self._logger.warning("Generated code has syntax errors", errors=validation_result["errors"])

        if self.add_retry:
            code = self._add_retry_decorator(code, method)

        code = self._format_code(code)

        return code

    def get_supported_libraries(self) -> list[str]:
        """
        Get list of supported HTTP client libraries.

        Returns:
            List of library names.
        """
        return [CodeLibrary.REQUESTS, CodeLibrary.HTTPX, CodeLibrary.AIOHTTP]

    def get_template_info(self, library: str, method: str) -> dict[str, str]:
        """
        Get information about which template will be used.

        Args:
            library: HTTP library name.
            method: HTTP method.

        Returns:
            Dictionary with template information.
        """
        template_name = self._select_template(method.upper(), library)
        template_dir = Path(__file__).parent / "templates"
        template_path = template_dir / template_name

        return {
            "library": library,
            "method": method.upper(),
            "template_name": template_name,
            "template_path": str(template_path),
            "exists": template_path.exists(),
        }

    def _detect_requested_languages(self, query: str) -> list[str]:
        """
        Detect which programming languages the user requested.

        Args:
            query: User's query.

        Returns:
            List of requested language names (e.g., ["python", "javascript"]).
        """
        query_lower = query.lower()

        # Language detection keywords
        language_keywords = {
            "python": ["python", "py"],
            "javascript": ["javascript", "js", "node", "nodejs", "node.js"],
            "typescript": ["typescript", "ts"],
            "java": ["java"],
            "csharp": ["c#", "csharp", "c sharp", ".net", "dotnet"],
            "go": ["go", "golang"],
            "ruby": ["ruby", "rb"],
            "php": ["php"],
            "rust": ["rust"],
            "swift": ["swift"],
        }

        detected_languages = []

        # Check for each language
        for lang, keywords in language_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    if lang not in detected_languages:
                        detected_languages.append(lang)
                    break

        # Default to Python if no language specified
        if not detected_languages:
            detected_languages = ["python"]

        self._logger.info(
            "Detected languages",
            languages=detected_languages,
            query=query[:100]
        )

        return detected_languages

    def _get_default_library_for_language(self, language: str) -> str:
        """
        Get the default HTTP library for a given language.

        Args:
            language: Programming language name.

        Returns:
            Default library name for that language.
        """
        library_defaults = {
            "python": "requests",
            "javascript": "fetch",
            "typescript": "fetch",
            "java": "HttpClient",
            "csharp": "HttpClient",
            "go": "net/http",
            "ruby": "net/http",
            "php": "curl",
            "rust": "reqwest",
            "swift": "URLSession",
        }

        return library_defaults.get(language, "standard library")

    def _generate_code_llm(
        self,
        endpoint_details: dict,
        language: str,
        original_query: str
    ) -> str:
        """
        Generate code using LLM for languages without templates.

        Args:
            endpoint_details: Extracted endpoint information.
            language: Target programming language.
            original_query: Original user query for context.

        Returns:
            Generated code string.
        """
        # Build code generation prompt
        prompt = f"""Generate clean, production-ready {language} code to call the following API endpoint:

Endpoint: {endpoint_details.get('method', 'GET')} {endpoint_details.get('endpoint', '')}
Description: {endpoint_details.get('description', 'No description available')}

"""

        # Add path parameters
        if endpoint_details.get('path_params'):
            prompt += "Path Parameters:\n"
            for param in endpoint_details['path_params']:
                prompt += f"  - {param['name']} ({param.get('type', 'string')}): {param.get('description', '')}\n"
            prompt += "\n"

        # Add query parameters
        if endpoint_details.get('query_params'):
            prompt += "Query Parameters:\n"
            for param in endpoint_details['query_params']:
                required = "required" if param.get('required') else "optional"
                prompt += f"  - {param['name']} ({param.get('type', 'string')}, {required}): {param.get('description', '')}\n"
            prompt += "\n"

        # Add request body
        if endpoint_details.get('request_body'):
            prompt += f"Request Body:\n{endpoint_details['request_body']}\n\n"

        # Add authentication
        if endpoint_details.get('auth_type') and endpoint_details['auth_type'] != 'none':
            prompt += f"Authentication: {endpoint_details['auth_type']}\n"
            if endpoint_details.get('auth_details'):
                prompt += f"Auth Header: {endpoint_details['auth_details'].get('header_name', 'Authorization')}\n"
            prompt += "\n"

        prompt += f"""Requirements:
- Use {self._get_default_library_for_language(language)} for HTTP requests
- Include error handling
- Add comments explaining the code
- Use modern {language} best practices
- Make it production-ready and type-safe (if applicable)

Generate ONLY the code, no explanations or markdown:"""

        # Call LLM to generate code
        try:
            code = self._llm_client.generate(
                prompt=prompt,
                system_prompt=f"You are an expert {language} developer. Generate clean, production-ready code.",
                temperature=0.3,
                max_tokens=1500,
            )

            # Clean up the code (remove markdown if present)
            code = code.strip()
            if code.startswith("```"):
                # Remove code block markers
                lines = code.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                code = "\n".join(lines)

            self._logger.info(
                "LLM code generation complete",
                language=language,
                code_length=len(code)
            )

            return code

        except Exception as e:
            self._logger.error(
                "LLM code generation failed",
                language=language,
                error=str(e)
            )
            # Return a simple fallback code template
            return self._generate_fallback_code(endpoint_details, language)

    def _generate_fallback_code(self, endpoint_details: dict, language: str) -> str:
        """
        Generate basic fallback code when LLM generation fails.

        Args:
            endpoint_details: Endpoint information.
            language: Target language.

        Returns:
            Basic code template.
        """
        endpoint = endpoint_details.get('endpoint', '/api/endpoint')
        method = endpoint_details.get('method', 'GET')

        if language == "javascript":
            return f"""// {method} {endpoint}
const response = await fetch('https://api.example.com{endpoint}', {{
  method: '{method}',
  headers: {{
    'Content-Type': 'application/json',
    // Add authorization header if needed
    // 'Authorization': 'Bearer YOUR_TOKEN'
  }}
}});

const data = await response.json();
console.log(data);
"""
        elif language == "typescript":
            return f"""// {method} {endpoint}
const response = await fetch('https://api.example.com{endpoint}', {{
  method: '{method}',
  headers: {{
    'Content-Type': 'application/json',
    // Add authorization header if needed
    // 'Authorization': 'Bearer YOUR_TOKEN'
  }}
}});

const data = await response.json();
console.log(data);
"""
        else:
            return f"""// {method} {endpoint}
// Code generation failed. Please check the endpoint documentation
// and implement the {language} code manually.
"""
