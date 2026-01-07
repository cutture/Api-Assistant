# Production Deployment Guide

This guide covers deploying the API Integration Assistant to production environments on major cloud providers.

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Cloud Provider Options](#cloud-provider-options)
3. [AWS Deployment](#aws-deployment)
4. [Google Cloud Platform (GCP) Deployment](#gcp-deployment)
5. [Azure Deployment](#azure-deployment)
6. [DigitalOcean Deployment](#digitalocean-deployment)
7. [Environment Configuration](#environment-configuration)
8. [SSL/TLS Configuration](#ssltls-configuration)
9. [Domain and DNS Setup](#domain-and-dns-setup)
10. [Database Scaling](#database-scaling)
11. [Monitoring and Alerting](#monitoring-and-alerting)
12. [Backup and Disaster Recovery](#backup-and-disaster-recovery)
13. [Security Hardening](#security-hardening)
14. [Performance Optimization](#performance-optimization)
15. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

Before deploying to production, ensure you have:

- ✅ Completed all tests (run `pytest` - should have 458+ passing tests)
- ✅ Set up a Groq API key for production LLM provider
- ✅ Configured environment variables (see [Environment Configuration](#environment-configuration))
- ✅ Set up a domain name and DNS records
- ✅ Obtained SSL/TLS certificates (Let's Encrypt recommended)
- ✅ Reviewed security settings (see [PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md))
- ✅ Set up monitoring and alerting (see [Monitoring and Alerting](#monitoring-and-alerting))
- ✅ Tested Docker images locally (see [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md))
- ✅ Configured backup strategy (see [Backup and Disaster Recovery](#backup-and-disaster-recovery))

---

## Cloud Provider Options

### Comparison Matrix

| Provider | Cost (est.) | Ease of Use | Features | Best For |
|----------|-------------|-------------|----------|----------|
| **DigitalOcean** | $12-48/mo | ⭐⭐⭐⭐⭐ | Simple, reliable | Small to medium deployments |
| **AWS** | $20-100/mo | ⭐⭐⭐ | Comprehensive | Enterprise, complex requirements |
| **GCP** | $25-90/mo | ⭐⭐⭐⭐ | Good AI/ML tools | AI-focused applications |
| **Azure** | $25-95/mo | ⭐⭐⭐ | Microsoft integration | Enterprise with Azure stack |

### Recommended Architecture

**For small-medium deployments (< 1000 users):**
- Single Docker container
- Managed database (optional)
- CDN for static assets
- Load balancer for SSL termination

**For large deployments (> 1000 users):**
- Multiple Docker containers (2-5)
- Load balancer with auto-scaling
- Separate database server
- Redis cache layer
- CDN for static assets

---

## AWS Deployment

### Option 1: AWS ECS (Elastic Container Service) - Recommended

**Step 1: Create ECR Repository**
```bash
# Install AWS CLI if not already installed
# Configure AWS credentials: aws configure

# Create ECR repository
aws ecr create-repository --repository-name api-assistant

# Get login credentials
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and push Docker image
docker build -t api-assistant .
docker tag api-assistant:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/api-assistant:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/api-assistant:latest
```

**Step 2: Create ECS Task Definition**

Create `aws/ecs-task-definition.json`:
```json
{
  "family": "api-assistant",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "containerDefinitions": [
    {
      "name": "api-assistant",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/api-assistant:latest",
      "portMappings": [
        {
          "containerPort": 8501,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "LLM_PROVIDER", "value": "groq"},
        {"name": "LOG_LEVEL", "value": "info"},
        {"name": "ENVIRONMENT", "value": "production"}
      ],
      "secrets": [
        {
          "name": "GROQ_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:<account-id>:secret:api-assistant/groq-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/api-assistant",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "mountPoints": [
        {
          "sourceVolume": "chroma-data",
          "containerPath": "/app/data/chroma_db"
        }
      ]
    }
  ],
  "volumes": [
    {
      "name": "chroma-data",
      "efsVolumeConfiguration": {
        "fileSystemId": "fs-xxxxxxxxx",
        "transitEncryption": "ENABLED"
      }
    }
  ]
}
```

**Step 3: Deploy with Terraform (recommended)**

See `scripts/terraform/aws/` for Terraform configuration.

```bash
cd scripts/terraform/aws
terraform init
terraform plan
terraform apply
```

**Step 4: Set up Application Load Balancer**
- Create ALB with HTTPS listener (port 443)
- Configure target group for port 8501
- Add SSL certificate (ACM)
- Configure health checks: `/health` endpoint

### Option 2: AWS EC2

For a simpler single-instance deployment:

```bash
# Launch EC2 instance (t3.medium or larger)
# Install Docker
sudo yum update -y
sudo yum install -y docker
sudo service docker start
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone repository
git clone https://github.com/your-org/api-assistant.git
cd api-assistant

# Set up environment
cp .env.example .env
nano .env  # Edit with production values

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

---

## Google Cloud Platform (GCP) Deployment

### Option 1: Cloud Run (Serverless) - Recommended for Variable Traffic

**Step 1: Build and Push to Container Registry**
```bash
# Enable APIs
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Configure Docker for GCP
gcloud auth configure-docker

# Build and push
docker build -t gcr.io/<project-id>/api-assistant .
docker push gcr.io/<project-id>/api-assistant
```

**Step 2: Deploy to Cloud Run**
```bash
gcloud run deploy api-assistant \
  --image gcr.io/<project-id>/api-assistant \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --timeout 300 \
  --set-env-vars "LLM_PROVIDER=groq,LOG_LEVEL=info,ENVIRONMENT=production" \
  --set-secrets "GROQ_API_KEY=groq-api-key:latest" \
  --min-instances 1 \
  --max-instances 10
```

**Step 3: Set up Cloud Filestore for persistent storage**
```bash
# Create Filestore instance for ChromaDB
gcloud filestore instances create api-assistant-data \
  --zone=us-central1-a \
  --tier=BASIC_HDD \
  --file-share=name="chromadb",capacity=1TB \
  --network=name="default"

# Mount in Cloud Run (requires VPC connector)
```

### Option 2: GKE (Google Kubernetes Engine)

For larger deployments with auto-scaling:

```bash
# Create GKE cluster
gcloud container clusters create api-assistant-cluster \
  --num-nodes 3 \
  --machine-type n1-standard-2 \
  --zone us-central1-a

# Deploy using kubectl
kubectl apply -f k8s/
```

See `scripts/k8s/` for Kubernetes manifests.

---

## Azure Deployment

### Option 1: Azure Container Instances (ACI)

**Step 1: Create Container Registry**
```bash
# Create resource group
az group create --name api-assistant-rg --location eastus

# Create container registry
az acr create --resource-group api-assistant-rg \
  --name apiassistantregistry --sku Basic

# Build and push
az acr build --registry apiassistantregistry \
  --image api-assistant:latest .
```

**Step 2: Deploy to ACI**
```bash
# Create Azure Files share for persistent storage
az storage account create \
  --resource-group api-assistant-rg \
  --name apiassistantstorage \
  --sku Standard_LRS

az storage share create \
  --account-name apiassistantstorage \
  --name chromadb-data

# Deploy container
az container create \
  --resource-group api-assistant-rg \
  --name api-assistant \
  --image apiassistantregistry.azurecr.io/api-assistant:latest \
  --cpu 2 --memory 4 \
  --registry-login-server apiassistantregistry.azurecr.io \
  --registry-username <username> \
  --registry-password <password> \
  --dns-name-label api-assistant \
  --ports 8501 \
  --environment-variables \
    LLM_PROVIDER=groq \
    LOG_LEVEL=info \
    ENVIRONMENT=production \
  --secure-environment-variables \
    GROQ_API_KEY=<your-key> \
  --azure-file-volume-account-name apiassistantstorage \
  --azure-file-volume-account-key <storage-key> \
  --azure-file-volume-share-name chromadb-data \
  --azure-file-volume-mount-path /app/data/chroma_db
```

### Option 2: Azure App Service

For managed platform:

```bash
# Create App Service plan
az appservice plan create \
  --name api-assistant-plan \
  --resource-group api-assistant-rg \
  --is-linux \
  --sku B2

# Create web app
az webapp create \
  --resource-group api-assistant-rg \
  --plan api-assistant-plan \
  --name api-assistant-app \
  --deployment-container-image-name apiassistantregistry.azurecr.io/api-assistant:latest

# Configure environment variables
az webapp config appsettings set \
  --resource-group api-assistant-rg \
  --name api-assistant-app \
  --settings \
    LLM_PROVIDER=groq \
    GROQ_API_KEY=<your-key> \
    LOG_LEVEL=info \
    ENVIRONMENT=production
```

---

## DigitalOcean Deployment

### Recommended: DigitalOcean App Platform

**Step 1: Create App**

1. Go to DigitalOcean dashboard → Apps → Create App
2. Choose "Docker Hub" or connect GitHub repository
3. Configure:
   - **Region**: Choose closest to your users
   - **Size**: Professional ($24/mo) - 2 vCPU, 4GB RAM
   - **Environment Variables**: Add from `.env.example`
   - **Port**: 8501

**Step 2: Add Volume for Persistence**
```bash
# Create volume via CLI
doctl compute volume create chroma-data \
  --region nyc1 \
  --size 10GiB

# Attach to app (via dashboard or API)
```

**Step 3: Deploy**
```bash
# Using doctl CLI
doctl apps create --spec .do/app.yaml

# Or use GitHub integration (recommended)
# Push to main branch → auto-deploy
```

### Alternative: DigitalOcean Droplet

For manual control:

```bash
# Create Droplet (4GB RAM minimum)
doctl compute droplet create api-assistant \
  --size s-2vcpu-4gb \
  --image docker-20-04 \
  --region nyc1 \
  --ssh-keys <your-ssh-key-id>

# SSH into droplet
ssh root@<droplet-ip>

# Clone and deploy
git clone https://github.com/your-org/api-assistant.git
cd api-assistant
cp .env.example .env
nano .env  # Edit configuration
docker-compose -f docker-compose.prod.yml up -d

# Set up firewall
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

---

## Environment Configuration

### Production Environment Variables

Create `.env.production`:

```bash
# LLM Provider Configuration
LLM_PROVIDER=groq
GROQ_API_KEY=<your-groq-api-key>
GROQ_MODEL=mixtral-8x7b-32768

# Application Settings
ENVIRONMENT=production
LOG_LEVEL=info
DEBUG=false

# Security Settings
MAX_FILE_SIZE_MB=10
ALLOWED_FILE_TYPES=.txt,.pdf,.md,.json,.yaml,.yml,.py,.js,.html,.css
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_BURST=10

# Performance Settings
EMBEDDING_CACHE_SIZE=5000
EMBEDDING_CACHE_TTL=3600
QUERY_CACHE_SIZE=100
QUERY_CACHE_TTL=1800
QUERY_CACHE_SIMILARITY_THRESHOLD=0.95

# ChromaDB Settings
CHROMA_PERSIST_DIRECTORY=/app/data/chroma_db
CHROMA_COLLECTION_NAME=api_docs

# Logging Configuration
LOG_FILE=/app/logs/app.log
LOG_MAX_BYTES=10485760
LOG_BACKUP_COUNT=5

# Health Check Configuration
HEALTH_CHECK_INTERVAL=30
HEALTH_CHECK_TIMEOUT=10
```

### Secret Management

**AWS Secrets Manager:**
```bash
# Store secret
aws secretsmanager create-secret \
  --name api-assistant/groq-api-key \
  --secret-string "gsk_..."

# Retrieve in application (already configured in ECS task definition)
```

**GCP Secret Manager:**
```bash
# Store secret
echo -n "gsk_..." | gcloud secrets create groq-api-key --data-file=-

# Grant access
gcloud secrets add-iam-policy-binding groq-api-key \
  --member="serviceAccount:<service-account>@<project>.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

**Azure Key Vault:**
```bash
# Create Key Vault
az keyvault create \
  --name api-assistant-kv \
  --resource-group api-assistant-rg \
  --location eastus

# Store secret
az keyvault secret set \
  --vault-name api-assistant-kv \
  --name groq-api-key \
  --value "gsk_..."
```

---

## SSL/TLS Configuration

### Option 1: Let's Encrypt (Free, Automated)

**With Nginx Reverse Proxy:**

```nginx
# /etc/nginx/sites-available/api-assistant
server {
    listen 80;
    server_name api-assistant.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api-assistant.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/api-assistant.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api-assistant.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Install Certbot:**
```bash
# Ubuntu/Debian
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d api-assistant.yourdomain.com

# Auto-renewal (already set up by certbot)
sudo certbot renew --dry-run
```

### Option 2: Cloud Provider Managed Certificates

**AWS Certificate Manager (ACM):**
- Automatic renewal
- Free for use with AWS services
- Configure on ALB

**GCP Managed Certificates:**
```bash
gcloud compute ssl-certificates create api-assistant-cert \
  --domains=api-assistant.yourdomain.com \
  --global
```

**Azure App Service Certificates:**
- Purchase or import in Azure Portal
- Automatic binding to App Service

---

## Domain and DNS Setup

### DNS Configuration

Add these DNS records:

```
# A Record (for direct IP)
api-assistant.yourdomain.com    A    <your-server-ip>

# Or CNAME (for cloud services)
api-assistant.yourdomain.com    CNAME    <cloud-service-url>

# Example for AWS ALB
api-assistant.yourdomain.com    CNAME    api-lb-123456.us-east-1.elb.amazonaws.com

# Example for GCP Cloud Run
api-assistant.yourdomain.com    CNAME    ghs.googlehosted.com
```

### Subdomain Best Practices

Recommended structure:
- `api-assistant.yourdomain.com` - Production
- `staging.api-assistant.yourdomain.com` - Staging
- `dev.api-assistant.yourdomain.com` - Development

---

## Database Scaling

### ChromaDB Persistence

**For single instance:**
- Use Docker volume or cloud storage mount
- Regular backups (see [Backup section](#backup-and-disaster-recovery))

**For multi-instance (load balanced):**

ChromaDB requires shared storage. Options:

1. **AWS EFS (Elastic File System)**
   ```bash
   # Create EFS
   aws efs create-file-system --tags Key=Name,Value=api-assistant-chroma

   # Mount in ECS task definition (see earlier example)
   ```

2. **GCP Filestore**
   ```bash
   gcloud filestore instances create chroma-data \
     --tier=BASIC_HDD \
     --file-share=name="chromadb",capacity=1TB \
     --zone=us-central1-a
   ```

3. **Azure Files**
   ```bash
   az storage share create \
     --account-name <storage-account> \
     --name chromadb
   ```

### Alternative: Client-Server ChromaDB

For very large deployments, run ChromaDB in server mode:

```yaml
# docker-compose with ChromaDB server
services:
  chroma:
    image: chromadb/chroma:latest
    ports:
      - "8000:8000"
    volumes:
      - chroma_data:/chroma/chroma
    environment:
      - ALLOW_RESET=false
      - ANONYMIZED_TELEMETRY=false

  app:
    # ... existing config ...
    environment:
      - CHROMA_HOST=chroma
      - CHROMA_PORT=8000
```

---

## Monitoring and Alerting

### Application Monitoring

**1. Health Checks**

Application exposes health endpoint at `/_stcore/health`:
```bash
# Simple health check
curl http://localhost:8501/_stcore/health

# Returns: {"status": "ok"}
```

**2. Performance Monitoring**

Built-in performance monitoring (see `src/core/performance.py`):

```python
from src.core.performance import get_performance_report

# Get performance metrics
report = get_performance_report()
print(report)
# {
#   "total_operations": 1250,
#   "operations": {
#     "embed_text": {"count": 500, "avg_time": 45.2, "errors": 0},
#     "vector_store_search": {"count": 750, "avg_time": 12.8, "errors": 2}
#   }
# }
```

**3. Log Aggregation**

Application uses structured logging (structlog). Export logs to:

- **CloudWatch (AWS)**
  ```bash
  # Already configured in ECS task definition
  # View logs:
  aws logs tail /ecs/api-assistant --follow
  ```

- **Cloud Logging (GCP)**
  ```bash
  # Automatic with Cloud Run
  # View logs:
  gcloud logging read "resource.type=cloud_run_revision"
  ```

- **Azure Monitor**
  ```bash
  # Configure in App Service
  # View logs in Azure Portal
  ```

- **Self-hosted (ELK Stack)**
  ```yaml
  # docker-compose with ELK
  services:
    elasticsearch:
      image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
      environment:
        - discovery.type=single-node

    logstash:
      image: docker.elastic.co/logstash/logstash:8.11.0
      volumes:
        - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf

    kibana:
      image: docker.elastic.co/kibana/kibana:8.11.0
      ports:
        - "5601:5601"
  ```

### Alerting Configuration

**Key Metrics to Monitor:**

1. **Response Time**: Alert if P95 > 30s
2. **Error Rate**: Alert if > 1% of requests fail
3. **CPU Usage**: Alert if > 80% for 5 minutes
4. **Memory Usage**: Alert if > 90%
5. **Disk Usage**: Alert if > 85%
6. **Rate Limit Hits**: Alert if > 100/hour (may indicate abuse)

**Example: AWS CloudWatch Alarms**
```bash
# High error rate alarm
aws cloudwatch put-metric-alarm \
  --alarm-name api-assistant-high-error-rate \
  --alarm-description "Error rate > 1%" \
  --metric-name ErrorCount \
  --namespace AWS/ECS \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions <sns-topic-arn>

# High CPU alarm
aws cloudwatch put-metric-alarm \
  --alarm-name api-assistant-high-cpu \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions <sns-topic-arn>
```

### Uptime Monitoring

Use external monitoring services:
- **UptimeRobot** (free tier available)
- **Pingdom**
- **StatusCake**
- **AWS Route 53 Health Checks**

---

## Backup and Disaster Recovery

### Backup Strategy

**1. ChromaDB Data**

**Daily automated backups:**
```bash
#!/bin/bash
# scripts/backup-chroma.sh

BACKUP_DIR="/backups/chroma"
DATE=$(date +%Y%m%d_%H%M%S)
CHROMA_DATA="/app/data/chroma_db"

# Create backup
tar -czf "${BACKUP_DIR}/chroma_backup_${DATE}.tar.gz" "${CHROMA_DATA}"

# Keep only last 30 days
find "${BACKUP_DIR}" -name "chroma_backup_*.tar.gz" -mtime +30 -delete

# Upload to S3 (optional)
aws s3 cp "${BACKUP_DIR}/chroma_backup_${DATE}.tar.gz" \
  s3://api-assistant-backups/chroma/
```

**Set up cron job:**
```bash
# Run daily at 2 AM
0 2 * * * /app/scripts/backup-chroma.sh
```

**2. Application Logs**

Rotate and backup logs:
```python
# Already configured in src/core/logging.py
# Logs rotated at 10MB, keeping 5 backup files
```

**3. Environment Configuration**

Store `.env` files in secure location:
- AWS Secrets Manager
- GCP Secret Manager
- Azure Key Vault
- Encrypted git repository (git-crypt)

### Disaster Recovery Plan

**RTO (Recovery Time Objective): 1 hour**
**RPO (Recovery Point Objective): 24 hours**

**Recovery Steps:**

1. **Data Loss Scenario**
   ```bash
   # Stop application
   docker-compose down

   # Restore from backup
   cd /app/data
   rm -rf chroma_db
   tar -xzf /backups/chroma/chroma_backup_YYYYMMDD_HHMMSS.tar.gz

   # Restart application
   docker-compose -f docker-compose.prod.yml up -d
   ```

2. **Server Failure Scenario**
   - Deploy new instance using Infrastructure as Code (Terraform)
   - Restore data from S3/GCS/Azure Blob
   - Update DNS to point to new instance
   - Verify health checks

3. **Complete Infrastructure Loss**
   - Use multi-region deployment (see below)
   - Failover to secondary region
   - Restore from offsite backups

### Multi-Region Deployment (High Availability)

For mission-critical applications:

```
Primary Region (us-east-1)
├── Application instances (2-3)
├── Load balancer
└── Shared storage (EFS)

Secondary Region (us-west-2)
├── Application instances (1-2, standby)
├── Load balancer
└── Replicated storage

Global:
├── Route 53 / Cloud DNS (health-based routing)
├── CloudFront / Cloud CDN
└── Cross-region backup replication
```

---

## Security Hardening

### Network Security

**1. Firewall Rules**

Only allow necessary ports:
```bash
# UFW (Ubuntu)
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp    # SSH (restrict to your IP)
ufw allow 80/tcp    # HTTP (redirect to HTTPS)
ufw allow 443/tcp   # HTTPS
ufw enable

# Or use cloud provider security groups
```

**2. DDoS Protection**

- **AWS**: Use AWS Shield (Standard is free, Advanced for $3k/mo)
- **GCP**: Cloud Armor
- **Azure**: DDoS Protection
- **Cloudflare**: Free tier includes DDoS protection

**3. WAF (Web Application Firewall)**

Protect against common attacks:
- SQL injection
- XSS
- Command injection
- Rate limiting

**AWS WAF Example:**
```bash
# Create WAF with rate limiting
aws wafv2 create-web-acl \
  --name api-assistant-waf \
  --scope REGIONAL \
  --default-action Allow={} \
  --rules file://waf-rules.json
```

### Application Security

**1. Input Validation**

Already implemented in `src/core/security.py`:
- SQL injection detection
- XSS prevention
- Command injection prevention
- File upload validation
- Rate limiting (60 req/min per user)

**2. Secrets Management**

- ✅ Never commit secrets to git
- ✅ Use environment variables
- ✅ Use cloud provider secret managers
- ✅ Rotate secrets regularly (quarterly)

**3. Container Security**

```bash
# Scan Docker image for vulnerabilities
docker scan api-assistant:latest

# Or use Trivy
trivy image api-assistant:latest
```

**4. Dependency Security**

```bash
# Check for vulnerable dependencies
pip-audit

# Or use safety
safety check

# Update dependencies regularly
pip install -U -r requirements.txt
```

### Compliance

**GDPR Compliance:**
- Implement data deletion on request
- Log data access
- Encrypt data at rest and in transit
- Maintain data processing records

**SOC 2 Compliance:**
- Enable audit logging
- Implement access controls
- Regular security assessments
- Incident response plan

---

## Performance Optimization

### Caching Strategy

Already implemented (Day 18):
- **Embedding Cache**: 5000 entries, 1h TTL
- **Query Cache**: 100 queries, 30min TTL, 95% similarity
- **Expected improvement**: 50-80% faster for repeated queries

### Load Balancing

**AWS ALB Configuration:**
```json
{
  "TargetGroups": [{
    "HealthCheckEnabled": true,
    "HealthCheckPath": "/_stcore/health",
    "HealthCheckIntervalSeconds": 30,
    "HealthyThresholdCount": 2,
    "UnhealthyThresholdCount": 3,
    "Matcher": {
      "HttpCode": "200"
    }
  }]
}
```

### Auto-Scaling

**GCP Cloud Run Auto-scaling:**
```bash
gcloud run services update api-assistant \
  --min-instances 2 \
  --max-instances 10 \
  --concurrency 80 \
  --cpu-throttling \
  --platform managed
```

**AWS ECS Auto-scaling:**
```bash
# Register scalable target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/api-assistant-cluster/api-assistant-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10

# Create scaling policy
aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/api-assistant-cluster/api-assistant-service \
  --policy-name cpu75-target-tracking \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration file://scaling-policy.json
```

### CDN Configuration

For static assets (if any):
- **AWS CloudFront**
- **GCP Cloud CDN**
- **Azure CDN**
- **Cloudflare CDN** (easiest, free tier available)

---

## Troubleshooting

### Common Issues

**1. Container fails to start**
```bash
# Check logs
docker logs api-assistant

# Common causes:
# - Missing environment variables
# - Port already in use
# - Insufficient memory
# - Invalid Groq API key
```

**2. High memory usage**
```bash
# Check memory usage
docker stats api-assistant

# Solutions:
# - Reduce EMBEDDING_CACHE_SIZE
# - Reduce QUERY_CACHE_SIZE
# - Increase container memory limit
# - Enable swap (not recommended for production)
```

**3. Slow response times**
```bash
# Check performance metrics
curl http://localhost:8501/api/metrics

# Solutions:
# - Enable caching (check cache hit rate)
# - Add more instances (horizontal scaling)
# - Upgrade instance size (vertical scaling)
# - Use faster LLM model (e.g., mixtral vs llama)
```

**4. SSL certificate errors**
```bash
# Verify certificate
openssl s_client -connect api-assistant.yourdomain.com:443

# Renew Let's Encrypt certificate
sudo certbot renew

# Check certificate expiration
sudo certbot certificates
```

**5. Database connection errors**
```bash
# Check ChromaDB mount
docker exec api-assistant ls -la /app/data/chroma_db

# Check permissions
docker exec api-assistant ls -la /app/data

# Solutions:
# - Ensure volume is mounted correctly
# - Check file permissions (should be owned by uid 1000)
# - Verify persistent storage is not full
```

### Getting Help

- **GitHub Issues**: https://github.com/your-org/api-assistant/issues
- **Documentation**: See [README.md](README.md) and other docs in `docs/`
- **Logs**: Check application logs for detailed error messages
- **Health Check**: Use `/_stcore/health` endpoint

---

## Cost Optimization

### Estimated Monthly Costs

**Small Deployment (< 100 users):**
- DigitalOcean App Platform: $24/mo
- Groq API (5M tokens): ~$5/mo
- Total: **~$30/mo**

**Medium Deployment (100-1000 users):**
- AWS ECS Fargate (2 tasks): ~$50/mo
- AWS EFS: ~$10/mo
- AWS ALB: ~$20/mo
- Groq API (50M tokens): ~$50/mo
- Total: **~$130/mo**

**Large Deployment (> 1000 users):**
- AWS ECS (5+ tasks): ~$150/mo
- Database: ~$50/mo
- Load balancing: ~$30/mo
- Groq API (500M tokens): ~$500/mo
- CDN: ~$20/mo
- Total: **~$750/mo**

### Cost Reduction Tips

1. **Use spot instances** (AWS EC2 Spot, GCP Preemptible VMs) - 60-80% cheaper
2. **Right-size instances** - Monitor and adjust based on actual usage
3. **Enable auto-scaling** - Scale down during low traffic periods
4. **Use reserved instances** - 30-50% discount for 1-3 year commitment
5. **Optimize LLM usage** - Cache results, use smaller models when possible
6. **Use CDN** - Reduce bandwidth costs
7. **Set up budget alerts** - Monitor spending in real-time

---

## Next Steps

After deployment:

1. ✅ Monitor application health and performance
2. ✅ Set up automated backups
3. ✅ Configure alerting
4. ✅ Review security settings
5. ✅ Optimize costs based on actual usage
6. ✅ Plan for scaling as user base grows
7. ✅ Document any custom configurations
8. ✅ Train team on deployment procedures

---

## Related Documentation

- [Docker Deployment Guide](DOCKER_DEPLOYMENT.md) - Local and Docker deployment
- [Production Checklist](PRODUCTION_CHECKLIST.md) - Pre-deployment checklist
- [Monitoring Guide](docs/MONITORING_GUIDE.md) - Detailed monitoring setup
- [Security Best Practices](docs/SECURITY.md) - Security hardening guide

---

**Last Updated**: 2025-12-27
**Version**: 1.0.0
