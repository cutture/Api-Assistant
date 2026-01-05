#!/bin/bash
# GCP Deployment Script for API Integration Assistant
# Usage: ./deploy.sh <environment> <image-tag>

set -e

# Configuration
ENVIRONMENT=${1:-production}
IMAGE_TAG=${2:-latest}
PROJECT_ID=${GCP_PROJECT_ID:-$(gcloud config get-value project)}
REGION=${GCP_REGION:-us-central1}
SERVICE_NAME="api-assistant-$ENVIRONMENT"

echo "🚀 Deploying API Integration Assistant to GCP Cloud Run"
echo "   Environment: $ENVIRONMENT"
echo "   Project: $PROJECT_ID"
echo "   Region: $REGION"
echo "   Image Tag: $IMAGE_TAG"
echo ""

# Step 1: Enable required APIs
echo "🔧 Ensuring required APIs are enabled..."
gcloud services enable \
    run.googleapis.com \
    containerregistry.googleapis.com \
    secretmanager.googleapis.com \
    --project=$PROJECT_ID

# Step 2: Build and push Docker image
echo "📦 Building Docker image..."
cd ../../..
gcloud builds submit \
    --tag gcr.io/$PROJECT_ID/api-assistant:$IMAGE_TAG \
    --project=$PROJECT_ID

# Step 3: Create secret if doesn't exist
if ! gcloud secrets describe groq-api-key --project=$PROJECT_ID 2>/dev/null; then
    echo "🔐 Creating Groq API key secret..."
    echo "Please enter your Groq API key:"
    read -s GROQ_KEY
    echo -n "$GROQ_KEY" | gcloud secrets create groq-api-key \
        --data-file=- \
        --project=$PROJECT_ID
else
    echo "✅ Secret groq-api-key already exists"
fi

# Step 4: Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."

# Get service account email
SERVICE_ACCOUNT="${SERVICE_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Create service account if doesn't exist
if ! gcloud iam service-accounts describe $SERVICE_ACCOUNT --project=$PROJECT_ID 2>/dev/null; then
    echo "📝 Creating service account..."
    gcloud iam service-accounts create $SERVICE_NAME \
        --display-name="API Assistant $ENVIRONMENT" \
        --project=$PROJECT_ID

    # Grant secret accessor role
    gcloud secrets add-iam-policy-binding groq-api-key \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="roles/secretmanager.secretAccessor" \
        --project=$PROJECT_ID
fi

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/api-assistant:$IMAGE_TAG \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 4Gi \
    --cpu 2 \
    --timeout 300 \
    --min-instances 1 \
    --max-instances 10 \
    --concurrency 80 \
    --service-account $SERVICE_ACCOUNT \
    --set-env-vars "LLM_PROVIDER=groq,LOG_LEVEL=info,ENVIRONMENT=$ENVIRONMENT" \
    --set-secrets "GROQ_API_KEY=groq-api-key:latest" \
    --project=$PROJECT_ID

# Step 5: Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --project=$PROJECT_ID \
    --format='value(status.url)')

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Service URL: $SERVICE_URL"
echo ""
echo "🔍 Service status:"
gcloud run services describe $SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --project=$PROJECT_ID \
    --format='table(status.conditions[].type,status.conditions[].status)'

echo ""
echo "📊 Test the service:"
echo "   curl $SERVICE_URL/_stcore/health"
echo ""
echo "🎉 Deployment successful!"
