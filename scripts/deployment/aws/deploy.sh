#!/bin/bash
# AWS Deployment Script for API Integration Assistant
# Usage: ./deploy.sh <environment> <image-tag>

set -e

# Configuration
ENVIRONMENT=${1:-production}
IMAGE_TAG=${2:-latest}
REGION=${AWS_REGION:-us-east-1}
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO="api-assistant"
CLUSTER_NAME="api-assistant-cluster"
SERVICE_NAME="api-assistant-service"

echo "🚀 Deploying API Integration Assistant to AWS"
echo "   Environment: $ENVIRONMENT"
echo "   Region: $REGION"
echo "   Image Tag: $IMAGE_TAG"
echo ""

# Step 1: Build and push Docker image
echo "📦 Building Docker image..."
docker build -t $ECR_REPO:$IMAGE_TAG ../../..

echo "🔐 Logging in to ECR..."
aws ecr get-login-password --region $REGION | \
    docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# Create ECR repository if it doesn't exist
if ! aws ecr describe-repositories --repository-names $ECR_REPO --region $REGION 2>/dev/null; then
    echo "📝 Creating ECR repository..."
    aws ecr create-repository --repository-name $ECR_REPO --region $REGION
fi

echo "⬆️  Pushing image to ECR..."
docker tag $ECR_REPO:$IMAGE_TAG $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPO:$IMAGE_TAG
docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPO:$IMAGE_TAG

# Step 2: Deploy with Terraform (if using)
if [ -f "terraform/main.tf" ]; then
    echo "🏗️  Deploying infrastructure with Terraform..."
    cd terraform
    terraform init
    terraform plan -var="environment=$ENVIRONMENT" -var="image_tag=$IMAGE_TAG"
    terraform apply -var="environment=$ENVIRONMENT" -var="image_tag=$IMAGE_TAG" -auto-approve
    cd ..
else
    # Step 3: Update ECS service (manual deployment)
    echo "🔄 Updating ECS service..."

    # Register new task definition
    TASK_DEF_JSON=$(cat <<EOF
{
  "family": "api-assistant-$ENVIRONMENT",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "containerDefinitions": [
    {
      "name": "api-assistant",
      "image": "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPO:$IMAGE_TAG",
      "portMappings": [{"containerPort": 8501, "protocol": "tcp"}],
      "environment": [
        {"name": "LLM_PROVIDER", "value": "groq"},
        {"name": "LOG_LEVEL", "value": "info"},
        {"name": "ENVIRONMENT", "value": "$ENVIRONMENT"}
      ],
      "secrets": [
        {
          "name": "GROQ_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:$REGION:$ACCOUNT_ID:secret:api-assistant/groq-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/api-assistant-$ENVIRONMENT",
          "awslogs-region": "$REGION",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
EOF
)

    TASK_DEF_ARN=$(aws ecs register-task-definition \
        --cli-input-json "$TASK_DEF_JSON" \
        --region $REGION \
        --query 'taskDefinition.taskDefinitionArn' \
        --output text)

    echo "✅ Registered task definition: $TASK_DEF_ARN"

    # Update service
    if aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $REGION | grep -q "ACTIVE"; then
        echo "🔄 Updating existing service..."
        aws ecs update-service \
            --cluster $CLUSTER_NAME \
            --service $SERVICE_NAME \
            --task-definition $TASK_DEF_ARN \
            --region $REGION \
            --force-new-deployment
    else
        echo "⚠️  Service not found. Please create the service manually or use Terraform."
        exit 1
    fi
fi

# Step 4: Wait for deployment to complete
echo "⏳ Waiting for deployment to complete..."
aws ecs wait services-stable \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $REGION

# Step 5: Verify deployment
echo "✅ Deployment complete!"
echo ""
echo "🔍 Service status:"
aws ecs describe-services \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $REGION \
    --query 'services[0].{Status:status,RunningCount:runningCount,DesiredCount:desiredCount}' \
    --output table

echo ""
echo "📊 Recent events:"
aws ecs describe-services \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $REGION \
    --query 'services[0].events[:5]' \
    --output table

echo ""
echo "🎉 Deployment successful!"
