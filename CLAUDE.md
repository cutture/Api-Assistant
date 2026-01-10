# CLAUDE.md - Project Reference for Claude AI

This file provides Claude with context about the Api-Assistant project for efficient assistance.

## Project Overview

**API Integration Assistant** - An AI-powered assistant that helps developers understand, document, and generate code for API integrations using advanced multi-agent orchestration and hybrid search.

**Version:** 1.0.0 (Production Ready)
**Status:** Production/Stable

### Key Capabilities
- Parse API specifications (OpenAPI, GraphQL, Postman, PDF, Markdown)
- Intelligent Q&A about APIs with source citations
- Multi-language code generation (Python, JS, TS, Java, Go, etc.)
- Documentation quality analysis and gap detection
- Visual diagram generation (sequence, auth flow, ER, overview)
- Persistent chat sessions with conversation history

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

- **v1.0.0** (Dec 2025) - Production release with full feature set
- Multi-agent system, hybrid search, Next.js frontend
- Cloud Run + Vercel deployment
- GCS FUSE for persistent storage
