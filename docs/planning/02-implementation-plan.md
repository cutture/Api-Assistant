# Intelligent Self-Validating Coding Agent: Implementation Plan

## Executive Summary

Transform the existing **API Integration Assistant** into an **Intelligent Self-Validating Coding Agent** that generates, executes, validates, and delivers production-ready code through an iterative refinement loop.

---

## Table of Contents

1. [Transformation Overview](#1-transformation-overview)
2. [Architecture Design](#2-architecture-design)
3. [Database Schema](#3-database-schema)
4. [API Endpoints](#4-api-endpoints)
5. [Frontend Changes](#5-frontend-changes)
6. [Implementation Phases](#6-implementation-phases)
7. [File Structure](#7-file-structure)
8. [Migration Triggers](#8-migration-triggers)
9. [Risk Assessment](#9-risk-assessment)

---

## 1. Transformation Overview

### What to REMOVE

| Component | Location | Reason |
|-----------|----------|--------|
| Document Upload Page | `frontend/src/app/documents/` | Replaced by artifacts system |
| Document Listing Page | `frontend/src/app/documents/` | Replaced by artifacts system |
| Mermaid Diagram Generation | `src/diagrams/` | Not needed for code generation |
| OpenAPI/GraphQL Parsers | `src/parsers/` | Keep minimal for context extraction |
| Document Upload Endpoints | `src/api/app.py` | Replace with artifact endpoints |
| Diagram Endpoints | `src/api/app.py` | Remove entirely |
| Doc Analyzer Agent | `src/agents/doc_analyzer.py` | Replace with Code Validator Agent |

### What to KEEP & REPURPOSE

| Component | Current Use | New Use |
|-----------|-------------|---------|
| ChromaDB | Document storage | Artifact context & code snippets |
| Sessions | Chat history | Coding session with execution history |
| RAG Agent | Document Q&A | Code context retrieval |
| Code Agent | Code generation | Enhanced with validation loop |
| Hybrid Search | Document search | Artifact & code search |
| User Auth | User management | Same + GitHub OAuth |
| LLM Client | Groq/Ollama | Multi-provider with routing |

### What to ADD

| Component | Purpose |
|-----------|---------|
| Artifacts System | Store uploaded files, generated code, downloads |
| Code Execution Engine | Container-based code runner |
| Test Generator Agent | Auto-generate tests for validation |
| Validation Loop | Iterative code refinement |
| GitHub Integration | Repository context & PR creation |
| ZIP Bundle Generator | Package multi-file outputs |
| Execution History | Track all code runs and results |

---

## 2. Architecture Design

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   Chat UI   │  │  Artifacts  │  │ Code Panel  │  │  Sessions   │    │
│  │  (Unified)  │  │   Manager   │  │ (Side View) │  │   List      │    │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘    │
└─────────┼────────────────┼────────────────┼────────────────┼───────────┘
          │                │                │                │
          ▼                ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           API GATEWAY (FastAPI)                          │
│  /chat  /artifacts  /execute  /sessions  /github  /auth                 │
└─────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         AGENT ORCHESTRATOR                               │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      SUPERVISOR (LangGraph)                      │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐    │   │
│  │  │  Query   │  │   Code   │  │   Test   │  │  Validation  │    │   │
│  │  │ Analyzer │  │Generator │  │Generator │  │    Loop      │    │   │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘    │   │
│  │       │             │             │               │             │   │
│  │       └─────────────┴─────────────┴───────────────┘             │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          EXECUTION LAYER                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ Cloud Run   │  │    LLM      │  │  ChromaDB   │  │   SQLite    │    │
│  │   Jobs      │  │  Router     │  │ (Artifacts) │  │  (Users,    │    │
│  │ (Execution) │  │ (Groq/etc)  │  │             │  │  Sessions)  │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        EXTERNAL SERVICES                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   GitHub    │  │    Groq     │  │  DeepSeek   │  │   Ollama    │    │
│  │    API      │  │    API      │  │    API      │  │   (Local)   │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

### Code Generation & Validation Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    CODE GENERATION & VALIDATION FLOW                      │
└──────────────────────────────────────────────────────────────────────────┘

User Request
     │
     ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Analyze   │────▶│  Classify   │────▶│  Route to   │
│   Request   │     │  Complexity │     │  LLM Tier   │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
     ┌────────────────────────────────────────┼────────────────────────────┐
     │                                        │                            │
     ▼                                        ▼                            ▼
┌─────────────┐                      ┌─────────────┐              ┌─────────────┐
│   Simple    │                      │   Medium    │              │   Complex   │
│  DeepSeek/  │                      │    Groq     │              │   Claude/   │
│   Ollama    │                      │  Llama 3.3  │              │    GPT-4    │
└──────┬──────┘                      └──────┬──────┘              └──────┬──────┘
       │                                    │                            │
       └────────────────────────────────────┼────────────────────────────┘
                                            │
                                            ▼
                                   ┌─────────────────┐
                                   │ Generate Code   │
                                   │ + Generate Tests│
                                   └────────┬────────┘
                                            │
                                            ▼
                                   ┌─────────────────┐
                                   │  Cloud Run Job  │
                                   │  Execute Code   │
                                   └────────┬────────┘
                                            │
                              ┌─────────────┴─────────────┐
                              │                           │
                              ▼                           ▼
                     ┌─────────────┐             ┌─────────────┐
                     │   PASSED    │             │   FAILED    │
                     └──────┬──────┘             └──────┬──────┘
                            │                          │
                            │                          ▼
                            │                 ┌─────────────────┐
                            │                 │ Retry < 5?      │
                            │                 └────────┬────────┘
                            │                    Yes   │   No
                            │              ┌───────────┴───────────┐
                            │              │                       │
                            │              ▼                       ▼
                            │     ┌─────────────┐         ┌─────────────┐
                            │     │ Analyze     │         │ Return      │
                            │     │ Errors &    │         │ Partial +   │
                            │     │ Regenerate  │         │ Explanation │
                            │     └──────┬──────┘         └─────────────┘
                            │            │
                            │            └──────────────────┐
                            │                               │
                            ▼                               │
                   ┌─────────────────┐                      │
                   │ Deliver Result  │◀─────────────────────┘
                   └────────┬────────┘
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
          ▼                 ▼                 ▼
   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
   │  Snippet    │  │  ZIP Bundle │  │  GitHub PR  │
   │  (Inline)   │  │  (Download) │  │  (if repo)  │
   └─────────────┘  └─────────────┘  └─────────────┘
```

### LLM Router Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           LLM ROUTER                                     │
└─────────────────────────────────────────────────────────────────────────┘

                         User Request
                              │
                              ▼
                    ┌─────────────────┐
                    │ Task Classifier │
                    │  (Complexity)   │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
   ┌─────────┐         ┌─────────┐         ┌─────────┐
   │ SIMPLE  │         │ MEDIUM  │         │ COMPLEX │
   │ Score<3 │         │Score 3-6│         │ Score>6 │
   └────┬────┘         └────┬────┘         └────┬────┘
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│ Ollama Local  │  │     Groq      │  │ Claude/GPT-4  │
│ deepseek-coder│  │ llama-3.3-70b │  │ (via API)     │
│ ~$0.00/req    │  │ ~$0.01/req    │  │ ~$0.10/req    │
└───────┬───────┘  └───────┬───────┘  └───────┬───────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │ Failover Chain  │
                   │ if primary fails│
                   └─────────────────┘

Complexity Scoring:
- Lines of code needed: +1 per 50 lines
- Number of files: +1 per file
- External dependencies: +1 per dependency
- API integrations: +2 per API
- Database operations: +2
- Authentication logic: +2
- Multi-language: +3
```

---

## 3. Database Schema

### New Tables (Extend Existing SQLite)

```sql
-- Artifacts: Store uploaded and generated files
CREATE TABLE artifacts (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    session_id TEXT REFERENCES sessions(id),
    name TEXT NOT NULL,
    type TEXT NOT NULL,  -- 'uploaded', 'generated', 'output'
    mime_type TEXT,
    file_path TEXT NOT NULL,  -- Path in storage
    size_bytes INTEGER,
    metadata JSON,  -- Language, dependencies, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,  -- For auto-cleanup
    INDEX idx_artifacts_user (user_id),
    INDEX idx_artifacts_session (session_id)
);

-- Code Executions: Track all execution attempts
CREATE TABLE code_executions (
    id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES sessions(id),
    user_id TEXT REFERENCES users(id),

    -- Request details
    prompt TEXT NOT NULL,
    language TEXT NOT NULL,
    complexity_score INTEGER,
    llm_provider TEXT,
    llm_model TEXT,

    -- Generated code
    generated_code TEXT,
    generated_tests TEXT,

    -- Execution results
    status TEXT NOT NULL,  -- 'pending', 'running', 'passed', 'failed', 'partial'
    attempt_number INTEGER DEFAULT 1,
    execution_time_ms INTEGER,

    -- Output
    stdout TEXT,
    stderr TEXT,
    test_results JSON,
    lint_results JSON,

    -- Delivery
    output_type TEXT,  -- 'snippet', 'zip', 'pr'
    output_artifact_id TEXT REFERENCES artifacts(id),

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,

    INDEX idx_executions_session (session_id),
    INDEX idx_executions_user (user_id),
    INDEX idx_executions_status (status)
);

-- Execution Attempts: Track retry history
CREATE TABLE execution_attempts (
    id TEXT PRIMARY KEY,
    execution_id TEXT REFERENCES code_executions(id),
    attempt_number INTEGER NOT NULL,

    code_version TEXT,
    error_type TEXT,
    error_message TEXT,
    fix_applied TEXT,

    started_at TIMESTAMP,
    completed_at TIMESTAMP,

    INDEX idx_attempts_execution (execution_id)
);

-- GitHub Connections: Store user's GitHub OAuth tokens
CREATE TABLE github_connections (
    id TEXT PRIMARY KEY,
    user_id TEXT UNIQUE REFERENCES users(id),
    github_user_id TEXT,
    github_username TEXT,
    access_token TEXT NOT NULL,  -- Encrypted
    refresh_token TEXT,
    token_expires_at TIMESTAMP,
    scopes TEXT,  -- Comma-separated: 'repo,read:user'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,

    INDEX idx_github_user (user_id)
);

-- Repository Contexts: Cached repo analysis
CREATE TABLE repository_contexts (
    id TEXT PRIMARY KEY,
    github_connection_id TEXT REFERENCES github_connections(id),
    repo_full_name TEXT NOT NULL,  -- 'owner/repo'
    default_branch TEXT,

    -- Analyzed structure
    languages JSON,
    framework_detected TEXT,
    package_manager TEXT,
    structure_summary TEXT,

    -- Cache control
    last_analyzed_at TIMESTAMP,
    last_commit_sha TEXT,

    INDEX idx_repo_name (repo_full_name)
);
```

### Retention Policy Implementation

```sql
-- Auto-cleanup job (run daily)
DELETE FROM artifacts
WHERE expires_at < CURRENT_TIMESTAMP;

DELETE FROM code_executions
WHERE created_at < datetime('now', '-30 days')
AND user_id IN (SELECT id FROM users WHERE tier = 'registered');

DELETE FROM code_executions
WHERE created_at < datetime('now', '-7 days')
AND user_id IN (SELECT id FROM users WHERE tier = 'free');

-- Keep last 50 execution logs per user
DELETE FROM code_executions
WHERE id NOT IN (
    SELECT id FROM code_executions e2
    WHERE e2.user_id = code_executions.user_id
    ORDER BY created_at DESC LIMIT 50
);
```

---

## 4. API Endpoints

### Remove These Endpoints

```
DELETE  /documents/upload
DELETE  /documents
DELETE  /documents/{id}
DELETE  /documents/bulk-delete
DELETE  /search (document search)
DELETE  /search/faceted
DELETE  /diagrams/*
```

### Keep These Endpoints

```
GET     /health
GET     /stats
POST    /chat (enhanced)
GET     /sessions
POST    /sessions
GET     /sessions/{id}
PATCH   /sessions/{id}
DELETE  /sessions/{id}
POST    /sessions/{id}/messages
DELETE  /sessions/{id}/messages
POST    /auth/* (all auth endpoints)
```

### New Endpoints

```yaml
# Artifacts Management
POST    /artifacts/upload:
  description: Upload files (code, specs, context)
  body: multipart/form-data
  response: { artifact_id, name, type, size }

GET     /artifacts:
  description: List user's artifacts
  query: session_id?, type?, page, limit
  response: { artifacts: [], total, page }

GET     /artifacts/{id}:
  description: Get artifact metadata
  response: { id, name, type, metadata, download_url }

GET     /artifacts/{id}/download:
  description: Download artifact file
  response: file stream

DELETE  /artifacts/{id}:
  description: Delete artifact

# Code Execution
POST    /execute:
  description: Generate and execute code
  body:
    prompt: string
    language?: string (auto-detect if not provided)
    session_id?: string
    context_artifacts?: string[] (artifact IDs for context)
    github_repo?: string (owner/repo)
    llm_preference?: 'fast' | 'balanced' | 'quality'
    output_preference?: 'snippet' | 'zip' | 'pr'
  response:
    execution_id: string
    status: 'queued'
    estimated_time_seconds: number

GET     /execute/{id}:
  description: Get execution status and results
  response:
    status: 'pending' | 'running' | 'passed' | 'failed' | 'partial'
    attempt: number
    code?: string
    tests?: string
    output?: { stdout, stderr, test_results }
    artifact_id?: string (if zip/file generated)
    pr_url?: string (if PR created)

GET     /execute/{id}/stream:
  description: SSE stream for real-time execution updates
  response: Server-Sent Events

POST    /execute/{id}/retry:
  description: Manually retry failed execution
  response: { execution_id, status: 'queued' }

GET     /executions:
  description: List user's executions
  query: session_id?, status?, page, limit
  response: { executions: [], total, page }

# GitHub Integration
GET     /github/connect:
  description: Initiate GitHub OAuth flow
  response: redirect to GitHub

GET     /github/callback:
  description: GitHub OAuth callback
  query: code, state
  response: redirect to frontend

GET     /github/status:
  description: Check GitHub connection status
  response: { connected, username, scopes }

DELETE  /github/disconnect:
  description: Remove GitHub connection

GET     /github/repos:
  description: List user's accessible repos
  response: { repos: [{ full_name, private, default_branch }] }

POST    /github/repos/{owner}/{repo}/analyze:
  description: Analyze repository structure
  response: { languages, framework, structure }

# Code Search (replaces document search)
POST    /search/code:
  description: Search artifacts and generated code
  body:
    query: string
    language?: string
    artifact_types?: string[]
  response: { results: [{ artifact_id, snippet, score }] }
```

---

## 5. Frontend Changes

### Pages to Remove

```
/documents          → Remove entirely
/documents/upload   → Remove entirely
/diagrams           → Remove entirely
```

### Pages to Keep & Modify

```
/                   → Landing page (update messaging)
/login              → Keep as-is
/register           → Keep as-is
/sessions           → Keep, add execution history view
/chat               → Major enhancement (see below)
```

### New Pages

```
/artifacts          → Artifact manager (uploads, generated files)
/settings/github    → GitHub connection settings
```

### Chat Page Enhancement

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Logo] Intelligent Coding Agent          [Artifacts] [Settings] [User] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────┐  ┌───────────────────────────────────┐│
│  │                             │  │                                   ││
│  │      CHAT PANEL             │  │        CODE PANEL                 ││
│  │                             │  │                                   ││
│  │  ┌─────────────────────┐   │  │  ┌─────────────────────────────┐ ││
│  │  │ User: Create a REST │   │  │  │ main.py              [Copy] │ ││
│  │  │ API for user auth   │   │  │  │─────────────────────────────│ ││
│  │  └─────────────────────┘   │  │  │ from fastapi import FastAPI │ ││
│  │                             │  │  │ from pydantic import Base.. │ ││
│  │  ┌─────────────────────┐   │  │  │                             │ ││
│  │  │ Agent: I'll create  │   │  │  │ app = FastAPI()             │ ││
│  │  │ an auth API with:   │   │  │  │                             │ ││
│  │  │ - JWT tokens        │   │  │  │ @app.post("/login")         │ ││
│  │  │ - User registration │   │  │  │ def login():                │ ││
│  │  │ - Password hashing  │   │  │  │     ...                     │ ││
│  │  │                     │   │  │  └─────────────────────────────┘ ││
│  │  │ [▼ Show execution]  │   │  │                                   ││
│  │  └─────────────────────┘   │  │  Files: [main.py] [models.py]    ││
│  │                             │  │  [test_auth.py] [requirements]   ││
│  │  ┌─────────────────────┐   │  │                                   ││
│  │  │ ████████░░ Running  │   │  │  ┌─────────────────────────────┐ ││
│  │  │ tests (attempt 2/5) │   │  │  │ [Download ZIP] [Copy All]   │ ││
│  │  └─────────────────────┘   │  │  └─────────────────────────────┘ ││
│  │                             │  │                                   ││
│  └─────────────────────────────┘  └───────────────────────────────────┘│
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │ [📎 Attach] [🔗 GitHub: owner/repo ▼]  Type your request...  [Send]││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                                                         │
│  Context: [artifact1.py ×] [api-spec.json ×]    Language: Python (auto)│
└─────────────────────────────────────────────────────────────────────────┘
```

### Component Changes

| Component | Change |
|-----------|--------|
| `ChatInput` | Add artifact attachment, GitHub repo selector |
| `ChatMessage` | Add execution status, expandable logs |
| `CodePanel` | NEW: Side panel for viewing generated code |
| `ArtifactManager` | NEW: Upload, list, manage artifacts |
| `ExecutionStatus` | NEW: Real-time execution progress |
| `GitHubRepoSelector` | NEW: Select connected repos |

---

## 6. Implementation Phases

### Phase 1: Foundation (Week 1-2)
**Goal:** Remove unused features, set up new database schema

```
Tasks:
├── Backend
│   ├── Remove document upload endpoints
│   ├── Remove diagram endpoints
│   ├── Remove document-related agents
│   ├── Add new database tables (artifacts, executions)
│   ├── Create artifact storage service
│   └── Update CORS and auth for new endpoints
│
├── Frontend
│   ├── Remove /documents pages
│   ├── Remove /diagrams pages
│   ├── Update navigation
│   └── Create basic artifact list page
│
└── Infrastructure
    ├── Update database migrations
    └── Test deployment
```

### Phase 2: Core Coding Agent (Week 3-4)
**Goal:** Basic code generation with execution

```
Tasks:
├── Backend
│   ├── Create LLM router (task classification)
│   ├── Implement code generation agent
│   ├── Implement test generation agent
│   ├── Create Cloud Run Job executor
│   ├── Build validation loop (5 retries)
│   └── Add execution endpoints
│
├── Frontend
│   ├── Enhance chat with code display
│   ├── Add execution status component
│   ├── Create code panel (side view)
│   └── Add copy/download buttons
│
└── Docker
    ├── Create Python execution image
    ├── Create Node.js execution image
    └── Test Cloud Run Jobs
```

### Phase 3: Output Delivery (Week 5)
**Goal:** Multiple output formats

```
Tasks:
├── Backend
│   ├── Implement snippet inline delivery
│   ├── Implement ZIP bundle generation
│   ├── Add artifact creation for outputs
│   └── Implement partial result handling
│
├── Frontend
│   ├── Add ZIP download button
│   ├── Show partial results on failure
│   └── Add artifact linking
│
└── Testing
    ├── Test all output types
    └── Test error scenarios
```

### Phase 4: GitHub Integration (Week 6-7)
**Goal:** Read-only GitHub integration

```
Tasks:
├── Backend
│   ├── Implement GitHub OAuth
│   ├── Add repository listing endpoint
│   ├── Create repo analyzer
│   ├── Clone repos for context
│   └── Store repo context in ChromaDB
│
├── Frontend
│   ├── Add GitHub settings page
│   ├── Add repo selector to chat
│   └── Show repo context indicator
│
└── Security
    ├── Encrypt GitHub tokens
    ├── Implement token refresh
    └── Add scope verification
```

### Phase 5: Language Expansion (Week 8)
**Goal:** Add Tier 2 languages

```
Tasks:
├── Docker Images
│   ├── Create Java execution image
│   ├── Create Go execution image
│   ├── Create C# execution image
│   └── Test all images
│
├── Backend
│   ├── Add language-specific test generators
│   ├── Add language-specific lint rules
│   └── Update complexity scoring
│
└── Frontend
    └── Update language selector
```

### Phase 6: Polish & Optimization (Week 9-10)
**Goal:** Production readiness

```
Tasks:
├── Performance
│   ├── Optimize Cloud Run Job cold starts
│   ├── Add execution caching
│   ├── Implement request queuing
│   └── Add rate limiting
│
├── UX
│   ├── Add progressive disclosure for logs
│   ├── Improve error messages
│   ├── Add keyboard shortcuts
│   └── Mobile responsiveness
│
├── Monitoring
│   ├── Add execution metrics
│   ├── Add cost tracking
│   ├── Set up alerts
│   └── Create dashboard
│
└── Documentation
    ├── Update README
    ├── Create user guide
    └── API documentation
```

---

## 7. File Structure

### Backend Changes

```
src/
├── api/
│   ├── app.py              # Update: remove old endpoints, add new
│   ├── models.py           # Update: add execution/artifact models
│   ├── auth.py             # Keep
│   ├── auth_router.py      # Keep
│   ├── artifact_router.py  # NEW: artifact endpoints
│   ├── execute_router.py   # NEW: execution endpoints
│   └── github_router.py    # NEW: GitHub integration
│
├── agents/
│   ├── supervisor.py       # Update: new agent routing
│   ├── query_analyzer.py   # Keep, enhance for code tasks
│   ├── code_generator.py   # NEW: enhanced code generation
│   ├── test_generator.py   # NEW: test generation
│   ├── validator.py        # NEW: validation loop
│   └── state.py            # Update: execution state
│
├── core/
│   ├── vector_store.py     # Keep, repurpose for artifacts
│   ├── hybrid_search.py    # Keep
│   ├── embeddings.py       # Keep
│   ├── llm_client.py       # Update: add router
│   ├── llm_router.py       # NEW: task-based routing
│   └── execution_engine.py # NEW: Cloud Run Job manager
│
├── services/
│   ├── artifact_service.py # NEW: artifact management
│   ├── execution_service.py# NEW: execution orchestration
│   ├── github_service.py   # NEW: GitHub API wrapper
│   └── zip_service.py      # NEW: ZIP bundle creation
│
├── database/
│   ├── models.py           # Update: add new tables
│   └── connection.py       # Keep
│
└── parsers/                # REMOVE most, keep minimal
    └── code_parser.py      # NEW: language detection
```

### Frontend Changes

```
frontend/src/
├── app/
│   ├── page.tsx            # Update: new landing
│   ├── chat/
│   │   └── page.tsx        # Major update: code panel
│   ├── sessions/
│   │   └── page.tsx        # Update: add execution history
│   ├── artifacts/          # NEW
│   │   └── page.tsx
│   ├── settings/
│   │   └── github/         # NEW
│   │       └── page.tsx
│   ├── documents/          # REMOVE
│   └── diagrams/           # REMOVE
│
├── components/
│   ├── chat/
│   │   ├── ChatMessage.tsx # Update: execution status
│   │   ├── ChatInput.tsx   # Update: attachments, repo
│   │   ├── CodePanel.tsx   # NEW
│   │   └── ExecutionStatus.tsx # NEW
│   ├── artifacts/          # NEW
│   │   ├── ArtifactList.tsx
│   │   ├── ArtifactUpload.tsx
│   │   └── ArtifactItem.tsx
│   └── github/             # NEW
│       ├── RepoSelector.tsx
│       └── ConnectionStatus.tsx
│
├── hooks/
│   ├── useChat.ts          # Update
│   ├── useExecution.ts     # NEW
│   ├── useArtifacts.ts     # NEW
│   └── useGitHub.ts        # NEW
│
└── lib/
    └── api/
        ├── client.ts       # Keep
        ├── artifacts.ts    # NEW
        ├── execution.ts    # NEW
        └── github.ts       # NEW
```

### Docker Images

```
docker/
├── execution/
│   ├── python/
│   │   ├── Dockerfile
│   │   └── requirements.txt  # Common packages
│   ├── node/
│   │   ├── Dockerfile
│   │   └── package.json
│   ├── java/
│   │   └── Dockerfile
│   ├── go/
│   │   └── Dockerfile
│   └── csharp/
│       └── Dockerfile
└── base/
    └── Dockerfile           # Shared base image
```

---

## 8. Migration Triggers

### When to Migrate to Microservice Architecture (Option B)

Add to CLAUDE.md:

```markdown
## Future Migration: Microservice Architecture

**Current:** Extended multi-agent system (monolith)
**Target:** Separate coding-agent microservice

**Trigger Conditions (ANY of these):**
1. Daily code executions exceed 500
2. Execution container costs exceed $100/month
3. Main API latency increases due to execution load
4. Need independent scaling of execution vs chat

**Migration Steps:**
1. Extract execution_service.py to new FastAPI app
2. Create internal API for main app → execution service
3. Deploy as separate Cloud Run service
4. Add service mesh for communication
5. Update frontend to handle service routing
```

### When to Add PR-Only Git Integration (Option C)

Add to CLAUDE.md:

```markdown
## Future Feature: PR-Only Git Integration

**Current:** Read-only repository access
**Target:** Create PRs with generated code

**Trigger Conditions (ANY of these):**
1. User requests reach 50+ for PR creation
2. Competitive pressure (other tools offer this)
3. Enterprise customers require it

**Implementation Steps:**
1. Add 'repo' scope to GitHub OAuth
2. Implement branch creation
3. Implement PR creation API
4. Add PR review UI in frontend
5. Add merge conflict detection
```

### When to Add GitLab/Bitbucket Support

Add to CLAUDE.md:

```markdown
## Future Feature: GitLab & Bitbucket Integration

**Current:** GitHub only
**Target:** GitLab, Bitbucket, generic Git

**Trigger Conditions:**
1. GitLab: 20+ user requests
2. Bitbucket: Enterprise customer requirement
3. Self-hosted: Enterprise deployment needs

**Implementation Steps:**
1. Abstract GitHub service to Git provider interface
2. Implement GitLab OAuth and API
3. Implement Bitbucket OAuth and API
4. Add provider selection in UI
5. Update repo selector component
```

---

## 9. Risk Assessment

### High Risk

| Risk | Impact | Mitigation |
|------|--------|------------|
| Cloud Run Job costs explode | High bills | Daily limits, budget alerts, user quotas |
| Generated code has security issues | User systems compromised | Sandbox execution, no network access, code scanning |
| LLM generates harmful code | Reputation damage | Output filtering, code review prompts |
| GitHub token leaks | User repos compromised | Encryption, minimal scopes, regular rotation |

### Medium Risk

| Risk | Impact | Mitigation |
|------|--------|------------|
| Validation loop infinite retries | Cost overrun | Hard 5-retry limit, timeout per attempt |
| Container escapes | System compromise | Use Cloud Run (managed), no privileged mode |
| Rate limits from LLM providers | Service disruption | Failover chain, caching, request queuing |
| Large ZIP files | Storage costs | Size limits (50MB max), auto-cleanup |

### Low Risk

| Risk | Impact | Mitigation |
|------|--------|------------|
| Language detection wrong | Poor UX | User confirmation before generation |
| Cold start latency | Slow first request | Keep-warm strategy, user feedback |
| ChromaDB data loss | Context lost | Regular backups to GCS |

---

## Appendix A: Environment Variables (New)

```bash
# Existing (keep)
SECRET_KEY=xxx
GROQ_API_KEY=xxx
LLM_PROVIDER=groq
CHROMA_PERSIST_DIR=/mnt/chroma_data/chroma_db

# New variables
# GitHub OAuth
GITHUB_CLIENT_ID=xxx
GITHUB_CLIENT_SECRET=xxx
GITHUB_CALLBACK_URL=https://your-app.com/github/callback

# Execution
EXECUTION_MAX_RETRIES=5
EXECUTION_TIMEOUT_SECONDS=120
EXECUTION_DAILY_LIMIT=100
CLOUD_RUN_PROJECT=your-project
CLOUD_RUN_REGION=asia-east1

# LLM Router
DEEPSEEK_API_KEY=xxx
DEEPSEEK_API_URL=https://api.deepseek.com
OLLAMA_BASE_URL=http://localhost:11434
LLM_SIMPLE_PROVIDER=ollama
LLM_MEDIUM_PROVIDER=groq
LLM_COMPLEX_PROVIDER=groq

# Artifact Storage
ARTIFACT_STORAGE_PATH=/mnt/artifacts
ARTIFACT_MAX_SIZE_MB=50
ARTIFACT_RETENTION_DAYS=30

# Cost Tracking
COST_ALERT_THRESHOLD=50
COST_LIMIT_MONTHLY=200
```

---

## Appendix B: Ollama Model Setup

```bash
# Required models for local execution
ollama pull deepseek-coder-v2:16b    # Primary code model (16GB VRAM)
ollama pull llama3.1:8b               # Fallback/fast model (6GB VRAM)
ollama pull qwen2.5-coder:7b          # Lightweight alternative (6GB VRAM)

# Optional for better quality
ollama pull codellama:34b             # Highest quality (24GB VRAM)
```

---

## Appendix C: Estimated Costs

| Component | Monthly Estimate (moderate usage) |
|-----------|----------------------------------|
| Cloud Run (main app) | $20-50 |
| Cloud Run Jobs (execution) | $30-100 |
| Cloud Storage (artifacts) | $5-10 |
| Groq API | $10-30 |
| DeepSeek API | $5-15 |
| **Total** | **$70-205/month** |

*Based on ~1000 executions/month, ~100 active users*

---

## Next Steps

1. **Review this plan** and provide feedback
2. **Confirm phase priorities** - which features are most important?
3. **Clarify any questions** before implementation begins
4. **I will update CLAUDE.md** with future migration triggers
5. **Begin Phase 1** implementation upon approval
