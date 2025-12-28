#!/bin/bash
# Health check script for monitoring services
# Usage: ./scripts/health-check.sh

set -e

BACKEND_URL=${BACKEND_URL:-http://localhost:8000}
FRONTEND_URL=${FRONTEND_URL:-http://localhost:3000}

echo "🏥 Running health checks..."
echo ""

# Check backend
echo "🔍 Checking backend at $BACKEND_URL..."
if curl -f -s "$BACKEND_URL/health" > /dev/null; then
    BACKEND_RESPONSE=$(curl -s "$BACKEND_URL/health")
    echo "✅ Backend is healthy"
    echo "   Response: $BACKEND_RESPONSE"
else
    echo "❌ Backend health check failed"
    exit 1
fi

echo ""

# Check frontend
echo "🔍 Checking frontend at $FRONTEND_URL..."
if curl -f -s "$FRONTEND_URL" > /dev/null; then
    echo "✅ Frontend is healthy"
else
    echo "❌ Frontend health check failed"
    exit 1
fi

echo ""
echo "✅ All health checks passed!"
