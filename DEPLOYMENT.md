# API Assistant - Deployment Guide

This guide covers deploying the API Assistant application across different environments: Local, QA, and Production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Local Development](#local-development)
4. [Docker Deployment](#docker-deployment)
5. [Cloud/VM Deployment](#cloudvm-deployment)
6. [Environment-Specific Configuration](#environment-specific-configuration)
7. [Monitoring and Health Checks](#monitoring-and-health-checks)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

- **Docker** (20.10+) and **Docker Compose** (2.0+)
- **Node.js** (20.x) and **npm** (for local development)
- **Python** (3.11+) and **pip** (for local development)
- **Git** (for version control)

### Optional
- **Ollama** (for local LLM, or use Groq cloud API)
- **PostgreSQL** (if using database persistence)

## Environment Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/Api-Assistant.git
cd Api-Assistant
```

### 2. Configure Environment Variables

Create environment files for each environment:

**Backend** (root directory):
```bash
cp .env.example .env
# Edit .env with your configuration
```

**Frontend** (`frontend/` directory):
```bash
cd frontend
cp .env.example .env.local
# Edit .env.local with your configuration
cd ..
```

## Local Development

### Quick Start with Script

```bash
# Run the setup script
./scripts/local-dev.sh

# Start backend (Terminal 1)
source venv/bin/activate
uvicorn src.api.app:app --reload

# Start frontend (Terminal 2)
cd frontend
npm run dev
```

### Manual Setup

#### Backend Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will be available at: `http://localhost:3000`

## Docker Deployment

Docker provides a consistent environment across development, QA, and production.

### Development Environment

```bash
# Using the deployment script
./scripts/deploy.sh development

# Or manually
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

Features:
- Hot-reloading enabled
- Source code mounted as volumes
- Debug logging enabled
- Swagger API docs available

### QA Environment

```bash
# Using the deployment script
./scripts/deploy.sh qa

# Or manually
docker-compose up --build -d
```

Features:
- Production-like configuration
- Analytics enabled
- Error reporting enabled
- Performance monitoring

### Production Environment

```bash
# Using the deployment script
./scripts/deploy.sh production

# Or manually
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

Features:
- Optimized builds
- No debug logging
- Health checks enabled
- Auto-restart on failure
- Resource limits applied

### Useful Docker Commands

```bash
# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Remove all data and containers
docker-compose down -v

# View running containers
docker-compose ps
```

## Cloud/VM Deployment

### AWS EC2 / Azure VM / Google Compute Engine

#### 1. Prepare the Server

```bash
# SSH into your server
ssh user@your-server-ip

# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login again for group changes to take effect
```

#### 2. Deploy the Application

```bash
# Clone repository
git clone https://github.com/yourusername/Api-Assistant.git
cd Api-Assistant

# Create production environment file
cp .env.example .env
nano .env  # Configure your production settings

# Deploy
./scripts/deploy.sh production

# Verify deployment
./scripts/health-check.sh
```

#### 3. Configure Firewall

```bash
# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
```

#### 4. Set Up Reverse Proxy (Nginx)

```bash
# Install Nginx
sudo apt-get install nginx -y

# Create configuration
sudo nano /etc/nginx/sites-available/api-assistant
```

Add this configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/api-assistant /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

#### 5. Set Up SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx -y

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is set up automatically
```

### Vercel (Frontend Only)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy frontend
cd frontend
vercel

# Set environment variables in Vercel dashboard
# NEXT_PUBLIC_API_URL=https://your-api-domain.com
```

### DigitalOcean App Platform

1. Connect your GitHub repository
2. Configure build settings:
   - **Frontend**: `frontend/`, build command: `npm run build`, output: `.next`
   - **Backend**: root directory, build command: `pip install -r requirements.txt`, start: `uvicorn src.api.app:app`
3. Set environment variables
4. Deploy

## Environment-Specific Configuration

### Development
- **API URL**: `http://localhost:8000`
- **Frontend URL**: `http://localhost:3000`
- **Debug**: Enabled
- **Hot Reload**: Enabled
- **Logging**: DEBUG level

### QA/Staging
- **API URL**: `http://qa.your-domain.com:8000` or subdomain
- **Frontend URL**: `http://qa.your-domain.com`
- **Debug**: Disabled
- **Analytics**: Enabled (test mode)
- **Logging**: INFO level

### Production
- **API URL**: `https://api.your-domain.com`
- **Frontend URL**: `https://your-domain.com`
- **Debug**: Disabled
- **Analytics**: Enabled
- **Error Reporting**: Enabled
- **Logging**: WARNING level
- **HTTPS**: Required
- **Rate Limiting**: Enabled

## Monitoring and Health Checks

### Health Check Endpoints

```bash
# Backend health check
curl http://localhost:8000/health

# Frontend health check
curl http://localhost:3000/api/health

# Run automated health check script
./scripts/health-check.sh
```

### Monitoring Services

**Backend Metrics** (available at `/metrics`):
- Request count
- Response times
- Error rates
- Active sessions

**Frontend Metrics**:
- Page load times
- Core Web Vitals
- JavaScript errors

### Logging

**View Application Logs**:
```bash
# Docker logs
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Frontend only
docker-compose logs -f frontend

# Last 100 lines
docker-compose logs --tail=100
```

## Troubleshooting

### Common Issues

#### 1. Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use different port
PORT=8001 uvicorn src.api.app:app
```

#### 2. Docker Build Fails

```bash
# Clear Docker cache
docker-compose build --no-cache

# Remove old containers
docker-compose down -v
docker system prune -a
```

#### 3. Frontend Can't Connect to Backend

Check your `.env.local`:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Check CORS settings in backend `.env`:
```bash
CORS_ORIGINS=http://localhost:3000
```

#### 4. Out of Memory

Increase Docker memory limit:
```bash
# docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
```

#### 5. Database Connection Issues

```bash
# Check if database is running
docker-compose ps

# Restart database
docker-compose restart db

# View database logs
docker-compose logs db
```

### Getting Help

- **Issues**: [GitHub Issues](https://github.com/yourusername/Api-Assistant/issues)
- **Logs**: Always check `docker-compose logs` first
- **Health Checks**: Run `./scripts/health-check.sh`

## Backup and Restore

### Backup Data

```bash
# Backup vector database
tar -czf backup-$(date +%Y%m%d).tar.gz data/chroma_db

# Backup environment files
tar -czf env-backup-$(date +%Y%m%d).tar.gz .env frontend/.env.local
```

### Restore Data

```bash
# Restore vector database
tar -xzf backup-YYYYMMDD.tar.gz
```

## Updates and Maintenance

### Update Application

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up --build -d

# Verify health
./scripts/health-check.sh
```

### Update Dependencies

**Backend**:
```bash
pip install --upgrade -r requirements.txt
```

**Frontend**:
```bash
cd frontend
npm update
npm audit fix
```

## Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Enable HTTPS in production
- [ ] Configure firewall rules
- [ ] Set up rate limiting
- [ ] Enable error reporting (Sentry)
- [ ] Regular security updates
- [ ] Backup data regularly
- [ ] Monitor logs for suspicious activity
- [ ] Use strong passwords
- [ ] Limit SSH access

## Performance Optimization

1. **Enable CDN** for static assets
2. **Configure caching** headers
3. **Use Redis** for session storage (optional)
4. **Enable gzip** compression
5. **Optimize images** before upload
6. **Monitor resource usage**
7. **Scale horizontally** when needed

## Next Steps

After deployment:
1. Configure monitoring (Datadog, New Relic, etc.)
2. Set up automated backups
3. Configure log aggregation (ELK Stack, CloudWatch)
4. Set up alerts for critical errors
5. Load testing
6. Security audit
7. Performance testing

For more information, see:
- [PERFORMANCE.md](frontend/PERFORMANCE.md) - Performance optimization guide
- [ACCESSIBILITY.md](frontend/ACCESSIBILITY.md) - Accessibility guidelines
- [README.md](README.md) - Project overview
