# 🐳 Docker Deployment Guide

Production-ready Docker configuration for API Integration Assistant.

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Deployment Options](#deployment-options)
- [Configuration](#configuration)
- [Volume Management](#volume-management)
- [Health Checks](#health-checks)
- [Scaling & Performance](#scaling--performance)
- [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ RAM available
- (Optional) NVIDIA GPU + nvidia-docker for local LLM

### Option 1: Local Deployment with Ollama (GPU Recommended)

```bash
# 1. Clone the repository
git clone <repository-url>
cd api-assistant

# 2. Create data directories
mkdir -p data/chroma_db logs

# 3. Configure environment (optional)
cp .env.example .env
# Edit .env with your settings

# 4. Start all services
docker-compose up -d

# 5. Pull Ollama model (first time only)
# The ollama-puller service does this automatically
# Or manually:
docker exec api-assistant-ollama ollama pull deepseek-coder:6.7b

# 6. Access the application
open http://localhost:8501
```

### Option 2: Production Deployment with Groq (Cloud LLM)

```bash
# 1. Set up environment variables
export GROQ_API_KEY="your-groq-api-key"

# 2. Create data directories
mkdir -p data/chroma_db logs

# 3. Start production deployment
docker-compose -f docker-compose.prod.yml up -d

# 4. Access the application
open http://localhost:3000
```

---

## 🔧 Deployment Options

### Development Setup (docker-compose.yml)

**Includes:**
- FastAPI backend
- Next.js frontend
- Ollama (local LLM server)
- ChromaDB (embedded in app)

**Use case:** Local development, GPU available

```bash
docker-compose up -d
```

### Production Setup (docker-compose.prod.yml)

**Includes:**
- FastAPI backend
- Next.js frontend
- Groq cloud LLM integration
- ChromaDB (embedded in app)

**Use case:** Production deployment, cloud hosting

```bash
docker-compose -f docker-compose.prod.yml up -d
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# ============================================================================
# LLM Provider Configuration
# ============================================================================

# Choose provider: "ollama" or "groq"
LLM_PROVIDER=ollama

# ----- Ollama Configuration (Local LLM) -----
OLLAMA_MODEL=deepseek-coder:6.7b
# Other options:
# - llama3.2:latest
# - codellama:7b
# - mistral:7b

# ----- Groq Configuration (Cloud LLM) -----
GROQ_API_KEY=your-groq-api-key-here
GROQ_REASONING_MODEL=llama-3.3-70b-versatile
GROQ_CODE_MODEL=llama-3.3-70b-versatile
GROQ_GENERAL_MODEL=llama-3.3-70b-versatile

# ============================================================================
# Application Settings
# ============================================================================

APP_PORT=8501
DEBUG=false
LOG_LEVEL=INFO

# Embeddings
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Web Search
ENABLE_WEB_SEARCH=true
WEB_SEARCH_MIN_RELEVANCE=0.5
WEB_SEARCH_MAX_RESULTS=5
```

### Port Configuration

| Service | Default Port | Environment Variable |
|---------|--------------|---------------------|
| FastAPI Backend | 8000 | `API_PORT` |
| Next.js Frontend | 3000 | `FRONTEND_PORT` |
| Ollama | 11434 | N/A |

---

## 💾 Volume Management

### Data Persistence

The application uses Docker volumes for persistent storage:

```yaml
volumes:
  chroma_data:      # ChromaDB vector store
  app_logs:         # Application logs
  ollama_data:      # Ollama models (local only)
```

### Backup ChromaDB Data

```bash
# Create backup
docker run --rm \
  -v api-assistant_chroma_data:/data \
  -v $(pwd)/backups:/backup \
  ubuntu tar czf /backup/chroma-backup-$(date +%Y%m%d).tar.gz /data

# Restore from backup
docker run --rm \
  -v api-assistant_chroma_data:/data \
  -v $(pwd)/backups:/backup \
  ubuntu tar xzf /backup/chroma-backup-20240101.tar.gz -C /
```

### View Logs

```bash
# Application logs
docker logs api-assistant-app -f

# Ollama logs
docker logs api-assistant-ollama -f

# All services
docker-compose logs -f
```

### Clear Data

```bash
# Stop containers
docker-compose down

# Remove volumes (WARNING: Deletes all data)
docker volume rm api-assistant_chroma_data
docker volume rm api-assistant_app_logs
docker volume rm api-assistant_ollama_data

# Restart
docker-compose up -d
```

---

## 🏥 Health Checks

All services include health checks:

### Check Service Health

```bash
# Check all services
docker-compose ps

# Check specific service health
docker inspect --format='{{.State.Health.Status}}' api-assistant-app

# View health check logs
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' api-assistant-app
```

### Health Endpoints

| Service | Health Check | Interval |
|---------|--------------|----------|
| Backend | `http://localhost:8000/health` | 30s |
| Frontend | `http://localhost:3000` | 30s |
| Ollama | `http://localhost:11434/api/tags` | 30s |

### Manual Health Check

```bash
# Check FastAPI backend
curl -f http://localhost:8000/health

# Check Next.js frontend
curl -f http://localhost:3000

# Check Ollama
curl -f http://localhost:11434/api/tags
```

---

## 📈 Scaling & Performance

### Resource Limits

Production deployment includes resource limits:

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
    reservations:
      cpus: '1'
      memory: 2G
```

### Recommended Resources

| Deployment Type | CPU | RAM | Storage |
|----------------|-----|-----|---------|
| Development (Ollama) | 4+ cores | 8GB+ | 20GB+ |
| Production (Groq) | 2+ cores | 4GB+ | 10GB+ |

### Enable GPU for Ollama

Edit `docker-compose.yml`:

```yaml
ollama:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

Then restart:

```bash
docker-compose down
docker-compose up -d
```

### Horizontal Scaling

For high-traffic deployments, use a reverse proxy:

```yaml
# nginx-proxy.yml
version: '3.8'
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - app

  app:
    # ... (your app config)
    deploy:
      replicas: 3  # Scale to 3 instances
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Ollama Model Not Found

**Symptom:** "Model not found" errors

**Solution:**
```bash
# Pull the model manually
docker exec api-assistant-ollama ollama pull deepseek-coder:6.7b

# Or restart ollama-puller service
docker-compose up -d ollama-puller
```

#### 2. Out of Memory

**Symptom:** Container crashes, OOM errors

**Solution:**
```bash
# Increase Docker memory limit
# Docker Desktop: Settings → Resources → Memory → Increase to 8GB+

# Or reduce model size
LLM_PROVIDER=groq  # Use cloud LLM instead
```

#### 3. Permission Denied on Volumes

**Symptom:** Cannot write to `/app/data` or `/app/logs`

**Solution:**
```bash
# Fix directory permissions
sudo chown -R 1000:1000 data/ logs/

# Or run as root (NOT RECOMMENDED)
# Add to docker-compose.yml:
#   user: root
```

#### 4. Port Already in Use

**Symptom:** "Port 8501 already allocated"

**Solution:**
```bash
# Change port in .env
APP_PORT=8502

# Or stop conflicting service
lsof -ti:8501 | xargs kill -9
```

#### 5. Health Check Failing

**Symptom:** Container marked as unhealthy

**Solution:**
```bash
# Check logs
docker logs api-assistant-app

# Test health endpoint manually
docker exec api-assistant-app curl -f http://localhost:8501/_stcore/health

# Increase start period if slow startup
# Edit docker-compose.yml:
#   healthcheck:
#     start_period: 120s
```

### Debug Mode

Enable debug logging:

```bash
# Set environment variable
DEBUG=true docker-compose up

# Or in .env file
DEBUG=true
LOG_LEVEL=DEBUG
```

### Container Shell Access

```bash
# Access application container
docker exec -it api-assistant-app /bin/bash

# Check file permissions
ls -la /app/data

# Check processes
ps aux

# Check network
curl http://ollama:11434/api/tags
```

---

## 🔄 Updates & Maintenance

### Update Application

```bash
# Pull latest code
git pull

# Rebuild images
docker-compose build --no-cache

# Restart services
docker-compose up -d

# Clean old images
docker image prune -a
```

### Update Ollama Model

```bash
# Pull new model version
docker exec api-assistant-ollama ollama pull deepseek-coder:latest

# List installed models
docker exec api-assistant-ollama ollama list
```

---

## 🚀 Production Deployment Checklist

Before deploying to production:

- [ ] Set `DEBUG=false` in environment
- [ ] Configure `GROQ_API_KEY` for cloud LLM
- [ ] Set up SSL/TLS certificate (use reverse proxy)
- [ ] Configure backup strategy for `chroma_data` volume
- [ ] Set up log aggregation (e.g., ELK stack)
- [ ] Configure monitoring (Prometheus + Grafana)
- [ ] Set resource limits in docker-compose
- [ ] Enable health checks
- [ ] Test disaster recovery procedure
- [ ] Document runbook for operations team

---

## 📞 Support

For issues or questions:

1. Check logs: `docker-compose logs -f`
2. Review health checks: `docker-compose ps`
3. Open GitHub issue with logs attached

---

## 📄 License

See `LICENSE` file in repository.
