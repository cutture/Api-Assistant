# CLAUDE.md - Project Reference for Claude AI

This file provides Claude with context about the Intelligent Coding Agent project for efficient assistance.

---

## Basic Rules to Follow for Development

1. **Think First, Read Code:** Always think through the problem first and read the codebase for relevant files before making changes.

2. **Verify Major Changes:** Before making any major changes, check in with the user to verify the plan.

3. **Explain Changes:** At every step, provide a high-level explanation of what changes were made.

4. **Keep It Simple:** Make every task and code change as simple as possible. Avoid massive or complex changes. Every change should impact as little code as possible. Simplicity is paramount.

5. **Maintain Architecture Documentation:** Keep a documentation file that describes how the architecture of the app works inside and out. See `docs/planning/02-implementation-plan.md` for current architecture.

6. **No Speculation:** Never speculate about code you have not opened. If a specific file is referenced, you MUST read it before answering. Investigate and read relevant files BEFORE answering questions about the codebase. Never make claims about code without investigating first - provide grounded, hallucination-free answers.

7. **Update Documentation During Implementation:** After each implementation step, update CLAUDE.md to reflect the current state. Also verify and update these documents as needed:
   - `docs/planning/02-implementation-plan.md` - Mark completed phases/tasks
   - `README.md` - Update if user-facing features change
   - `GOOGLE_CLOUD_RUN_DEPLOYMENT.md` - Update if deployment changes
   - `env.example.yaml` - Update if new environment variables added

---

## Project Overview

**Intelligent Self-Validating Coding Agent** - An AI-powered coding assistant that generates, executes, validates, and delivers production-ready code through an iterative refinement loop with container-based execution.

**Version:** 2.0.0 (In Development)
**Status:** Transforming from API Assistant to Coding Agent
**Previous:** API Integration Assistant v1.0.0

### Key Capabilities
- Multi-language code generation (Python, JS, TS, Java, Go, C#)
- Container-based code execution with automated testing
- Self-validating loop (5 retries with multi-signal validation)
- Artifact management (uploads, generated files, downloadable outputs)
- GitHub integration (read-only for context, PR-only in v2)
- Cost-optimized LLM routing (Ollama → Groq → Premium)
- Three output modes: inline snippets, ZIP bundles, GitHub PRs
- Persistent chat sessions with execution history

### Transformation Notes (Phase 1 Complete)
**Removed Backend Features:**
- Mermaid diagram generation (`src/diagrams/` module removed)
- Document analyzer agent (`doc_analyzer.py` removed)
- Gap analysis agent (`gap_analysis_agent.py` removed)
- Result diversification module (`result_diversification.py` removed)
- Document management endpoints (upload, CRUD, bulk-delete)
- Faceted search endpoint

**Removed Frontend Features:**
- Diagrams page and components (`/diagrams` route)
- Search page and components (`/search` route)
- Document management page (`/` was documents, now redirects to chat)
- Document components (uploader, list, stats)
- Search-related stores and hooks
- Diagram-related stores and hooks

**Backend Features Kept:**
- Basic search endpoint (for RAG agent)
- Session management endpoints
- Chat endpoint with file upload support
- Authentication endpoints
- Parsers (minimal, for chat file uploads)
- Advanced filtering (for vector store search)

**Frontend Features Kept:**
- Chat page (now the main landing page)
- Sessions page
- Settings page
- Login/Register/Auth pages
- Navigation updated to "Coding Agent" branding

**Repurposed:**
- ChromaDB: Now stores code context (artifacts coming in Phase 2)
- Sessions: Will include execution history in Phase 2
- RAG Agent: Now retrieves code context

### Transformation Notes (Phase 2 Complete)
**New Backend Features:**
- Database tables for code execution (Artifact, CodeExecution, ExecutionAttempt)
- LLM Router service (`src/core/llm_router.py`) for cost-optimized routing
- Enhanced Code Generator agent (`src/agents/code_generator.py`)
- Test Generator agent (`src/agents/test_generator.py`)
- Validation Loop orchestrator (`src/agents/validator.py`)
- Execute API endpoints (`/execute/*`)
- Execution Service (`src/services/execution_service.py`) for local/Cloud Run execution

**New Frontend Features:**
- CodePanel component for displaying generated code
- ExecutionStatus component for showing execution progress
- Executions API client

**Config Changes:**
- Added execution settings (max_retries, timeout, daily_limit)
- Added artifact storage settings
- Added Cloud Run Jobs configuration

### Transformation Notes (Phase 3 Complete)
**New Backend Services:**
- Artifact Service (`src/services/artifact_service.py`) - Storage abstraction for local/GCS
- ZIP Service (`src/services/zip_service.py`) - Bundle generation for code downloads
- Cleanup Service (`src/services/cleanup_service.py`) - Scheduled cleanup for expired artifacts
- Artifacts API Router (`src/api/artifact_router.py`) - /artifacts/* endpoints

**New Frontend Features:**
- ArtifactList component - Displays and manages user artifacts
- ArtifactUpload component - Drag-and-drop file upload
- Artifacts page (`/artifacts`) - Full artifact management UI
- ZIP download functionality in CodePanel
- Missing UI components: Collapsible, Progress, Table

**New Dependencies:**
- Frontend: jszip for client-side ZIP creation
- Frontend: @radix-ui/react-collapsible, @radix-ui/react-progress

**API Endpoints Added:**
- POST /artifacts/upload - Upload artifacts
- GET /artifacts - List artifacts with filtering
- GET /artifacts/{id} - Get artifact metadata
- GET /artifacts/{id}/download - Download artifact file
- DELETE /artifacts/{id} - Delete artifact

### Transformation Notes (Phase 4 Complete)
**New Backend Services:**
- Diff Service (`src/services/diff_service.py`) - Code comparison with unified/HTML diff
- Sandbox Service (`src/services/sandbox_service.py`) - Playwright-based screenshots and UI testing
- Preview Service (`src/services/preview_service.py`) - Live preview server management

**New API Routers:**
- Sandbox Router (`src/api/sandbox_router.py`) - /sandbox/* endpoints
- Preview Router (`src/api/preview_router.py`) - /preview/* endpoints

**New Frontend Features:**
- DiffViewer component - Unified/split view code diff display
- PreviewPanel component - Live preview with iframe embedding
- Sandbox API client - Screenshot and UI test API calls
- Preview API client - Preview session management

**API Endpoints Added:**
- POST /sandbox/screenshot - Take screenshot of URL
- POST /sandbox/test-ui - Run UI tests on URL
- POST /preview - Start preview server
- GET /preview/{id} - Get preview status
- DELETE /preview/{id} - Stop preview
- GET /preview - List user previews
- GET /preview/stats - Preview service stats
- POST /preview/cleanup - Clean expired previews

---

## Tech Stack

### Backend
- **Framework:** FastAPI (Python 3.11)
- **AI/ML:** LangChain, LangGraph (multi-agent), Sentence Transformers
- **Vector DB:** ChromaDB with hybrid search (BM25 + semantic)
- **LLM Providers:** Groq (cloud) or Ollama (local)
- **Search:** Cross-encoder re-ranking, query expansion, result diversification

### Frontend
- **Framework:** Next.js 16 with App Router
- **UI:** React 19, TypeScript, Tailwind CSS, Radix UI
- **State:** React Query (server), Zustand (UI)
- **HTTP:** Axios with retry logic

### Infrastructure
- **Container:** Docker multi-stage build
- **Backend Hosting:** Google Cloud Run (asia-east1)
- **Frontend Hosting:** Vercel
- **CI/CD:** Google Cloud Build (auto-deploy on push to main)
- **Storage:** Google Cloud Storage with FUSE mount for ChromaDB persistence

---

## Directory Structure

```
Api-Assistant/
├── src/                      # Backend (Python)
│   ├── api/                  # FastAPI routes & models
│   │   ├── app.py           # Main app (entry point)
│   │   ├── models.py        # Pydantic request/response models
│   │   ├── auth.py          # JWT/API key authentication middleware
│   │   └── auth_router.py   # Authentication endpoints (/auth/*)
│   ├── auth/                # Authentication services
│   │   ├── password.py      # Password hashing (bcrypt)
│   │   ├── jwt.py           # JWT token handling
│   │   ├── user_service.py  # User CRUD operations
│   │   └── oauth.py         # Google OAuth implementation
│   ├── database/            # SQLAlchemy database
│   │   ├── models.py        # User, OAuthAccount, Token models
│   │   └── connection.py    # Database connection setup
│   ├── agents/              # LangGraph multi-agent system
│   │   ├── supervisor.py    # Agent orchestrator
│   │   ├── query_analyzer.py
│   │   ├── rag_agent.py
│   │   ├── code_agent.py
│   │   ├── doc_analyzer.py
│   │   └── state.py         # Shared agent state
│   ├── core/                # Core services
│   │   ├── vector_store.py  # ChromaDB wrapper
│   │   ├── hybrid_search.py # BM25 + vector fusion
│   │   ├── cross_encoder.py # Re-ranking
│   │   ├── embeddings.py    # Sentence transformers
│   │   └── llm_client.py    # LLM abstraction
│   ├── parsers/             # Document parsers
│   │   ├── openapi_parser.py
│   │   ├── graphql_parser.py
│   │   ├── postman_parser.py
│   │   ├── pdf_parser.py
│   │   └── format_handler.py # Auto-detection
│   ├── diagrams/            # Mermaid diagram generation
│   ├── sessions/            # Session management
│   ├── services/            # Supporting services
│   └── config.py            # Settings (Pydantic)
├── frontend/                # Next.js frontend
│   ├── src/
│   │   ├── app/            # Pages (chat, search, sessions, diagrams)
│   │   │   ├── login/      # Login page with OAuth
│   │   │   ├── register/   # Registration page
│   │   │   └── auth/callback/ # OAuth callback handler
│   │   ├── components/     # React components
│   │   ├── hooks/          # React Query hooks
│   │   ├── lib/
│   │   │   ├── api/        # API clients with JWT
│   │   │   └── contexts/   # AuthContext for auth state
│   │   └── stores/         # Zustand stores
│   └── e2e/                # Playwright tests
├── tests/                   # Backend tests (831+ tests)
├── data/                    # ChromaDB + SQLite storage
├── Dockerfile              # Multi-stage Docker build
├── cloudbuild.yaml         # Cloud Build CI/CD
├── requirements.txt        # Python dependencies
└── env.example.yaml        # Environment template
```

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `src/api/app.py` | FastAPI app entry point, all routes |
| `src/api/auth.py` | JWT and API key authentication middleware |
| `src/api/auth_router.py` | Authentication API endpoints (/auth/*) |
| `src/config.py` | Environment configuration (Pydantic Settings) |
| `src/agents/supervisor.py` | LangGraph agent orchestrator |
| `src/core/vector_store.py` | ChromaDB vector store operations |
| `src/database/models.py` | SQLAlchemy User and OAuth models |
| `src/auth/user_service.py` | User CRUD and authentication logic |
| `frontend/src/lib/api/client.ts` | Axios API client with JWT interceptors |
| `frontend/src/lib/contexts/AuthContext.tsx` | React auth state management |
| `Dockerfile` | Production Docker image |
| `cloudbuild.yaml` | Cloud Build CI/CD pipeline |
| `env.example.yaml` | Environment variables template |

---

## API Endpoints

### Health & Stats
- `GET /health` - Health check
- `GET /stats` - Collection statistics

### Documents
- `POST /documents/upload` - Upload files (multipart)
- `POST /documents` - Add documents (JSON)
- `GET /documents/{id}` - Get document
- `DELETE /documents/{id}` - Delete document
- `POST /documents/bulk-delete` - Bulk delete

### Search
- `POST /search` - Hybrid search (modes: vector, hybrid, reranked)
- `POST /search/faceted` - Faceted search with aggregations

### Chat
- `POST /chat` - AI chat with RAG, file uploads, URL scraping

### Authentication
- `POST /auth/register` - Create new user account
- `POST /auth/login` - Login with email/password
- `POST /auth/logout` - Logout (client-side token deletion)
- `POST /auth/refresh` - Refresh JWT access token
- `GET /auth/me` - Get current user profile
- `GET /auth/password-requirements` - Get password rules
- `POST /auth/verify-email` - Verify email with token
- `POST /auth/resend-verification` - Resend verification email
- `GET /auth/oauth/google` - Initiate Google OAuth
- `GET /auth/oauth/google/callback` - Google OAuth callback
- `POST /auth/guest` - Create guest session

### Sessions
- `POST /sessions` - Create session (auto-links to authenticated user)
- `GET /sessions` - List sessions (filtered by user if authenticated)
- `GET /sessions/{id}` - Get session
- `PATCH /sessions/{id}` - Update session
- `DELETE /sessions/{id}` - Delete session
- `POST /sessions/{id}/activate` - Reactivate expired session
- `POST /sessions/{id}/messages` - Add message
- `DELETE /sessions/{id}/messages` - Clear history

### Diagrams
- `POST /diagrams/sequence` - Sequence diagram
- `POST /diagrams/auth-flow` - Auth flow diagram
- `POST /diagrams/er` - ER diagram from GraphQL
- `POST /diagrams/overview` - API overview diagram

---

## Environment Variables

### Required
```bash
SECRET_KEY=<random-string>        # Session encryption
GROQ_API_KEY=<api-key>           # If using Groq LLM
```

### LLM Configuration
```bash
LLM_PROVIDER=groq                 # groq or ollama
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_REASONING_MODEL=llama-3.3-70b-versatile
GROQ_CODE_MODEL=llama-3.3-70b-versatile
GROQ_GENERAL_MODEL=llama-3.3-70b-versatile
```

### Storage & Search
```bash
CHROMA_PERSIST_DIR=/mnt/chroma_data/chroma_db  # Cloud Run with GCS
CHROMA_COLLECTION_NAME=api_docs
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### Security & CORS
```bash
ALLOWED_ORIGINS=https://your-frontend.vercel.app
REQUIRE_AUTH=false
API_KEYS=key1,key2               # Comma-separated
```

### Frontend (Vercel)
```bash
NEXT_PUBLIC_API_BASE_URL=https://your-backend.run.app
NEXT_PUBLIC_ENABLE_DEBUG=false
```

---

## Common Commands

### Local Development
```bash
# Backend
pip install -r requirements.txt
uvicorn src.api.app:app --reload --port 8000

# Frontend
cd frontend && npm install && npm run dev
```

### Testing
```bash
# Backend tests
pytest tests/ -v

# Frontend tests
cd frontend && npm test
cd frontend && npm run test:e2e
```

### Docker
```bash
docker build -t api-assistant:test .
docker run -p 8000:8000 -e SECRET_KEY=test api-assistant:test
```

### Google Cloud
```bash
# Deploy manually
gcloud run deploy api-assistant --image <image> --region asia-east1

# Update env vars
gcloud run services update api-assistant --region asia-east1 --update-env-vars "KEY=value"

# View logs
gcloud run services logs read api-assistant --region asia-east1 --limit 50

# Restart service
gcloud run services update api-assistant --region asia-east1 --update-labels="restart=true"
```

---

## Architecture Patterns

### Multi-Agent System (LangGraph)
```
User Query → Query Analyzer → Supervisor
                                  ↓
              ┌───────────────────┼───────────────────┐
              ↓                   ↓                   ↓
         RAG Agent          Code Agent         Doc Analyzer
              ↓                   ↓                   ↓
              └───────────────────┴───────────────────┘
                                  ↓
                           Final Response
```

### Hybrid Search Pipeline
```
Query → Query Expansion → BM25 Search ─┐
                       → Vector Search ─┼→ RRF Fusion → Re-ranking → Results
```

### Data Persistence (Cloud Run)
```
Upload → ChromaDB → /mnt/chroma_data → GCS FUSE → Cloud Storage Bucket
```

### User Authentication Flow
```
User → Login Page → Email/Password OR Google OAuth
           ↓
    Backend /auth/* endpoints
           ↓
    JWT Token Generation
           ↓
    Frontend stores tokens (localStorage)
           ↓
    API requests include Authorization: Bearer <token>
           ↓
    Backend validates JWT → Returns user-specific data
```

### Authentication Methods
| Method | Use Case | Token Type |
|--------|----------|------------|
| Email/Password | User registration & login | JWT (access + refresh) |
| Google OAuth | Social login | JWT (access + refresh) |
| API Key | CLI/Programmatic access | X-API-Key header |
| Guest | Anonymous access | JWT (guest token) |

---

## Deployment Architecture

```
GitHub (main branch)
        ↓ push
Cloud Build Trigger
        ↓
Build Docker Image → Push to Artifact Registry
        ↓
Deploy to Cloud Run (gen2, asia-east1)
        ↓
GCS Bucket mounted via FUSE for ChromaDB persistence

Vercel (auto-deploy on push)
        ↓
Frontend served globally via Vercel CDN
```

---

## Key Documentation

| Document | Purpose |
|----------|---------|
| `README.md` | Project overview and quick start |
| `GOOGLE_CLOUD_RUN_DEPLOYMENT.md` | Complete GCP deployment guide |
| `TESTING_GUIDE.md` | Testing procedures |
| `docs/AGENT_ARCHITECTURE.md` | Multi-agent system design |
| `docs/SEARCH_GUIDE.md` | Search modes and query expansion |
| `docs/LLM_PROVIDER_GUIDE.md` | LLM provider configuration |

---

## Troubleshooting Quick Reference

### CORS Errors
- Set `ALLOWED_ORIGINS` env var (not `FRONTEND_URL`)
- Example: `ALLOWED_ORIGINS=https://your-app.vercel.app`

### Data Not Persisting (Cloud Run)
1. Create GCS bucket
2. Grant IAM permissions to compute service account
3. Add volume mount: `--add-volume` and `--add-volume-mount`
4. Set `CHROMA_PERSIST_DIR=/mnt/chroma_data/chroma_db`

### Upload Failures
- Check CORS configuration
- Verify API key if `REQUIRE_AUTH=true`
- Check backend logs: `gcloud run services logs read api-assistant`

### Cloud Build Failures
- Ensure Cloud Build service account has `roles/run.admin` and `roles/iam.serviceAccountUser`

---

## Version History

- **v2.0.0** (Jan 2026) - Intelligent Self-Validating Coding Agent (in development)
  - Container-based code execution with Cloud Run Jobs
  - Artifact system replacing document management
  - GitHub integration (read-only)
  - LLM routing for cost optimization
  - ZIP bundle and snippet delivery

- **v1.0.0** (Dec 2025) - API Integration Assistant
  - Multi-agent system, hybrid search, Next.js frontend
  - Cloud Run + Vercel deployment
  - GCS FUSE for persistent storage

---

## Future Roadmap & Migration Triggers

This section documents planned features and the conditions that should trigger their implementation.

### Migration: Microservice Architecture

**Current State:** Extended multi-agent system (monolith)
**Target State:** Separate coding-agent microservice

**Trigger Conditions (implement when ANY occurs):**
1. Daily code executions exceed 500
2. Execution container costs exceed $100/month
3. Main API latency increases >200ms due to execution load
4. Need independent scaling of execution vs chat

**Implementation Reference:** See `docs/planning/02-implementation-plan.md` Section 8

---

### Feature: PR-Only Git Integration (v2)

**Current State:** Read-only repository access
**Target State:** Create branches and PRs with generated code

**Trigger Conditions (implement when ANY occurs):**
1. User requests reach 50+ for PR creation feature
2. Competitive pressure (other tools offer this)
3. Enterprise customer explicitly requires it

**Implementation Steps:**
1. Add 'repo' write scope to GitHub OAuth
2. Implement branch creation from generated code
3. Implement PR creation via GitHub API
4. Add PR preview and review UI in frontend
5. Add merge conflict detection and resolution hints

---

### Feature: GitLab & Bitbucket Support

**Current State:** GitHub only
**Target State:** GitLab, Bitbucket, and generic Git support

**Trigger Conditions:**
- GitLab: 20+ user requests OR enterprise customer requirement
- Bitbucket: Enterprise customer requirement
- Self-hosted Git: Enterprise/on-premise deployment need

**Implementation Steps:**
1. Abstract GitHubService to generic GitProvider interface
2. Implement GitLabProvider with OAuth and API
3. Implement BitbucketProvider with OAuth and API
4. Add provider selection dropdown in settings UI
5. Update RepoSelector component for multi-provider

---

### Feature: Premium LLM Tier (Claude/GPT-4)

**Current State:** Groq + Ollama only
**Target State:** Add Claude and GPT-4 for complex tasks

**Trigger Conditions:**
1. Complex task success rate falls below 80%
2. User feedback indicates quality issues on complex code
3. Enterprise customers require specific model support

**Implementation:**
1. Add Anthropic API client
2. Add OpenAI API client
3. Update LLM router for complexity > 6 tasks
4. Add user preference for premium models
5. Implement cost tracking and billing alerts

---

### Recommended Ollama Models

For local code generation, install these models:

```bash
# Primary (recommended)
ollama pull deepseek-coder-v2:16b    # Best quality/speed (12GB VRAM)

# Alternatives by VRAM
ollama pull qwen2.5-coder:7b          # 6GB VRAM - lightweight
ollama pull codellama:13b             # 10GB VRAM - good balance
ollama pull llama3.1:8b               # 6GB VRAM - fast general

# High-end (if available)
ollama pull codellama:34b             # 24GB VRAM - highest quality
```
