# Changelog

All notable changes to the API Integration Assistant will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2025-12-26

### Added - Phase 2: Multi-Agent System

#### Multi-Agent Orchestration
- **Supervisor Agent** powered by LangGraph StateGraph for intelligent query routing
- **Query Analyzer** with intent classification and confidence scoring
- **Specialized Routing** based on query intent (code generation, documentation gaps, etc.)
- **Processing Path Tracking** showing which agents handled each query
- **Error Recovery** with graceful degradation across agent pipeline

#### Multi-Language Code Generation
- Support for **10+ programming languages** (Python, JavaScript, TypeScript, Java, C#, Go, Ruby, PHP, Rust, Swift)
- Template-based Python code generation with best practices
- LLM-powered code generation for non-Python languages
- Multi-language requests in single query ("show me Python and JavaScript code")
- Language-specific library selection (requests, fetch, HttpClient, etc.)
- Fallback mechanisms for robustcodegen generation

#### LLM Provider Switching
- **Flexible Provider System**: Easy switching between Ollama (local) and Groq (cloud)
- **Agent-Specific Models**: Different Groq models for different agent types
  - Query Analyzer: Reasoning model
  - Code Generator: Code-optimized model
  - RAG Agent: General model
  - Doc Analyzer: Reasoning model
- **Configuration via Environment**: Simple `LLM_PROVIDER` setting
- **Groq Integration**: Lightning-fast inference (50-100 tokens/sec)
- **Factory Functions**: `create_reasoning_client()`, `create_code_client()`, etc.

#### Conversation Context
- **Intelligent History Management**: Maintains context across multiple exchanges
- **Smart Summarization**: Automatically summarizes long conversations
  - Short (<6 exchanges): Full history
  - Long (>6 exchanges): First 3 + summary + last 3
- **LLM-Powered Summaries**: Uses LLM to create concise conversation summaries
- **Context-Aware Follow-ups**: Understands references to previous questions

#### Web Search Fallback
- **DuckDuckGo Integration**: Free web search without API key requirement
- **Automatic Fallback**: Triggers when vector store relevance < threshold (default 0.5)
- **Hybrid Retrieval**: Combines vector store + web search results
- **Source Distinction**: Web sources clearly marked with URLs in citations
- **Configurable Settings**:
  - `ENABLE_WEB_SEARCH`: Enable/disable web search feature
  - `WEB_SEARCH_MIN_RELEVANCE`: Relevance threshold for fallback trigger (0.0-1.0)
  - `WEB_SEARCH_MAX_RESULTS`: Maximum web results to fetch
- **Seamless Integration**: Search logic integrated into RAG Agent retrieve node

#### UI Enhancements
- **Real-Time Agent Status**: Live updates showing which agents are processing
- **Intent Analysis Display**: Shows detected intent, confidence level, and keywords
- **Agent Pipeline Visualization**: Step-by-step view of agent execution path
- **Source Citations**: Expandable sections showing retrieved documents with relevance scores
- **Code Snippet Display**: Syntax-highlighted code with language tags and library info
- **Unique Widget Keys**: Fixed Streamlit key conflicts across chat history
- **Agent Icons**: Visual indicators for each agent type (🔍 📚 💻 📋)
- **Confidence Metrics**: Visual confidence scores for intent analysis

#### Testing Infrastructure
- **271 Comprehensive Tests** across 11 test files
- **E2E Integration Tests** (21 tests): Full pipeline workflows
- **UI Component Tests** (19 tests): Streamlit rendering logic
- **Agent Tests** (200 tests): Individual agent functionality
- **Core Tests** (31 tests): Core services and utilities
- **Test Validation Script**: Automated test structure verification
- **Testing Documentation**: Comprehensive guide in tests/README.md

#### Documentation
- **LLM Provider Guide**: Complete guide for switching between Ollama and Groq
- **Updated README**: Comprehensive feature documentation
- **Configuration Tables**: Clear environment variable documentation
- **Usage Examples**: Detailed examples for all major features
- **Troubleshooting Guide**: Common issues and solutions

### Changed

#### Architecture
- Refactored agent system to use LangGraph StateGraph
- Unified LLM client to support multiple providers
- Enhanced state management with structured types
- Improved error handling with recoverable error tracking

#### Configuration
- Added `LLM_PROVIDER` configuration option
- Added Groq model configuration variables
- Enhanced validation for environment variables
- Better default values for all settings

#### Performance
- 20-50x faster inference when using Groq provider
- Optimized conversation context building
- Efficient state passing between agents
- Reduced token usage with smart summarization

### Fixed

- **Streamlit Key Conflicts**: Fixed duplicate widget keys across chat history (commit: a7037d5)
- **Decommissioned Model**: Updated from `deepseek-r1-distill-llama-70b` to `llama-3.3-70b-versatile` (commit: 13e75c0)
- **AttributeError**: Fixed None-safe intent extraction in supervisor logging (commit: 13e75c0)
- **JSON Parsing**: Enhanced JSON extraction from LLM responses with markdown removal (commit: f86cbbe)
- **VectorStore Access**: Fixed incorrect `vector_store.vector_store` attribute access (commit: 4a66ded)
- **Multi-Language Support**: Fixed code generation to detect and support multiple languages (commit: daf4876)
- **Conversation Context**: Added intelligent history management for follow-up questions (commit: 8c9be02)
- **Test Assertions**: Fixed UI test icon expectations and mock setup (commit: 32e768a)

### Security

- Maintained privacy option with local Ollama deployment
- Secure API key handling for Groq provider
- No credentials stored in code or logs

## [0.1.0] - 2025-12-19

### Added - Phase 1: RAG Foundation

#### Core Features
- OpenAPI/Swagger specification parsing
- Vector database (ChromaDB) integration
- Sentence transformer embeddings (all-MiniLM-L6-v2)
- Basic RAG (Retrieval Augmented Generation) pipeline
- Streamlit UI with chat interface

#### Agents
- Query Analyzer with intent classification
- RAG Agent with document retrieval
- Code Generator with Python templates
- Documentation Analyzer for gap detection

#### Storage & Processing
- Persistent vector storage in ChromaDB
- OpenAPI endpoint chunking and metadata extraction
- Multi-query retrieval for better recall
- Source citation in responses

#### Testing
- Unit tests for individual agents
- Integration tests for agent workflows
- 200+ tests total

### Infrastructure
- Python 3.11+ support
- Ollama integration for local LLMs
- Modular architecture with src/ structure
- Environment-based configuration

---

## Version Numbering

- **0.1.0**: Phase 1 - RAG Foundation
- **0.2.0**: Phase 2 - Multi-Agent System
- **0.3.0**: Phase 3 - Production Hardening (planned)
- **0.4.0**: Phase 4 - Advanced Features (planned)

## Links

- [Repository](https://github.com/yourusername/api-assistant)
- [Issues](https://github.com/yourusername/api-assistant/issues)
- [Pull Requests](https://github.com/yourusername/api-assistant/pulls)
