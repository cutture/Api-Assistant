#!/bin/bash
# Deployment script for API Assistant
# Usage: ./scripts/deploy.sh [development|qa|production]

set -e

ENVIRONMENT=${1:-development}
echo "🚀 Deploying API Assistant to $ENVIRONMENT environment..."

# Load environment-specific variables
if [ -f ".env.$ENVIRONMENT" ]; then
    export $(cat .env.$ENVIRONMENT | grep -v '^#' | xargs)
    echo "✅ Loaded environment variables from .env.$ENVIRONMENT"
else
    echo "⚠️  Warning: .env.$ENVIRONMENT not found, using default values"
fi

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "📋 Checking prerequisites..."
if ! command_exists docker; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command_exists docker-compose; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ All prerequisites met"

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down || true

# Build and start services based on environment
case $ENVIRONMENT in
    development)
        echo "🏗️  Building and starting development environment..."
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d
        ;;
    qa)
        echo "🏗️  Building and starting QA environment..."
        docker-compose -f docker-compose.yml up --build -d
        ;;
    production)
        echo "🏗️  Building and starting production environment..."
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
        ;;
    *)
        echo "❌ Unknown environment: $ENVIRONMENT"
        echo "Usage: ./scripts/deploy.sh [development|qa|production]"
        exit 1
        ;;
esac

# Wait for services to be healthy
echo "⏳ Waiting for services to become healthy..."
sleep 5

# Check backend health
echo "🏥 Checking backend health..."
for i in {1..30}; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is healthy"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Backend health check failed"
        docker-compose logs backend
        exit 1
    fi
    echo "⏳ Waiting for backend... ($i/30)"
    sleep 2
done

# Check frontend health
echo "🏥 Checking frontend health..."
for i in {1..30}; do
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        echo "✅ Frontend is healthy"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Frontend health check failed"
        docker-compose logs frontend
        exit 1
    fi
    echo "⏳ Waiting for frontend... ($i/30)"
    sleep 2
done

# Show running containers
echo ""
echo "📦 Running containers:"
docker-compose ps

echo ""
echo "✅ Deployment successful!"
echo ""
echo "🌐 Application is running:"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📝 Useful commands:"
echo "   View logs:        docker-compose logs -f"
echo "   Stop services:    docker-compose down"
echo "   Restart services: docker-compose restart"
echo ""
