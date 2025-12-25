"""
Code Generator Agent for creating API integration code.

This agent generates production-ready Python code for calling API endpoints
using various HTTP client libraries (requests, httpx, aiohttp).
"""

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
    ):
        """
        Initialize the Code Generator agent.

        Args:
            llm_client: LLM client for extracting endpoint details.
            default_library: Default HTTP library to use.
            base_url: Default API base URL.
        """
        super().__init__()
        self._llm_client = llm_client or LLMClient()
        self.default_library = default_library
        self.base_url = base_url

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

            # Step 2: Determine which library to use
            library = self._determine_library(query)

            # Step 3: Generate code using template
            code = self._generate_code(endpoint_details, library)

            # Step 4: Create code snippet object
            code_snippet = {
                "language": "python",
                "library": library,
                "code": code,
                "endpoint": endpoint_details.get("endpoint", ""),
                "method": endpoint_details.get("method", "GET"),
                "description": endpoint_details.get("description", ""),
            }

            # Update state
            updated_state = {
                **state,
                "code_snippets": [code_snippet],
                "response": f"Generated Python code using {library} library for {endpoint_details.get('method')} {endpoint_details.get('endpoint')}",
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
