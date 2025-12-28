# Quick Start Guide

Get the API Assistant running in 5 minutes!

## Choose Your Setup

### Option 1: Docker (Recommended) ⚡

**Prerequisites**: Docker and Docker Compose installed

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/Api-Assistant.git
cd Api-Assistant

# 2. Start all services
./scripts/deploy.sh development

# 3. Access the application
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
# API Docs: http://localhost:8000/docs
```

That's it! The application is now running.

### Option 2: Local Development 🔧

**Prerequisites**: Python 3.11+, Node.js 20+, npm

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/Api-Assistant.git
cd Api-Assistant

# 2. Run setup script
./scripts/local-dev.sh

# 3. Start backend (Terminal 1)
source venv/bin/activate
uvicorn src.api.app:app --reload

# 4. Start frontend (Terminal 2)
cd frontend
npm run dev
```

Access:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000

## First Steps

1. **Upload API Documentation**
   - Navigate to http://localhost:3000
   - Click "Documents" → "Upload"
   - Select your OpenAPI/Swagger JSON/YAML file

2. **Search APIs**
   - Go to "Search" tab
   - Enter your query (e.g., "user authentication endpoints")
   - View results with relevance scores

3. **Chat with AI**
   - Open "Chat" tab
   - Ask questions about your APIs
   - Get code examples and integration help

4. **Create Sessions**
   - Navigate to "Sessions"
   - Create a new session to track conversations
   - Customize search settings per session

5. **Generate Diagrams**
   - Visit "Diagrams" tab
   - Generate sequence diagrams from endpoints
   - Create authentication flow diagrams

## Configuration

### LLM Provider

Choose between local (Ollama) or cloud (Groq):

**Option A: Ollama (Local, Free)**
```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Pull model
ollama pull deepseek-coder:6.7b

# Update .env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
```

**Option B: Groq (Cloud, Fast, Free API)**
```bash
# Get API key from https://console.groq.com

# Update .env
LLM_PROVIDER=groq
GROQ_API_KEY=your_api_key_here
```

## Environments

### Development
```bash
./scripts/deploy.sh development
```
- Hot-reloading enabled
- Debug mode ON
- Source code mounted

### QA/Testing
```bash
./scripts/deploy.sh qa
```
- Production-like setup
- Analytics enabled
- Performance monitoring

### Production
```bash
./scripts/deploy.sh production
```
- Optimized builds
- Security hardened
- Auto-restart enabled

## Common Commands

```bash
# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart services
docker-compose restart

# Check health
./scripts/health-check.sh

# Run tests
cd frontend && npm test

# Build for production
cd frontend && npm run build
```

## Troubleshooting

**Port already in use?**
```bash
# Change ports in docker-compose.yml
ports:
  - "3001:3000"  # Frontend
  - "8001:8000"  # Backend
```

**Frontend can't connect to backend?**
```bash
# Update frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Docker build fails?**
```bash
# Clear cache and rebuild
docker-compose down -v
docker system prune -a
docker-compose up --build
```

## Next Steps

- 📖 Read [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment guides
- 🎨 Check [frontend/ACCESSIBILITY.md](frontend/ACCESSIBILITY.md) for accessibility features
- ⚡ See [frontend/PERFORMANCE.md](frontend/PERFORMANCE.md) for optimization tips
- 🧪 Review test setup in `frontend/jest.config.js`

## Need Help?

- [GitHub Issues](https://github.com/yourusername/Api-Assistant/issues)
- [Documentation](README.md)
- [Deployment Guide](DEPLOYMENT.md)

Happy coding! 🚀
