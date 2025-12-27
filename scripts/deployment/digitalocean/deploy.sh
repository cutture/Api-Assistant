#!/bin/bash
# DigitalOcean Deployment Script for API Integration Assistant
# Usage: ./deploy.sh <environment>

set -e

# Configuration
ENVIRONMENT=${1:-production}
APP_NAME="api-assistant-$ENVIRONMENT"
REGION=${DO_REGION:-nyc1}

echo "🚀 Deploying API Integration Assistant to DigitalOcean"
echo "   Environment: $ENVIRONMENT"
echo "   App Name: $APP_NAME"
echo "   Region: $REGION"
echo ""

# Check if doctl is installed
if ! command -v doctl &> /dev/null; then
    echo "❌ doctl CLI is not installed"
    echo "   Install: https://docs.digitalocean.com/reference/doctl/how-to/install/"
    exit 1
fi

# Check if authenticated
if ! doctl account get &> /dev/null; then
    echo "❌ Not authenticated with DigitalOcean"
    echo "   Run: doctl auth init"
    exit 1
fi

# Step 1: Create app spec
echo "📝 Creating app specification..."
cat > .do-app-spec.yaml <<EOF
name: $APP_NAME
region: $REGION

services:
  - name: web
    github:
      repo: your-org/api-assistant
      branch: main
      deploy_on_push: true

    dockerfile_path: Dockerfile

    instance_count: 1
    instance_size_slug: professional-xs

    http_port: 8501

    health_check:
      http_path: /_stcore/health
      initial_delay_seconds: 60
      period_seconds: 30
      timeout_seconds: 10
      success_threshold: 1
      failure_threshold: 3

    envs:
      - key: LLM_PROVIDER
        value: groq
      - key: LOG_LEVEL
        value: info
      - key: ENVIRONMENT
        value: $ENVIRONMENT
      - key: GROQ_API_KEY
        value: YOUR_GROQ_API_KEY
        type: SECRET

alerts:
  - rule: DEPLOYMENT_FAILED
  - rule: DOMAIN_FAILED
EOF

echo ""
echo "⚠️  Before deploying, please:"
echo "   1. Update the GitHub repo in .do-app-spec.yaml"
echo "   2. Set your Groq API key in DigitalOcean App Platform UI"
echo ""
echo "Press Enter to continue or Ctrl+C to cancel..."
read

# Step 2: Create or update app
if doctl apps list --format Name | grep -q "^$APP_NAME$"; then
    echo "🔄 Updating existing app..."
    APP_ID=$(doctl apps list --format ID,Name | grep "$APP_NAME" | awk '{print $1}')
    doctl apps update $APP_ID --spec .do-app-spec.yaml
else
    echo "🆕 Creating new app..."
    doctl apps create --spec .do-app-spec.yaml
    APP_ID=$(doctl apps list --format ID,Name | grep "$APP_NAME" | awk '{print $1}')
fi

# Step 3: Wait for deployment
echo "⏳ Waiting for deployment to complete..."
echo "   This may take 5-10 minutes..."

while true; do
    STATUS=$(doctl apps get $APP_ID --format ActiveDeployment.Phase --no-header)
    echo "   Status: $STATUS"

    if [ "$STATUS" = "ACTIVE" ]; then
        break
    elif [ "$STATUS" = "ERROR" ] || [ "$STATUS" = "CANCELED" ]; then
        echo "❌ Deployment failed!"
        exit 1
    fi

    sleep 10
done

# Step 4: Get app URL
APP_URL=$(doctl apps get $APP_ID --format DefaultIngress --no-header)

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 App URL: https://$APP_URL"
echo ""
echo "📊 App details:"
doctl apps get $APP_ID

echo ""
echo "📋 View logs:"
echo "   doctl apps logs $APP_ID --type deploy"
echo "   doctl apps logs $APP_ID --type run"
echo ""
echo "💡 Configure custom domain:"
echo "   1. Go to DigitalOcean App Platform dashboard"
echo "   2. Select your app -> Settings -> Domains"
echo "   3. Add your domain and configure DNS"
echo ""
echo "🎉 Deployment successful!"

# Cleanup
rm .do-app-spec.yaml
