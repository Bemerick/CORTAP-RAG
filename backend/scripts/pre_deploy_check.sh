#!/bin/bash
# Pre-Deployment Checklist for CORTAP RAG
# Run this script before deploying to Render

set -e

echo "🔍 CORTAP RAG Pre-Deployment Checklist"
echo "========================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS=0
FAIL=0

# Function to check if a command exists
check_command() {
    if command -v "$1" &> /dev/null; then
        echo -e "${GREEN}✅${NC} $1 installed"
        ((PASS++))
        return 0
    else
        echo -e "${RED}❌${NC} $1 not found"
        ((FAIL++))
        return 1
    fi
}

# Function to check if a file exists
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✅${NC} $1 exists"
        ((PASS++))
        return 0
    else
        echo -e "${RED}❌${NC} $1 missing"
        ((FAIL++))
        return 1
    fi
}

# Function to check if a directory exists
check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✅${NC} $1 exists"
        ((PASS++))
        return 0
    else
        echo -e "${RED}❌${NC} $1 missing"
        ((FAIL++))
        return 1
    fi
}

echo "1️⃣  Checking Required Tools..."
echo "--------------------------------"
check_command "python3"
if check_command "pip"; then
    :
elif check_command "pip3"; then
    :
fi
check_command "node"
check_command "npm"
check_command "git"
echo ""

echo "2️⃣  Checking Project Structure..."
echo "--------------------------------"
check_file "render.yaml"
check_file "backend/requirements.txt"
check_file "backend/alembic.ini"
check_dir "backend/alembic/versions"
check_file "backend/main.py"
check_file "frontend/package.json"
echo ""

echo "3️⃣  Checking Database Configuration..."
echo "--------------------------------"
check_file "backend/database/__init__.py"
check_file "backend/database/connection.py"
check_file "backend/models/schemas.py"
check_dir "backend/alembic/versions"

# Check if migrations exist
MIGRATION_COUNT=$(ls -1 backend/alembic/versions/*.py 2>/dev/null | grep -v __pycache__ | wc -l)
if [ "$MIGRATION_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅${NC} Found $MIGRATION_COUNT migration(s)"
    ((PASS++))
else
    echo -e "${RED}❌${NC} No migrations found"
    ((FAIL++))
fi
echo ""

echo "4️⃣  Checking Git Status..."
echo "--------------------------------"
if git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC} Git repository initialized"
    ((PASS++))

    # Check for uncommitted changes
    if git diff-index --quiet HEAD --; then
        echo -e "${GREEN}✅${NC} No uncommitted changes"
        ((PASS++))
    else
        echo -e "${YELLOW}⚠️${NC}  Uncommitted changes detected"
        echo "    Run: git add . && git commit -m 'Deploy to Render'"
        ((FAIL++))
    fi

    # Check current branch
    BRANCH=$(git rev-parse --abbrev-ref HEAD)
    echo -e "${GREEN}✅${NC} Current branch: $BRANCH"
    ((PASS++))
else
    echo -e "${RED}❌${NC} Not a git repository"
    ((FAIL++))
fi
echo ""

echo "5️⃣  Checking Python Dependencies..."
echo "--------------------------------"
cd backend
PIP_CMD="pip"
if ! command -v pip &> /dev/null; then
    PIP_CMD="pip3"
fi

if $PIP_CMD list 2>/dev/null | grep -iq "alembic"; then
    echo -e "${GREEN}✅${NC} alembic installed"
    ((PASS++))
else
    echo -e "${RED}❌${NC} alembic not installed"
    echo "    Run: pip install -r requirements.txt"
    ((FAIL++))
fi

if $PIP_CMD list 2>/dev/null | grep -iq "sqlalchemy"; then
    echo -e "${GREEN}✅${NC} sqlalchemy installed"
    ((PASS++))
else
    echo -e "${RED}❌${NC} sqlalchemy not installed"
    echo "    Run: pip install -r requirements.txt"
    ((FAIL++))
fi

if $PIP_CMD list 2>/dev/null | grep -iq "psycopg2"; then
    echo -e "${GREEN}✅${NC} psycopg2 installed"
    ((PASS++))
else
    echo -e "${RED}❌${NC} psycopg2 not installed"
    echo "    Run: pip install -r requirements.txt"
    ((FAIL++))
fi
cd ..
echo ""

echo "6️⃣  Checking Environment Configuration..."
echo "--------------------------------"
check_file "backend/.env.example"

if [ -f "backend/.env" ]; then
    echo -e "${GREEN}✅${NC} backend/.env exists"
    ((PASS++))

    # Check for required variables
    if grep -q "DATABASE_URL" backend/.env; then
        echo -e "${GREEN}✅${NC} DATABASE_URL defined in .env"
        ((PASS++))
    else
        echo -e "${YELLOW}⚠️${NC}  DATABASE_URL not in .env (OK for Render)"
        ((PASS++))
    fi

    if grep -q "OPENAI_API_KEY" backend/.env; then
        echo -e "${GREEN}✅${NC} OPENAI_API_KEY defined in .env"
        ((PASS++))
    else
        echo -e "${RED}❌${NC} OPENAI_API_KEY not in .env"
        ((FAIL++))
    fi
else
    echo -e "${YELLOW}⚠️${NC}  backend/.env not found (OK for Render)"
    echo "    Render will use environment variables"
    ((PASS++))
fi
echo ""

echo "7️⃣  Checking Render Configuration..."
echo "--------------------------------"
if grep -q "type: pserv" render.yaml; then
    echo -e "${GREEN}✅${NC} PostgreSQL service configured"
    ((PASS++))
else
    echo -e "${RED}❌${NC} PostgreSQL service not configured"
    ((FAIL++))
fi

if grep -q "alembic upgrade head" render.yaml; then
    echo -e "${GREEN}✅${NC} Build command includes migrations"
    ((PASS++))
else
    echo -e "${RED}❌${NC} Build command missing migrations"
    echo "    Add: alembic upgrade head"
    ((FAIL++))
fi

if grep -q "DATABASE_URL" render.yaml; then
    echo -e "${GREEN}✅${NC} DATABASE_URL configured in render.yaml"
    ((PASS++))
else
    echo -e "${RED}❌${NC} DATABASE_URL not in render.yaml"
    ((FAIL++))
fi
echo ""

echo "========================================"
echo "📊 Results: $PASS passed, $FAIL failed"
echo "========================================"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! Ready to deploy to Render! 🚀${NC}"
    echo ""
    echo "Next steps:"
    echo "1. git push origin main"
    echo "2. Create services on Render (see docs/RENDER_DEPLOYMENT.md)"
    echo "3. Set OPENAI_API_KEY in Render environment variables"
    echo ""
    exit 0
else
    echo -e "${RED}❌ $FAIL check(s) failed. Please fix issues before deploying.${NC}"
    echo ""
    echo "See docs/RENDER_DEPLOYMENT.md for detailed instructions."
    echo ""
    exit 1
fi
