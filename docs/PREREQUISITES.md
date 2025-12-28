# Prerequisites & Setup Guide

This guide covers all prerequisites and setup instructions for developing and running the API Integration Assistant, including both the current backend/Streamlit UI and the new Next.js frontend.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Backend Setup (Required)](#backend-setup-required)
3. [Current Streamlit UI Setup](#current-streamlit-ui-setup)
4. [New Next.js Frontend Setup](#new-nextjs-frontend-setup)
5. [Development Tools](#development-tools)
6. [Environment Configuration](#environment-configuration)
7. [Verification](#verification)

---

## System Requirements

### Operating System
- **Linux** (Ubuntu 20.04+ recommended)
- **macOS** (10.15 Catalina or later)
- **Windows** (10/11 with WSL2 recommended for development)

### Required Software

| Software | Minimum Version | Recommended Version | Purpose |
|----------|----------------|---------------------|---------|
| **Python** | 3.9 | 3.11 | Backend API & ML models |
| **Node.js** | 18.0 | 20.x LTS | Next.js frontend |
| **npm** or **yarn** | npm 9+ / yarn 1.22+ | npm 10+ | Package management |
| **Git** | 2.30+ | Latest | Version control |

### Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **RAM** | 8 GB | 16 GB+ |
| **Storage** | 10 GB free | 20 GB+ free |
| **CPU** | 2 cores | 4+ cores |

**Note**: The application uses embedding models (sentence-transformers) which benefit from more RAM and CPU cores.

---

## Backend Setup (Required)

The FastAPI backend must be running for both the current Streamlit UI and the new Next.js frontend to function.

### 1. Install Python

**Linux/macOS:**
```bash
# Check current version
python3 --version

# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip

# macOS (via Homebrew)
brew install python@3.11
```

**Windows:**
1. Download Python 3.11 from [python.org](https://www.python.org/downloads/)
2. Run installer, check "Add Python to PATH"
3. Verify: `python --version`

### 2. Create Virtual Environment

```bash
# Navigate to project root
cd Api-Assistant

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# Linux/macOS:
source .venv/bin/activate

# Windows PowerShell:
.venv\Scripts\Activate.ps1

# Windows Command Prompt:
.venv\Scripts\activate.bat
```

### 3. Install Python Dependencies

```bash
# Ensure virtual environment is activated (you should see (.venv) in prompt)
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

**Expected Installation Time**: 5-10 minutes (downloads ~2GB including ML models)

### 4. Verify Backend Installation

```bash
# Test CLI
python api_assistant_cli.py info version

# Expected output:
# API Integration Assistant CLI
# Version: 1.0.0
# Python: 3.11.x
```

---

## Current Streamlit UI Setup

The current UI is included with the backend dependencies. No additional setup required.

### Running Streamlit UI

```bash
# Ensure virtual environment is activated
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\Activate.ps1  # Windows PowerShell

# Start Streamlit
# Linux/macOS:
PYTHONPATH=. streamlit run src/main.py

# Windows PowerShell:
$env:PYTHONPATH = "."; streamlit run src/main.py
```

**Expected Output**:
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

**Troubleshooting**:
- Port 8501 already in use: `streamlit run src/main.py --server.port 8502`
- PYTHONPATH errors: Run from project root directory

---

## New Next.js Frontend Setup

This section covers setup for the new Next.js UI being developed as part of the UI replacement plan.

### 1. Install Node.js and npm

**Linux (Ubuntu/Debian):**
```bash
# Using NodeSource repository for latest LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify
node --version  # Should show v20.x.x
npm --version   # Should show 10.x.x
```

**macOS:**
```bash
# Using Homebrew
brew install node@20

# Verify
node --version
npm --version
```

**Windows:**
1. Download Node.js 20.x LTS from [nodejs.org](https://nodejs.org/)
2. Run installer (includes npm)
3. Verify in new terminal: `node --version` and `npm --version`

### 2. Alternative: Install Yarn (Optional)

```bash
# Via npm
npm install -g yarn

# Verify
yarn --version
```

### 3. Initialize Next.js Project (Week 1 Task)

This will be done as part of Week 1 implementation:

```bash
# From project root
npx create-next-app@latest frontend \
  --typescript \
  --tailwind \
  --app \
  --src-dir \
  --import-alias "@/*" \
  --no-eslint

cd frontend
npm install
```

**Project Structure** (will be created):
```
frontend/
├── src/
│   ├── app/          # Next.js 14 App Router
│   ├── components/   # React components
│   ├── lib/          # Utilities, API client, stores
│   └── styles/       # Global styles
├── public/           # Static assets
├── package.json
├── tsconfig.json
└── next.config.js
```

### 4. Install Frontend Dependencies (Week 1 Task)

```bash
cd frontend

# Core dependencies
npm install axios zustand @tanstack/react-query

# shadcn/ui setup
npx shadcn-ui@latest init
npx shadcn-ui@latest add button input card dialog toast

# Dev dependencies
npm install -D @types/node @typescript-eslint/parser
```

---

## Development Tools

### Recommended IDE/Editor

**Visual Studio Code** (Recommended):
```bash
# Install VS Code extensions
code --install-extension ms-python.python
code --install-extension dbaeumer.vscode-eslint
code --install-extension esbenp.prettier-vscode
code --install-extension bradlc.vscode-tailwindcss
```

**Alternative**: PyCharm, WebStorm, or any editor with Python and TypeScript support

### Browser Developer Tools

**Recommended Browsers**:
- Chrome/Chromium (best DevTools)
- Firefox Developer Edition
- Edge (Chromium-based)

---

## Environment Configuration

### 1. Environment Variables

Create `.env` file in project root:

```bash
# .env (for backend)

# LLM Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

# Alternative: Use Groq for faster inference
# GROQ_API_KEY=your_groq_api_key_here
# GROQ_MODEL=llama-3.1-70b-versatile

# ChromaDB Configuration
CHROMA_PERSIST_DIRECTORY=./data/chroma_db

# Session Storage
SESSIONS_FILE=./data/sessions.json

# Logging
LOG_LEVEL=INFO

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

Create `.env.local` file in `frontend/` directory:

```bash
# frontend/.env.local (for Next.js)

# Backend API URL
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Feature flags (optional)
NEXT_PUBLIC_ENABLE_ANALYTICS=false
NEXT_PUBLIC_ENABLE_DEBUG=true
```

### 2. Git Configuration

Add to `.gitignore`:

```bash
# Python
.venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
pip-log.txt
pip-delete-this-directory.txt

# Node.js
frontend/node_modules/
frontend/.next/
frontend/out/
frontend/build/

# Environment
.env
.env.local
.env.*.local

# Data
data/chroma_db/
data/sessions.json
data/exports/

# IDE
.vscode/
.idea/
*.swp
*.swo
```

---

## Verification

### Backend Verification Checklist

```bash
# ✅ 1. Python version
python --version
# Expected: Python 3.9+ (3.11 recommended)

# ✅ 2. Virtual environment activated
which python
# Expected: /path/to/Api-Assistant/.venv/bin/python

# ✅ 3. Dependencies installed
pip list | grep streamlit
pip list | grep langchain
pip list | grep chromadb
# Expected: All packages present

# ✅ 4. CLI working
python api_assistant_cli.py info version
# Expected: Version 1.0.0

# ✅ 5. Parse test file
python api_assistant_cli.py parse file test_data/openapi/jsonplaceholder.yaml
# Expected: Successfully parsed X endpoints

# ✅ 6. Streamlit starts
PYTHONPATH=. streamlit run src/main.py &
# Expected: Server starts on http://localhost:8501
# Kill with: pkill -f streamlit
```

### Frontend Verification Checklist (After Week 1 Setup)

```bash
# ✅ 1. Node.js version
node --version
# Expected: v18.0+ (v20.x recommended)

# ✅ 2. npm version
npm --version
# Expected: 9.0+ (10.x recommended)

# ✅ 3. Next.js project created
cd frontend
ls -la
# Expected: package.json, tsconfig.json, next.config.js present

# ✅ 4. Dependencies installed
npm list --depth=0 | grep next
npm list --depth=0 | grep axios
# Expected: All core dependencies present

# ✅ 5. TypeScript compiles
npx tsc --noEmit
# Expected: No errors

# ✅ 6. Dev server starts
npm run dev
# Expected: Server starts on http://localhost:3000

# ✅ 7. Backend connectivity (after API client setup)
curl http://localhost:8000/health
# Expected: {"status":"healthy"}
```

---

## Common Issues & Solutions

### Issue 1: Python version mismatch

**Problem**: System has Python 3.8 but project needs 3.9+

**Solution**:
```bash
# Install pyenv for multiple Python versions
curl https://pyenv.run | bash

# Install Python 3.11
pyenv install 3.11.0
pyenv local 3.11.0

# Create venv
python -m venv .venv
```

### Issue 2: Port conflicts

**Problem**: Port 8501 (Streamlit) or 8000 (FastAPI) already in use

**Solution**:
```bash
# Find process using port
lsof -i :8501  # Linux/macOS
netstat -ano | findstr :8501  # Windows

# Kill process or use different port
streamlit run src/main.py --server.port 8502
```

### Issue 3: ChromaDB initialization fails

**Problem**: Permission errors or corrupted database

**Solution**:
```bash
# Remove existing database
rm -rf data/chroma_db/

# Re-initialize (will auto-create on first parse)
python api_assistant_cli.py parse file test_data/openapi/jsonplaceholder.yaml --add
```

### Issue 4: Node.js installation issues on Linux

**Problem**: Package manager has old Node.js version

**Solution**:
```bash
# Use nvm (Node Version Manager)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc

nvm install 20
nvm use 20
```

### Issue 5: Ollama not available

**Problem**: LLM model not found

**Solution**:
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull model
ollama pull llama3.2:3b

# Verify
ollama list
```

---

## Next Steps

After completing prerequisites:

1. ✅ **Backend Ready**: Run `python api_assistant_cli.py info version`
2. ✅ **Streamlit Ready**: Run `PYTHONPATH=. streamlit run src/main.py`
3. ⏳ **Week 1 Implementation**: Initialize Next.js project (see `docs/UI_REPLACEMENT_PLAN.md`)

---

## Additional Resources

- **Python**: https://www.python.org/downloads/
- **Node.js**: https://nodejs.org/
- **Next.js Docs**: https://nextjs.org/docs
- **shadcn/ui**: https://ui.shadcn.com/
- **Ollama**: https://ollama.com/
- **ChromaDB**: https://docs.trychroma.com/

---

**Need Help?**
- Check `TESTING_GUIDE.md` for testing workflows
- Review `QUICK_START.md` for quick commands
- See `docs/UI_REPLACEMENT_PLAN.md` for implementation plan
