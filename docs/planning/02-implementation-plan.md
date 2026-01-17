# Intelligent Self-Validating Coding Agent: Implementation Plan

## Executive Summary

Transform the existing **API Integration Assistant** into an **Intelligent Self-Validating Coding Agent** that generates, executes, validates, and delivers production-ready code through an iterative refinement loop.

---

## Table of Contents

1. [Transformation Overview](#1-transformation-overview)
2. [Storage Architecture](#2-storage-architecture)
3. [System Architecture](#3-system-architecture)
4. [Database Schema](#4-database-schema)
5. [API Endpoints](#5-api-endpoints)
6. [Frontend Changes](#6-frontend-changes)
7. [Implementation Phases](#7-implementation-phases)
8. [File Structure](#8-file-structure)
9. [Migration Triggers](#9-migration-triggers)
10. [Risk Assessment](#10-risk-assessment)
11. [Appendices](#11-appendices)

---

## 1. Transformation Overview

### What to REMOVE

| Component | Location | Reason |
|-----------|----------|--------|
| **Frontend Pages** | | |
| Document Upload Page | `frontend/src/app/documents/` | Replaced by artifacts |
| Document Listing Page | `frontend/src/app/documents/` | Replaced by artifacts |
| Diagrams Page | `frontend/src/app/diagrams/` | Not needed |
| Search Page | `frontend/src/app/search/` | Replace with code search |
| **Backend - Diagrams** | | |
| Mermaid Generator | `src/diagrams/mermaid_generator.py` | Not needed |
| Diagram Endpoints | `src/api/app.py` | Remove entirely |
| **Backend - Parsers** | | |
| OpenAPI Parser | `src/parsers/openapi_parser.py` | Not needed |
| GraphQL Parser | `src/parsers/graphql_parser.py` | Not needed |
| Postman Parser | `src/parsers/postman_parser.py` | Not needed |
| PDF Parser | `src/parsers/pdf_parser.py` | Not needed |
| Document Parser | `src/parsers/document_parser.py` | Not needed |
| **Backend - Agents** | | |
| Doc Analyzer Agent | `src/agents/doc_analyzer.py` | Replace with Validator |
| Gap Analysis Agent | `src/agents/gap_analysis_agent.py` | Not needed |
| **Backend - Core** | | |
| Advanced Filtering | `src/core/advanced_filtering.py` | Document-specific |
| Result Diversification | `src/core/result_diversification.py` | Not needed |
| **Backend - Endpoints** | | |
| Document Upload | `POST /documents/upload` | Remove |
| Document CRUD | `/documents/*` | Remove |
| Faceted Search | `POST /search/faceted` | Remove |
| All Diagram Endpoints | `/diagrams/*` | Remove |

### What to KEEP & REPURPOSE

| Component | Current Use | New Use |
|-----------|-------------|---------|
| ChromaDB | Document embeddings | **Semantic code search** (see Section 2) |
| Sessions | Chat history | Coding session + execution history |
| RAG Agent | Document Q&A | Code context retrieval |
| Code Agent | Code generation | Enhanced with validation loop |
| Hybrid Search | Document search | Code & artifact search |
| Cross-Encoder | Re-ranking | Code search ranking |
| Query Expansion | Search enhancement | Code query enhancement |
| URL Scraper | Web scraping | GitHub README scraping |
| User Auth | User management | Same + GitHub OAuth |
| LLM Client | Groq/Ollama | Multi-provider with routing |

### What to ADD

| Component | Purpose | Priority |
|-----------|---------|----------|
| **Core Features** | | |
| Artifacts System | Store uploads, generated code, downloads | High |
| Code Execution Engine | Container-based code runner | High |
| Test Generator Agent | Auto-generate tests | High |
| Validation Loop | 5-retry iterative refinement | High |
| ZIP Bundle Generator | Package multi-file outputs | High |
| **High Priority Features** | | |
| Browser Sandbox | UI testing with screenshots | High |
| Live Preview URLs | Temporary app preview | High |
| Code Diff Visualization | Show changes between retries | High |
| Security Vulnerability Scan | Snyk/npm audit integration | High |
| API Mock Server | Auto-generate mock endpoints | High |
| **Medium Priority Features** | | |
| Template Library | Pre-built code templates | Medium |
| Execution Replay | Re-run previous executions | Medium |
| Code Quality Score | Maintainability rating | Medium |
| Dependency Analysis | Package analysis & licenses | Medium |
| Database Query Generation | Natural language → SQL | Medium |
| **Lower Priority Features** | | |
| GitHub Integration | Repository context | Low (v2) |
| Collaborative Sessions | Team sharing | Low (Future) |
| Webhook Triggers | CI/CD integration | Low (Future) |

---

## 2. Storage Architecture

### Clear Role Definition

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        STORAGE ARCHITECTURE                              │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     SQLite      │     │   Filesystem    │     │    ChromaDB     │
│   (Structured)  │     │    (Files)      │     │   (Semantic)    │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ • Users         │     │ • Uploaded      │     │ • Code          │
│ • Sessions      │     │   artifacts     │     │   embeddings    │
│ • Executions    │     │ • Generated     │     │ • Semantic      │
│ • Artifacts     │     │   code files    │     │   search index  │
│   (metadata)    │     │ • ZIP bundles   │     │ • Repository    │
│ • GitHub tokens │     │ • Screenshots   │     │   context       │
│ • Repo contexts │     │ • Preview apps  │     │ • Code snippets │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### SQLite Responsibilities
- All structured/relational data
- User accounts, sessions, OAuth tokens
- Artifact metadata (name, type, path, user_id)
- Execution history and attempt logs
- Repository connection metadata

### Filesystem Responsibilities
- Actual file content storage
- Path: `/data/artifacts/{user_id}/{artifact_id}/`
- Uploaded files, generated code, ZIP bundles
- Screenshots from browser sandbox
- Temporary preview app files

### ChromaDB Responsibilities (Semantic Code Search)
**Primary Purpose:** Enable natural language code search

| Use Case | Example Query | ChromaDB Role |
|----------|---------------|---------------|
| Find similar code | "authentication middleware" | Returns semantically similar code |
| Repository context | "how does auth work in this repo" | Retrieves relevant code sections |
| Code pattern search | "error handling patterns" | Finds similar implementations |
| Artifact search | "find my Python login script" | Semantic artifact matching |

**What gets embedded in ChromaDB:**
1. Generated code snippets (chunked)
2. Cloned repository code (when GitHub connected)
3. Uploaded code artifacts
4. Code documentation/comments

**Collection Structure:**
```python
# Collection: code_context
{
    "id": "chunk_123",
    "embedding": [...],  # 384-dim vector
    "metadata": {
        "user_id": "user_456",
        "artifact_id": "artifact_789",
        "language": "python",
        "type": "generated",  # or "uploaded", "repository"
        "file_path": "auth/middleware.py",
        "repo": "owner/repo",  # if from GitHub
        "created_at": "2026-01-17T..."
    },
    "document": "def authenticate(request):\n    ..."
}
```

---

## 3. System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   Chat UI   │  │  Artifacts  │  │ Code Panel  │  │  Sessions   │    │
│  │  (Unified)  │  │   Manager   │  │ (Side View) │  │   List      │    │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘    │
│         │                │                │                │            │
│  ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐                     │
│  │  Preview    │  │   Diff      │  │  Security   │                     │
│  │  Panel      │  │   Viewer    │  │  Report     │                     │
│  └─────────────┘  └─────────────┘  └─────────────┘                     │
└─────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           API GATEWAY (FastAPI)                          │
│  /chat  /artifacts  /execute  /preview  /sessions  /github  /auth       │
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
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────────┘    │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                      │   │
│  │  │ Security │  │  Mock    │  │ Template │                      │   │
│  │  │ Scanner  │  │ Server   │  │ Selector │                      │   │
│  │  └──────────┘  └──────────┘  └──────────┘                      │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          EXECUTION LAYER                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ Cloud Run   │  │  Browser    │  │  Preview    │  │    LLM      │    │
│  │   Jobs      │  │  Sandbox    │  │  Server     │  │   Router    │    │
│  │ (Execution) │  │(Playwright) │  │ (Temp URLs) │  │ (Groq/etc)  │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          STORAGE LAYER                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                     │
│  │   SQLite    │  │ Filesystem  │  │  ChromaDB   │                     │
│  │ (Metadata)  │  │  (Files)    │  │  (Search)   │                     │
│  └─────────────┘  └─────────────┘  └─────────────┘                     │
└─────────────────────────────────────────────────────────────────────────┘
```

### Code Generation & Validation Flow

```
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
│  Ollama     │                      │    Groq     │              │   Claude/   │
│  local      │                      │  Llama 3.3  │              │    GPT-4    │
└──────┬──────┘                      └──────┬──────┘              └──────┬──────┘
       │                                    │                            │
       └────────────────────────────────────┴────────────────────────────┘
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
                                            ▼
                                   ┌─────────────────┐
                                   │  Multi-Signal   │
                                   │  Validation     │
                                   └────────┬────────┘
                                            │
                    ┌───────────────────────┼───────────────────────┐
                    │                       │                       │
                    ▼                       ▼                       ▼
           ┌─────────────┐         ┌─────────────┐         ┌─────────────┐
           │    Tests    │         │    Lint     │         │  Security   │
           │   Pass?     │         │   Pass?     │         │   Pass?     │
           └──────┬──────┘         └──────┬──────┘         └──────┬──────┘
                  │                       │                       │
                  └───────────────────────┼───────────────────────┘
                                          │
                              ┌───────────┴───────────┐
                              │                       │
                              ▼                       ▼
                     ┌─────────────┐         ┌─────────────┐
                     │ ALL PASSED  │         │ ANY FAILED  │
                     └──────┬──────┘         └──────┬──────┘
                            │                       │
                            │                       ▼
                            │              ┌─────────────────┐
                            │              │ Retry < 5?      │
                            │              └────────┬────────┘
                            │                 Yes   │   No
                            │           ┌──────────┴──────────┐
                            │           │                     │
                            │           ▼                     ▼
                            │  ┌─────────────┐       ┌─────────────┐
                            │  │  Analyze &  │       │   Partial   │
                            │  │  Regenerate │       │   Result    │
                            │  └──────┬──────┘       └─────────────┘
                            │         │
                            │         └───────────────┐
                            │                         │
                            ▼                         │
                   ┌─────────────────┐                │
                   │ Deliver Result  │◀───────────────┘
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
                   │ Groq→DeepSeek→  │
                   │ Ollama→OpenAI   │
                   └─────────────────┘

Complexity Scoring:
- Lines of code needed: +1 per 50 lines
- Number of files: +1 per file
- External dependencies: +1 per dependency
- API integrations: +2 per API
- Database operations: +2
- Authentication logic: +2
- Multi-language: +3
- UI components: +2
```

---

## 4. Database Schema

### New Tables (Extend Existing SQLite)

```sql
-- Artifacts: Store uploaded and generated files (metadata only)
CREATE TABLE artifacts (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    session_id TEXT REFERENCES sessions(id),
    name TEXT NOT NULL,
    type TEXT NOT NULL,  -- 'uploaded', 'generated', 'output', 'screenshot', 'preview'
    mime_type TEXT,
    file_path TEXT NOT NULL,  -- Relative path in /data/artifacts/
    size_bytes INTEGER,
    language TEXT,  -- For code files
    metadata JSON,  -- Additional info (dependencies, etc.)
    chromadb_ids JSON,  -- Array of ChromaDB chunk IDs for this artifact
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,  -- For auto-cleanup
    INDEX idx_artifacts_user (user_id),
    INDEX idx_artifacts_session (session_id),
    INDEX idx_artifacts_type (type)
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

    -- Multi-signal validation results
    test_passed BOOLEAN,
    lint_passed BOOLEAN,
    security_passed BOOLEAN,

    -- Output
    stdout TEXT,
    stderr TEXT,
    test_results JSON,
    lint_results JSON,
    security_results JSON,

    -- Delivery
    output_type TEXT,  -- 'snippet', 'zip', 'pr'
    output_artifact_id TEXT REFERENCES artifacts(id),

    -- Quality metrics
    quality_score INTEGER,  -- 1-10

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,

    INDEX idx_executions_session (session_id),
    INDEX idx_executions_user (user_id),
    INDEX idx_executions_status (status)
);

-- Execution Attempts: Track retry history with diffs
CREATE TABLE execution_attempts (
    id TEXT PRIMARY KEY,
    execution_id TEXT REFERENCES code_executions(id),
    attempt_number INTEGER NOT NULL,

    code_version TEXT,
    diff_from_previous TEXT,  -- Unified diff format
    error_type TEXT,
    error_message TEXT,
    fix_applied TEXT,

    -- Per-attempt validation
    test_passed BOOLEAN,
    lint_passed BOOLEAN,
    security_passed BOOLEAN,

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

    -- ChromaDB reference
    chromadb_collection TEXT,  -- Collection name for this repo

    -- Cache control
    last_analyzed_at TIMESTAMP,
    last_commit_sha TEXT,

    INDEX idx_repo_name (repo_full_name)
);

-- Preview Sessions: Temporary live preview URLs
CREATE TABLE preview_sessions (
    id TEXT PRIMARY KEY,
    execution_id TEXT REFERENCES code_executions(id),
    user_id TEXT REFERENCES users(id),

    preview_url TEXT NOT NULL,
    port INTEGER,
    container_id TEXT,

    status TEXT NOT NULL,  -- 'starting', 'running', 'stopped'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,  -- 30 min default

    INDEX idx_preview_execution (execution_id)
);

-- Code Templates: Pre-built templates
CREATE TABLE code_templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT,  -- 'api', 'auth', 'crud', 'ui', 'utility'
    language TEXT NOT NULL,
    framework TEXT,

    template_code TEXT NOT NULL,
    variables JSON,  -- Placeholders to fill

    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_templates_category (category),
    INDEX idx_templates_language (language)
);

-- API Mocks: Generated mock servers
CREATE TABLE api_mocks (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    session_id TEXT REFERENCES sessions(id),

    name TEXT NOT NULL,
    spec_type TEXT,  -- 'openapi', 'custom'
    endpoints JSON NOT NULL,  -- Array of {method, path, response}

    mock_url TEXT,
    port INTEGER,
    status TEXT NOT NULL,  -- 'running', 'stopped'

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,

    INDEX idx_mocks_user (user_id)
);
```

### Retention Policy

```sql
-- Auto-cleanup job (run daily via cron)

-- Clean expired artifacts
DELETE FROM artifacts WHERE expires_at < CURRENT_TIMESTAMP;

-- Clean old executions based on user tier
DELETE FROM code_executions
WHERE created_at < datetime('now', '-90 days')
AND user_id IN (SELECT id FROM users WHERE tier = 'premium');

DELETE FROM code_executions
WHERE created_at < datetime('now', '-30 days')
AND user_id IN (SELECT id FROM users WHERE tier = 'registered');

DELETE FROM code_executions
WHERE created_at < datetime('now', '-7 days')
AND user_id IN (SELECT id FROM users WHERE tier = 'free');

-- Keep last 50 execution logs per user
WITH ranked AS (
    SELECT id, ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) as rn
    FROM code_executions
)
DELETE FROM code_executions WHERE id IN (SELECT id FROM ranked WHERE rn > 50);

-- Clean expired preview sessions
DELETE FROM preview_sessions WHERE expires_at < CURRENT_TIMESTAMP;

-- Clean expired mock servers
DELETE FROM api_mocks WHERE expires_at < CURRENT_TIMESTAMP;
```

---

## 5. API Endpoints

### Remove These Endpoints

```
DELETE  /documents/upload
DELETE  /documents
DELETE  /documents/{id}
DELETE  /documents/bulk-delete
DELETE  /search (document search)
DELETE  /search/faceted
DELETE  /diagrams/sequence
DELETE  /diagrams/auth-flow
DELETE  /diagrams/er
DELETE  /diagrams/overview
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
# ============ ARTIFACTS ============
POST    /artifacts/upload:
  description: Upload files (code, specs, context)
  body: multipart/form-data
  response: { artifact_id, name, type, size, chromadb_indexed }

GET     /artifacts:
  description: List user's artifacts
  query: session_id?, type?, language?, page, limit
  response: { artifacts: [], total, page }

GET     /artifacts/{id}:
  description: Get artifact metadata
  response: { id, name, type, metadata, download_url }

GET     /artifacts/{id}/download:
  description: Download artifact file
  response: file stream

DELETE  /artifacts/{id}:
  description: Delete artifact (also removes from ChromaDB)

# ============ CODE EXECUTION ============
POST    /execute:
  description: Generate and execute code
  body:
    prompt: string
    language?: string (auto-detect if not provided)
    session_id?: string
    context_artifacts?: string[] (artifact IDs)
    github_repo?: string (owner/repo)
    llm_preference?: 'fast' | 'balanced' | 'quality'
    output_preference?: 'snippet' | 'zip' | 'pr'
    template_id?: string (use template)
    enable_security_scan?: boolean (default: true)
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
    output?: { stdout, stderr, test_results, lint_results, security_results }
    quality_score?: number
    artifact_id?: string
    pr_url?: string

GET     /execute/{id}/stream:
  description: SSE stream for real-time updates
  response: Server-Sent Events

GET     /execute/{id}/diff:
  description: Get diff between attempts
  query: from_attempt, to_attempt
  response: { unified_diff, changes_summary }

POST    /execute/{id}/retry:
  description: Manually retry failed execution
  body: { custom_prompt?: string }
  response: { execution_id, status: 'queued' }

GET     /executions:
  description: List user's executions
  query: session_id?, status?, language?, page, limit
  response: { executions: [], total, page }

POST    /executions/{id}/replay:
  description: Re-run a previous execution
  body: { modifications?: string }
  response: { new_execution_id }

# ============ PREVIEW & SANDBOX ============
POST    /preview:
  description: Start live preview server
  body:
    execution_id: string
    port?: number
  response:
    preview_id: string
    url: string
    expires_at: timestamp

GET     /preview/{id}:
  description: Get preview status
  response: { status, url, expires_at }

DELETE  /preview/{id}:
  description: Stop preview server

POST    /sandbox/screenshot:
  description: Take screenshot of URL
  body:
    url: string
    viewport?: { width, height }
    full_page?: boolean
  response:
    screenshot_artifact_id: string
    download_url: string

POST    /sandbox/test-ui:
  description: Run UI tests on preview
  body:
    preview_id: string
    test_script?: string
  response:
    passed: boolean
    screenshots: string[]
    errors?: string[]

# ============ SECURITY SCANNING ============
POST    /security/scan:
  description: Scan code for vulnerabilities
  body:
    code: string
    language: string
  response:
    vulnerabilities: [{ severity, type, line, message, fix_suggestion }]
    risk_score: number

GET     /security/scan/{execution_id}:
  description: Get security scan results for execution
  response: { vulnerabilities, risk_score, scanned_at }

# ============ MOCK SERVER ============
POST    /mocks:
  description: Create mock API server
  body:
    name: string
    endpoints: [{ method, path, response, status_code }]
    spec_url?: string (OpenAPI URL to generate from)
  response:
    mock_id: string
    url: string
    expires_at: timestamp

GET     /mocks:
  description: List user's mock servers
  response: { mocks: [] }

GET     /mocks/{id}:
  description: Get mock server details
  response: { id, url, endpoints, status }

PATCH   /mocks/{id}:
  description: Update mock endpoints
  body: { endpoints: [] }

DELETE  /mocks/{id}:
  description: Stop and delete mock server

# ============ TEMPLATES ============
GET     /templates:
  description: List available templates
  query: category?, language?, framework?
  response: { templates: [] }

GET     /templates/{id}:
  description: Get template details
  response: { id, name, code, variables }

POST    /templates/{id}/generate:
  description: Generate code from template
  body: { variables: {} }
  response: { code, execution_id? }

# ============ CODE SEARCH ============
POST    /search/code:
  description: Semantic search over code
  body:
    query: string
    language?: string
    artifact_types?: string[]
    repo?: string
    limit?: number
  response: { results: [{ artifact_id, snippet, score, file_path }] }

# ============ GITHUB INTEGRATION ============
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
  description: Analyze and index repository
  response: { languages, framework, structure, indexed_files }

GET     /github/repos/{owner}/{repo}/context:
  description: Get repo context for code generation
  response: { summary, key_files, patterns }
```

---

## 6. Frontend Changes

### Pages to Remove

```
/documents          → Remove entirely
/documents/upload   → Remove entirely
/diagrams           → Remove entirely
/search             → Remove (replace with code search in chat)
```

### Pages to Keep & Modify

```
/                   → Landing page (update messaging for Coding Agent)
/login              → Keep as-is
/register           → Keep as-is
/sessions           → Keep, add execution history column
/chat               → Major enhancement (see below)
/settings           → Add GitHub connection section
```

### New Pages

```
/artifacts          → Artifact manager (uploads, generated files, downloads)
/templates          → Browse and use code templates
/settings/github    → GitHub connection management
```

### Enhanced Chat Page Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  [Logo] Intelligent Coding Agent    [Templates] [Artifacts] [⚙️] [👤 User]  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────┐  ┌─────────────────────────────────────┐│
│  │         CHAT PANEL            │  │           CODE PANEL                ││
│  │                               │  │                                     ││
│  │  ┌───────────────────────┐   │  │  ┌─────────────────────────────┐   ││
│  │  │ 👤 Create a REST API  │   │  │  │ Files: [main.py ▼]          │   ││
│  │  │ for user auth with    │   │  │  │        [models.py]          │   ││
│  │  │ JWT tokens            │   │  │  │        [test_auth.py]       │   ││
│  │  └───────────────────────┘   │  │  │        [requirements.txt]   │   ││
│  │                               │  │  └─────────────────────────────┘   ││
│  │  ┌───────────────────────┐   │  │                                     ││
│  │  │ 🤖 I'll create an     │   │  │  ┌─────────────────────────────┐   ││
│  │  │ auth API with:        │   │  │  │ 1  from fastapi import...   │   ││
│  │  │ • JWT authentication  │   │  │  │ 2  from pydantic import...  │   ││
│  │  │ • Password hashing    │   │  │  │ 3                           │   ││
│  │  │ • User registration   │   │  │  │ 4  app = FastAPI()          │   ││
│  │  │                       │   │  │  │ 5                           │   ││
│  │  │ ┌─────────────────┐   │   │  │  │ 6  @app.post("/login")      │   ││
│  │  │ │ ▶ Execution Log │   │   │  │  │ 7  async def login(...):    │   ││
│  │  │ │ Attempt 2/5     │   │   │  │  │ 8      ...                  │   ││
│  │  │ │ ✅ Tests passed │   │   │  │  └─────────────────────────────┘   ││
│  │  │ │ ✅ Lint passed  │   │   │  │                                     ││
│  │  │ │ ⚠️ 1 security   │   │   │  │  ┌─────────────────────────────┐   ││
│  │  │ │    warning      │   │   │  │  │ [📋 Copy] [📥 ZIP] [👁 Diff] │   ││
│  │  │ └─────────────────┘   │   │  │  │ [🔍 Preview] [🛡️ Security]  │   ││
│  │  └───────────────────────┘   │  │  └─────────────────────────────┘   ││
│  │                               │  │                                     ││
│  │  ┌───────────────────────┐   │  ├─────────────────────────────────────┤│
│  │  │ ████████████░░ 80%    │   │  │        PREVIEW PANEL (collapsible)  ││
│  │  │ Running security scan │   │  │  ┌─────────────────────────────┐   ││
│  │  └───────────────────────┘   │  │  │  [Live Preview Screenshot]   │   ││
│  │                               │  │  │                              │   ││
│  └───────────────────────────────┘  │  │  URL: https://preview-xxx... │   ││
│                                      │  │  Expires in: 28:45           │   ││
│  ┌───────────────────────────────────┴──┴─────────────────────────────┐   ││
│  │ [📎] [🔗 GitHub: owner/repo ▼] [📝 Template ▼]  Type request... [➤] │   ││
│  └──────────────────────────────────────────────────────────────────────┘   ││
│                                                                             ││
│  Context: [auth.py ×] [spec.json ×]     Lang: Python (auto)  Quality: 8/10 ││
└─────────────────────────────────────────────────────────────────────────────┘
```

### New Components

| Component | Purpose |
|-----------|---------|
| `CodePanel` | Side panel for viewing generated code with syntax highlighting |
| `ExecutionStatus` | Real-time execution progress with expandable logs |
| `DiffViewer` | Side-by-side diff between retry attempts |
| `PreviewPanel` | Live preview iframe with screenshot |
| `SecurityReport` | Vulnerability scan results display |
| `ArtifactManager` | Upload, list, manage artifacts |
| `TemplateSelector` | Browse and select code templates |
| `GitHubRepoSelector` | Select connected repos |
| `QualityScore` | Visual quality score indicator |
| `MockServerManager` | Create and manage API mocks |

---

## 7. Implementation Phases

### Phase 1: Foundation & Cleanup
**Goal:** Remove unused features, set up storage architecture

```
Tasks:
├── Backend Removal
│   ├── Remove /diagrams endpoints and src/diagrams/
│   ├── Remove document parsers (keep text_parser for code)
│   ├── Remove doc_analyzer and gap_analysis agents
│   ├── Remove /documents endpoints
│   ├── Remove /search/faceted endpoint
│   ├── Remove advanced_filtering.py, result_diversification.py
│   └── Clean up unused imports
│
├── Database Setup
│   ├── Create artifacts table
│   ├── Create code_executions table
│   ├── Create execution_attempts table
│   ├── Set up filesystem storage structure
│   └── Configure ChromaDB for code collection
│
├── Frontend Removal
│   ├── Remove /documents pages
│   ├── Remove /diagrams page
│   ├── Remove /search page
│   ├── Update navigation
│   └── Update landing page messaging
│
└── Infrastructure
    ├── Update Dockerfile
    ├── Test deployment
    └── Update CI/CD
```

### Phase 2: Core Coding Agent
**Goal:** Basic code generation with validation loop

```
Tasks:
├── Backend
│   ├── Create LLM router (task classification)
│   ├── Implement code_generator.py agent
│   ├── Implement test_generator.py agent
│   ├── Create validation loop with 5 retries
│   ├── Add /execute endpoints
│   ├── Create Cloud Run Job executor
│   └── Implement multi-signal validation (tests, lint)
│
├── Frontend
│   ├── Create CodePanel component
│   ├── Create ExecutionStatus component
│   ├── Enhance ChatMessage for code display
│   ├── Add copy/download buttons
│   └── Real-time SSE updates
│
└── Docker
    ├── Create Python execution image
    ├── Create Node.js execution image
    └── Test Cloud Run Jobs integration
```

### Phase 3: Output Delivery & Artifacts
**Goal:** Multiple output formats, artifact management

```
Tasks:
├── Backend
│   ├── Implement artifact service
│   ├── Add /artifacts endpoints
│   ├── Implement ZIP bundle generation
│   ├── Implement snippet inline delivery
│   ├── Index artifacts in ChromaDB
│   └── Implement partial result handling
│
├── Frontend
│   ├── Create ArtifactManager page
│   ├── Add artifact upload component
│   ├── Add ZIP download button
│   ├── Show partial results on failure
│   └── Link artifacts to executions
│
└── Storage
    ├── Set up filesystem structure
    ├── Implement cleanup jobs
    └── Test retention policies
```

### Phase 4: High Priority Features (Part 1)
**Goal:** Browser sandbox, live preview, code diff

```
Tasks:
├── Browser Sandbox
│   ├── Set up Playwright container
│   ├── Implement screenshot endpoint
│   ├── Add UI test runner
│   └── Create sandbox service
│
├── Live Preview
│   ├── Create preview server container
│   ├── Implement preview session management
│   ├── Add temporary URL generation
│   ├── Create PreviewPanel component
│   └── Handle preview expiration
│
├── Code Diff
│   ├── Store diff between attempts
│   ├── Create DiffViewer component
│   ├── Add /execute/{id}/diff endpoint
│   └── Integrate into chat UI
│
└── Frontend
    ├── Add preview panel to chat
    ├── Add diff viewer modal
    └── Screenshot gallery
```

### Phase 5: High Priority Features (Part 2)
**Goal:** Security scanning, API mock server

```
Tasks:
├── Security Scanning
│   ├── Integrate Snyk or npm audit
│   ├── Create security scanner service
│   ├── Add /security/scan endpoints
│   ├── Create SecurityReport component
│   ├── Add security to validation loop
│   └── Block high-severity by default
│
├── API Mock Server
│   ├── Create mock server container
│   ├── Implement endpoint configuration
│   ├── Add /mocks endpoints
│   ├── Create MockServerManager component
│   └── Auto-generate from specs
│
└── Integration
    ├── Add security badge to executions
    ├── Link mocks to executions
    └── Update validation flow
```

### Phase 6: Medium Priority Features
**Goal:** Templates, replay, quality scoring

```
Tasks:
├── Template Library
│   ├── Create templates table
│   ├── Seed initial templates (REST API, CRUD, auth)
│   ├── Add /templates endpoints
│   ├── Create TemplateSelector component
│   ├── Integrate templates into code generation
│   └── Track template usage
│
├── Execution Replay
│   ├── Add /executions/{id}/replay endpoint
│   ├── Store execution parameters
│   ├── Add replay button to history
│   └── Support modifications on replay
│
├── Code Quality Score
│   ├── Implement quality scoring algorithm
│   ├── Factors: complexity, test coverage, lint, security
│   ├── Create QualityScore component
│   ├── Show score in execution results
│   └── Track quality over time
│
└── Dependency Analysis
    ├── Parse requirements/package.json
    ├── Check for known vulnerabilities
    ├── Show license information
    └── Add to execution output
```

### Phase 7: Database Query & Language Expansion
**Goal:** SQL generation, Tier 2 languages

```
Tasks:
├── Database Query Generation
│   ├── Add SQL/NoSQL query generation to code agent
│   ├── Support PostgreSQL, MySQL, MongoDB
│   ├── Validate queries before execution
│   └── Add query explanation
│
├── Language Expansion
│   ├── Create Java execution image
│   ├── Create Go execution image
│   ├── Create C# execution image
│   ├── Add language-specific test generators
│   ├── Add language-specific lint rules
│   └── Update complexity scoring per language
│
└── Testing
    ├── Test all language images
    ├── Verify validation for each language
    └── Performance benchmarks
```

### Phase 8: GitHub Integration
**Goal:** Read-only GitHub integration

```
Tasks:
├── Backend
│   ├── Implement GitHub OAuth
│   ├── Add /github endpoints
│   ├── Create repo analyzer
│   ├── Clone repos for context
│   ├── Index repo code in ChromaDB
│   └── Encrypt GitHub tokens
│
├── Frontend
│   ├── Add GitHub settings page
│   ├── Create GitHubRepoSelector
│   ├── Show repo context indicator
│   └── Handle disconnection
│
└── Security
    ├── Minimal OAuth scopes (read-only)
    ├── Token refresh handling
    └── Audit logging
```

### Phase 9: Polish & Production Readiness
**Goal:** Performance, monitoring, documentation

```
Tasks:
├── Performance
│   ├── Optimize Cloud Run Job cold starts
│   ├── Add execution caching
│   ├── Implement request queuing
│   ├── Add rate limiting
│   └── ChromaDB query optimization
│
├── Monitoring
│   ├── Add execution metrics
│   ├── Add cost tracking dashboard
│   ├── Set up alerts
│   ├── Error tracking (Sentry)
│   └── Usage analytics
│
├── UX Polish
│   ├── Progressive disclosure for logs
│   ├── Keyboard shortcuts
│   ├── Mobile responsiveness
│   ├── Loading states
│   └── Error message improvements
│
└── Documentation
    ├── Update README
    ├── Create user guide
    ├── API documentation (OpenAPI)
    └── Architecture docs
```

### Phase 10: Lower Priority Features (Future)
**Goal:** Advanced features based on demand

```
Future Tasks (implement based on triggers):
├── Collaborative Sessions
│   ├── Real-time session sharing
│   ├── Team workspaces
│   └── Permission management
│
├── Webhook Triggers
│   ├── CI/CD integration
│   ├── Slack/Discord bots
│   └── Scheduled executions
│
├── PR-Only Git Integration
│   ├── Branch creation
│   ├── PR creation
│   └── Conflict detection
│
└── GitLab/Bitbucket Support
    ├── Abstract Git provider
    ├── GitLab OAuth
    └── Bitbucket OAuth
```

---

## 8. File Structure

### Backend Changes

```
src/
├── api/
│   ├── app.py                 # Update: remove old, add new endpoints
│   ├── models.py              # Update: add execution/artifact models
│   ├── auth.py                # Keep
│   ├── auth_router.py         # Keep
│   ├── artifact_router.py     # NEW: artifact endpoints
│   ├── execute_router.py      # NEW: execution endpoints
│   ├── preview_router.py      # NEW: preview/sandbox endpoints
│   ├── security_router.py     # NEW: security scan endpoints
│   ├── mock_router.py         # NEW: mock server endpoints
│   ├── template_router.py     # NEW: template endpoints
│   ├── search_router.py       # NEW: code search endpoints
│   └── github_router.py       # NEW: GitHub integration
│
├── agents/
│   ├── supervisor.py          # Update: new agent routing
│   ├── query_analyzer.py      # Keep, enhance for code tasks
│   ├── rag_agent.py           # Keep for code context retrieval
│   ├── code_generator.py      # NEW: enhanced code generation
│   ├── test_generator.py      # NEW: test generation
│   ├── validator.py           # NEW: validation loop orchestrator
│   ├── security_agent.py      # NEW: security scanning
│   └── state.py               # Update: execution state
│
├── core/
│   ├── vector_store.py        # Update: code-focused collections
│   ├── hybrid_search.py       # Keep
│   ├── cross_encoder.py       # Keep for code ranking
│   ├── query_expansion.py     # Keep for code search
│   ├── embeddings.py          # Keep
│   ├── llm_client.py          # Update: add router
│   ├── llm_router.py          # NEW: task-based routing
│   └── execution_engine.py    # NEW: Cloud Run Job manager
│
├── services/
│   ├── artifact_service.py    # NEW: artifact management
│   ├── execution_service.py   # NEW: execution orchestration
│   ├── preview_service.py     # NEW: live preview management
│   ├── sandbox_service.py     # NEW: browser sandbox
│   ├── security_service.py    # NEW: vulnerability scanning
│   ├── mock_service.py        # NEW: mock server management
│   ├── template_service.py    # NEW: template management
│   ├── github_service.py      # NEW: GitHub API wrapper
│   ├── zip_service.py         # NEW: ZIP bundle creation
│   ├── diff_service.py        # NEW: code diff generation
│   └── quality_service.py     # NEW: code quality scoring
│
├── database/
│   ├── models.py              # Update: add new tables
│   └── connection.py          # Keep
│
├── parsers/                   # SIMPLIFIED
│   ├── __init__.py
│   ├── code_parser.py         # NEW: language detection
│   └── text_parser.py         # Keep for plain text
│
├── diagrams/                  # REMOVE entirely
├── sessions/                  # Keep
├── auth/                      # Keep
└── config.py                  # Update: new settings
```

### Frontend Changes

```
frontend/src/
├── app/
│   ├── page.tsx               # Update: new landing
│   ├── chat/
│   │   └── page.tsx           # Major update: code panel, preview
│   ├── sessions/
│   │   └── page.tsx           # Update: execution history
│   ├── artifacts/             # NEW
│   │   └── page.tsx
│   ├── templates/             # NEW
│   │   └── page.tsx
│   ├── settings/
│   │   ├── page.tsx           # Update
│   │   └── github/            # NEW
│   │       └── page.tsx
│   ├── login/                 # Keep
│   ├── register/              # Keep
│   ├── auth/callback/         # Keep
│   ├── documents/             # REMOVE
│   ├── diagrams/              # REMOVE
│   └── search/                # REMOVE
│
├── components/
│   ├── chat/
│   │   ├── ChatMessage.tsx    # Update: execution status
│   │   ├── ChatInput.tsx      # Update: attachments, repo, templates
│   │   ├── CodePanel.tsx      # NEW: side code viewer
│   │   ├── ExecutionStatus.tsx # NEW: real-time progress
│   │   ├── DiffViewer.tsx     # NEW: code diff display
│   │   ├── PreviewPanel.tsx   # NEW: live preview
│   │   └── QualityScore.tsx   # NEW: quality indicator
│   ├── artifacts/             # NEW
│   │   ├── ArtifactList.tsx
│   │   ├── ArtifactUpload.tsx
│   │   └── ArtifactItem.tsx
│   ├── templates/             # NEW
│   │   ├── TemplateList.tsx
│   │   ├── TemplateCard.tsx
│   │   └── TemplateSelector.tsx
│   ├── security/              # NEW
│   │   ├── SecurityReport.tsx
│   │   └── VulnerabilityItem.tsx
│   ├── mocks/                 # NEW
│   │   ├── MockServerManager.tsx
│   │   └── EndpointEditor.tsx
│   └── github/                # NEW
│       ├── RepoSelector.tsx
│       └── ConnectionStatus.tsx
│
├── hooks/
│   ├── useChat.ts             # Update
│   ├── useExecution.ts        # NEW
│   ├── useArtifacts.ts        # NEW
│   ├── useTemplates.ts        # NEW
│   ├── usePreview.ts          # NEW
│   ├── useSecurity.ts         # NEW
│   ├── useMocks.ts            # NEW
│   └── useGitHub.ts           # NEW
│
└── lib/
    └── api/
        ├── client.ts          # Keep
        ├── artifacts.ts       # NEW
        ├── execution.ts       # NEW
        ├── preview.ts         # NEW
        ├── security.ts        # NEW
        ├── mocks.ts           # NEW
        ├── templates.ts       # NEW
        └── github.ts          # NEW
```

### Docker Images

```
docker/
├── execution/
│   ├── python/
│   │   ├── Dockerfile
│   │   └── requirements.txt    # pytest, flake8, black, bandit
│   ├── node/
│   │   ├── Dockerfile
│   │   └── package.json        # jest, eslint, prettier
│   ├── java/
│   │   └── Dockerfile          # JUnit, Maven
│   ├── go/
│   │   └── Dockerfile          # go test, golint
│   └── csharp/
│       └── Dockerfile          # NUnit, dotnet
├── preview/
│   └── Dockerfile              # Node.js for serving previews
├── sandbox/
│   └── Dockerfile              # Playwright for browser testing
└── mock/
    └── Dockerfile              # Mock server (Prism or custom)
```

---

## 9. Migration Triggers

### When to Migrate to Microservice Architecture

**Current:** Extended multi-agent system (monolith)
**Target:** Separate coding-agent microservice

**Trigger Conditions (implement when ANY occurs):**
1. Daily code executions exceed 500
2. Execution container costs exceed $100/month
3. Main API latency increases >200ms due to execution load
4. Need independent scaling of execution vs chat

**Migration Steps:**
1. Extract execution_service.py to new FastAPI app
2. Create internal API for main app → execution service
3. Deploy as separate Cloud Run service
4. Add service mesh for communication
5. Update frontend to handle service routing

---

### When to Add PR-Only Git Integration

**Current:** Read-only repository access
**Target:** Create branches and PRs with generated code

**Trigger Conditions (implement when ANY occurs):**
1. User requests reach 50+ for PR creation
2. Competitive pressure (other tools offer this)
3. Enterprise customers require it

**Implementation Steps:**
1. Add 'repo' write scope to GitHub OAuth
2. Implement branch creation
3. Implement PR creation API
4. Add PR review UI in frontend
5. Add merge conflict detection

---

### When to Add GitLab/Bitbucket Support

**Current:** GitHub only
**Target:** GitLab, Bitbucket, generic Git

**Trigger Conditions:**
- GitLab: 20+ user requests OR enterprise customer
- Bitbucket: Enterprise customer requirement
- Self-hosted: Enterprise deployment needs

**Implementation Steps:**
1. Abstract GitHub service to Git provider interface
2. Implement GitLab OAuth and API
3. Implement Bitbucket OAuth and API
4. Add provider selection in UI
5. Update repo selector component

---

## 10. Risk Assessment

### High Risk

| Risk | Impact | Mitigation |
|------|--------|------------|
| Cloud Run Job costs explode | High bills | Daily limits (100/user), budget alerts, quotas |
| Generated code has security issues | User systems compromised | Security scan by default, sandbox execution |
| LLM generates harmful code | Reputation damage | Output filtering, review prompts |
| GitHub token leaks | User repos compromised | Encryption, minimal scopes, rotation |
| Preview server abuse | Resource drain | 30-min expiry, rate limiting |

### Medium Risk

| Risk | Impact | Mitigation |
|------|--------|------------|
| Validation loop infinite retries | Cost overrun | Hard 5-retry limit, timeout per attempt |
| Container escapes | System compromise | Use Cloud Run (managed), no privileged |
| Rate limits from LLM providers | Service disruption | Failover chain, caching, queuing |
| Large ZIP files | Storage costs | 50MB max, auto-cleanup |
| ChromaDB grows too large | Performance issues | Index pruning, user quotas |

### Low Risk

| Risk | Impact | Mitigation |
|------|--------|------------|
| Language detection wrong | Poor UX | User confirmation |
| Cold start latency | Slow first request | Keep-warm, user feedback |
| Template outdated | Bad code | Version templates, community updates |

---

## 11. Appendices

### Appendix A: Environment Variables

```bash
# Existing (keep)
SECRET_KEY=xxx
GROQ_API_KEY=xxx
LLM_PROVIDER=groq
CHROMA_PERSIST_DIR=/data/chroma

# Database
DATABASE_URL=sqlite:///data/app.db

# Artifact Storage (filesystem, not GCS)
ARTIFACT_STORAGE_PATH=/data/artifacts
ARTIFACT_MAX_SIZE_MB=50
ARTIFACT_RETENTION_DAYS=30

# Execution
EXECUTION_MAX_RETRIES=5
EXECUTION_TIMEOUT_SECONDS=120
EXECUTION_DAILY_LIMIT=100
CLOUD_RUN_PROJECT=your-project
CLOUD_RUN_REGION=asia-east1

# Preview
PREVIEW_BASE_URL=https://preview.your-domain.com
PREVIEW_EXPIRY_MINUTES=30
PREVIEW_MAX_CONCURRENT=10

# Security Scanning
SNYK_API_KEY=xxx  # Optional
ENABLE_SECURITY_SCAN=true
BLOCK_HIGH_SEVERITY=true

# LLM Router
DEEPSEEK_API_KEY=xxx
OLLAMA_BASE_URL=http://localhost:11434
LLM_SIMPLE_PROVIDER=ollama
LLM_MEDIUM_PROVIDER=groq
LLM_COMPLEX_PROVIDER=groq

# GitHub OAuth
GITHUB_CLIENT_ID=xxx
GITHUB_CLIENT_SECRET=xxx
GITHUB_CALLBACK_URL=https://your-app.com/github/callback

# Cost Tracking
COST_ALERT_THRESHOLD=50
COST_LIMIT_MONTHLY=200
```

### Appendix B: Ollama Model Setup

```bash
# Required models for local execution
ollama pull deepseek-coder-v2:16b    # Primary code (12GB VRAM)
ollama pull llama3.1:8b               # Fallback (6GB VRAM)
ollama pull qwen2.5-coder:7b          # Lightweight (6GB VRAM)

# Optional for better quality
ollama pull codellama:34b             # High quality (24GB VRAM)
```

### Appendix C: Estimated Costs

| Component | Monthly Estimate |
|-----------|-----------------|
| Cloud Run (main app) | $20-50 |
| Cloud Run Jobs (execution) | $30-100 |
| Preview servers | $10-30 |
| Sandbox (Playwright) | $10-20 |
| Mock servers | $5-10 |
| Filesystem storage | $5-10 |
| Groq API | $10-30 |
| DeepSeek API | $5-15 |
| Snyk (optional) | $0-50 |
| **Total** | **$95-315/month** |

*Based on ~1000 executions/month, ~100 active users*

### Appendix D: Code Quality Scoring Algorithm

```python
def calculate_quality_score(execution_result):
    score = 10  # Start with perfect score

    # Test coverage (-2 max)
    if execution_result.test_coverage < 50:
        score -= 2
    elif execution_result.test_coverage < 80:
        score -= 1

    # Lint issues (-2 max)
    lint_errors = len(execution_result.lint_results.get('errors', []))
    if lint_errors > 5:
        score -= 2
    elif lint_errors > 0:
        score -= 1

    # Security vulnerabilities (-3 max)
    high_vulns = sum(1 for v in execution_result.security_results
                     if v['severity'] == 'high')
    medium_vulns = sum(1 for v in execution_result.security_results
                       if v['severity'] == 'medium')
    score -= min(high_vulns * 2, 3)
    score -= min(medium_vulns * 0.5, 1)

    # Complexity penalty (-2 max)
    if execution_result.complexity_score > 8:
        score -= 2
    elif execution_result.complexity_score > 6:
        score -= 1

    # Retry penalty (-1 max)
    if execution_result.attempt_number > 3:
        score -= 1

    return max(1, min(10, score))
```

---

## Summary

This implementation plan transforms the API Assistant into a full-featured **Intelligent Self-Validating Coding Agent** with:

| Category | Features |
|----------|----------|
| **Core** | Code generation, validation loop, multi-language support |
| **Output** | Inline snippets, ZIP bundles, GitHub PRs |
| **Validation** | Tests, lint, security scanning |
| **Visual** | Browser sandbox, live preview, code diff |
| **Tooling** | Templates, mock servers, replay |
| **Integration** | GitHub (read-only), semantic code search |
| **Quality** | Quality scoring, dependency analysis |

**Storage is simplified:**
- **SQLite** for all metadata
- **Filesystem** for files
- **ChromaDB** for semantic code search only

**Implementation follows priority:**
1. Foundation & cleanup
2. Core coding agent
3. Output delivery
4. High-priority features (sandbox, preview, security)
5. Medium-priority features (templates, replay, quality)
6. Language expansion
7. GitHub integration
8. Polish & production
