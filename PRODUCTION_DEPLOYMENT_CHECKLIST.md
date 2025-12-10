# Production Deployment Checklist

## Database Migration Status ✅

### Migration Files (Ready for Production)
1. ✅ `989ceebf408f_initial_schema_with_compliance_tables.py` - Base schema
2. ✅ `f83e4032d4e2_add_historical_audit_reviews.py` - Historical audits tables
3. ✅ `9dc402e9cbef_add_awards_and_projects_tables.py` - Awards & projects tables

### Migration Chain Verification
```
9dc402e9cbef (HEAD) → f83e4032d4e2 → 989ceebf408f → None
```

All migrations have proper:
- ✅ Upgrade functions
- ✅ Downgrade functions (rollback support)
- ✅ Foreign key constraints with CASCADE
- ✅ Indexes for performance
- ✅ Sequential revision IDs

---

## Code Changes Summary

### Modified Files (Application Layer)
1. **backend/retrieval/hybrid_engine.py**
   - ✅ Added `_format_ranking_result()` for ranking queries
   - ✅ Enhanced `_execute_historical_query()` with multi-word recipient name extraction
   - ✅ Added `source_collection` metadata to all historical queries

2. **backend/retrieval/query_router.py**
   - ✅ Added ranking/superlative query patterns
   - ✅ Improved historical query pattern matching

3. **backend/retrieval/rag_pipeline.py**
   - ✅ Added `source_collection` field to format_sources()

4. **backend/database/audit_queries.py**
   - ✅ Added `get_recipients_by_deficiency_count()` for ranking queries

5. **backend/database/models.py**
   - ✅ Added historical audit models (Recipient, AuditReview, HistoricalAssessment, LessonsLearned, Award, Project)

### New Files (Scripts & Utilities)
- `backend/database/audit_queries.py` - Query helpers for historical data
- `backend/scripts/ingest_historical_audits.py` - Data ingestion script
- `backend/scripts/extract_audit_reports_claude.py` - AI-powered extraction
- Documentation files (*.md)

---

## Pre-Deployment Checklist

### 1. Database Preparation
- [ ] **Backup production database** (CRITICAL!)
- [ ] Verify DATABASE_URL environment variable is set
- [ ] Test database connection from production environment
- [ ] Check disk space for new tables

### 2. Migration Execution Plan

**Option A: Automatic Migration (Recommended)**
```bash
# In production environment
cd backend
alembic upgrade head
```

**Option B: Step-by-Step Migration (Safer)**
```bash
# Step 1: Historical audit tables
alembic upgrade f83e4032d4e2

# Verify tables created successfully
psql $DATABASE_URL -c "\dt"

# Step 2: Awards and projects tables
alembic upgrade 9dc402e9cbef

# Verify final state
alembic current
```

### 3. Post-Migration Verification
```bash
# Check all tables exist
psql $DATABASE_URL -c "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;"

# Check migration version
alembic current

# Verify indexes
psql $DATABASE_URL -c "SELECT tablename, indexname FROM pg_indexes WHERE schemaname='public' ORDER BY tablename, indexname;"
```

### 4. Rollback Plan (If Needed)
```bash
# Rollback to previous version
alembic downgrade f83e4032d4e2  # Remove awards/projects tables
alembic downgrade 989ceebf408f   # Remove historical audit tables
alembic downgrade base           # Full rollback (ONLY IF CRITICAL)
```

---

## Environment Variables Required

### Production Environment
```bash
# Database
DATABASE_URL=postgresql://user:pass@host:port/dbname

# OpenAI API
OPENAI_API_KEY=sk-...

# ChromaDB
CHROMA_DB_PATH=/path/to/chroma_db

# LLM Configuration
LLM_MODEL=gpt-4-turbo-preview
EMBEDDING_MODEL=text-embedding-3-large
```

---

## Data Ingestion Plan (Post-Migration)

### Phase 1: Historical Audit Data
```bash
# 1. Ingest extracted deficiencies into database
python backend/scripts/ingest_historical_audits.py

# 2. Ingest narratives into ChromaDB
python backend/scripts/ingest_historical_narratives.py

# 3. Verify ingestion
python backend/scripts/test_historical_queries.py
```

### Phase 2: Verification
- [ ] Query test: "What deficiencies did GNHTD have?"
- [ ] Ranking test: "What audit had the most deficiencies?"
- [ ] Multi-word name test: "What deficiencies did Greater New Haven Transit have?"
- [ ] Source collection metadata test (check API response includes `source_collection`)

---

## Production Deployment Steps

### Step 1: Code Deployment
```bash
# 1. Commit all changes
git add .
git commit -m "feat: Add historical audit support with ranking queries and improved routing"

# 2. Push to main branch
git push origin main

# 3. Production environment will auto-deploy (if using Render/similar)
```

### Step 2: Database Migration
```bash
# SSH into production or use admin panel
alembic upgrade head
```

### Step 3: Data Ingestion
```bash
# Run ingestion scripts in production
python scripts/ingest_historical_audits.py
python scripts/ingest_historical_narratives.py
```

### Step 4: Smoke Tests
```bash
# Test ranking query
curl -X POST https://your-app.com/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "what audit had the most deficiencies"}'

# Verify source_collection in response
```

---

## Rollback Procedure

If issues are detected after deployment:

### Code Rollback
```bash
git revert HEAD
git push origin main
```

### Database Rollback
```bash
# Rollback migrations in reverse order
alembic downgrade -1  # Go back one migration
# OR
alembic downgrade f83e4032d4e2  # Go to specific revision
```

---

## Success Criteria

- [x] All migration files have upgrade/downgrade functions
- [x] Migration chain is linear and correct
- [x] No hard-coded database URLs in code
- [x] Foreign keys use CASCADE for referential integrity
- [x] Indexes created for frequently queried columns
- [ ] Production database backed up
- [ ] Migrations tested in staging environment
- [ ] Rollback plan documented and tested

---

## Known Issues / Notes

1. **ChromaDB Telemetry Warnings**: Safe to ignore
   ```
   Failed to send telemetry event: capture() takes 1 positional argument but 3 were given
   ```

2. **Existing Embedding IDs**: Expected during re-ingestion
   ```
   Add of existing embedding ID: deficiency_XXXX
   ```

3. **Database Password**: Ensure production DATABASE_URL has correct credentials

---

## Contact & Support

- Database Admin: [Your DBA contact]
- DevOps Lead: [Your DevOps contact]
- Migration Issues: Check `backend/alembic/versions/` for migration code

---

**Last Updated**: December 10, 2025
**Migration HEAD**: 9dc402e9cbef
**Ready for Production**: ✅ YES
