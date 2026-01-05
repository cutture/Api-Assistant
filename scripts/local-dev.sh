#!/bin/bash
# Local development setup script
# Usage: ./scripts/local-dev.sh

set -e

echo "🚀 Setting up local development environment..."

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file. Please review and update values if needed."
fi

# Check if frontend/.env.local exists
if [ ! -f "frontend/.env.local" ]; then
    echo "📝 Creating frontend/.env.local..."
    cp frontend/.env.development frontend/.env.local
    echo "✅ Created frontend/.env.local file"
fi

# Install backend dependencies
echo "📦 Installing Python dependencies..."
if command -v python3 > /dev/null 2>&1; then
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo "✅ Created Python virtual environment"
    fi
    source venv/bin/activate || . venv/Scripts/activate
    pip install -r requirements.txt
    echo "✅ Installed Python dependencies"
else
    echo "⚠️  Python 3 not found. Skipping backend setup."
fi

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
    echo "✅ Installed frontend dependencies"
else
    echo "ℹ️  node_modules already exists"
fi
cd ..

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/chroma_db
mkdir -p data/uploads
echo "✅ Created data directories"

echo ""
echo "✅ Local development setup complete!"
echo ""
echo "🏃 To start development servers:"
echo ""
echo "Backend (Terminal 1):"
echo "  source venv/bin/activate"
echo "  uvicorn src.api.app:app --reload"
echo ""
echo "Frontend (Terminal 2):"
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "Or use Docker:"
echo "  ./scripts/deploy.sh development"
echo ""
