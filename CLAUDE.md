# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Intelligent Self-Validating Coding Agent** (v2.0.0) - An AI-powered coding assistant that generates, executes, validates, and delivers production-ready code through an iterative refinement loop.

**Stack**: FastAPI (Python 3.11) + Next.js 16 (React 19, TypeScript) + ChromaDB + LangGraph

## Build & Development Commands

```bash
# Backend
pip install -r requirements.txt
uvicorn src.api.app:app --reload --port 8000

# Frontend
cd frontend && npm install && npm run dev

# Run all backend tests
pytest tests/ -v

# Run single test file
pytest tests/test_api/test_app.py -v

# Run tests with coverage
pytest --cov=src --cov-report=html

# Frontend tests
cd frontend && npm test
cd frontend && npm run test:e2e

# Docker build
docker build -t coding-agent:test .
docker run -p 8000:8000 -e SECRET_KEY=test coding-agent:test

# Lint (if configured)
cd frontend && npm run lint
```

## Architecture

### Multi-Agent System (LangGraph)

The core orchestration happens in `src/agents/supervisor.py` using LangGraph StateGraph:

```
User Query → Query Analyzer → Supervisor
                                  ↓
              ┌───────────────────┼───────────────────┐
              ↓                   ↓                   ↓
         RAG Agent          Code Agent          Validator
              ↓                   ↓                   ↓
              └───────────────────┴───────────────────┘
                                  ↓
                           Final Response
```

- **Query Analyzer** (`query_analyzer.py`): Intent classification and routing
- **RAG Agent** (`rag_agent.py`): Vector search with hybrid BM25 + semantic, web search fallback
- **Code Generator** (`code_generator.py`): Multi-language code generation
- **Validator** (`validator.py`): Self-validating loop with up to 5 retries

### Backend Structure

```
src/
├── api/app.py          # FastAPI entry point, all route mounting
├── api/auth.py         # JWT/API key middleware (verify_api_key, get_current_user)
├── api/*_router.py     # Feature routers (artifacts, github, webhooks, etc.)
├── agents/             # LangGraph agents (supervisor orchestrates all)
├── core/               # Vector store, embeddings, LLM client, hybrid search
├── services/           # Business logic (artifact_service, execution_service, etc.)
├── database/models.py  # SQLAlchemy models (User, Artifact, CodeExecution)
└── config.py           # Pydantic Settings (all env vars defined here)
```

### Frontend Structure

```
frontend/src/
├── app/                # Next.js App Router pages
│   ├── chat/          # Main chat interface (landing page)
│   ├── sessions/      # Session management
│   ├── artifacts/     # Artifact management
│   └── auth/          # Login, register, OAuth callback
├── components/         # React components by feature
├── lib/api/           # API clients (client.ts has axios with JWT interceptors)
├── lib/contexts/      # AuthContext for auth state
└── stores/            # Zustand stores for UI state
```

### Authentication Flow

```
Login → POST /auth/login → JWT tokens → localStorage
     ↓
API requests → Authorization: Bearer <token> → auth.py middleware
     ↓
Token refresh → POST /auth/refresh (7-day refresh token)
```

Three auth methods: Email/Password, Google OAuth, GitHub OAuth (for repo access)

### Data Flow

1. **Chat**: User message → `/chat` endpoint → Supervisor agent → Response with code
2. **Artifacts**: Generated code → `artifact_service.py` → Local storage or GCS
3. **Execution**: Code → `execution_service.py` → Docker container (local) or Cloud Run Jobs (prod)

## Key Patterns

### Adding a New API Router

1. Create `src/api/new_router.py` with FastAPI APIRouter
2. Add router to `src/api/app.py` in the router mounting section
3. Create corresponding frontend API client in `frontend/src/lib/api/`

### Adding Environment Variables

1. Add to `src/config.py` Settings class with Field() and default
2. Add to `.env.example` with documentation
3. Reference via `from src.config import settings`

### Database Models

All models in `src/database/models.py`. Uses SQLAlchemy with async sessions.
Connection setup in `src/database/connection.py`.

## Configuration

All environment variables defined in `src/config.py`. Key ones:

- `LLM_PROVIDER`: "ollama" (local) or "groq" (cloud)
- `GROQ_API_KEY`: Required if using Groq
- `SECRET_KEY`: Required for JWT signing
- `ENVIRONMENT`: "local" or "production" (affects artifact storage, execution)

See `.env.example` for full list with documentation.

## Deployment

- **Backend**: Google Cloud Run (asia-east1) with GCS FUSE for ChromaDB
- **Frontend**: Vercel
- **CI/CD**: `cloudbuild.yaml` triggers on push to main

```bash
# Manual deploy
gcloud run deploy api-assistant --image <image> --region asia-east1

# View logs
gcloud run services logs read api-assistant --region asia-east1 --limit 50
```

## Development Guidelines

1. **Read before modifying**: Always read existing code before making changes
2. **Keep changes minimal**: Avoid over-engineering; only change what's necessary
3. **Update .env.example**: When adding new environment variables
4. **Test locally**: Run `pytest` before committing backend changes

## Troubleshooting

- **CORS errors**: Set `ALLOWED_ORIGINS` env var to frontend URL
- **ChromaDB errors**: Delete `data/chroma_db/` and restart
- **Import errors**: Run `pip install -r requirements.txt`
- **Frontend API errors**: Check `NEXT_PUBLIC_API_BASE_URL` in frontend/.env
