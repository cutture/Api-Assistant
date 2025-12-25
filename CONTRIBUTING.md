# Contributing to API Integration Assistant

First off, thank you for considering contributing to the API Integration Assistant! It's people like you that make this tool better for everyone.

## Code of Conduct

This project and everyone participating in it is governed by our commitment to fostering an open and welcoming environment. Be respectful, inclusive, and considerate in all interactions.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When creating a bug report, include as many details as possible:

**Bug Report Template:**

```markdown
## Description
A clear description of the bug.

## Steps to Reproduce
1. Go to '...'
2. Click on '...'
3. See error

## Expected Behavior
What you expected to happen.

## Actual Behavior
What actually happened.

## Environment
- OS: [e.g. Windows 11, macOS 14, Ubuntu 22.04]
- Python version: [e.g. 3.11.5]
- LLM Provider: [Ollama/Groq]
- Browser: [if UI-related]

## Additional Context
Any other relevant information, screenshots, logs, etc.
```

### Suggesting Enhancements

Enhancement suggestions are welcome! Please provide:

1. **Use case**: Why this enhancement would be useful
2. **Proposed solution**: How you envision it working
3. **Alternatives**: Other approaches you considered
4. **Examples**: Screenshots, mockups, or code snippets

### Pull Requests

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Make** your changes
4. **Test** your changes thoroughly
5. **Commit** with clear messages
6. **Push** to your fork
7. **Open** a Pull Request

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Git
- Ollama (for local mode) or Groq API key (for cloud mode)

### Setup Steps

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/api-assistant.git
cd api-assistant

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-asyncio black ruff mypy

# Copy environment configuration
cp .env.example .env
# Edit .env with your settings
```

### Running the Application

```bash
# Start the application
streamlit run src/main.py
```

### Running Tests

```bash
# Run all tests
pytest -v

# Run specific test suite
pytest tests/test_agents/ -v
pytest tests/test_e2e/ -v

# Run with coverage
pytest --cov=src --cov-report=html

# Validate test structure
python tests/validate_tests.py
```

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with some modifications:

- **Line length**: 100 characters (not 79)
- **Docstrings**: Google style
- **Type hints**: Required for public functions
- **Imports**: Organized (stdlib, third-party, local)

### Code Formatting

```bash
# Format code with black
black src/ tests/

# Check code quality with ruff
ruff check src/ tests/

# Type checking with mypy
mypy src/
```

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**

```
feat(agents): Add support for multi-language code generation

Implemented LLM-based code generation for JavaScript, TypeScript,
Java, and other languages beyond Python templates.

Closes #123
```

```
fix(ui): Resolve Streamlit key conflict in sources section

Fixed duplicate widget keys when rendering sources across multiple
messages in chat history.

Fixes #456
```

### Documentation

- **Docstrings**: All public functions, classes, and modules must have docstrings
- **Type hints**: Use type hints for function parameters and return values
- **Comments**: Explain *why*, not *what* (the code shows what)
- **README**: Update if adding new features or changing usage

**Docstring Example:**

```python
def process_query(query: str, context: Optional[str] = None) -> dict:
    """
    Process a user query through the agent pipeline.

    Args:
        query: The user's question or request.
        context: Optional conversation context from previous exchanges.

    Returns:
        Dict containing:
            - response: Generated answer
            - sources: Retrieved documents
            - intent: Classified intent

    Raises:
        ValueError: If query is empty.

    Example:
        >>> result = process_query("How do I authenticate?")
        >>> print(result["response"])
    """
    # Implementation
```

## Testing Guidelines

### Writing Tests

- **Test coverage**: Aim for >80% coverage for new code
- **Test organization**: Place tests in appropriate test_* directories
- **Test naming**: Use descriptive names (`test_handles_empty_query`)
- **Assertions**: Use specific assertions (`assert x == 5`, not `assert x`)
- **Mocking**: Mock external dependencies (LLM, vector store, file I/O)

**Test Example:**

```python
class TestQueryAnalyzer:
    """Test query analyzer functionality."""

    @pytest.fixture
    def mock_llm_client(self):
        """Create mock LLM client."""
        client = MagicMock(spec=LLMClient)
        client.generate.return_value = '{"intent": "code_generation"}'
        return client

    def test_classifies_code_generation_intent(self, mock_llm_client):
        """Test that code generation requests are correctly classified."""
        # Arrange
        analyzer = QueryAnalyzer(llm_client=mock_llm_client)
        query = "Generate Python code to create a user"

        # Act
        result = analyzer.process({"query": query})

        # Assert
        assert result["intent_analysis"]["primary_intent"] == "code_generation"
        assert result["intent_analysis"]["confidence"] > 0.8
```

### Test Coverage Requirements

- **New features**: Must include tests
- **Bug fixes**: Must include regression test
- **Critical paths**: Should have >90% coverage
- **Edge cases**: Test error conditions and boundary cases

## Pull Request Process

### Before Submitting

1. ✅ All tests pass (`pytest -v`)
2. ✅ Code is formatted (`black src/ tests/`)
3. ✅ No linting errors (`ruff check src/ tests/`)
4. ✅ Documentation is updated
5. ✅ CHANGELOG.md is updated (if applicable)

### PR Description Template

```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update

## Testing
- [ ] All existing tests pass
- [ ] New tests added and passing
- [ ] Manual testing performed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] CHANGELOG.md updated

## Related Issues
Closes #(issue number)
```

### Review Process

1. **Automated Checks**: CI/CD runs tests and linting
2. **Code Review**: Maintainer reviews code quality and design
3. **Feedback**: Address any requested changes
4. **Approval**: Once approved, PR will be merged

## Project Architecture

### Directory Structure

```
src/
├── agents/          # Multi-agent system
│   ├── supervisor.py    # LangGraph orchestrator
│   ├── query_analyzer.py
│   ├── rag_agent.py
│   ├── code_agent.py
│   └── doc_analyzer.py
├── core/            # Core services
│   ├── llm_client.py
│   ├── embeddings.py
│   └── monitoring.py
├── services/        # Business logic
│   ├── vector_store.py
│   └── openapi_parser.py
└── ui/              # User interface
    ├── chat.py
    └── sidebar.py
```

### Key Patterns

- **Dependency Injection**: Use constructor injection for dependencies
- **Factory Pattern**: Use factory functions for complex object creation
- **State Management**: Immutable state dictionaries passed between agents
- **Error Handling**: Graceful degradation with user-friendly messages

## Areas for Contribution

### High Priority

- [ ] Docker deployment configuration
- [ ] CI/CD pipeline setup
- [ ] Performance benchmarking and optimization
- [ ] Additional API spec format support (RAML, API Blueprint)
- [ ] Mobile-responsive UI improvements

### Medium Priority

- [ ] Postman collection import
- [ ] API testing capabilities
- [ ] Export generated code to files
- [ ] Dark mode for UI
- [ ] Keyboard shortcuts

### Low Priority (Ideas Welcome!)

- [ ] Multi-modal support (images in docs)
- [ ] Collaborative features (shared workspaces)
- [ ] Plugin system for custom agents
- [ ] GraphQL API support
- [ ] WebSocket API support

## Questions?

Feel free to:
- Open an issue for discussion
- Join our community discussions
- Reach out to maintainers

## Recognition

Contributors will be:
- Listed in CHANGELOG.md
- Credited in release notes
- Added to a future CONTRIBUTORS.md file

Thank you for contributing! 🎉
