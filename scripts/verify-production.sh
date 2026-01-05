#!/bin/bash
# Production readiness verification script
# Usage: ./scripts/verify-production.sh

set -e

echo "🔍 Verifying production readiness..."
echo ""

ERRORS=0
WARNINGS=0

# Color codes
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Helper functions
error() {
    echo -e "${RED}❌ ERROR: $1${NC}"
    ((ERRORS++))
}

warning() {
    echo -e "${YELLOW}⚠️  WARNING: $1${NC}"
    ((WARNINGS++))
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

info() {
    echo "ℹ️  $1"
}

# Check 1: Environment files
echo "📝 Checking environment configuration..."
if [ -f ".env" ]; then
    success "Backend .env file exists"

    # Check for required variables
    if grep -q "LLM_PROVIDER=" .env; then
        success "LLM_PROVIDER is configured"
    else
        error "LLM_PROVIDER not set in .env"
    fi

    if grep -q "SECRET_KEY=" .env && ! grep -q "your-secret-key-change-this" .env; then
        success "SECRET_KEY is configured and changed from default"
    else
        error "SECRET_KEY not set or still using default value"
    fi
else
    error "Backend .env file missing"
fi

if [ -f "frontend/.env.local" ] || [ -f "frontend/.env.production" ]; then
    success "Frontend environment file exists"
else
    warning "Frontend environment file missing"
fi
echo ""

# Check 2: Docker
echo "🐳 Checking Docker setup..."
if command -v docker &> /dev/null; then
    success "Docker is installed ($(docker --version))"
else
    error "Docker is not installed"
fi

if command -v docker-compose &> /dev/null; then
    success "Docker Compose is installed ($(docker-compose --version))"
else
    error "Docker Compose is not installed"
fi
echo ""

# Check 3: Required files
echo "📁 Checking required files..."
FILES=(
    "Dockerfile.backend"
    "frontend/Dockerfile"
    "docker-compose.yml"
    "requirements.txt"
    "frontend/package.json"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        success "$file exists"
    else
        error "$file is missing"
    fi
done
echo ""

# Check 4: Port availability
echo "🔌 Checking port availability..."
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    warning "Port 3000 is already in use"
else
    success "Port 3000 is available"
fi

if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    warning "Port 8000 is already in use"
else
    success "Port 8000 is available"
fi
echo ""

# Check 5: Dependencies
echo "📦 Checking dependencies..."

# Backend
if [ -f "requirements.txt" ]; then
    success "Backend requirements.txt found"
    REQ_COUNT=$(wc -l < requirements.txt)
    info "Backend has $REQ_COUNT dependencies"
fi

# Frontend
if [ -f "frontend/package.json" ]; then
    success "Frontend package.json found"
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        success "Node.js is installed ($NODE_VERSION)"
        if [[ ${NODE_VERSION:1:2} -ge 20 ]]; then
            success "Node.js version is >= 20"
        else
            warning "Node.js version should be >= 20 (current: $NODE_VERSION)"
        fi
    else
        warning "Node.js is not installed (required for local development)"
    fi
fi
echo ""

# Check 6: Security
echo "🔒 Checking security configuration..."

if [ -f ".gitignore" ]; then
    if grep -q ".env" .gitignore; then
        success ".env files are gitignored"
    else
        error ".env files are not in .gitignore"
    fi

    if grep -q "node_modules" .gitignore; then
        success "node_modules is gitignored"
    else
        warning "node_modules should be in .gitignore"
    fi
fi

# Check for secrets in code
if grep -r "SECRET_KEY.*=.*['\"].*['\"]" src/ --include="*.py" 2>/dev/null | grep -v "SECRET_KEY.*=.*os.getenv" > /dev/null; then
    error "Hardcoded SECRET_KEY found in source code"
else
    success "No hardcoded secrets detected"
fi
echo ""

# Check 7: Build verification
echo "🏗️  Checking build configuration..."

if [ -f "frontend/next.config.ts" ]; then
    if grep -q "output.*standalone" frontend/next.config.ts; then
        success "Next.js standalone output is configured"
    else
        warning "Next.js standalone output not configured (required for Docker)"
    fi
fi

if [ -f "frontend/tsconfig.json" ]; then
    success "TypeScript configuration found"
fi
echo ""

# Check 8: Scripts
echo "📜 Checking deployment scripts..."
SCRIPTS=(
    "scripts/deploy.sh"
    "scripts/local-dev.sh"
    "scripts/health-check.sh"
)

for script in "${SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        if [ -x "$script" ]; then
            success "$script exists and is executable"
        else
            warning "$script exists but is not executable (run: chmod +x $script)"
        fi
    else
        error "$script is missing"
    fi
done
echo ""

# Check 9: Documentation
echo "📚 Checking documentation..."
DOCS=(
    "README.md"
    "DEPLOYMENT.md"
    "QUICKSTART.md"
)

for doc in "${DOCS[@]}"; do
    if [ -f "$doc" ]; then
        success "$doc exists"
    else
        warning "$doc is missing"
    fi
done
echo ""

# Check 10: GitHub workflows
echo "⚙️  Checking CI/CD configuration..."
if [ -d ".github/workflows" ]; then
    success ".github/workflows directory exists"
    WORKFLOW_COUNT=$(ls -1 .github/workflows/*.yml 2>/dev/null | wc -l)
    if [ "$WORKFLOW_COUNT" -gt 0 ]; then
        success "Found $WORKFLOW_COUNT GitHub workflow(s)"
    else
        warning "No GitHub workflows found"
    fi
else
    warning ".github/workflows directory missing"
fi
echo ""

# Summary
echo "================================"
echo "📊 Verification Summary"
echo "================================"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! Ready for production.${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  $WARNINGS warning(s) found. Review before production deployment.${NC}"
    exit 0
else
    echo -e "${RED}❌ $ERRORS error(s) and $WARNINGS warning(s) found. Fix errors before deploying.${NC}"
    exit 1
fi
