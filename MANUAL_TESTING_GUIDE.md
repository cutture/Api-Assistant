# Manual Testing Guide

This guide provides step-by-step instructions to set up and test the Intelligent Coding Agent application locally.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Setup](#local-setup)
   - [Backend Setup](#backend-setup)
   - [Frontend Setup](#frontend-setup)
3. [Test Cases](#test-cases)
   - [Authentication](#1-authentication)
   - [Sessions](#2-sessions)
   - [Chat & Code Generation](#3-chat--code-generation)
   - [Search](#4-search)
   - [Artifacts](#5-artifacts)
   - [Security Scanning](#6-security-scanning)
   - [Mock Servers](#7-mock-servers)
   - [Templates](#8-templates)
   - [Database Queries](#9-database-queries)
   - [GitHub Integration](#10-github-integration)
   - [Webhooks](#11-webhooks)
   - [Scheduled Tasks](#12-scheduled-tasks)
   - [Collaboration](#13-collaboration)
   - [Git Providers](#14-git-providers-gitlabbitbucket)
   - [Live Preview & Sandbox](#15-live-preview--sandbox)

---

## Prerequisites

Before starting, ensure you have the following installed:

- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** - [Download](https://nodejs.org/)
- **Git** - [Download](https://git-scm.com/)
- **Groq API Key** (recommended) - [Get free key](https://console.groq.com)
- **OR Ollama** (for local LLM) - [Download](https://ollama.com/download)

---

## Local Setup

### Backend Setup

1. **Clone the repository and navigate to it:**
   ```bash
   git clone <your-repo-url>
   cd Api-Assistant
   ```

2. **Create a Python virtual environment:**
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create environment configuration:**
   ```bash
   # Create .env file from example
   cp env.example.yaml .env
   ```

5. **Edit `.env` file with your configuration:**
   ```bash
   # Required
   SECRET_KEY=your-secret-key-here-min-32-chars

   # LLM Provider (choose one)
   # Option A: Groq (recommended - fast cloud inference)
   LLM_PROVIDER=groq
   GROQ_API_KEY=your-groq-api-key

   # Option B: Ollama (local, private)
   # LLM_PROVIDER=ollama
   # OLLAMA_BASE_URL=http://localhost:11434

   # Optional: GitHub OAuth (for GitHub integration)
   GITHUB_CLIENT_ID=your-github-client-id
   GITHUB_CLIENT_SECRET=your-github-client-secret

   # CORS (for frontend)
   ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
   ```

6. **Start the backend server:**
   ```bash
   uvicorn src.api.app:app --reload --port 8000
   ```

7. **Verify backend is running:**
   - Open http://localhost:8000/health in your browser
   - You should see: `{"status": "healthy", "version": "1.0.0", ...}`
   - API docs available at: http://localhost:8000/docs

### Frontend Setup

1. **Open a new terminal and navigate to frontend:**
   ```bash
   cd frontend
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

3. **Create frontend environment file:**
   ```bash
   # Create .env.local file
   echo "NEXT_PUBLIC_API_BASE_URL=http://localhost:8000" > .env.local
   ```

4. **Start the frontend development server:**
   ```bash
   npm run dev
   ```

5. **Access the application:**
   - Open http://localhost:3000 in your browser
   - You should see the Coding Agent login page

---

## Test Cases

### 1. Authentication

#### 1.1 User Registration
1. Navigate to http://localhost:3000/register
2. Fill in the registration form:
   - Email: `test@example.com`
   - Password: `TestPassword123!`
   - Confirm Password: `TestPassword123!`
3. Click "Register"
4. **Expected:** Redirected to login page or chat (if auto-login enabled)

#### 1.2 User Login
1. Navigate to http://localhost:3000/login
2. Enter credentials:
   - Email: `test@example.com`
   - Password: `TestPassword123!`
3. Click "Login"
4. **Expected:** Redirected to /chat page

#### 1.3 Guest Access
1. Navigate to http://localhost:3000/login
2. Click "Continue as Guest" (if available)
3. **Expected:** Access to limited functionality without account

#### 1.4 Logout
1. While logged in, click on user menu (top right)
2. Click "Logout"
3. **Expected:** Redirected to login page, session cleared

#### 1.5 API Test (Backend)
```bash
# Register a new user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "api@test.com", "password": "TestPass123!"}'

# Login and get token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "api@test.com", "password": "TestPass123!"}'

# Expected: {"access_token": "...", "refresh_token": "...", "token_type": "bearer"}
```

---

### 2. Sessions

#### 2.1 Create Session
1. Login to the application
2. Navigate to /sessions
3. Click "New Session" button
4. **Expected:** New session appears in the list

#### 2.2 View Sessions
1. Navigate to /sessions
2. **Expected:** List of your sessions with:
   - Session ID
   - Created date
   - Last accessed date
   - Status (active/inactive/expired)

#### 2.3 Delete Session
1. Navigate to /sessions
2. Click delete icon on a session
3. Confirm deletion
4. **Expected:** Session removed from list

#### 2.4 API Test (Backend)
```bash
# Get auth token first (from login)
TOKEN="your-access-token"

# Create session
curl -X POST http://localhost:8000/sessions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'

# List sessions
curl -X GET http://localhost:8000/sessions \
  -H "Authorization: Bearer $TOKEN"

# Get specific session
curl -X GET http://localhost:8000/sessions/{session_id} \
  -H "Authorization: Bearer $TOKEN"
```

---

### 3. Chat & Code Generation

#### 3.1 Basic Chat
1. Navigate to /chat
2. Type: "Hello, what can you help me with?"
3. Press Enter or click Send
4. **Expected:** AI response explaining capabilities

#### 3.2 Code Generation (Python)
1. In chat, type: "Write a Python function to calculate factorial"
2. **Expected:**
   - Code panel appears on the right
   - Python code with proper syntax highlighting
   - Copy button works

#### 3.3 Code Generation (JavaScript)
1. Type: "Write a JavaScript function to reverse a string"
2. **Expected:** JavaScript code displayed in code panel

#### 3.4 Multi-language Request
1. Type: "Show me how to make an HTTP GET request in Python and JavaScript"
2. **Expected:** Both Python and JavaScript examples

#### 3.5 Code with Tests
1. Type: "Write a Python function to check if a number is prime, include unit tests"
2. **Expected:** Function code AND test cases

#### 3.6 File Upload in Chat
1. Click attachment icon in chat
2. Upload a code file (e.g., `.py` or `.js`)
3. Ask: "Explain what this code does"
4. **Expected:** Analysis of uploaded code

#### 3.7 API Test (Backend)
```bash
TOKEN="your-access-token"

# Send chat message
curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Write a Python hello world function",
    "session_id": "optional-session-id"
  }'
```

---

### 4. Search

#### 4.1 Basic Search
1. Use the search functionality (if available in UI)
2. Search for: "authentication"
3. **Expected:** Relevant results from indexed content

#### 4.2 API Test (Backend)
```bash
# Vector search
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "user authentication",
    "n_results": 5,
    "mode": "vector"
  }'

# Hybrid search
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "create user API",
    "n_results": 5,
    "mode": "hybrid"
  }'

# Search with query expansion
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "auth",
    "n_results": 5,
    "mode": "hybrid",
    "use_query_expansion": true
  }'
```

---

### 5. Artifacts

#### 5.1 Upload Artifact
1. Navigate to /artifacts
2. Click "Upload" or drag-and-drop a file
3. Select a code file (e.g., `example.py`)
4. **Expected:** File appears in artifact list

#### 5.2 List Artifacts
1. Navigate to /artifacts
2. **Expected:** List showing:
   - File name
   - Type (uploaded/generated)
   - Size
   - Upload date

#### 5.3 Download Artifact
1. Click download icon on an artifact
2. **Expected:** File downloads to your computer

#### 5.4 Delete Artifact
1. Click delete icon on an artifact
2. Confirm deletion
3. **Expected:** Artifact removed from list

#### 5.5 API Test (Backend)
```bash
TOKEN="your-access-token"

# Upload artifact
curl -X POST http://localhost:8000/artifacts/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/your/file.py" \
  -F "artifact_type=uploaded"

# List artifacts
curl -X GET http://localhost:8000/artifacts \
  -H "Authorization: Bearer $TOKEN"

# Download artifact
curl -X GET http://localhost:8000/artifacts/{artifact_id}/download \
  -H "Authorization: Bearer $TOKEN" \
  -o downloaded_file.py

# Delete artifact
curl -X DELETE http://localhost:8000/artifacts/{artifact_id} \
  -H "Authorization: Bearer $TOKEN"
```

---

### 6. Security Scanning

#### 6.1 Scan Code for Vulnerabilities
1. Use the security scanning feature
2. Paste or upload code with potential issues:
   ```python
   import os
   password = "hardcoded_secret123"
   os.system(user_input)  # Command injection
   query = f"SELECT * FROM users WHERE id = {user_id}"  # SQL injection
   ```
3. **Expected:** Report showing:
   - Hardcoded credentials (critical)
   - Command injection (high)
   - SQL injection (high)

#### 6.2 API Test (Backend)
```bash
TOKEN="your-access-token"

# Scan code
curl -X POST http://localhost:8000/security/scan \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "password = \"secret123\"\nos.system(user_input)",
    "language": "python"
  }'

# Get supported languages
curl -X GET http://localhost:8000/security/supported-languages \
  -H "Authorization: Bearer $TOKEN"
```

---

### 7. Mock Servers

#### 7.1 Create Mock Server
1. Navigate to mock server management
2. Click "Create Mock Server"
3. Configure endpoint:
   - Method: GET
   - Path: /api/users
   - Response: `[{"id": 1, "name": "John"}]`
   - Status: 200
4. **Expected:** Mock server created with base URL

#### 7.2 Test Mock Endpoint
1. Copy the mock server URL
2. Make request to the endpoint
3. **Expected:** Returns configured response

#### 7.3 API Test (Backend)
```bash
TOKEN="your-access-token"

# Create mock server
curl -X POST http://localhost:8000/mocks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test API",
    "endpoints": [
      {
        "method": "GET",
        "path": "/users",
        "response_body": [{"id": 1, "name": "Test"}],
        "status_code": 200,
        "headers": {},
        "delay_ms": 0
      }
    ]
  }'

# List mock servers
curl -X GET http://localhost:8000/mocks \
  -H "Authorization: Bearer $TOKEN"

# Generate CRUD endpoints
curl -X POST http://localhost:8000/mocks/generate/crud \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"resource_name": "products"}'

# Delete mock server
curl -X DELETE http://localhost:8000/mocks/{mock_id} \
  -H "Authorization: Bearer $TOKEN"
```

---

### 8. Templates

#### 8.1 Browse Templates
1. Navigate to templates section
2. **Expected:** List of available templates:
   - REST API (FastAPI/Express)
   - Authentication
   - Database models
   - Testing

#### 8.2 Use Template
1. Select a template (e.g., "FastAPI REST API")
2. Fill in parameters:
   - Resource name: "products"
   - Fields: id, name, price
3. Click "Generate"
4. **Expected:** Generated code from template

#### 8.3 API Test (Backend)
```bash
TOKEN="your-access-token"

# List templates
curl -X GET http://localhost:8000/templates \
  -H "Authorization: Bearer $TOKEN"

# Get template categories
curl -X GET http://localhost:8000/templates/categories \
  -H "Authorization: Bearer $TOKEN"

# Render template
curl -X POST http://localhost:8000/templates/{template_id}/render \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "resource_name": "products",
      "fields": ["id", "name", "price"]
    }
  }'
```

---

### 9. Database Queries

#### 9.1 Generate SELECT Query
1. Navigate to database query builder
2. Select database type: PostgreSQL
3. Enter: "Get all users who registered in the last 7 days"
4. **Expected:** Generated SQL query with validation

#### 9.2 Validate Query
1. Enter a SQL query
2. Click "Validate"
3. **Expected:**
   - Validation result (valid/invalid)
   - Risk level assessment
   - Security warnings if applicable

#### 9.3 API Test (Backend)
```bash
TOKEN="your-access-token"

# Validate query
curl -X POST http://localhost:8000/database/validate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT * FROM users WHERE id = 1",
    "database_type": "postgresql"
  }'

# Generate SELECT query
curl -X POST http://localhost:8000/database/generate/select \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "table": "users",
    "columns": ["id", "name", "email"],
    "conditions": {"status": "active"},
    "database_type": "postgresql"
  }'

# Natural language to query
curl -X POST http://localhost:8000/database/generate/natural-language \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Get all orders from last month with total over 100",
    "database_type": "postgresql",
    "schema_context": "orders(id, user_id, total, created_at)"
  }'

# Get supported database types
curl -X GET http://localhost:8000/database/types \
  -H "Authorization: Bearer $TOKEN"
```

---

### 10. GitHub Integration

> **Note:** Requires GitHub OAuth configuration in `.env`

#### 10.1 Connect GitHub Account
1. Navigate to settings or GitHub integration section
2. Click "Connect GitHub"
3. Authorize the application
4. **Expected:** GitHub account connected, username displayed

#### 10.2 List Repositories
1. After connecting GitHub
2. View repository list
3. **Expected:** Your GitHub repositories displayed

#### 10.3 Analyze Repository
1. Select a repository
2. Click "Analyze"
3. **Expected:**
   - Framework detection (React, FastAPI, etc.)
   - Project structure analysis
   - Dependencies list

#### 10.4 API Test (Backend)
```bash
TOKEN="your-access-token"

# Check GitHub connection status
curl -X GET http://localhost:8000/github/status \
  -H "Authorization: Bearer $TOKEN"

# List repositories (requires GitHub OAuth)
curl -X GET http://localhost:8000/github/repos \
  -H "Authorization: Bearer $TOKEN"

# Analyze repository
curl -X POST http://localhost:8000/github/repos/{owner}/{repo}/analyze \
  -H "Authorization: Bearer $TOKEN"

# Get file content
curl -X GET "http://localhost:8000/github/repos/{owner}/{repo}/file?path=README.md" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 11. Webhooks

#### 11.1 Create Webhook
1. Navigate to webhook settings
2. Click "Create Webhook"
3. Configure:
   - URL: `https://your-server.com/webhook`
   - Events: `execution.completed`, `artifact.created`
   - Provider: Custom HTTP
4. **Expected:** Webhook created with secret key

#### 11.2 Test Webhook
1. Click "Test" on a webhook
2. **Expected:** Test payload sent to URL

#### 11.3 API Test (Backend)
```bash
TOKEN="your-access-token"

# Create webhook
curl -X POST http://localhost:8000/webhooks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Webhook",
    "url": "https://example.com/webhook",
    "events": ["execution.completed", "artifact.created"],
    "provider": "custom"
  }'

# List webhooks
curl -X GET http://localhost:8000/webhooks \
  -H "Authorization: Bearer $TOKEN"

# Get available events
curl -X GET http://localhost:8000/webhooks/events \
  -H "Authorization: Bearer $TOKEN"

# Test webhook
curl -X POST http://localhost:8000/webhooks/{webhook_id}/test \
  -H "Authorization: Bearer $TOKEN"

# Get delivery history
curl -X GET http://localhost:8000/webhooks/{webhook_id}/deliveries \
  -H "Authorization: Bearer $TOKEN"
```

---

### 12. Scheduled Tasks

#### 12.1 Create Scheduled Task
1. Navigate to scheduler section
2. Click "Create Task"
3. Configure:
   - Name: "Daily Cleanup"
   - Type: Cron
   - Schedule: `0 0 * * *` (daily at midnight)
   - Task Type: cleanup
4. **Expected:** Task created and scheduled

#### 12.2 Pause/Resume Task
1. Click "Pause" on a running task
2. **Expected:** Task status changes to paused
3. Click "Resume"
4. **Expected:** Task status changes to active

#### 12.3 API Test (Backend)
```bash
TOKEN="your-access-token"

# Create scheduled task (cron)
curl -X POST http://localhost:8000/scheduler/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Daily Report",
    "task_type": "webhook",
    "schedule_type": "cron",
    "schedule_value": "0 9 * * *",
    "payload": {"webhook_id": "123"}
  }'

# Create one-time task
curl -X POST http://localhost:8000/scheduler/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "One-time Task",
    "task_type": "cleanup",
    "schedule_type": "once",
    "schedule_value": "2024-12-31T23:59:00Z"
  }'

# List tasks
curl -X GET http://localhost:8000/scheduler/tasks \
  -H "Authorization: Bearer $TOKEN"

# Pause task
curl -X POST http://localhost:8000/scheduler/tasks/{task_id}/pause \
  -H "Authorization: Bearer $TOKEN"

# Resume task
curl -X POST http://localhost:8000/scheduler/tasks/{task_id}/resume \
  -H "Authorization: Bearer $TOKEN"

# Run immediately
curl -X POST http://localhost:8000/scheduler/tasks/{task_id}/run \
  -H "Authorization: Bearer $TOKEN"

# Get execution history
curl -X GET http://localhost:8000/scheduler/tasks/{task_id}/executions \
  -H "Authorization: Bearer $TOKEN"
```

---

### 13. Collaboration

#### 13.1 Create Team
1. Navigate to collaboration/teams section
2. Click "Create Team"
3. Enter team name and description
4. **Expected:** Team created, you are owner

#### 13.2 Share Session
1. Open a session
2. Click "Share"
3. Configure:
   - Team or public link
   - Expiration (optional)
4. **Expected:** Share link generated

#### 13.3 API Test (Backend)
```bash
TOKEN="your-access-token"

# Create team
curl -X POST http://localhost:8000/collaboration/teams \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Team",
    "description": "Development team"
  }'

# List teams
curl -X GET http://localhost:8000/collaboration/teams \
  -H "Authorization: Bearer $TOKEN"

# Add team member
curl -X POST http://localhost:8000/collaboration/teams/{team_id}/members \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-uuid",
    "permission": "editor"
  }'

# Share session
curl -X POST http://localhost:8000/collaboration/sessions/share \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session-uuid",
    "name": "Shared Session",
    "is_public": true
  }'

# Join shared session
curl -X POST http://localhost:8000/collaboration/sessions/shared/{share_id}/join \
  -H "Authorization: Bearer $TOKEN"
```

---

### 14. Git Providers (GitLab/Bitbucket)

> **Note:** Requires GitLab/Bitbucket OAuth configuration

#### 14.1 Connect GitLab
1. Navigate to settings
2. Click "Connect GitLab"
3. Authorize the application
4. **Expected:** GitLab account connected

#### 14.2 API Test (Backend)
```bash
TOKEN="your-access-token"

# Get available providers
curl -X GET http://localhost:8000/git/providers \
  -H "Authorization: Bearer $TOKEN"

# Check GitLab connection status
curl -X GET http://localhost:8000/git/gitlab/status \
  -H "Authorization: Bearer $TOKEN"

# List GitLab repositories
curl -X GET http://localhost:8000/git/gitlab/repos \
  -H "Authorization: Bearer $TOKEN"

# Create branch (GitLab)
curl -X POST http://localhost:8000/git/gitlab/repos/{owner}/{repo}/branches \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "branch_name": "feature/new-feature",
    "source_branch": "main"
  }'

# Check for conflicts
curl -X POST http://localhost:8000/git/gitlab/repos/{owner}/{repo}/conflicts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "base_branch": "main",
    "head_branch": "feature/new-feature"
  }'
```

---

### 15. Live Preview & Sandbox

#### 15.1 Start Preview Server
1. Generate some code (e.g., a simple web app)
2. Click "Preview" button
3. **Expected:** Preview URL generated, opens in iframe

#### 15.2 Take Screenshot
1. Enter a URL to screenshot
2. Configure viewport (optional)
3. Click "Capture"
4. **Expected:** Screenshot generated and displayed

#### 15.3 API Test (Backend)
```bash
TOKEN="your-access-token"

# Start preview
curl -X POST http://localhost:8000/preview \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "execution_id": "exec-uuid",
    "code": "print(\"Hello World\")",
    "language": "python"
  }'

# Get preview status
curl -X GET http://localhost:8000/preview/{preview_id} \
  -H "Authorization: Bearer $TOKEN"

# List previews
curl -X GET http://localhost:8000/preview \
  -H "Authorization: Bearer $TOKEN"

# Take screenshot
curl -X POST http://localhost:8000/sandbox/screenshot \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "viewport": {"width": 1280, "height": 720},
    "full_page": false
  }'

# Run UI test
curl -X POST http://localhost:8000/sandbox/test-ui \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "assertions": [
      {"type": "title_contains", "value": "Example"}
    ]
  }'
```

---

## Troubleshooting

### Backend Issues

**Port already in use:**
```bash
# Find process using port 8000
lsof -i :8000
# Kill the process
kill -9 <PID>
```

**Database errors:**
```bash
# Reset database
rm -rf data/users.db data/chroma_db
# Restart backend
uvicorn src.api.app:app --reload --port 8000
```

**Import errors:**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Frontend Issues

**Module not found:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**API connection errors:**
1. Verify backend is running: http://localhost:8000/health
2. Check `.env.local` has correct API URL
3. Check CORS settings in backend `.env`

### LLM Issues

**Groq API errors:**
- Verify `GROQ_API_KEY` is set correctly
- Check API key at https://console.groq.com

**Ollama errors:**
```bash
# Check Ollama is running
ollama serve

# Pull required model
ollama pull deepseek-coder:6.7b
```

---

## Running Automated Tests

### Backend Tests
```bash
# Run all tests
pytest -v

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_api/test_app.py -v
```

### Frontend Tests
```bash
cd frontend

# Unit tests
npm test

# E2E tests (requires backend running)
npm run test:e2e
```

---

## API Documentation

When the backend is running, access:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json
