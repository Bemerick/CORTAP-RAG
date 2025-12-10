#!/bin/bash
# Production Readiness Verification Script

echo "=================================================="
echo "CORTAP-RAG Production Readiness Check"
echo "=================================================="
echo ""

ERRORS=0
WARNINGS=0

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check 1: Alembic migrations exist
echo "✓ Checking Alembic migrations..."
if [ -f "backend/alembic/versions/f83e4032d4e2_add_historical_audit_reviews.py" ] && \
   [ -f "backend/alembic/versions/9dc402e9cbef_add_awards_and_projects_tables.py" ]; then
    echo -e "${GREEN}  ✓ All migration files present${NC}"
else
    echo -e "${RED}  ✗ Missing migration files${NC}"
    ((ERRORS++))
fi

# Check 2: No hardcoded credentials
echo ""
echo "✓ Checking for hardcoded credentials..."
if grep -r "password.*=" backend/ --include="*.py" | grep -v "# " | grep -v "DATABASE_URL" | grep -v "example" | grep -q .; then
    echo -e "${YELLOW}  ⚠ Potential hardcoded credentials found${NC}"
    ((WARNINGS++))
else
    echo -e "${GREEN}  ✓ No hardcoded credentials detected${NC}"
fi

# Check 3: Migration chain integrity
echo ""
echo "✓ Checking migration chain..."
cd backend
if python3 scripts/check_migrations.py > /dev/null 2>&1; then
    echo -e "${GREEN}  ✓ Migration chain is valid${NC}"
else
    echo -e "${RED}  ✗ Migration chain has errors${NC}"
    ((ERRORS++))
fi
cd ..

# Check 4: Required files exist
echo ""
echo "✓ Checking required files..."
REQUIRED_FILES=(
    "backend/database/audit_queries.py"
    "backend/alembic/versions/f83e4032d4e2_add_historical_audit_reviews.py"
    "backend/alembic/versions/9dc402e9cbef_add_awards_and_projects_tables.py"
    "PRODUCTION_DEPLOYMENT_CHECKLIST.md"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}  ✓ $file${NC}"
    else
        echo -e "${RED}  ✗ Missing: $file${NC}"
        ((ERRORS++))
    fi
done

# Check 5: Git status (uncommitted changes)
echo ""
echo "✓ Checking git status..."
if git diff --quiet && git diff --cached --quiet; then
    echo -e "${YELLOW}  ⚠ All changes committed (ready to push)${NC}"
else
    echo -e "${YELLOW}  ⚠ Uncommitted changes present${NC}"
    echo "  Run: git status"
    ((WARNINGS++))
fi

# Check 6: Environment variables documented
echo ""
echo "✓ Checking environment documentation..."
if grep -q "DATABASE_URL" PRODUCTION_DEPLOYMENT_CHECKLIST.md; then
    echo -e "${GREEN}  ✓ Environment variables documented${NC}"
else
    echo -e "${RED}  ✗ Environment variables not documented${NC}"
    ((ERRORS++))
fi

# Check 7: Rollback plan exists
echo ""
echo "✓ Checking rollback documentation..."
if grep -q "Rollback" PRODUCTION_DEPLOYMENT_CHECKLIST.md; then
    echo -e "${GREEN}  ✓ Rollback plan documented${NC}"
else
    echo -e "${RED}  ✗ Rollback plan missing${NC}"
    ((ERRORS++))
fi

# Summary
echo ""
echo "=================================================="
echo "Summary"
echo "=================================================="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ Production Ready: YES${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. git add ."
    echo "  2. git commit -m 'feat: Add historical audit support with ranking queries'"
    echo "  3. git push origin main"
    echo "  4. Run migrations in production: alembic upgrade head"
    echo ""
else
    echo -e "${RED}✗ Production Ready: NO${NC}"
    echo -e "${RED}  Errors: $ERRORS${NC}"
fi

if [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}  Warnings: $WARNINGS${NC}"
fi

exit $ERRORS
