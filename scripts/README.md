# Deployment and Operations Scripts

This directory contains scripts for deploying and operating the API Integration Assistant.

## Directory Structure

```
scripts/
├── deployment/          # Cloud provider deployment scripts
│   ├── aws/            # AWS deployment
│   ├── gcp/            # Google Cloud deployment
│   ├── azure/          # Azure deployment
│   └── digitalocean/   # DigitalOcean deployment
├── backup/             # Backup and restore scripts
└── monitoring/         # Monitoring setup and health checks
```

## Deployment Scripts

### AWS Deployment

Deploy to AWS ECS (Elastic Container Service):

```bash
# Deploy to production
./scripts/deployment/aws/deploy.sh production latest

# Deploy to staging
./scripts/deployment/aws/deploy.sh staging latest

# Deploy specific version
./scripts/deployment/aws/deploy.sh production v1.2.3
```

**Prerequisites:**
- AWS CLI installed and configured (`aws configure`)
- Docker installed
- Appropriate AWS permissions (ECS, ECR, IAM, CloudWatch)

**What it does:**
1. Builds Docker image
2. Pushes to ECR (Elastic Container Registry)
3. Updates ECS task definition
4. Deploys to ECS service
5. Waits for deployment to stabilize

### GCP Deployment

Deploy to Google Cloud Run:

```bash
# Set project ID
export GCP_PROJECT_ID=your-project-id

# Deploy to production
./scripts/deployment/gcp/deploy.sh production latest

# Deploy to staging
export GCP_REGION=us-west1
./scripts/deployment/gcp/deploy.sh staging latest
```

**Prerequisites:**
- gcloud CLI installed and authenticated (`gcloud auth login`)
- Docker installed
- Project with billing enabled
- Required APIs enabled (done automatically by script)

**What it does:**
1. Enables required GCP APIs
2. Builds and pushes image to Container Registry
3. Creates/updates Cloud Run service
4. Sets up secrets for API keys
5. Configures auto-scaling

### Azure Deployment

Deploy to Azure Container Instances or App Service:

```bash
# Deploy to production
./scripts/deployment/azure/deploy.sh production latest

# Deploy to staging with specific location
export AZURE_LOCATION=westus2
./scripts/deployment/azure/deploy.sh staging latest
```

**Prerequisites:**
- Azure CLI installed and authenticated (`az login`)
- Docker installed
- Active Azure subscription

**What it does:**
1. Creates resource group
2. Creates container registry (ACR)
3. Builds and pushes image to ACR
4. Creates App Service plan
5. Deploys web app
6. Configures environment variables

### DigitalOcean Deployment

Deploy to DigitalOcean App Platform:

```bash
# Deploy to production
./scripts/deployment/digitalocean/deploy.sh production

# Deploy to staging
export DO_REGION=sfo3
./scripts/deployment/digitalocean/deploy.sh staging
```

**Prerequisites:**
- doctl CLI installed and authenticated (`doctl auth init`)
- GitHub repository (for auto-deployment)

**What it does:**
1. Creates app specification
2. Deploys to App Platform
3. Waits for deployment to complete
4. Provides app URL and next steps

**Note:** You'll need to update the GitHub repository URL in the generated spec file.

## Backup Scripts

### Backup ChromaDB Data

Create a backup of the ChromaDB vector database:

```bash
# Basic backup (saves to /backups/chroma)
./scripts/backup/backup-chroma.sh

# Backup to custom location
./scripts/backup/backup-chroma.sh /mnt/backup/chroma

# With cloud upload (configure environment variables first)
export S3_BACKUP_BUCKET=my-backups
export BACKUP_RETENTION_DAYS=60
./scripts/backup/backup-chroma.sh
```

**Environment Variables:**
- `CHROMA_DATA_DIR`: Source directory (default: `/app/data/chroma_db`)
- `BACKUP_RETENTION_DAYS`: Days to keep backups (default: 30)
- `S3_BACKUP_BUCKET`: AWS S3 bucket for cloud backup
- `GCS_BACKUP_BUCKET`: GCP Cloud Storage bucket
- `AZURE_BACKUP_CONTAINER`: Azure Blob Storage container

**What it does:**
1. Creates compressed tar archive of ChromaDB data
2. Verifies backup integrity
3. Uploads to cloud storage (if configured)
4. Cleans up old backups (older than retention period)

**Automated Backups:**

Add to crontab for daily backups at 2 AM:
```bash
0 2 * * * /app/scripts/backup/backup-chroma.sh /backups/chroma
```

### Restore ChromaDB Data

Restore from a previous backup:

```bash
# List available backups
./scripts/backup/restore-chroma.sh

# Restore from specific backup
./scripts/backup/restore-chroma.sh /backups/chroma/chroma_backup_20250127_120000.tar.gz
```

**What it does:**
1. Verifies backup integrity
2. Stops application (if running)
3. Backs up current data (safety backup)
4. Restores from backup file
5. Fixes permissions
6. Restarts application

**⚠️ WARNING:** This will replace current ChromaDB data!

## Monitoring Scripts

### Setup Monitoring

Set up monitoring and alerting for your deployment:

```bash
# AWS CloudWatch
./scripts/monitoring/setup-monitoring.sh aws

# GCP Cloud Monitoring
./scripts/monitoring/setup-monitoring.sh gcp

# Azure Monitor
./scripts/monitoring/setup-monitoring.sh azure

# Prometheus + Grafana (self-hosted)
./scripts/monitoring/setup-monitoring.sh prometheus
```

**What it does:**
- Creates monitoring dashboards
- Sets up log aggregation
- Configures alerts for:
  - High CPU usage (> 80%)
  - High memory usage (> 90%)
  - High error rates
  - Health check failures
- Sets up notification channels (email, Slack, etc.)

### Health Check

Run comprehensive health checks:

```bash
# Check local deployment
./scripts/monitoring/health-check.sh

# Check production deployment
export APP_URL=https://api-assistant.yourdomain.com
./scripts/monitoring/health-check.sh

# With alerts
export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
export ALERT_EMAIL=admin@yourdomain.com
./scripts/monitoring/health-check.sh
```

**Checks performed:**
- ✅ HTTP connectivity
- ✅ Response time (should be < 1s)
- ✅ SSL certificate validity (if HTTPS)
- ✅ Docker container status (if local)
- ✅ CPU usage (should be < 80%)
- ✅ Memory usage (should be < 85%)
- ✅ Disk space (should be < 85%)

**Exit codes:**
- `0`: All checks passed (or warnings only)
- `1`: One or more checks failed

**Automated Health Checks:**

Add to crontab for monitoring every 5 minutes:
```bash
*/5 * * * * /app/scripts/monitoring/health-check.sh > /var/log/health-check.log 2>&1
```

## Common Workflows

### Initial Deployment

```bash
# 1. Choose your cloud provider
PROVIDER=aws  # or gcp, azure, digitalocean

# 2. Configure environment
cp .env.example .env.production
nano .env.production  # Edit with production values

# 3. Run deployment
./scripts/deployment/$PROVIDER/deploy.sh production latest

# 4. Set up monitoring
./scripts/monitoring/setup-monitoring.sh $PROVIDER

# 5. Set up automated backups
crontab -e
# Add: 0 2 * * * /app/scripts/backup/backup-chroma.sh
```

### Rolling Update

```bash
# 1. Build new version
docker build -t api-assistant:v1.2.3 .

# 2. Deploy
./scripts/deployment/aws/deploy.sh production v1.2.3

# 3. Verify health
sleep 30
./scripts/monitoring/health-check.sh

# 4. Monitor for issues
# Check logs and metrics for 1-2 hours
```

### Disaster Recovery

```bash
# 1. Identify backup to restore
ls -lh /backups/chroma/

# 2. Restore from backup
./scripts/backup/restore-chroma.sh /backups/chroma/chroma_backup_YYYYMMDD_HHMMSS.tar.gz

# 3. Verify application health
./scripts/monitoring/health-check.sh

# 4. Test functionality
# Upload a test file and run a query
```

## Environment Variables Reference

### Common Variables

```bash
# Application
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_...
ENVIRONMENT=production
LOG_LEVEL=info

# Cloud Provider
AWS_REGION=us-east-1
GCP_PROJECT_ID=my-project
GCP_REGION=us-central1
AZURE_LOCATION=eastus
DO_REGION=nyc1

# Backup
CHROMA_DATA_DIR=/app/data/chroma_db
BACKUP_RETENTION_DAYS=30
S3_BACKUP_BUCKET=my-backups
GCS_BACKUP_BUCKET=my-backups
AZURE_BACKUP_CONTAINER=backups

# Monitoring
APP_URL=https://api-assistant.yourdomain.com
HEALTH_CHECK_TIMEOUT=10
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
ALERT_EMAIL=admin@yourdomain.com
```

## Troubleshooting

### Deployment Issues

**Problem:** Deployment fails with permission errors

**Solution:**
```bash
# AWS - Check IAM permissions
aws sts get-caller-identity
aws iam get-user

# GCP - Re-authenticate
gcloud auth login
gcloud auth application-default login

# Azure - Re-login
az login
az account show
```

**Problem:** Image push fails

**Solution:**
```bash
# AWS - Re-authenticate with ECR
aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin ACCOUNT.dkr.ecr.us-east-1.amazonaws.com

# GCP - Re-configure Docker
gcloud auth configure-docker

# Azure - Get ACR credentials
az acr credential show --name myregistry
```

### Backup Issues

**Problem:** Backup fails with "disk full"

**Solution:**
```bash
# Check disk space
df -h

# Clean up old backups manually
find /backups/chroma -name "*.tar.gz" -mtime +7 -delete

# Reduce retention period
export BACKUP_RETENTION_DAYS=7
./scripts/backup/backup-chroma.sh
```

**Problem:** Restore fails with permission errors

**Solution:**
```bash
# Fix ownership
sudo chown -R 1000:1000 /app/data/chroma_db

# Or run restore as root
sudo ./scripts/backup/restore-chroma.sh backup.tar.gz
```

### Monitoring Issues

**Problem:** Health check always fails

**Solution:**
```bash
# Check if service is running
docker ps | grep api-assistant

# Check service URL is correct
echo $APP_URL
curl -v $APP_URL/_stcore/health

# Increase timeout
export HEALTH_CHECK_TIMEOUT=30
./scripts/monitoring/health-check.sh
```

## Security Considerations

1. **Never commit secrets** to version control
2. **Use secret managers** for API keys (AWS Secrets Manager, GCP Secret Manager, etc.)
3. **Restrict script execution** to authorized users only
4. **Audit script changes** before running in production
5. **Test in staging first** before running in production
6. **Enable script logging** for audit trails
7. **Use least privilege** IAM roles/permissions

## Related Documentation

- [Production Deployment Guide](../PRODUCTION_DEPLOYMENT.md)
- [Production Checklist](../PRODUCTION_CHECKLIST.md)
- [Docker Deployment](../DOCKER_DEPLOYMENT.md)
- [Main README](../README.md)

## Support

For issues or questions:
- Check the [Troubleshooting section](#troubleshooting)
- Review logs: `docker logs api-assistant` or cloud provider logs
- Open an issue on GitHub
- Consult the production deployment guide

---

**Version:** 1.0.0
**Last Updated:** 2025-12-27
