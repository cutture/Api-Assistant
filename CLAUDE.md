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

### Transformation Notes (Phase 5 Complete)
**New Backend Services:**
- Security Service (`src/services/security_service.py`) - Vulnerability scanning with pattern matching and Bandit
- Mock Service (`src/services/mock_service.py`) - API mock server management

**New API Routers:**
- Security Router (`src/api/security_router.py`) - /security/* endpoints
- Mock Router (`src/api/mock_router.py`) - /mocks/* endpoints

**New Frontend Features:**
- SecurityReport component - Vulnerability display with severity badges
- MockServerManager component - Mock server creation and management UI
- Security API client - Code and dependency scanning
- Mocks API client - Mock server CRUD operations

**Security Scanning Capabilities:**
- Pattern-based static analysis for Python, JavaScript, TypeScript, Java, Go, C#
- SQL injection, XSS, command injection, hardcoded secrets detection
- CWE and OWASP category mapping
- Bandit integration for Python (when available)
- npm audit and pip-audit for dependency scanning

**Mock Server Capabilities:**
- Create mock endpoints with custom responses
- Auto-generate CRUD endpoints from resource name
- Generate mocks from OpenAPI specifications
- Request logging and statistics
- Automatic expiration and cleanup

**API Endpoints Added:**
- POST /security/scan - Scan code for vulnerabilities
- POST /security/scan/dependencies - Scan package files
- GET /security/supported-languages - List supported languages
- POST /mocks - Create mock server
- GET /mocks - List mock servers
- GET /mocks/{id} - Get mock details
- PATCH /mocks/{id} - Update mock endpoints
- DELETE /mocks/{id} - Delete mock server
- POST /mocks/{id}/stop - Stop mock server
- GET /mocks/{id}/logs - Get request logs
- POST /mocks/generate/crud - Generate CRUD endpoints
- POST /mocks/generate/openapi - Generate from OpenAPI spec

### Transformation Notes (Phase 6 Complete)
**New Backend Services:**
- Template Service (`src/services/template_service.py`) - Code template library with built-in templates
- Quality Service (`src/services/quality_service.py`) - Code quality scoring algorithm

**New API Routers:**
- Template Router (`src/api/template_router.py`) - /templates/* endpoints

**New Frontend Features:**
- TemplateSelector component - Template browsing, filtering, and rendering UI
- QualityScore component - Quality score visualization with detailed metrics
- Templates API client - Template CRUD and rendering

**Template Library Features:**
- Built-in templates for REST API, Authentication, Database models, Testing
- Support for Python, JavaScript, TypeScript, Java, Go, C#
- Template parameters with placeholders ({{param}})
- Custom template creation by users
- Template usage tracking

**Quality Score Features:**
- Multi-factor quality scoring (0-100)
- Complexity metrics (cyclomatic complexity, nesting depth, function length)
- Documentation coverage analysis
- Test coverage estimation
- Integration with lint and security scan results
- Actionable recommendations

**API Endpoints Added:**
- GET /templates - List templates with filtering
- GET /templates/categories - Get template categories
- GET /templates/languages - Get supported languages
- GET /templates/{id} - Get template details
- POST /templates - Create custom template
- PATCH /templates/{id} - Update custom template
- DELETE /templates/{id} - Delete custom template
- POST /templates/{id}/render - Render template with parameters

### Transformation Notes (Phase 7 Complete)
**New Backend Services:**
- Database Service (`src/services/database_service.py`) - SQL/NoSQL query generation, validation, and explanation
- Language Service (`src/services/language_service.py`) - Multi-language support with test generators and lint rules

**New API Routers:**
- Database Router (`src/api/database_router.py`) - /database/* endpoints

**New Frontend Features:**
- DatabaseQueryBuilder component - Query building with validation and explanation
- Database API client - Query generation and validation

**Database Query Features:**
- Support for PostgreSQL, MySQL, SQLite, MongoDB
- Query validation with risk assessment (low, medium, high, critical)
- SQL injection and dangerous pattern detection
- Query explanation with performance hints
- Natural language to query conversion
- Parameterized query generation
- CREATE, SELECT, INSERT, UPDATE, DELETE generation
- MongoDB find and aggregate pipeline generation

**Language Support Features:**
- Language configurations for Python, JavaScript, TypeScript, Java, Go, C#, Rust
- Language detection from code or filename
- Test generation templates for each language
- Language-specific lint rules
- Complexity scoring with language weights
- Method/function name extraction
- Docker image configurations per language

**API Endpoints Added:**
- POST /database/validate - Validate query for security and syntax
- POST /database/explain - Get query explanation
- POST /database/generate/select - Generate SELECT query
- POST /database/generate/insert - Generate INSERT query
- POST /database/generate/update - Generate UPDATE query
- POST /database/generate/delete - Generate DELETE query
- POST /database/generate/create-table - Generate CREATE TABLE
- POST /database/generate/mongodb/find - Generate MongoDB find
- POST /database/generate/mongodb/aggregate - Generate MongoDB aggregation
- POST /database/generate/natural-language - Convert natural language to query
- GET /database/types - Get supported database types
- GET /database/risk-levels - Get risk level information

### Transformation Notes (Phase 8 Complete)
**New Backend Services:**
- GitHub Service (`src/services/github_service.py`) - Repository operations, context analysis, framework detection
- GitHub OAuth (`src/auth/oauth.py`) - Extended with GitHubOAuth class for GitHub OAuth flow

**New API Routers:**
- GitHub Router (`src/api/github_router.py`) - /github/* endpoints

**New Frontend Features:**
- ConnectionStatus component - GitHub connection status with connect/disconnect
- RepoSelector component - Repository browsing with search and analysis
- GitHub API client - OAuth flow, repository listing, file access

**GitHub Integration Features:**
- GitHub OAuth 2.0 flow with read:user, user:email, repo scopes
- Repository listing with pagination and sorting
- Repository context analysis (framework detection, structure analysis)
- Framework detection for FastAPI, Django, Flask, React, Next.js, Vue, Angular, Express, Spring, ASP.NET
- Package manager detection from configuration files
- File content retrieval for code context
- In-memory token storage (secure per-user)
- CSRF protection with state parameter

**API Endpoints Added:**
- GET /github/connect - Initiate GitHub OAuth flow
- GET /github/callback - OAuth callback handler
- GET /github/status - Get connection status
- DELETE /github/disconnect - Disconnect GitHub account
- GET /github/repos - List user repositories
- POST /github/repos/{owner}/{repo}/analyze - Analyze repository context
- GET /github/repos/{owner}/{repo}/context - Get cached repository context
- GET /github/repos/{owner}/{repo}/file - Get file content

### Transformation Notes (Phase 9 Complete)
**New Backend Services:**
- Rate Limiter (`src/services/rate_limiter.py`) - Sliding window rate limiting per user/IP/API key
- Metrics Service (`src/services/metrics_service.py`) - Execution metrics, LLM cost tracking, usage analytics
- Middleware (`src/api/middleware.py`) - Rate limiting, metrics collection, error tracking middleware

**Performance & Monitoring Features:**
- Configurable rate limiting (requests per minute/hour/day)
- Execution-specific rate limits for code generation
- Different rate limit tiers (anonymous, registered, premium)
- LLM cost estimation and tracking
- Daily metrics aggregation
- Cost alerts and budget monitoring
- Sentry integration for error tracking (optional)
- Request timing and response headers

**New Frontend Features:**
- LoadingSpinner component - Multiple sizes with accessible loading states
- LoadingOverlay component - Full-page loading with backdrop
- LoadingDots component - Animated loading indicator
- Skeleton components - Content placeholder loading
- ErrorBoundary component - React error boundary with fallback UI
- ErrorMessage component - Inline error display
- useKeyboardShortcuts hook - Global keyboard shortcut handling

**Config Settings Added:**
- `enable_rate_limiting` - Toggle rate limiting
- `rate_limit_requests_per_minute/hour/day` - Request limits
- `rate_limit_executions_per_minute/hour/day` - Execution limits
- `enable_metrics` - Toggle metrics collection
- `cost_alert_threshold` - Cost alert threshold (USD)
- `cost_limit_monthly` - Monthly cost limit (USD)
- `sentry_dsn` - Sentry DSN for error tracking

**Response Headers Added:**
- `X-RateLimit-Limit` - Current rate limit
- `X-RateLimit-Remaining` - Remaining requests
- `X-RateLimit-Reset` - Reset timestamp
- `X-RateLimit-Window` - Current limit window
- `X-Response-Time-Ms` - Request duration

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
│   │   ├── auth_router.py   # Authentication endpoints (/auth/*)
│   │   ├── artifact_router.py # Artifact management (/artifacts/*)
│   │   ├── sandbox_router.py  # Browser sandbox (/sandbox/*)
│   │   ├── preview_router.py  # Live preview (/preview/*)
│   │   ├── security_router.py # Security scanning (/security/*)
│   │   ├── mock_router.py     # Mock servers (/mocks/*)
│   │   └── github_router.py   # GitHub integration (/github/*)
│   ├── auth/                # Authentication services
│   │   ├── password.py      # Password hashing (bcrypt)
│   │   ├── jwt.py           # JWT token handling
│   │   ├── user_service.py  # User CRUD operations
│   │   └── oauth.py         # Google & GitHub OAuth implementation
│   ├── database/            # SQLAlchemy database
│   │   ├── models.py        # User, OAuthAccount, Token, Artifact, CodeExecution
│   │   └── connection.py    # Database connection setup
│   ├── agents/              # LangGraph multi-agent system
│   │   ├── supervisor.py    # Agent orchestrator
│   │   ├── query_analyzer.py
│   │   ├── rag_agent.py
│   │   ├── code_agent.py
│   │   ├── code_generator.py # Enhanced code generation
│   │   ├── test_generator.py # Auto test generation
│   │   ├── validator.py     # Validation loop orchestrator
│   │   └── state.py         # Shared agent state
│   ├── core/                # Core services
│   │   ├── vector_store.py  # ChromaDB wrapper
│   │   ├── hybrid_search.py # BM25 + vector fusion
│   │   ├── cross_encoder.py # Re-ranking
│   │   ├── embeddings.py    # Sentence transformers
│   │   ├── llm_client.py    # LLM abstraction
│   │   └── llm_router.py    # Cost-optimized LLM routing
│   ├── parsers/             # Code parsers (minimal)
│   │   └── code_parser.py   # Language detection
│   ├── sessions/            # Session management
│   ├── services/            # Supporting services
│   │   ├── artifact_service.py   # Artifact storage (local/GCS)
│   │   ├── zip_service.py        # ZIP bundle generation
│   │   ├── cleanup_service.py    # Expired artifact cleanup
│   │   ├── execution_service.py  # Code execution orchestration
│   │   ├── diff_service.py       # Code diff comparison
│   │   ├── sandbox_service.py    # Playwright screenshots/testing
│   │   ├── preview_service.py    # Live preview server
│   │   ├── security_service.py   # Vulnerability scanning
│   │   ├── mock_service.py       # API mock server management
│   │   └── github_service.py     # GitHub repository operations
│   └── config.py            # Settings (Pydantic)
├── frontend/                # Next.js frontend
│   ├── src/
│   │   ├── app/            # Pages (chat, sessions, artifacts, settings)
│   │   │   ├── chat/       # Main chat page with code panel
│   │   │   ├── sessions/   # Session management
│   │   │   ├── artifacts/  # Artifact management
│   │   │   ├── settings/   # User settings
│   │   │   ├── login/      # Login page with OAuth
│   │   │   ├── register/   # Registration page
│   │   │   └── auth/callback/ # OAuth callback handler
│   │   ├── components/     # React components
│   │   │   ├── chat/       # ChatMessage, ChatInput
│   │   │   ├── code/       # CodePanel, DiffViewer, PreviewPanel
│   │   │   ├── artifacts/  # ArtifactList, ArtifactUpload
│   │   │   ├── security/   # SecurityReport
│   │   │   ├── mocks/      # MockServerManager
│   │   │   ├── github/     # ConnectionStatus, RepoSelector
│   │   │   └── ui/         # Radix UI primitives
│   │   ├── hooks/          # React Query hooks
│   │   ├── lib/
│   │   │   ├── api/        # API clients (artifacts, sandbox, preview)
│   │   │   └── contexts/   # AuthContext for auth state
│   │   └── stores/         # Zustand stores
│   └── e2e/                # Playwright tests
├── tests/                   # Backend tests
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
| `src/api/artifact_router.py` | Artifact management endpoints (/artifacts/*) |
| `src/api/sandbox_router.py` | Browser sandbox endpoints (/sandbox/*) |
| `src/api/preview_router.py` | Live preview endpoints (/preview/*) |
| `src/config.py` | Environment configuration (Pydantic Settings) |
| `src/agents/supervisor.py` | LangGraph agent orchestrator |
| `src/agents/code_generator.py` | Enhanced code generation agent |
| `src/agents/test_generator.py` | Auto test generation agent |
| `src/agents/validator.py` | Validation loop orchestrator |
| `src/core/vector_store.py` | ChromaDB vector store operations |
| `src/core/llm_router.py` | Cost-optimized LLM routing |
| `src/database/models.py` | SQLAlchemy User, OAuth, Artifact, CodeExecution |
| `src/services/artifact_service.py` | Artifact storage abstraction (local/GCS) |
| `src/services/execution_service.py` | Code execution orchestration |
| `src/services/diff_service.py` | Code diff comparison service |
| `src/services/sandbox_service.py` | Playwright screenshots/UI testing |
| `src/services/preview_service.py` | Live preview server management |
| `src/services/security_service.py` | Vulnerability scanning service |
| `src/services/mock_service.py` | Mock API server management |
| `src/auth/user_service.py` | User CRUD and authentication logic |
| `frontend/src/lib/api/client.ts` | Axios API client with JWT interceptors |
| `frontend/src/lib/contexts/AuthContext.tsx` | React auth state management |
| `frontend/src/components/code/CodePanel.tsx` | Side panel for viewing generated code |
| `frontend/src/components/code/DiffViewer.tsx` | Code diff visualization |
| `frontend/src/components/code/PreviewPanel.tsx` | Live preview iframe |
| `frontend/src/components/security/SecurityReport.tsx` | Vulnerability report display |
| `frontend/src/components/mocks/MockServerManager.tsx` | Mock server management UI |
| `src/services/github_service.py` | GitHub repository operations |
| `src/api/github_router.py` | GitHub API endpoints (/github/*) |
| `frontend/src/lib/api/github.ts` | GitHub API client |
| `frontend/src/components/github/ConnectionStatus.tsx` | GitHub connection status UI |
| `frontend/src/components/github/RepoSelector.tsx` | Repository browser UI |
| `src/services/rate_limiter.py` | Rate limiting service |
| `src/services/metrics_service.py` | Metrics and cost tracking service |
| `src/api/middleware.py` | Rate limiting and metrics middleware |
| `frontend/src/components/ui/loading.tsx` | Loading spinner and skeleton components |
| `frontend/src/components/ui/error-boundary.tsx` | Error boundary components |
| `frontend/src/hooks/useKeyboardShortcuts.ts` | Keyboard shortcuts hook |
| `Dockerfile` | Production Docker image |
| `cloudbuild.yaml` | Cloud Build CI/CD pipeline |
| `env.example.yaml` | Environment variables template |

---

## API Endpoints

### Health & Stats
- `GET /health` - Health check
- `GET /stats` - Collection statistics

### Chat
- `POST /chat` - AI chat with RAG, file uploads, code generation

### Search
- `POST /search` - Hybrid search for code context (modes: vector, hybrid, reranked)

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

### Artifacts (Phase 3)
- `POST /artifacts/upload` - Upload artifact files
- `GET /artifacts` - List artifacts with filtering
- `GET /artifacts/{id}` - Get artifact metadata
- `GET /artifacts/{id}/download` - Download artifact file
- `DELETE /artifacts/{id}` - Delete artifact

### Sandbox (Phase 4)
- `POST /sandbox/screenshot` - Take screenshot of URL
- `POST /sandbox/test-ui` - Run UI tests on URL

### Preview (Phase 4)
- `POST /preview` - Start live preview server
- `GET /preview/{id}` - Get preview status
- `DELETE /preview/{id}` - Stop preview
- `GET /preview` - List user previews
- `GET /preview/stats` - Preview service stats
- `POST /preview/cleanup` - Clean expired previews

### Security (Phase 5)
- `POST /security/scan` - Scan code for vulnerabilities
- `POST /security/scan/dependencies` - Scan package files
- `GET /security/scan/{execution_id}` - Get execution security scan
- `GET /security/supported-languages` - List supported languages

### Mocks (Phase 5)
- `POST /mocks` - Create mock server
- `GET /mocks` - List user mock servers
- `GET /mocks/stats` - Get mock service stats
- `GET /mocks/{id}` - Get mock server details
- `PATCH /mocks/{id}` - Update mock endpoints
- `DELETE /mocks/{id}` - Delete mock server
- `POST /mocks/{id}/stop` - Stop mock server
- `GET /mocks/{id}/logs` - Get request logs
- `POST /mocks/generate/crud` - Generate CRUD endpoints
- `POST /mocks/generate/openapi` - Generate from OpenAPI spec
- `POST /mocks/cleanup` - Clean expired mocks

### GitHub (Phase 8)
- `GET /github/connect` - Initiate GitHub OAuth flow
- `GET /github/callback` - OAuth callback handler
- `GET /github/status` - Get connection status
- `DELETE /github/disconnect` - Disconnect GitHub account
- `GET /github/repos` - List user repositories
- `POST /github/repos/{owner}/{repo}/analyze` - Analyze repository context
- `GET /github/repos/{owner}/{repo}/context` - Get cached repository context
- `GET /github/repos/{owner}/{repo}/file` - Get file content

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

### GitHub OAuth (Phase 8)
```bash
GITHUB_CLIENT_ID=<github-oauth-client-id>
GITHUB_CLIENT_SECRET=<github-oauth-client-secret>
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
| GitHub OAuth | Repository access | In-memory token storage |
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
