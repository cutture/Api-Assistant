#!/bin/bash
# Azure Deployment Script for API Integration Assistant
# Usage: ./deploy.sh <environment> <image-tag>

set -e

# Configuration
ENVIRONMENT=${1:-production}
IMAGE_TAG=${2:-latest}
RESOURCE_GROUP="api-assistant-$ENVIRONMENT-rg"
LOCATION=${AZURE_LOCATION:-eastus}
REGISTRY_NAME="apiassistant${ENVIRONMENT}acr"
APP_NAME="api-assistant-$ENVIRONMENT"
PLAN_NAME="api-assistant-$ENVIRONMENT-plan"

echo "🚀 Deploying API Integration Assistant to Azure"
echo "   Environment: $ENVIRONMENT"
echo "   Resource Group: $RESOURCE_GROUP"
echo "   Location: $LOCATION"
echo "   Image Tag: $IMAGE_TAG"
echo ""

# Step 1: Create resource group
echo "📝 Creating resource group..."
az group create \
    --name $RESOURCE_GROUP \
    --location $LOCATION \
    --output table

# Step 2: Create container registry
echo "📦 Creating container registry..."
if ! az acr show --name $REGISTRY_NAME --resource-group $RESOURCE_GROUP 2>/dev/null; then
    az acr create \
        --resource-group $RESOURCE_GROUP \
        --name $REGISTRY_NAME \
        --sku Basic \
        --output table
fi

# Step 3: Build and push Docker image
echo "🔨 Building and pushing Docker image..."
cd ../../..
az acr build \
    --registry $REGISTRY_NAME \
    --image api-assistant:$IMAGE_TAG \
    --file Dockerfile \
    .

# Step 4: Create App Service plan
echo "🏗️  Creating App Service plan..."
if ! az appservice plan show --name $PLAN_NAME --resource-group $RESOURCE_GROUP 2>/dev/null; then
    az appservice plan create \
        --name $PLAN_NAME \
        --resource-group $RESOURCE_GROUP \
        --is-linux \
        --sku B2 \
        --output table
fi

# Step 5: Create web app
echo "🌐 Creating web app..."
if ! az webapp show --name $APP_NAME --resource-group $RESOURCE_GROUP 2>/dev/null; then
    az webapp create \
        --resource-group $RESOURCE_GROUP \
        --plan $PLAN_NAME \
        --name $APP_NAME \
        --deployment-container-image-name $REGISTRY_NAME.azurecr.io/api-assistant:$IMAGE_TAG \
        --output table

    # Enable container logging
    az webapp log config \
        --name $APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --docker-container-logging filesystem \
        --output table
else
    # Update existing app
    echo "🔄 Updating existing web app..."
    az webapp config container set \
        --name $APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --docker-custom-image-name $REGISTRY_NAME.azurecr.io/api-assistant:$IMAGE_TAG \
        --output table
fi

# Step 6: Configure environment variables
echo "⚙️  Configuring environment variables..."

# Prompt for Groq API key if not set
if [ -z "$GROQ_API_KEY" ]; then
    echo "Please enter your Groq API key:"
    read -s GROQ_API_KEY
fi

az webapp config appsettings set \
    --resource-group $RESOURCE_GROUP \
    --name $APP_NAME \
    --settings \
        LLM_PROVIDER=groq \
        GROQ_API_KEY="$GROQ_API_KEY" \
        LOG_LEVEL=info \
        ENVIRONMENT=$ENVIRONMENT \
        WEBSITES_PORT=8501 \
    --output table

# Step 7: Restart web app
echo "🔄 Restarting web app..."
az webapp restart \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --output table

# Step 8: Get URL and status
APP_URL=$(az webapp show \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query defaultHostName \
    --output tsv)

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 App URL: https://$APP_URL"
echo ""
echo "🔍 App status:"
az webapp show \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query '{State:state,DefaultHostName:defaultHostName}' \
    --output table

echo ""
echo "📊 Test the service:"
echo "   curl https://$APP_URL/_stcore/health"
echo ""
echo "📋 View logs:"
echo "   az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
echo ""
echo "🎉 Deployment successful!"
