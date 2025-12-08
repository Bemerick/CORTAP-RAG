# Database Migrations Guide

## Overview

This project uses **Alembic** for database schema migrations. Alembic ensures that your database schema stays in sync with your SQLAlchemy models across development, staging, and production environments.

---

## Why Alembic?

✅ **Version Control for Database Schema** - Track all schema changes in git
✅ **Automatic Migration Generation** - Detects model changes and creates migrations
✅ **Rollback Support** - Safely revert schema changes if needed
✅ **Environment Consistency** - Same schema across dev/staging/production
✅ **Team Collaboration** - Multiple developers can work on schema changes

---

## Directory Structure

```
backend/
├── alembic/
│   ├── versions/          # Migration scripts
│   │   └── 989ceebf408f_initial_schema_with_compliance_tables.py
│   ├── env.py             # Alembic environment configuration
│   ├── script.py.mako     # Template for new migrations
│   └── README
├── alembic.ini            # Alembic configuration
└── database/
    └── models.py          # SQLAlchemy models (source of truth)
```

---

## Initial Setup (Already Complete)

The database migration system is already configured with:

1. ✅ Alembic installed (`alembic==1.13.1`)
2. ✅ Initial migration created (`989ceebf408f`)
3. ✅ Database stamped with baseline revision
4. ✅ Environment variable support for `DATABASE_URL`

**Current Schema** (Revision: `989ceebf408f`):
- `compliance_sections` - 23 FTA compliance sections
- `compliance_questions` - 100+ compliance questions
- `compliance_indicators` - 493 indicators of compliance
- `compliance_deficiencies` - 338 potential deficiencies

---

## Common Migration Commands

### Check Current Version
```bash
DATABASE_URL='postgresql://...' alembic current
```

Output:
```
989ceebf408f (head)
```

### View Migration History
```bash
DATABASE_URL='postgresql://...' alembic history
```

### Create a New Migration (Auto-detect changes)
```bash
DATABASE_URL='postgresql://...' alembic revision --autogenerate -m "Add new column to questions table"
```

### Apply Migrations (Upgrade to Latest)
```bash
DATABASE_URL='postgresql://...' alembic upgrade head
```

### Rollback Last Migration
```bash
DATABASE_URL='postgresql://...' alembic downgrade -1
```

### Rollback to Specific Revision
```bash
DATABASE_URL='postgresql://...' alembic downgrade 989ceebf408f
```

---

## Production Deployment Workflow

### Step 1: Deploy on Render with PostgreSQL

1. **Create PostgreSQL Database on Render**
   - Go to Render Dashboard → New → PostgreSQL
   - Name: `cortap-compliance-db`
   - Plan: Starter ($7/month) or Free
   - Copy the **Internal Database URL**

2. **Add DATABASE_URL to Backend Service**
   - Go to your backend service → Environment
   - Add environment variable:
     - Key: `DATABASE_URL`
     - Value: `postgresql://...` (from step 1)

3. **Deploy Backend**
   - Push code to GitHub
   - Render will auto-deploy

### Step 2: Run Migrations on Render

**Option A: Using Render Shell (Recommended)**
```bash
# Connect to Render shell
# In Render Dashboard → Your Service → Shell

# Run migrations
alembic upgrade head
```

**Option B: One-Time Job**
Create a one-time job in Render:
```bash
alembic upgrade head
```

**Option C: Build Command (Automatic)**
Update `render.yaml`:
```yaml
services:
  - type: web
    name: cortap-rag-backend
    buildCommand: |
      pip install -r requirements.txt
      alembic upgrade head  # Run migrations on every deploy
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Step 3: Verify Migration Success

**Check Migration Status:**
```bash
# In Render shell
alembic current

# Expected output:
# 989ceebf408f (head)
```

**Verify Tables Exist:**
```bash
# In Render shell with psql
psql $DATABASE_URL -c "\dt"

# Expected output:
# compliance_sections
# compliance_questions
# compliance_indicators
# compliance_deficiencies
# alembic_version
```

### Step 4: Load Data

After migrations, load structured data:
```bash
# In Render shell
python scripts/ingest_structured_data.py
```

---

## Development Workflow

### Making Schema Changes

1. **Modify Models**
   Edit `backend/database/models.py`:
   ```python
   class ComplianceQuestion(Base):
       __tablename__ = "compliance_questions"

       # Add new column
       priority = Column(String(20), nullable=True)  # NEW
   ```

2. **Generate Migration**
   ```bash
   DATABASE_URL='postgresql://...' alembic revision --autogenerate -m "Add priority to questions"
   ```

3. **Review Generated Migration**
   Check `alembic/versions/XXXX_add_priority_to_questions.py`:
   ```python
   def upgrade() -> None:
       op.add_column('compliance_questions',
           sa.Column('priority', sa.String(length=20), nullable=True))

   def downgrade() -> None:
       op.drop_column('compliance_questions', 'priority')
   ```

4. **Test Migration Locally**
   ```bash
   # Apply migration
   DATABASE_URL='postgresql://...' alembic upgrade head

   # Verify
   DATABASE_URL='postgresql://...' alembic current
   ```

5. **Commit Migration File**
   ```bash
   git add alembic/versions/XXXX_add_priority_to_questions.py
   git commit -m "Add priority field to questions table"
   git push
   ```

6. **Deploy to Production**
   - Push triggers Render auto-deploy
   - Run `alembic upgrade head` on Render (if not in build command)

---

## Rollback Procedure

If a migration causes issues in production:

### Immediate Rollback

```bash
# Connect to Render shell
# Downgrade to previous version
alembic downgrade -1

# Verify rollback
alembic current
```

### Full Rollback to Baseline

```bash
# Rollback to initial schema
alembic downgrade 989ceebf408f

# Verify
alembic current
# Output: 989ceebf408f
```

### Re-apply After Fixing

```bash
# After fixing the migration file
alembic upgrade head
```

---

## Migration Best Practices

### 1. Always Review Auto-Generated Migrations

Alembic's autogenerate is smart but not perfect. Always review:
- Check column types are correct
- Verify indexes are created
- Ensure foreign keys are set
- Check for data migrations (requires manual code)

### 2. Test Locally First

```bash
# Test upgrade
alembic upgrade head

# Test downgrade (rollback)
alembic downgrade -1

# Re-upgrade
alembic upgrade head
```

### 3. Backup Before Major Changes

```bash
# On Render, before migration
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

### 4. Small, Atomic Migrations

Instead of one huge migration:
```bash
# Good: Multiple small migrations
alembic revision -m "Add priority column"
alembic revision -m "Add index on priority"
alembic revision -m "Populate priority values"

# Bad: One giant migration with 10 changes
```

### 5. Never Edit Applied Migrations

Once a migration is applied (especially in production), never edit it. Create a new migration instead:

```bash
# Wrong: Edit old migration
# Right: Create new migration to fix
alembic revision -m "Fix priority column type"
```

---

## Troubleshooting

### Problem: "Can't locate revision identified by 'XXXX'"

**Cause**: Migration file missing or database not stamped

**Solution**:
```bash
# List available migrations
alembic history

# Stamp database with correct revision
alembic stamp head
```

### Problem: "Target database is not up to date"

**Cause**: Local database ahead of code

**Solution**:
```bash
# Check current version
alembic current

# Downgrade to match code
alembic downgrade <revision_id>
```

### Problem: "Alembic can't find my models"

**Cause**: Import path issues in `alembic/env.py`

**Solution**: Verify `alembic/env.py` has:
```python
from database.models import Base
target_metadata = Base.metadata
```

### Problem: "Auto-generate creates empty migration"

**Cause**: Database already matches models

**This is normal!** It means your database is already in sync. No migration needed.

---

## Environment Variables

Alembic uses `DATABASE_URL` from environment:

**Development (.env file)**:
```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/cortap_compliance
```

**Production (Render Environment)**:
```bash
DATABASE_URL=postgresql://user:pass@dpg-xxxxx.oregon-postgres.render.com/cortap_db
```

**Override in Command Line**:
```bash
DATABASE_URL='postgresql://...' alembic upgrade head
```

---

## Migration File Anatomy

```python
"""Add priority to questions

Revision ID: abc123def456
Revises: 989ceebf408f
Create Date: 2025-12-06 10:30:00.123456
"""

def upgrade() -> None:
    """Apply the migration (forward)."""
    op.add_column('compliance_questions',
        sa.Column('priority', sa.String(length=20), nullable=True))

    # Optional: Set default values for existing rows
    op.execute("UPDATE compliance_questions SET priority = 'medium' WHERE priority IS NULL")

def downgrade() -> None:
    """Revert the migration (backward)."""
    op.drop_column('compliance_questions', 'priority')
```

---

## Data Migrations

For data changes (not just schema), add logic to migrations:

```python
from alembic import op
from sqlalchemy.sql import table, column

def upgrade() -> None:
    # Schema change
    op.add_column('compliance_questions',
        sa.Column('priority', sa.String(20)))

    # Data migration
    questions_table = table('compliance_questions',
        column('question_code', sa.String),
        column('priority', sa.String)
    )

    # Set priority based on section
    op.execute(
        questions_table.update()
        .where(questions_table.c.question_code.like('TVI%'))
        .values(priority='high')
    )
```

---

## CI/CD Integration

### GitHub Actions (Future)

```yaml
name: Database Migration Check

on: [pull_request]

jobs:
  migration-check:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v2
      - name: Install dependencies
        run: pip install -r backend/requirements.txt

      - name: Run migrations
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test
        run: |
          cd backend
          alembic upgrade head
          alembic current
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Check current version | `alembic current` |
| View history | `alembic history --verbose` |
| Create migration | `alembic revision --autogenerate -m "message"` |
| Apply all migrations | `alembic upgrade head` |
| Apply next migration | `alembic upgrade +1` |
| Rollback one migration | `alembic downgrade -1` |
| Rollback to specific version | `alembic downgrade <revision>` |
| Rollback all migrations | `alembic downgrade base` |
| Stamp database | `alembic stamp head` |
| Show SQL without running | `alembic upgrade head --sql` |

---

## Support

For Alembic documentation: https://alembic.sqlalchemy.org/

For project-specific questions, see:
- `docs/DATABASE_SCHEMA.md` - Database schema documentation
- `docs/HYBRID_ARCHITECTURE.md` - System architecture
- `backend/database/models.py` - SQLAlchemy models
