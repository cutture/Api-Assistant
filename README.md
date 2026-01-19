# 🚀 Intelligent Self-Validating Coding Agent

**Version 2.0.0** - In Development 🔧

An AI-powered coding assistant that generates, executes, validates, and delivers production-ready code through an iterative refinement loop with container-based execution.

[![Tests](https://img.shields.io/badge/tests-831%20passing-success)](tests/)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.0.0-yellow)](CHANGELOG_V2.md)

## 🆕 What's New in v2.0.0

This major version transforms the API Integration Assistant into an **Intelligent Coding Agent** with:

### Core Capabilities
- **Multi-language code generation** (Python, JS, TS, Java, Go, C#)
- **Container-based code execution** with automated testing
- **Self-validating loop** (5 retries with multi-signal validation)
- **Artifact management** (uploads, generated files, downloadable outputs)

### New Features (Phases 1-10)
- **GitHub Integration** - OAuth, repository context, PR creation support
- **Webhook Triggers** - CI/CD integration with Slack/Discord notifications
- **Security Scanning** - Vulnerability detection with CWE/OWASP mapping
- **Mock API Servers** - Auto-generate from OpenAPI specs
- **Code Templates** - Pre-built templates for common patterns
- **Quality Scoring** - Complexity metrics and code quality analysis
- **Database Query Generation** - SQL/NoSQL from natural language
- **Live Preview** - Temporary preview URLs for generated code
- **Rate Limiting & Metrics** - Production-ready monitoring

### Three Output Modes
1. **Inline Snippets** - Code displayed directly in chat
2. **ZIP Bundles** - Download multi-file projects
3. **GitHub PRs** - Push directly to repositories

---

## ✨ Key Features

### 🤖 **Multi-Agent Orchestration**
- **Intelligent Query Routing**: Automatically routes queries to specialized agents based on intent
- **Supervisor Agent**: LangGraph-powered coordinator managing the entire pipeline
- **Intent Classification**: 90%+ accuracy in understanding user requests

### 💻 **Multi-Language Code Generation**
- Generate integration code in **Python**, **JavaScript**, **TypeScript**, **Java**, **Go**, and more
- Template-based Python generation with best practices
- LLM-powered generation for other languages
- Supports multiple languages in a single request

### 📚 **Advanced RAG Pipeline**
- Multi-query retrieval for comprehensive context
- Source citation with relevance scores
- Conversation history with intelligent summarization
- Context-aware follow-up questions

### ⚡ **Flexible LLM Provider**
- **Ollama** (local): Privacy-focused, offline capability
- **Groq** (cloud): Lightning-fast inference (50-100 tokens/sec)
- Easy switching via environment variable
- Agent-specific model selection for optimal performance

### 🎯 **Specialized Agents**
1. **Query Analyzer**: Intent classification and routing
2. **RAG Agent**: Document retrieval and synthesis
3. **Code Generator**: Multi-language code generation
4. **Documentation Analyzer**: Gap detection and quality assessment

### 🔍 **Real-Time Agent Visibility**
- Live agent pipeline tracking
- Intent analysis with confidence scores
- Processing path visualization
- Source document citations

### 🔎 **Advanced Search (v1.0.0 New!)**
- **Hybrid Search**: Vector + BM25 keyword search with configurable weights
- **Re-ranking**: Cross-encoder deep semantic re-ranking
- **Query Expansion**: Automatic synonym and concept expansion
- **Result Diversification**: MMR algorithm to reduce redundancy
- **Faceted Search**: Group results by metadata fields
- **Advanced Filtering**: Complex boolean queries with 13 operators

### 🛠️ **Professional CLI Tool (v1.0.0 New!)**
- **30+ Commands**: Complete CLI built with Typer and Rich
- **Batch Processing**: Parse multiple API specs at once
- **Diagram Generation**: Auto-generate Mermaid diagrams
- **Session Management**: Multi-user support with conversation history
- **Beautiful Output**: Color-coded tables and progress indicators
- **Shell Completion**: Auto-completion for commands

### 📊 **Diagram Generation (v1.0.0 New!)**
- **Sequence Diagrams**: API request/response flows with participants and interactions
- **Authentication Flow**: OAuth2, Bearer, API Key, and Basic auth visualizations
- **ER Diagrams**: GraphQL schema entity-relationship visualization
- **API Overview**: High-level API structure and endpoint groupings
- **All 4 Types Exposed**: Complete frontend UI for all diagram generation
- **Mermaid Format**: GitHub-compatible diagram export with live preview

### 🔄 **Multi-Format Support (v1.0.0 New!)**
- **OpenAPI 3.0+**: Full YAML and JSON support
- **GraphQL**: SDL schema parsing with type system
- **Postman Collections**: v2.0 and v2.1 support
- **Auto-Detection**: Automatic format recognition
- **Unified Handler**: Single interface for all formats

### 🌐 **REST API (v1.0.0 New!)**
- **15+ Endpoints**: Complete REST API with FastAPI
- **Interactive Docs**: Auto-generated Swagger/ReDoc
- **Health Checks**: `/health`, `/ready`, `/stats` endpoints
- **CORS Support**: Cross-origin resource sharing
- **Rate Limiting**: Token bucket per-user limits
- **API Key Auth**: Secure API access

### 🎨 **Modern Web Frontend (v1.0.0 Latest!)**
- **Next.js 16 + React 19**: Modern App Router architecture
- **TypeScript Throughout**: Full type safety across the stack
- **Comprehensive Settings Page**: Configure all application preferences
  - LLM Provider selection (Ollama/Groq) with dynamic configuration
  - Search defaults (mode, re-ranking, query expansion, diversification)
  - UI preferences (theme, scores, metadata display)
  - Session defaults (TTL, auto-cleanup)
- **Complete Diagram UI**: All 4 diagram types with dedicated input forms
- **Session Management**: Create, update, delete, and filter user sessions
  - **Session Update UI**: Inline editing of session metadata, TTL, and settings
  - **Edit/Save/Cancel**: Full session modification with validation
  - **Session Reactivation**: Reactivate expired/inactive sessions with one click
  - **Active Session Dropdown Menu**: Quick access to session operations in chat
    - View Session: Navigate to session details from chat
    - Clear Conversation History: Permanently delete messages while preserving session
    - End Session: Mark as inactive and create new session
  - **Clear History**: Delete conversation history from chat or session details page
  - **Confirmation Dialogs**: Safety prompts for all destructive operations
- **Chat Interface**: AI-powered conversations with source citations
- **Search Interface**: Advanced search with filters and result display
- **Document Management**: Upload and manage API specifications
- **🌙 Dark Mode Support**: Light/Dark/System themes with live switching
  - Theme persistence via localStorage
  - System preference detection with auto-updates
  - Seamless theme toggle in Settings page
- **🔒 Authentication & Authorization**: Production-ready auth system
  - Login page with email/password authentication
  - Guest mode for local testing (no auth required)
  - Protected routes with automatic redirect
  - User menu with logout functionality
  - localStorage session persistence
- **🔄 Request Retry Logic**: Automatic retry with exponential backoff
  - Auto-retry on 408, 429, 500, 502, 503, 504 errors
  - 3 retries max with 1s → 2s → 4s delays
  - Improved resilience against transient failures
- **Production Ready**: Docker deployment, health checks, CI/CD pipelines

### 🧪 **Comprehensive Testing (v1.0.0 Latest!)**
- **Backend Tests**: 831 tests with 99.9% pass rate
- **Frontend Unit Tests**: Component testing with Jest + React Testing Library
- **Integration Tests**: API client testing with MSW (Mock Service Worker)
- **E2E Tests**: 7 complete user flow tests with Playwright
  - Sessions, Diagrams, Navigation (existing)
  - Document Upload, Chat, Search, Error Scenarios (new)
- **Test Coverage**: 931+ total tests across backend and frontend

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI with async/await support
- **Agent System**: LangGraph StateGraph for multi-agent orchestration
- **Vector DB**: ChromaDB with persistent storage
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **LLM Providers**: Ollama (local) / Groq (cloud)
- **Monitoring**: Langfuse integration
- **API Parsing**: Prance + OpenAPI Spec Validator

### Frontend
- **Framework**: Next.js 16.1.1 with App Router
- **UI Library**: React 19.2.3 with TypeScript 5.x
- **State Management**: React Query 5.90.12 (server) + Zustand 5.0.9 (UI)
- **Components**: Radix UI primitives with Tailwind CSS 3.4.19
- **HTTP Client**: Axios 1.13.2 with interceptors + retry logic
- **Authentication**: Custom AuthContext with localStorage persistence
- **Theming**: ThemeProvider with light/dark/system mode support
- **Diagrams**: Mermaid 11.12.2 with react-mermaid2
- **Testing**: Jest 30.2.0, React Testing Library 16.3.1, Playwright 1.57.0
- **DevOps**: Docker multi-stage builds, GitHub Actions CI/CD

## 📋 Prerequisites

- **Python 3.11+**
- **Ollama** with `deepseek-coder:6.7b` model (for local mode)
  ```bash
  # Install Ollama: https://ollama.com/download
  ollama pull deepseek-coder:6.7b
  ```
- **OR Groq API Key** (for cloud mode - get free at https://console.groq.com)
- **Git**

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd api-assistant
```

### 2. Create virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
# Copy example config
cp .env.example .env

# Edit .env with your preferred LLM provider:

# Option 1: Use Ollama (local, private)
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-coder:6.7b

# Option 2: Use Groq (cloud, fast)
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
```

### 5. Start Ollama (if using local mode)

```bash
ollama serve
```

### 6. Run the application

**Backend (FastAPI):**
```bash
# Terminal 1 - Start FastAPI backend
uvicorn src.api.app:app --reload --port 8000
```

**Frontend (Next.js):**
```bash
# Terminal 2 - Start Next.js frontend
cd frontend
npm run dev
```

Open your browser to `http://localhost:3000`

## 📖 Usage Guide

### Upload an API Specification

1. Click **"📁 Upload API Specification"** in the sidebar
2. Select your OpenAPI/Swagger JSON or YAML file
3. Wait for processing (you'll see endpoint count)
4. Start asking questions!

### Ask Questions

**General Questions:**
- "What is this API about?"
- "How do I authenticate with this API?"
- "What are all the available endpoints?"

**Code Generation:**
- "Generate Python code to create a new user"
- "Show me JavaScript code to fetch all pets"
- "Give me both Python and JavaScript code for the login endpoint"

**Endpoint Lookup:**
- "Which endpoint creates an order?"
- "Find the endpoint for deleting users"

**Documentation Analysis:**
- "What's missing in the documentation?"
- "Find undocumented endpoints"

### Agent Pipeline Visualization

Watch the agents work in real-time:

1. **🔍 Query Analysis** - Intent classification with confidence
2. **📚 RAG Retrieval** - Document search with relevance scores
3. **💻 Code Generation** - Multi-language code output
4. **📋 Documentation Analysis** - Gap detection

## 📁 Project Structure

```
api-assistant/
├── src/                      # Backend source code
│   ├── api/                  # FastAPI REST API
│   │   ├── app.py            # Main FastAPI application
│   │   └── models.py         # Pydantic request/response models
│   ├── agents/               # Multi-agent system
│   │   ├── supervisor.py     # LangGraph orchestrator
│   │   ├── query_analyzer.py # Intent classifier
│   │   ├── rag_agent.py      # RAG pipeline
│   │   ├── code_agent.py     # Code generator
│   │   └── state.py          # Agent state management
│   ├── core/                 # Core services
│   │   ├── vector_store.py   # Advanced search (hybrid, re-ranking)
│   │   ├── llm_client.py     # LLM abstraction (Ollama/Groq)
│   │   ├── embeddings.py     # Embedding service
│   │   └── filters.py        # Advanced filtering system
│   ├── parsers/              # Multi-format parsers
│   │   ├── openapi_parser.py # OpenAPI 3.0+ parser
│   │   ├── graphql_parser.py # GraphQL schema parser
│   │   └── postman_parser.py # Postman collection parser
│   ├── diagrams/             # Diagram generation
│   │   └── mermaid_generator.py # Mermaid diagram generator
│   ├── sessions/             # Session management
│   │   └── session_manager.py # Multi-user session handling
│   └── cli/                  # CLI tool (30+ commands)
│       └── main.py           # Typer CLI application
├── frontend/                 # Next.js frontend application
│   ├── src/
│   │   ├── app/              # Next.js App Router pages
│   │   │   ├── page.tsx      # Home page
│   │   │   ├── search/       # Search interface
│   │   │   ├── chat/         # AI chat interface
│   │   │   ├── sessions/     # Session management
│   │   │   ├── diagrams/     # Diagram generation (4 types)
│   │   │   ├── documents/    # Document upload
│   │   │   └── settings/     # Settings page (NEW)
│   │   ├── components/       # React components
│   │   │   ├── sessions/     # Session components
│   │   │   ├── diagrams/     # Diagram components
│   │   │   ├── ui/           # Radix UI components
│   │   │   └── layout/       # Layout components
│   │   ├── hooks/            # React Query hooks
│   │   ├── lib/              # API clients and utilities
│   │   ├── stores/           # Zustand state management (NEW)
│   │   └── types/            # TypeScript type definitions
│   ├── e2e/                  # E2E tests with Playwright (NEW)
│   │   ├── sessions.spec.ts
│   │   ├── diagrams.spec.ts
│   │   ├── navigation.spec.ts
│   │   ├── document-upload.spec.ts (NEW)
│   │   ├── chat.spec.ts (NEW)
│   │   ├── search.spec.ts (NEW)
│   │   └── error-scenarios.spec.ts (NEW)
│   └── __tests__/            # Unit & integration tests
├── tests/                    # Backend tests (831 tests, 99.9% pass)
│   ├── test_agents/          # Agent tests
│   ├── test_core/            # Core functionality
│   ├── test_api/             # REST API tests
│   ├── test_parsers/         # Parser tests
│   └── test_diagrams/        # Diagram tests
├── docs/                     # Documentation
│   ├── ARCHITECTURAL_REVIEW.md # Comprehensive architecture analysis
│   ├── LLM_PROVIDER_GUIDE.md   # LLM provider switching guide
│   ├── AGENT_ARCHITECTURE.md   # Multi-agent system design
│   ├── SEARCH_GUIDE.md         # Search modes & query expansion guide
│   └── Week_*/                 # Weekly development guides
├── scripts/                  # Deployment scripts
│   ├── deploy.sh             # Multi-environment deployment
│   ├── local-dev.sh          # Local development setup
│   ├── health-check.sh       # Health monitoring
│   └── verify-production.sh  # Production readiness checks
├── data/
│   └── chroma_db/            # Vector database storage
├── requirements.txt          # Python dependencies
├── .env.example              # Example configuration
└── README.md                 # This file
```

## 🧪 Testing

### Run All Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests (458 total)
pytest -v

# Run with coverage
pytest --cov=src --cov-report=html
```

### Run Specific Test Suites

```bash
# Agent tests
pytest tests/test_agents/ -v

# End-to-end integration tests
pytest tests/test_e2e/ -v

# UI component tests
pytest tests/test_ui/ -v

# Validate test structure
python tests/validate_tests.py
```

**Test Coverage:**
- 458 total tests across 14 files
- 60+ test classes
- 100% structure validation
- Covers agents, core services, security, performance, and end-to-end flows

## 🚢 Deployment

### Docker Deployment

Deploy using Docker for consistent, isolated environments:

```bash
# Local deployment with Ollama
docker-compose up -d

# Production deployment with Groq
docker-compose -f docker-compose.prod.yml up -d
```

See [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) for complete Docker setup instructions.

### Production Deployment

Deploy to cloud platforms with one command:

```bash
# AWS (ECS)
./scripts/deployment/aws/deploy.sh production latest

# Google Cloud (Cloud Run)
./scripts/deployment/gcp/deploy.sh production latest

# Azure (App Service)
./scripts/deployment/azure/deploy.sh production latest

# DigitalOcean (App Platform)
./scripts/deployment/digitalocean/deploy.sh production
```

**Complete deployment guides:**
- [Production Deployment Guide](PRODUCTION_DEPLOYMENT.md) - Comprehensive cloud deployment
- [Production Checklist](PRODUCTION_CHECKLIST.md) - Pre-deployment verification
- [Scripts README](scripts/README.md) - Deployment script documentation

### Monitoring & Observability

**Application Monitoring** (Langfuse):
- Real-time agent tracing
- Token usage tracking
- Performance metrics
- Quality monitoring

**Infrastructure Monitoring**:
```bash
# Set up monitoring for your cloud provider
./scripts/monitoring/setup-monitoring.sh aws   # or gcp, azure, prometheus

# Run health checks
./scripts/monitoring/health-check.sh
```

See [Monitoring Guide](docs/MONITORING_GUIDE.md) for complete monitoring setup.

### Backup & Disaster Recovery

**Automated backups:**
```bash
# Manual backup
./scripts/backup/backup-chroma.sh

# Restore from backup
./scripts/backup/restore-chroma.sh /path/to/backup.tar.gz

# Set up daily backups (cron)
0 2 * * * /app/scripts/backup/backup-chroma.sh
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `LLM_PROVIDER` | LLM provider (`ollama` or `groq`) | `ollama` | Yes |
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` | If using Ollama |
| `OLLAMA_MODEL` | Ollama model name | `deepseek-coder:6.7b` | If using Ollama |
| `GROQ_API_KEY` | Groq API key | - | If using Groq |
| `GROQ_REASONING_MODEL` | Groq model for reasoning | `llama-3.3-70b-versatile` | If using Groq |
| `GROQ_CODE_MODEL` | Groq model for code gen | `llama-3.3-70b-versatile` | If using Groq |
| `GROQ_GENERAL_MODEL` | Groq model for general tasks | `llama-3.3-70b-versatile` | If using Groq |
| `EMBEDDING_MODEL` | Sentence transformer model | `all-MiniLM-L6-v2` | No |
| `CHROMA_PERSIST_DIR` | ChromaDB storage path | `./data/chroma_db` | No |

### Switching LLM Providers

See [docs/LLM_PROVIDER_GUIDE.md](docs/LLM_PROVIDER_GUIDE.md) for detailed instructions.

**Quick switch to Groq for faster testing:**

```bash
# In .env file
LLM_PROVIDER=groq
GROQ_API_KEY=your_api_key_here
```

**Switch back to Ollama for privacy:**

```bash
# In .env file
LLM_PROVIDER=ollama
```

Restart the application after changing providers.

## 🎯 Advanced Features

### Conversation Context

The assistant maintains intelligent conversation history:
- **Short conversations** (<6 exchanges): Full history
- **Long conversations** (>6 exchanges): First 3 + summary + last 3
- Automatically summarizes middle exchanges for efficiency

### Multi-Language Code Generation

Request code in multiple languages simultaneously:

> "Generate Python and JavaScript code to fetch all users"

Supported languages:
- Python (template-based)
- JavaScript / TypeScript (LLM-generated)
- Java, C#, Go, Ruby, PHP, Rust, Swift (LLM-generated)

### Agent-Specific Models (Groq only)

When using Groq, different agents use optimized models:
- **Query Analyzer**: Reasoning model for intent classification
- **Code Generator**: Code-optimized model
- **RAG Agent**: General model for synthesis
- **Doc Analyzer**: Reasoning model for analysis

## 📊 Performance

| Metric | Ollama (Local) | Groq (Cloud) |
|--------|----------------|--------------|
| Speed | 2-5 tokens/sec | 50-100 tokens/sec |
| Privacy | ✅ Fully private | ⚠️ Cloud API |
| Cost | Free | Free tier available |
| Offline | ✅ Yes | ❌ No |

## 🗺️ Development Roadmap

- [x] **Phase 1**: RAG Foundation (Days 1-7)
  - OpenAPI parsing
  - Vector storage
  - Basic RAG pipeline
  - Individual agents

- [x] **Phase 2**: Multi-Agent System (Days 8-14)
  - Supervisor orchestration with LangGraph
  - Multi-agent coordination
  - Real-time UI updates
  - LLM provider switching
  - Comprehensive testing (271 tests)

- [x] **Phase 3**: Production Hardening (Days 15-20)
  - ✅ Error handling & recovery
  - ✅ Structured logging & observability
  - ✅ Docker & production deployment
  - ✅ Performance optimization & caching (50-80% faster)
  - ✅ Security & input validation
  - ✅ Cloud deployment scripts (AWS, GCP, Azure, DigitalOcean)
  - ✅ Backup & disaster recovery
  - ✅ Monitoring & alerting

- [ ] **Phase 4**: Advanced Features
  - Postman collection import
  - API testing capabilities
  - Collaborative features
  - Multi-modal support

## 🐛 Troubleshooting

### Ollama Issues

**Connection refused:**
```bash
# Make sure Ollama is running
ollama serve

# Check if model is available
ollama list
```

**Model not found:**
```bash
ollama pull deepseek-coder:6.7b
```

### Groq Issues

**API key not set:**
```bash
# Add to .env
GROQ_API_KEY=your_key_here
```

**Model not found:**
- Check [Groq docs](https://console.groq.com/docs/models) for available models
- Update model name in `.env`

### General Issues

**Import errors:**
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

**ChromaDB errors:**
```bash
# Clear database and restart
rm -rf data/chroma_db
uvicorn src.api.app:app --reload --port 8000
```

## 📚 Documentation

Comprehensive guides and documentation:

- **[Search Guide](docs/SEARCH_GUIDE.md)** - Understanding search modes and query expansion
- **[LLM Provider Guide](docs/LLM_PROVIDER_GUIDE.md)** - Switching between Ollama and Groq
- **[Agent Architecture](docs/AGENT_ARCHITECTURE.md)** - Multi-agent system design
- **[CLI Guide](CLI_GUIDE.md)** - Complete CLI command reference
- **[Testing Guide](TESTING_GUIDE.md)** - Running and writing tests
- **[Production Deployment](PRODUCTION_DEPLOYMENT.md)** - Deploy to production
- **[Docker Deployment](DOCKER_DEPLOYMENT.md)** - Docker and docker-compose setup

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

```bash
# Clone repo
git clone <your-repo-url>
cd api-assistant

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dev dependencies
pip install -r requirements.txt
pip install pytest pytest-asyncio black ruff

# Run tests
pytest -v

# Format code
black src/ tests/
ruff check src/ tests/
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [LangGraph](https://langchain.com/langgraph) for multi-agent orchestration
- [Ollama](https://ollama.com/) for local LLM inference
- [Groq](https://groq.com/) for lightning-fast cloud inference
- [ChromaDB](https://www.trychroma.com/) for vector storage
- [Next.js](https://nextjs.org/) & [React](https://react.dev/) for modern web frontend
- [FastAPI](https://fastapi.tiangolo.com/) for high-performance REST API
- [Langfuse](https://langfuse.com/) for LLM observability

---

**Built with ❤️ for developers who integrate APIs**
