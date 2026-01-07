# API Integration Assistant - Test Suite

This directory contains comprehensive tests for the API Integration Assistant.

## Test Organization

```
tests/
├── test_agents/          # Individual agent tests
│   ├── test_query_analyzer.py
│   ├── test_rag_agent.py
│   ├── test_code_agent.py
│   ├── test_doc_analyzer.py
│   ├── test_supervisor.py
│   └── test_integration.py
├── test_core/            # Core functionality tests
│   └── test_monitoring.py
├── test_e2e/             # End-to-end integration tests
│   └── test_full_pipeline.py
├── test_api/             # REST API tests
├── test_cli/             # CLI command tests
├── test_parsers/         # API parser tests
├── test_diagrams/        # Diagram generation tests
└── test_sessions/        # Session management tests
```

## Running Tests

### Prerequisites

Make sure pytest is installed:
```bash
pip install pytest pytest-asyncio
```

### Run All Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=src --cov-report=html
```

### Run Specific Test Suites

```bash
# Run only agent tests
pytest tests/test_agents/ -v

# Run only E2E tests
pytest tests/test_e2e/ -v

# Run specific test file
pytest tests/test_e2e/test_full_pipeline.py -v

# Run specific test class
pytest tests/test_e2e/test_full_pipeline.py::TestSupervisorE2E -v

# Run specific test
pytest tests/test_e2e/test_full_pipeline.py::TestSupervisorE2E::test_general_question_workflow -v
```

### Run Tests by Marker

```bash
# Run only integration tests
pytest -m integration -v

# Run only unit tests
pytest -m unit -v

# Skip slow tests
pytest -m "not slow" -v
```

## Test Coverage

### Day 12 E2E Tests (`test_e2e/test_full_pipeline.py`)

**22 comprehensive end-to-end tests covering:**

1. **Supervisor Orchestration** (6 tests)
   - General question workflow
   - Code generation workflow
   - Documentation gap detection
   - Error recovery in pipeline
   - Low confidence query handling
   - Multi-agent coordination

2. **Multi-Language Code Generation** (3 tests)
   - Python code generation
   - JavaScript code generation
   - Multiple languages in single request

3. **LLM Provider Switching** (4 tests)
   - Groq provider configuration
   - Ollama provider configuration
   - Reasoning model selection
   - Code model selection

4. **Conversation Context** (2 tests)
   - Short conversation history
   - Long conversation with summarization

5. **Error Handling** (4 tests)
   - Invalid JSON from LLM
   - None intent analysis
   - Vector store timeout
   - Graceful degradation

6. **Agent Metadata** (3 tests)
   - Processing path tracking
   - Intent metadata return
   - Sources metadata return

### Week 1 Integration Tests (`test_agents/test_integration.py`)

**15+ tests covering:**

1. **Individual Agent Workflows**
   - Query Analyzer processing
   - RAG Agent retrieval
   - Code Generator templates
   - Documentation Analyzer gaps

2. **Multi-Agent Chains**
   - Query Analyzer → RAG
   - Query Analyzer → RAG → Code Generator

3. **Error Handling**
   - LLM failures with fallback
   - Empty retrieval results
   - Invalid data handling

4. **State Management**
   - State immutability
   - Processing path tracking
   - Metadata accumulation

## Writing New Tests

### Test Structure

```python
import pytest
from unittest.mock import MagicMock, patch

class TestYourFeature:
    """Test suite for your feature."""

    @pytest.fixture
    def mock_dependency(self):
        """Create mock dependency."""
        return MagicMock()

    def test_basic_functionality(self, mock_dependency):
        """Test basic functionality."""
        # Arrange
        ...

        # Act
        result = your_function(mock_dependency)

        # Assert
        assert result == expected
```

### Best Practices

1. **Use descriptive test names**: `test_handles_invalid_json_from_llm`
2. **Follow AAA pattern**: Arrange, Act, Assert
3. **Mock external dependencies**: LLM clients, vector stores, file I/O
4. **Test error paths**: Not just happy paths
5. **Keep tests isolated**: Each test should be independent
6. **Use fixtures**: Share common setup between tests

### Mocking Examples

```python
# Mock LLM client
@pytest.fixture
def mock_llm_client(self):
    client = MagicMock(spec=LLMClient)
    client.generate.return_value = "Mock response"
    return client

# Mock vector store
@pytest.fixture
def mock_vector_store(self):
    store = MagicMock()
    store.similarity_search_with_score.return_value = [
        (MagicMock(page_content="Test", metadata={}), 0.9)
    ]
    return store

```

## Continuous Integration

These tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest -v --cov=src --cov-report=xml
```

## Test Configuration

Tests use environment variables from `.env.test` (if present) or fall back to mocks.

### LLM Provider Testing

To test with real LLM providers (optional):

```bash
# Set environment variables
export LLM_PROVIDER=groq
export GROQ_API_KEY=your_key

# Run tests
pytest tests/test_e2e/ -v
```

**Note**: E2E tests use mocks by default to avoid API costs and ensure deterministic results.

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError: No module named 'pytest'**
   ```bash
   pip install pytest pytest-asyncio
   ```

2. **Import errors**
   ```bash
   # Run from project root
   cd /path/to/Api-Assistant
   pytest
   ```

3. **Fixture not found**
   - Make sure `conftest.py` is in the test directory or parent
   - Check fixture scope (function, class, module, session)

4. **Tests fail with "No such file or directory"**
   - Ensure you're in the project root
   - Check that all `__init__.py` files exist

## Test Metrics

Current test coverage:
- **Total Tests**: 831+ comprehensive tests
- **Agent Tests**: 15+ tests
- **E2E Tests**: 22 tests
- **API Tests**: 50+ tests
- **Parser Tests**: 30+ tests
- **Coverage Target**: >80%

## Future Test Improvements

- [ ] Add performance benchmarks
- [ ] Add load testing for concurrent requests
- [ ] Add mutation testing
- [ ] Increase coverage to 90%+
