# Enterprise API Integration Assistant - Project Context

## Document Purpose
This document provides complete context for the Enterprise API Integration Assistant project, enabling seamless continuation of development in Claude Code or Claude Projects. It contains all requirements, decisions, specifications, and implementation details from the initial planning through current development.

---

## 1. Project Overview

### Problem Statement
Developers spend excessive time understanding and integrating various enterprise APIs.

### Solution
An AI-powered assistant that helps understand, document, and generate code for API integrations.

### MVP Core Features
1. AI assistant for API understanding and code generation
2. Code-snippet analysis
3. Documentation-gap identification
4. User-query pattern analysis
5. Automatic-update suggestions

### Dataset Reference
- Kaggle Ultimate API Dataset (1000 data sources)
- URL: https://www.kaggle.com/datasets/shivd24coder/ultimate-api-dataset-1000-data-sources

---

## 2. Developer Profile

### Background
- **Name**: Chetan
- **Primary Expertise**: Senior Sitecore Developer (.NET, C#)
- **Framework Experience**: Sitecore 10.x, .NET Framework 4.8.1, MVC architecture
- **Learning Goals**: Python, AI/ML development, React JS, Vue JS
- **Project Role**: Individual developer building MVP

### Development Preferences
- Follow best practices in coding
- Adhere to design principles and industrial standards
- Cost-effective solutions (free/open-source preferred)
- Clean architecture patterns

---

## 3. System Specifications

### Hardware
| Component | Specification |
|-----------|---------------|
| **Machine** | Dell Inspiron 5593 |
| **OS** | Windows 11 Pro (25H2), Build 26200.7462 |
| **RAM** | 16 GB (15.8 GB usable) |
| **System Type** | 64-bit, x64-based processor |
| **GPU (Dedicated)** | NVIDIA GeForce MX230 (2GB VRAM) |
| **GPU (Integrated)** | Intel Iris Plus Graphics |

### GPU Considerations
- MX230's 2GB VRAM is insufficient for loading LLMs on GPU
- Solution: CPU-only inference mode for Ollama
- Performance: ~5-8 tokens/second (acceptable for development)

---

## 4. Installed Software & Versions

### Core Development Tools
| Software | Version | Purpose |
|----------|---------|---------|
| **Python** | 3.13.7 | Primary language |
| **Git** | 2.49.0.windows.1 | Version control |
| **VS Code** | 1.107.1 | IDE |
| **Docker Desktop** | 28.3.2 (build 578ccf6) | Containerization |

### VS Code Extensions
- Python
- Pylance
- Python Debugger

### AI/LLM Tools
| Tool | Version/Model | Notes |
|------|---------------|-------|
| **Ollama** | 0.13.5 | Local LLM inference |
| **DeepSeek Coder** | 6.7b | Primary code generation model |
| **Phi3 Mini** | - | Alternative smaller model |
| **Gemma3** | 1b (815 MB) | Lightweight backup |

### Other Tools
- Postman (API testing)

---

## 5. Technical Architecture Decisions

### Chosen Tech Stack
| Layer | Technology | Rationale |
|-------|------------|-----------|
| **UI** | Streamlit | Rapid development, Python-native |
| **LLM Orchestration** | LangGraph | Production-ready, excellent RAG integration |
| **Vector Database** | ChromaDB | Simple setup, sufficient for MVP scale |
| **Embeddings** | Sentence-Transformers (all-MiniLM-L6-v2) | Free, local, 384 dimensions |
| **Local LLM** | Ollama + DeepSeek Coder 6.7B | Free, privacy-preserving |
| **Cloud Fallback** | Groq API (optional) | Free tier: 100K tokens/day |

### Architecture Pattern
- **Modular Monolith** for MVP (simpler deployment, faster iteration)
- **Supervisor/Worker Agent Pattern** for Phase 2
- **RAG Pipeline**: Query → Embedding → ChromaDB Search → Context Assembly → LLM Generation

### Why These Choices?
1. **ChromaDB over Qdrant**: Simpler setup for MVP, upgrade path exists
2. **Ollama over Cloud APIs**: Zero cost, works offline, privacy
3. **Streamlit over React**: Faster development, Python-only stack
4. **all-MiniLM-L6-v2**: Good quality, small size (~80MB), fast inference

---

## 6. Project Structure

```
C:\Users\cheta\Desktop\GenAI\Projects\api-assistant\
├── .env                      # Environment variables (not in git)
├── .env.example              # Environment template
├── .gitignore                # Git ignore rules
├── requirements.txt          # Python dependencies
├── README.md                 # Project documentation
├── pyproject.toml            # Modern Python project config
├── run.py                    # Launcher script (handles PYTHONPATH)
├── PROJECT_CONTEXT.md        # This file
├── PROJECT_ROADMAP.md        # Day-by-day development plan
├── QUICK_CHECKLIST.md        # Quick reference checklist
│
├── src/
│   ├── __init__.py
│   ├── config.py             # Pydantic settings management
│   ├── main.py               # Streamlit entry point
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── embeddings.py     # Sentence-transformers service
│   │   ├── vector_store.py   # ChromaDB operations
│   │   └── llm_client.py     # Ollama client with streaming
│   │
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── base_parser.py    # Parser interface & data models
│   │   └── openapi_parser.py # OpenAPI 3.x & Swagger 2.0 parser
│   │
│   ├── agents/               # Phase 2: LangGraph agents
│   │   ├── __init__.py       # ✅ Updated with exports
│   │   ├── state.py          # ✅ NEW: Shared state definitions
│   │   └── base_agent.py     # ✅ NEW: Base agent interface
│   │
│   └── ui/
│       ├── __init__.py
│       ├── chat.py           # Chat interface component
│       └── sidebar.py        # Settings & file upload
│
├── data/
│   ├── chroma_db/            # Vector database storage
│   └── uploads/              # User uploaded files
│   └── samples/
│       └── petstore-api.json # Sample API spec for testing
│
├── tests/
│   ├── __init__.py
│   └── test_agents/          # ✅ NEW: Agent tests
│       ├── __init__.py
│       └── test_foundation.py # ✅ NEW: Day 1 tests
│
└── docker/
    ├── Dockerfile            # Multi-stage build
    └── docker-compose.yml    # Full stack deployment
```

---

## 7. Key Dependencies (requirements.txt)

```
# Core Framework
streamlit>=1.28.0
python-dotenv>=1.0.0

# LLM & Embeddings
langchain>=0.3.0
langchain-community>=0.3.0
langchain-core>=0.3.0
langgraph>=0.2.0
sentence-transformers>=2.2.0

# Vector Database
chromadb>=0.4.0

# Ollama Integration
ollama>=0.3.0

# OpenAPI Parsing
prance>=23.6.0
openapi-spec-validator>=0.7.0
PyYAML>=6.0

# HTTP & Async
httpx>=0.25.0
aiohttp>=3.9.0

# Data Processing
pandas>=2.0.0
pydantic>=2.0.0
pydantic-settings>=2.0.0

# Utilities
tenacity>=8.2.0
structlog>=23.1.0

# Development
pytest>=7.4.0
pytest-asyncio>=0.21.0
```

---

## 8. Implementation Progress

### Completed (Phase 1: RAG Foundation) ✅
- [x] Project structure created
- [x] Virtual environment setup
- [x] All dependencies installed
- [x] ChromaDB vector store implementation
- [x] Sentence-transformers embedding service
- [x] OpenAPI/Swagger parser (supports 2.0 & 3.x)
- [x] Ollama LLM client with streaming
- [x] Streamlit chat interface
- [x] File upload and processing
- [x] Basic RAG pipeline working
- [x] Sample PetStore API spec included
- [x] Docker configuration prepared

### In Progress (Phase 2: Agent Layer) 🔄
#### Day 1 - Completed ✅ (December 25, 2024)
- [x] LangGraph foundation setup
- [x] Created `src/agents/state.py`:
  - `QueryIntent` enum (6 intent types)
  - `AgentState` TypedDict for LangGraph
  - `IntentAnalysis`, `RetrievedDocument`, `SourceCitation` Pydantic models
  - `AgentMessage`, `AgentError` models
  - Helper functions: `create_initial_state()`, `add_to_processing_path()`, `set_error()`
- [x] Created `src/agents/base_agent.py`:
  - `BaseAgent` abstract class with `__call__` for LangGraph
  - `PassThroughAgent` for testing
  - `AgentRegistry` for centralized management
  - Automatic error handling and logging
- [x] Updated `src/agents/__init__.py` with exports
- [x] Created `tests/test_agents/test_foundation.py` (230 lines of tests)

#### Day 2-14 - Pending
- [ ] Query Analyzer agent (intent classification)
- [ ] RAG Agent enhancement (citations, multi-query)
- [ ] Code Generator agent (templates)
- [ ] Documentation Analyzer agent
- [ ] Supervisor/Orchestrator agent
- [ ] Langfuse monitoring integration
- [ ] UI updates for agent activity

### Pending (Phase 3: Production Hardening)
- [ ] Docker Compose deployment tested
- [ ] Error handling with circuit breakers
- [ ] Deploy to HuggingFace Spaces or Railway
- [ ] Semantic caching implementation

---

## 9. Issues Encountered & Solutions

### Issue 1: Ollama Memory Errors
**Error**: `model requires more system memory (2.3 GiB) than is available (1.9 GiB)`

**Root Cause**: Other applications consuming RAM

**Solution**: Close Chrome, Docker Desktop, and other memory-heavy apps before running Ollama

---

### Issue 2: CUDA Buffer Allocation Error
**Error**: `unable to allocate CUDA0 buffer`

**Root Cause**: MX230's 2GB VRAM insufficient for 6.7B model

**Initial Attempt**: Set `CUDA_VISIBLE_DEVICES=-1` to force CPU mode

**Final Solution**: Simply restart Ollama after system restart - it auto-detects and uses CPU when GPU memory is insufficient

---

### Issue 3: Python Module Import Error
**Error**: `ModuleNotFoundError: No module named 'src'`

**Root Cause**: Python path not including project root

**Solution**: Set PYTHONPATH before running Streamlit:
```powershell
$env:PYTHONPATH = "."; streamlit run src/main.py
```

**Permanent Fix**: Created `run.py` launcher script that handles path automatically

---

### Issue 4: Message Type Mismatch
**Error**: `AttributeError: 'dict' object has no attribute 'role'`

**Root Cause**: Example questions stored as dicts, but `render_message()` expected Message objects

**Solution**: Updated `chat.py` to handle both dict and Message object formats using `isinstance()` check

---

## 10. Running the Application

### Prerequisites
1. Ollama running with DeepSeek Coder model
2. Virtual environment activated

### Start Commands
```powershell
# Terminal 1: Start Ollama (if not running as service)
ollama serve

# Terminal 2: Run the application
cd C:\Users\cheta\Desktop\GenAI\Projects\api-assistant
.\venv\Scripts\Activate.ps1
$env:PYTHONPATH = "."; streamlit run src/main.py

# Alternative using run.py
python run.py
```

### Access
- Local URL: http://localhost:8501
- Network URL: http://192.168.1.3:8501

### Run Tests
```powershell
# Run all tests
pytest tests/ -v

# Run agent foundation tests
pytest tests/test_agents/test_foundation.py -v
```

---

## 11. GitHub Repository

- **Repository**: https://github.com/cutture/Api-Assistant.git
- **Branch**: main
- **Status**: Phase 2 Day 1 complete

### Recent Commits
```
- Initial commit: API Integration Assistant MVP (Phase 1)
- Day 1: LangGraph foundation - state schema and base agent (Phase 2)
```

---

## 12. Planned Enhancements (Roadmap)

### Phase 2: Agent Layer (Current - Day 1 Complete)
1. ✅ LangGraph foundation with state management
2. Query Analyzer agent (intent classification) - Day 2
3. RAG Agent with citations - Day 3
4. Code Generator with templates - Days 4-5
5. Documentation Analyzer - Day 6
6. Supervisor/Orchestrator - Days 8-9
7. Langfuse monitoring - Day 10

### Phase 3: Production Hardening
1. Docker Compose deployment
2. Circuit breaker pattern for error handling
3. Semantic caching with GPTCache
4. Deploy to HuggingFace Spaces (free GPU)

### Phase 4: Advanced Features
1. Hybrid search (vector + BM25 keyword)
2. Re-ranking with bge-reranker
3. Multiple API spec format support (GraphQL, Postman)
4. CLI tool with Typer
5. Mermaid diagram generation

### Future Considerations
1. Multimodal support (image understanding)
2. MCP (Model Context Protocol) integration
3. VS Code extension
4. Multi-user collaboration

---

## 13. Cost Estimates

### Current (MVP - Local)
| Component | Cost |
|-----------|------|
| Compute | $0 (local) |
| LLM | $0 (Ollama) |
| Storage | $0 (local ChromaDB) |
| **Total** | **$0/month** |

### Planned (Cloud Deployment)
| Component | Estimated Cost |
|-----------|----------------|
| HuggingFace Spaces | $0-9/month |
| Groq API (backup) | $0 (free tier) |
| Domain (optional) | ~$12/year |
| **Total** | **$0-20/month** |

---

## 14. Key Code Patterns

### Configuration Management (Pydantic Settings)
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "deepseek-coder:6.7b"
    chroma_persist_dir: str = "./data/chroma_db"
    
    model_config = SettingsConfigDict(env_file=".env")
```

### Singleton Pattern (Embedding Service)
```python
class EmbeddingService:
    _instance = None
    _model = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

### Agent State Pattern (NEW - Phase 2)
```python
from typing import TypedDict

class AgentState(TypedDict, total=False):
    query: str
    intent_analysis: Optional[dict]
    retrieved_documents: list[dict]
    response: str
    sources: list[dict]
    processing_path: list[str]
    error: Optional[dict]
```

### Base Agent Pattern (NEW - Phase 2)
```python
class BaseAgent(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @abstractmethod
    def process(self, state: AgentState) -> AgentState:
        pass
    
    def __call__(self, state: AgentState) -> AgentState:
        # Automatic error handling and logging
        state = add_to_processing_path(state, self.name)
        return self.process(state)
```

### RAG Pipeline Flow
```
User Query
    ↓
Embed Query (all-MiniLM-L6-v2)
    ↓
Search ChromaDB (top-k results)
    ↓
Build Context from Results
    ↓
Construct Prompt (system + context + query)
    ↓
Stream Response from Ollama
    ↓
Display in Streamlit Chat
```

---

## 15. Environment Variables

```env
# LLM Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-coder:6.7b

# Embeddings
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Vector Database
CHROMA_PERSIST_DIR=./data/chroma_db
CHROMA_COLLECTION_NAME=api_docs

# Optional: Cloud Fallback
GROQ_API_KEY=your_key_here

# Application
DEBUG=false
LOG_LEVEL=INFO
```

---

## 16. Testing the Application

### Manual Test Steps
1. Start the application
2. Upload `data/samples/petstore-api.json`
3. Click "Process Files"
4. Verify "9 documents indexed" message
5. Ask: "What endpoints are available?"
6. Ask: "Generate Python code to create a new pet"
7. Ask: "How do I authenticate?"

### Unit Test Steps (NEW - Phase 2)
```powershell
# Run agent foundation tests
pytest tests/test_agents/test_foundation.py -v

# Expected: All tests pass (20+ tests)
```

### Expected Behavior
- Streaming responses from Ollama
- Relevant context retrieved from ChromaDB
- Python code blocks with syntax highlighting
- ~5-10 second response time on CPU

---

## 17. Useful Commands Reference

### Virtual Environment
```powershell
# Create
python -m venv venv

# Activate (PowerShell)
.\venv\Scripts\Activate.ps1

# Deactivate
deactivate
```

### Ollama
```powershell
# List models
ollama list

# Pull model
ollama pull deepseek-coder:6.7b

# Run model
ollama run deepseek-coder:6.7b "Hello"

# Serve (if not running as service)
ollama serve
```

### Streamlit
```powershell
# Run with PYTHONPATH
$env:PYTHONPATH = "."; streamlit run src/main.py

# Clear cache
streamlit cache clear
```

### Git
```powershell
git status
git add .
git commit -m "message"
git push origin main
```

### Pytest
```powershell
# Run all tests
pytest tests/ -v

# Run specific file
pytest tests/test_agents/test_foundation.py -v

# Run with coverage
pytest tests/ -v --cov=src
```

---

## 18. Contact & Resources

### Project Repository
https://github.com/cutture/Api-Assistant.git

### Key Documentation Links
- Streamlit: https://docs.streamlit.io/
- LangChain: https://python.langchain.com/docs/
- LangGraph: https://langchain-ai.github.io/langgraph/
- ChromaDB: https://docs.trychroma.com/
- Ollama: https://ollama.com/
- Sentence Transformers: https://www.sbert.net/

---

## Document Version
- **Created**: December 24, 2025
- **Last Updated**: December 25, 2024
- **Phase**: Phase 2 In Progress (Day 1 Complete)
- **Next Milestone**: Query Analyzer Agent (Day 2)
