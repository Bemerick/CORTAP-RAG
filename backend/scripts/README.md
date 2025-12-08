# Database Ingestion Scripts

Scripts for setting up and loading the PostgreSQL database for the hybrid RAG+Database system.

## Prerequisites

1. **Install dependencies**:
   ```bash
   pip install sqlalchemy psycopg2-binary
   ```

2. **Setup PostgreSQL**:
   ```bash
   # Local development (macOS with Homebrew)
   brew install postgresql@15
   brew services start postgresql@15
   createdb cortap_compliance

   # Or use Docker
   docker run --name cortap-postgres \
     -e POSTGRES_PASSWORD=postgres \
     -e POSTGRES_DB=cortap_compliance \
     -p 5432:5432 \
     -d postgres:15
   ```

3. **Set DATABASE_URL** environment variable:
   ```bash
   # Local PostgreSQL
   export DATABASE_URL="postgresql://localhost:5432/cortap_compliance"

   # Or with username/password
   export DATABASE_URL="postgresql://user:password@localhost:5432/cortap_compliance"

   # Render/Production
   export DATABASE_URL="postgresql://user:pass@hostname:5432/dbname"
   ```

---

## Scripts

### 1. `init_db.py` - Initialize Database Tables

Creates database tables (no data).

**Usage:**
```bash
# Create tables
python scripts/init_db.py

# Drop existing tables first (CAREFUL!)
python scripts/init_db.py --drop

# Use custom database URL
python scripts/init_db.py --database-url postgresql://user:pass@host/db
```

**What it does:**
- Connects to PostgreSQL
- Creates 4 tables:
  - `compliance_sections`
  - `compliance_questions`
  - `compliance_indicators`
  - `compliance_deficiencies`
- Creates indexes for fast lookups

---

### 2. `ingest_structured_data.py` - Load JSON Data

Loads data from `FTA_Complete_Extraction.json` into PostgreSQL.

**Usage:**
```bash
# Ingest with defaults
python scripts/ingest_structured_data.py

# Use custom JSON path
python scripts/ingest_structured_data.py --json-path /path/to/guide.json

# Drop existing tables and data first (CAREFUL!)
python scripts/ingest_structured_data.py --drop-existing

# Use custom database URL
python scripts/ingest_structured_data.py --database-url postgresql://user:pass@host/db
```

**What it does:**
- Loads and validates JSON structure
- Ingests all 23 sections with:
  - Questions (sub_areas)
  - Indicators of compliance
  - Deficiencies
- Verifies data integrity
- Validates Title VI has correct counts (11 questions, 25 indicators)

**Output:**
```
================================================================================
FTA Compliance Guide - Structured Data Ingestion
================================================================================

📖 Reading JSON file: docs/guide/FTA_Complete_Extraction.json
✅ Loaded 23 sections

🔍 Validating JSON structure...
✅ JSON structure valid (23 sections)

✅ Database connection successful

🔨 Creating database tables...
✅ Database tables created successfully

📥 Ingesting data into PostgreSQL...

Section      | Questions | Indicators | Deficiencies | Name
--------------------------------------------------------------------------------
  ✓ Legal      | Q:  3 | I:  6 | D:  5 | LEGAL
  ✓ TVI        | Q: 11 | I: 25 | D: 18 | TITLE VI
  ✓ F          | Q:  8 | I: 38 | D: 12 | FINANCIAL MANAGEMENT AND CAPACITY
  ...
--------------------------------------------------------------------------------
TOTAL        |   150   |   400    |     300     | 23 sections

✅ Successfully ingested all data!

🔍 Verifying ingestion...

  Sections:       23
  Questions:     150
  Indicators:    400
  Deficiencies:  300

  Title VI Validation:
    Questions:     11 (expected: 11)
    Indicators:    25 (expected: 25)
    Deficiencies:  18
    ✅ Title VI data matches expected counts!

  ✅ No orphaned records found

================================================================================
✅ INGESTION COMPLETE!
================================================================================

Database ready at: postgresql://localhost:5432/cortap_compliance

Next steps:
  1. Test queries: python scripts/test_db_queries.py
  2. Build query router: backend/retrieval/query_router.py
  3. Integrate with API: backend/api/routes.py
```

---

### 3. `test_db_queries.py` - Test Database Queries

Runs test queries to verify data was ingested correctly.

**Usage:**
```bash
python scripts/test_db_queries.py
```

**What it tests:**
1. Get all indicators for Title VI
2. Get detailed information for specific question (TVI1)
3. Search deficiencies containing "notify FTA"
4. Count indicators and deficiencies by section
5. Filter questions by applicability

**Example output:**
```
================================================================================
Database Query Tests
================================================================================
✅ Database connection successful

================================================================================
TEST: Get all indicators for Title VI
================================================================================

📋 TITLE VI (TVI)
   Page Range: 11-1 to 11-15
   Questions: 11

**TVI1. Did the recipient prepare and submit a Title VI Program?**
   Applicability: All recipients
   a. Did the recipient develop and submit a Title VI Program...
   b. If the recipient submitted a Title VI Program and FTA...

...

✅ Total indicators: 25

================================================================================
✅ ALL TESTS PASSED!
================================================================================
```

---

## Quick Start Workflow

**First time setup:**
```bash
# 1. Create database
createdb cortap_compliance

# 2. Set environment variable
export DATABASE_URL="postgresql://localhost:5432/cortap_compliance"

# 3. Initialize tables
python scripts/init_db.py

# 4. Load data
python scripts/ingest_structured_data.py

# 5. Test
python scripts/test_db_queries.py
```

**Re-ingest (if JSON changes):**
```bash
# Drop and recreate everything
python scripts/ingest_structured_data.py --drop-existing
```

---

## Troubleshooting

### Cannot connect to database
```
❌ Database connection failed: could not connect to server
```

**Solution:**
- Check PostgreSQL is running: `pg_isready`
- Verify DATABASE_URL is correct
- Check firewall/port 5432

### Permission denied
```
❌ permission denied for database
```

**Solution:**
- Create database: `createdb cortap_compliance`
- Or grant permissions: `GRANT ALL ON DATABASE cortap_compliance TO your_user;`

### Unique constraint violation
```
❌ duplicate key value violates unique constraint
```

**Solution:**
- Drop existing data: `python scripts/ingest_structured_data.py --drop-existing`
- Or manually clear: `python scripts/init_db.py --drop`

---

## Database Inspection

**Using psql:**
```bash
psql cortap_compliance

# List tables
\dt

# Count records
SELECT 'sections' as table, COUNT(*) FROM compliance_sections
UNION ALL SELECT 'questions', COUNT(*) FROM compliance_questions
UNION ALL SELECT 'indicators', COUNT(*) FROM compliance_indicators
UNION ALL SELECT 'deficiencies', COUNT(*) FROM compliance_deficiencies;

# Get Title VI data
SELECT * FROM compliance_sections WHERE section_code = 'TVI';
```

**Using Python:**
```python
from database.connection import get_db_manager
from database.models import ComplianceSection

db = get_db_manager()
with db.session_scope() as session:
    sections = session.query(ComplianceSection).all()
    for section in sections:
        print(f"{section.section_code}: {section.section_name}")
```

---

## Next Steps

After successful ingestion:

1. **Build Query Router**: `backend/retrieval/query_router.py`
   - Classify queries as database/RAG/hybrid
   - Extract section names from questions

2. **Database Service Layer**: `backend/database/compliance_db.py`
   - Query methods for common operations
   - Format results for API responses

3. **Hybrid Query Engine**: `backend/retrieval/hybrid_query_engine.py`
   - Orchestrate database + RAG queries
   - Combine results

4. **API Integration**: `backend/api/routes.py`
   - Update `/api/v1/query` endpoint
   - Return database results for indicator queries

---

**Last Updated**: December 5, 2025
