# Production Internet Deployment Guide

**Last Updated:** 2026-01-04
**Status:** ✅ **CRITICAL SECURITY FIXES APPLIED**

This guide walks you through deploying the API-Assistant application to the internet with proper security hardening.

---

## ⚠️ CRITICAL: Security Checklist

Before deploying to the internet, you **MUST** complete these security steps:

### ✅ Completed (Already Fixed in Code)
- [x] CORS configuration uses environment variable (not `allow_origins=["*"]`)
- [x] API key authentication middleware implemented
- [x] BM25 performance bottleneck fixed (lazy rebuild)
- [x] SECRET_KEY removed from repository

### 🔴 **YOU MUST DO** (Required Before Deployment)

- [ ] Generate unique SECRET_KEY for your deployment
- [ ] Generate API keys for authentication
- [ ] Configure ALLOWED_ORIGINS for your frontend domain
- [ ] Enable REQUIRE_AUTH=true in production
- [ ] Set up HTTPS/SSL certificate
- [ ] Configure environment variables on hosting platform
- [ ] Test authentication before going live

---

## Step 1: Generate Secrets

### A. Generate SECRET_KEY

```bash
# Generate a unique secret key
python -c "import secrets; print(secrets.token_hex(32))"
```

**Output example:** `a1b2c3d4e5f6...` (64 characters)

⚠️ **NEVER commit this to git!**

### B. Generate API Keys

```bash
# Generate your first API key
python -c "import secrets; print(f'api-key-{secrets.token_urlsafe(32)}')"
```

**Output example:** `api-key-AbCdEfGh123456789...`

Generate multiple keys for:
- Frontend application
- Mobile app (if applicable)
- Third-party integrations
- Testing/staging environment

---

## Step 2: Configure Environment Variables

### Production .env File

Create/update your `.env` file with production values:

```bash
# ----- LLM Configuration -----
LLM_PROVIDER=groq
GROQ_API_KEY=your_actual_groq_api_key_here
GROQ_REASONING_MODEL=llama-3.3-70b-versatile
GROQ_CODE_MODEL=llama-3.3-70b-versatile
GROQ_GENERAL_MODEL=llama-3.3-70b-versatile

# ----- Embedding Configuration -----
EMBEDDING_MODEL=all-MiniLM-L6-v2

# ----- Vector Database -----
CHROMA_PERSIST_DIR=./data/chroma_db
CHROMA_COLLECTION_NAME=api_docs

# ----- Application Settings -----
APP_NAME=API Integration Assistant
DEBUG=false  # CRITICAL: Must be false in production
LOG_LEVEL=INFO

# ----- Upload Settings -----
MAX_UPLOAD_SIZE_MB=10
ALLOWED_EXTENSIONS=json,yaml,yml,md,txt

# ----- Web Search Fallback -----
ENABLE_WEB_SEARCH=true
WEB_SEARCH_MIN_RELEVANCE=0.5
WEB_SEARCH_MAX_RESULTS=5

# ----- SECURITY CONFIGURATION (CRITICAL!) -----
# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=PASTE_YOUR_GENERATED_KEY_HERE

# CORS Origins - Your actual frontend domain
# Production example: https://your-app.com,https://www.your-app.com
ALLOWED_ORIGINS=https://your-frontend-domain.com

# API Authentication - MUST be true for internet deployment
REQUIRE_AUTH=true

# API Keys - Generated with: python -c "import secrets; print(f'api-key-{secrets.token_urlsafe(32)}')"
# Multiple keys separated by commas
API_KEYS=api-key-PASTE_YOUR_KEYS_HERE,api-key-SECOND_KEY_IF_NEEDED
```

---

## Step 3: Frontend Configuration

Update your frontend to include the API key in requests.

### frontend/.env.production

```bash
NEXT_PUBLIC_API_URL=https://your-backend-domain.com
NEXT_PUBLIC_API_KEY=api-key-YOUR_FRONTEND_API_KEY_HERE
```

### frontend/src/lib/api/client.ts

The code is already set up to use the API key. Verify it includes:

```typescript
// Should already be in the file from security fixes
const API_KEY = process.env.NEXT_PUBLIC_API_KEY;

api.interceptors.request.use((config) => {
  if (API_KEY) {
    config.headers['X-API-Key'] = API_KEY;
  }
  return config;
});
```

---

## Step 4: Deployment Options

### Option A: Docker Deployment (Recommended)

#### 1. Build Docker Images

```bash
# Build backend
docker build -t api-assistant-backend -f Dockerfile .

# Build frontend
cd frontend
docker build -t api-assistant-frontend -f Dockerfile .
```

#### 2. Create docker-compose.production.yml

```yaml
version: '3.8'

services:
  backend:
    image: api-assistant-backend
    env_file:
      - .env  # Your production .env
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data  # Persist ChromaDB data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    image: api-assistant-frontend
    environment:
      - NEXT_PUBLIC_API_URL=https://your-backend-domain.com
      - NEXT_PUBLIC_API_KEY=${FRONTEND_API_KEY}
    ports:
      - "3000:3000"
    depends_on:
      - backend
    restart: unless-stopped

  # Optional: Nginx reverse proxy for HTTPS
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro  # SSL certificates
    depends_on:
      - backend
      - frontend
    restart: unless-stopped
```

#### 3. Deploy

```bash
# Start services
docker-compose -f docker-compose.production.yml up -d

# Check logs
docker-compose -f docker-compose.production.yml logs -f

# Check health
curl http://localhost:8000/health
```

### Option B: Cloud Platform Deployment

#### AWS Elastic Beanstalk

```bash
# Install EB CLI
pip install awsebcli

# Initialize
eb init -p python-3.11 api-assistant

# Set environment variables
eb setenv SECRET_KEY="your-secret" \
          API_KEYS="your-keys" \
          ALLOWED_ORIGINS="https://your-domain.com" \
          REQUIRE_AUTH=true

# Deploy
eb create production-env
eb deploy
```

#### Google Cloud Run

```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT_ID/api-assistant

# Deploy with secrets
gcloud run deploy api-assistant \
  --image gcr.io/PROJECT_ID/api-assistant \
  --platform managed \
  --region us-central1 \
  --set-env-vars REQUIRE_AUTH=true,ALLOWED_ORIGINS=https://your-domain.com \
  --set-secrets SECRET_KEY=secret-key:latest,API_KEYS=api-keys:latest
```

#### Heroku

```bash
# Create app
heroku create your-app-name

# Set environment variables
heroku config:set SECRET_KEY="your-secret"
heroku config:set API_KEYS="your-keys"
heroku config:set ALLOWED_ORIGINS="https://your-frontend.com"
heroku config:set REQUIRE_AUTH=true

# Deploy
git push heroku main
```

#### DigitalOcean App Platform

1. Connect your GitHub repository
2. Configure environment variables in the web UI
3. Deploy from dashboard

---

## Step 5: SSL/HTTPS Configuration

### Using Certbot (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Auto-renewal (already set up by Certbot)
sudo certbot renew --dry-run
```

### Using Cloud Provider SSL

- **AWS**: Use ACM (AWS Certificate Manager)
- **GCP**: Use Google-managed SSL certificates
- **Cloudflare**: Enable SSL in dashboard (Free)

---

## Step 6: Testing in Production

### A. Test API Authentication

```bash
# Should FAIL (no API key)
curl -X POST https://your-backend-domain.com/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'

# Expected: 401 Unauthorized

# Should SUCCEED (with valid API key)
curl -X POST https://your-backend-domain.com/search \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{"query": "test"}'

# Expected: 200 OK with search results
```

### B. Test CORS

```bash
# Check CORS headers
curl -I -X OPTIONS https://your-backend-domain.com/search \
  -H "Origin: https://your-frontend-domain.com" \
  -H "Access-Control-Request-Method: POST"

# Should see:
# Access-Control-Allow-Origin: https://your-frontend-domain.com
```

### C. Test Frontend

1. Open https://your-frontend-domain.com
2. Try uploading a document
3. Try searching
4. Check browser console for errors

### D. Load Test (Optional but Recommended)

```bash
# Install Apache Bench
sudo apt install apache2-utils

# Test with 100 requests, 10 concurrent
ab -n 100 -c 10 \
  -H "X-API-Key: your-key" \
  -p search_payload.json \
  -T application/json \
  https://your-backend-domain.com/search
```

---

## Step 7: Monitoring & Logging

### A. Enable Structured Logging

The application already uses structlog. Configure log shipping:

```bash
# Example: Ship logs to CloudWatch
pip install watchtower

# Or use Docker logging driver
docker-compose.yml:
  logging:
    driver: "awslogs"
    options:
      awslogs-region: "us-east-1"
      awslogs-group: "api-assistant"
```

### B. Set Up Health Checks

Configure your load balancer/platform to hit:
```
GET /health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-04T..."
}
```

### C. Monitor Performance

- Use `/stats` endpoint to track document count
- Monitor search response times
- Set up alerts for 4xx/5xx errors

---

## Step 8: Backup Strategy

### ChromaDB Data

```bash
# Backup
tar -czf chroma_backup_$(date +%Y%m%d).tar.gz ./data/chroma_db

# Restore
tar -xzf chroma_backup_20260104.tar.gz -C ./data/
```

### Automated Backups

```bash
# Cron job (daily at 2 AM)
0 2 * * * /path/to/backup_script.sh
```

Example backup_script.sh:
```bash
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d)
tar -czf $BACKUP_DIR/chroma_$DATE.tar.gz /app/data/chroma_db
# Upload to S3
aws s3 cp $BACKUP_DIR/chroma_$DATE.tar.gz s3://your-bucket/backups/
# Keep only last 30 days
find $BACKUP_DIR -name "chroma_*.tar.gz" -mtime +30 -delete
```

---

## Step 9: Security Hardening Checklist

- [ ] **Firewall**: Only ports 80, 443, and SSH open
- [ ] **SSH**: Disable password auth, use SSH keys only
- [ ] **User permissions**: Run app as non-root user
- [ ] **Rate limiting**: Configure nginx/load balancer rate limits
- [ ] **DDoS protection**: Use Cloudflare or AWS Shield
- [ ] **Security headers**: Add in nginx.conf:
  ```nginx
  add_header X-Frame-Options "SAMEORIGIN";
  add_header X-Content-Type-Options "nosniff";
  add_header X-XSS-Protection "1; mode=block";
  add_header Strict-Transport-Security "max-age=31536000";
  ```
- [ ] **Database access**: ChromaDB not exposed to internet
- [ ] **Environment vars**: Never in git, use secrets management
- [ ] **Dependency updates**: Regular security patches

---

## Step 10: Scaling Considerations

### Horizontal Scaling

For high traffic, consider:

1. **Multiple backend instances** behind load balancer
2. **Shared ChromaDB** via persistent volume (EFS, GCE Persistent Disk)
3. **Session storage** in Redis instead of JSON files
4. **Caching layer** for frequent searches

### Performance Tuning

```bash
# Increase worker processes (uvicorn)
uvicorn src.api.app:app --workers 4 --host 0.0.0.0 --port 8000

# Configure nginx upstream
upstream backend {
    least_conn;
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}
```

---

## Troubleshooting

### Issue: 401 Unauthorized

**Cause**: API key missing or invalid

**Fix**:
```bash
# Check backend logs
docker logs api-assistant-backend

# Verify API key in frontend .env
echo $NEXT_PUBLIC_API_KEY

# Test with curl
curl -H "X-API-Key: your-key" https://your-domain.com/health
```

### Issue: CORS Errors

**Cause**: Frontend domain not in ALLOWED_ORIGINS

**Fix**:
```bash
# Update .env
ALLOWED_ORIGINS=https://your-actual-frontend.com

# Restart backend
docker-compose restart backend

# Verify
curl -I https://your-domain.com/health
```

### Issue: Slow Search Performance

**Cause**: BM25 index needs rebuild

**Fix**: Already fixed with lazy rebuild pattern. First search after adding documents will be slower (~1-2s), subsequent searches fast.

### Issue: Out of Memory

**Cause**: Large document collection

**Fix**:
```bash
# Increase Docker memory limit
docker run -m 4g api-assistant-backend

# Or in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G
```

---

## Maintenance

### Weekly

- [ ] Check error logs
- [ ] Review failed requests
- [ ] Monitor disk usage

### Monthly

- [ ] Update dependencies
- [ ] Review API key usage
- [ ] Check backup integrity
- [ ] Review security alerts

### Quarterly

- [ ] Security audit
- [ ] Performance review
- [ ] Capacity planning

---

## Cost Optimization

### Groq API

- Free tier: 30 requests/minute
- Monitor usage via Groq dashboard
- Set up alerts for quota limits

### Hosting Costs (Estimated)

- **Basic (< 1000 users/month)**:
  - DigitalOcean Droplet: $12/month
  - Cloudflare (Free tier): $0
  - **Total**: ~$12/month

- **Medium (< 10,000 users/month)**:
  - AWS t3.medium: ~$30/month
  - CloudFront + S3: ~$5/month
  - **Total**: ~$35/month

- **Large (> 10,000 users/month)**:
  - AWS ECS Fargate: ~$50-100/month
  - Load Balancer: ~$20/month
  - RDS for sessions: ~$30/month
  - **Total**: ~$100-150/month

---

## Summary

✅ **Completed:**
- CORS configured for production
- API authentication implemented
- Performance bottleneck fixed
- Security hardening applied

🚀 **To Deploy:**
1. Generate secrets (SECRET_KEY, API_KEYS)
2. Configure environment variables
3. Enable REQUIRE_AUTH=true
4. Set ALLOWED_ORIGINS to your domain
5. Deploy with Docker or cloud platform
6. Configure SSL/HTTPS
7. Test authentication
8. Monitor and maintain

**Your application is now ready for internet deployment with production-grade security!**

---

**Need Help?**
- Check logs: `docker-compose logs -f`
- Health check: `curl https://your-domain.com/health`
- Review: `PROJECT_AUDIT_REPORT.md` for known issues
- Reference: `CRITICAL_FIXES_GUIDE.md` for detailed fixes

**Security Issues?**
Report to: [your-security-email@domain.com]
