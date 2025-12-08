# Hybrid RAG+Database Implementation Plan

## Executive Summary

This plan outlines the step-by-step implementation of a hybrid query system that combines PostgreSQL for structured data (indicators, questions) with the existing RAG system for conceptual queries.

**Goal**: Achieve 100% accuracy for indicator counting/listing queries while maintaining flexibility for conceptual questions.

**Timeline**: 3 weeks (assuming 1-2 developers)

**Risk Level**: Low (additive changes, existing RAG system remains functional)

---

## Prerequisites

### 1. JSON Guide Structure Analysis
**Before we begin**, we need to understand your JSON file format:

**Required Information**:
- [ ] Path to JSON file
- [ ] JSON schema/structure
- [ ] Sample of how sections, questions, and indicators are organized
- [ ] Total number of sections, questions, indicators

**Action**: Please share a sample of your JSON structure so we can design the parser correctly.

### 2. Environment Setup
**New Dependencies**:
```txt
# Database
sqlalchemy==2.0.23
psycopg2-binary==2.9.9  # PostgreSQL driver
alembic==1.12.1          # Database migrations

# Optional (for production)
redis==5.0.1             # Caching
```

**Infrastructure**:
- PostgreSQL database (local dev + Render production)
- Optional: Redis for query caching

---

## Phase 1: Database Foundation (Days 1-3)

### Task 1.1: Database Schema Design
**Owner**: Backend Developer
**Duration**: 4 hours
**Dependencies**: JSON structure review

**Deliverables**:
- [x] Complete SQL schema in `docs/HYBRID_ARCHITECTURE.md`
- [ ] Alembic migration scripts
- [ ] Entity-relationship diagram (ERD)

**Files to Create**:
```
backend/
├── database/
│   ├── __init__.py
│   ├── models.py          # SQLAlchemy ORM models
│   ├── connection.py      # Database connection management
│   └── compliance_db.py   # Service layer (queries)
├── alembic/
│   ├── versions/
│   │   └── 001_initial_schema.py
│   └── alembic.ini
```

**Acceptance Criteria**:
- [ ] Schema supports all compliance sections (23 sections)
- [ ] Foreign key relationships enforce data integrity
- [ ] Indexes created for common queries
- [ ] Migration scripts tested on empty database

**SQL to Run**:
```sql
-- See HYBRID_ARCHITECTURE.md for full schema
CREATE TABLE compliance_sections (...);
CREATE TABLE compliance_questions (...);
CREATE TABLE compliance_indicators (...);
```

### Task 1.2: JSON Parser & Ingestion Script
**Owner**: Backend Developer
**Duration**: 6 hours
**Dependencies**: JSON file provided, schema created

**Deliverables**:
- [ ] JSON parsing logic
- [ ] Data validation
- [ ] Database population script
- [ ] Ingestion CLI command

**Files to Create**:
```
backend/
├── ingestion/
│   ├── json_parser.py         # Parse JSON guide structure
│   └── load_structured_data.py # Insert into PostgreSQL
├── scripts/
│   └── ingest_db.py           # CLI: python scripts/ingest_db.py
```

**Implementation**:
```python
# backend/scripts/ingest_db.py
"""
CLI script to ingest JSON guide into PostgreSQL.

Usage:
    python scripts/ingest_db.py --json-path docs/guide/guide_structure.json
"""

def main():
    # Load JSON
    data = parse_json_guide(json_path)

    # Validate structure
    validate_guide_data(data)

    # Insert into database
    db = ComplianceDB(settings.database_url)
    load_sections(db, data["sections"])

    print(f"✅ Loaded {len(data['sections'])} sections")
```

**Acceptance Criteria**:
- [ ] Successfully parses JSON file without errors
- [ ] Validates all required fields present
- [ ] Inserts data into PostgreSQL
- [ ] Handles duplicates gracefully (upsert logic)
- [ ] Logs progress (sections/questions/indicators loaded)
- [ ] Completes ingestion in < 5 minutes

**Testing**:
```bash
# Test on sample JSON
python scripts/ingest_db.py --json-path tests/fixtures/sample_guide.json

# Verify database
psql -d cortap_compliance -c "SELECT COUNT(*) FROM compliance_sections;"
# Expected: 23 sections

psql -d cortap_compliance -c "SELECT COUNT(*) FROM compliance_indicators;"
# Expected: ~200-300 total indicators across all sections
```

### Task 1.3: Database Service Layer
**Owner**: Backend Developer
**Duration**: 4 hours
**Dependencies**: Schema created, data loaded

**Deliverables**:
- [ ] Query methods for common operations
- [ ] Unit tests for database queries
- [ ] Connection pooling setup

**Files to Create**:
```
backend/database/compliance_db.py
tests/test_compliance_db.py
```

**Key Methods**:
```python
class ComplianceDB:
    def get_indicators_by_section(section_code: str) -> Dict
    def get_all_sections() -> List[Dict]
    def search_sections(query: str) -> List[Dict]
    def get_question_details(question_code: str) -> Dict
```

**Acceptance Criteria**:
- [ ] All query methods return expected data structure
- [ ] Query performance < 100ms for indicator retrieval
- [ ] Connection pooling prevents connection leaks
- [ ] Unit tests achieve 90%+ coverage

---

## Phase 2: Query Routing System (Days 4-6)

### Task 2.1: Query Classifier
**Owner**: ML/Backend Developer
**Duration**: 4 hours
**Dependencies**: None (can start in parallel with Phase 1)

**Deliverables**:
- [ ] Query classification logic
- [ ] Pattern matching for database/RAG/hybrid routes
- [ ] Unit tests with 95%+ accuracy

**Files to Create**:
```
backend/retrieval/query_router.py
tests/test_query_router.py
```

**Implementation**:
```python
# backend/retrieval/query_router.py

class QueryRouter:
    """Route queries to database, RAG, or hybrid backend."""

    def classify(self, question: str) -> str:
        """Returns: 'database', 'rag', or 'hybrid'"""
        # Pattern matching logic (see HYBRID_ARCHITECTURE.md)
        pass

    def extract_section_name(self, question: str) -> Optional[str]:
        """Extract section code from question."""
        # e.g., "title vi" -> "Title_VI"
        pass
```

**Test Cases**:
```python
# tests/test_query_router.py

def test_database_route():
    router = QueryRouter()
    assert router.classify("What are the indicators for Title VI?") == "database"
    assert router.classify("How many indicators are there?") == "database"

def test_rag_route():
    assert router.classify("What is the purpose of ADA?") == "rag"
    assert router.classify("Explain the requirements") == "rag"

def test_hybrid_route():
    assert router.classify("What are the Title VI requirements and indicators?") == "hybrid"

def test_section_extraction():
    assert router.extract_section_name("indicators for title vi") == "Title_VI"
    assert router.extract_section_name("ADA compliance") == "ADA_General"
```

**Acceptance Criteria**:
- [ ] 95%+ accuracy on test query set (create 100 test queries)
- [ ] Handles variations ("Title VI" vs "title 6" vs "civil rights")
- [ ] Returns None for ambiguous queries → defaults to RAG
- [ ] Performance < 10ms per classification

### Task 2.2: Section Name Mapping
**Owner**: Backend Developer
**Duration**: 2 hours
**Dependencies**: JSON structure known

**Deliverables**:
- [ ] Complete mapping of common names → section codes
- [ ] Fuzzy matching for typos
- [ ] Configuration file for easy updates

**Files to Create**:
```
backend/config/section_mappings.json
backend/retrieval/section_matcher.py
```

**Example Mapping**:
```json
{
  "Title_VI": [
    "title vi",
    "title 6",
    "civil rights",
    "nondiscrimination",
    "tvi"
  ],
  "ADA_General": [
    "ada",
    "americans with disabilities",
    "disabilities act",
    "accessibility"
  ],
  "Charter_Bus": [
    "charter bus",
    "charter service",
    "charter operations"
  ]
}
```

**Acceptance Criteria**:
- [ ] Covers all 23 compliance sections
- [ ] Handles common abbreviations and synonyms
- [ ] Case-insensitive matching
- [ ] Returns best match even with typos (Levenshtein distance)

---

## Phase 3: Hybrid Query Engine (Days 7-10)

### Task 3.1: Database Query Handler
**Owner**: Backend Developer
**Duration**: 4 hours
**Dependencies**: Database service layer complete

**Deliverables**:
- [ ] Query handler for pure database queries
- [ ] Response formatter
- [ ] Error handling

**Files to Create**:
```
backend/retrieval/database_query_handler.py
```

**Implementation**:
```python
class DatabaseQueryHandler:
    """Handle pure database queries for structured data."""

    def __init__(self, db: ComplianceDB):
        self.db = db

    def handle_query(self, question: str) -> Dict:
        """
        Execute database query and format response.

        Returns:
            {
                "answer": "There are 22 indicators...",
                "confidence": "high",
                "source": "database",
                "metadata": {...}
            }
        """
        section_code = extract_section(question)
        data = self.db.get_indicators_by_section(section_code)
        answer = self.format_response(data)

        return {
            "answer": answer,
            "confidence": "high",
            "source": "database",
            "metadata": {
                "section_code": section_code,
                "total_indicators": data["total_indicators"]
            }
        }

    def format_response(self, data: Dict) -> str:
        """Format database results as user-friendly text."""
        # Format as vertical list with headers
        pass
```

**Acceptance Criteria**:
- [ ] Returns correct count for all sections
- [ ] Formats output with proper grouping (by question)
- [ ] Includes source page numbers
- [ ] Handles errors gracefully (section not found)
- [ ] Response matches expected format from design doc

### Task 3.2: Hybrid Engine Core
**Owner**: Backend Developer
**Duration**: 6 hours
**Dependencies**: Query router, database handler, existing RAG pipeline

**Deliverables**:
- [ ] Main hybrid engine orchestration
- [ ] Result merging logic
- [ ] Logging and metrics

**Files to Create**:
```
backend/retrieval/hybrid_query_engine.py
```

**Implementation**:
```python
class HybridQueryEngine:
    """Orchestrate database + RAG queries."""

    def __init__(self, db: ComplianceDB, rag: RAGPipeline):
        self.db = db
        self.rag = rag
        self.router = QueryRouter()
        self.db_handler = DatabaseQueryHandler(db)

    def process_query(self, question: str, history: List = None) -> Dict:
        """
        Main entry point: route and execute query.
        """
        route = self.router.classify(question)

        if route == "database":
            return self.db_handler.handle_query(question)

        elif route == "rag":
            return self._handle_rag_query(question, history)

        else:  # hybrid
            return self._handle_hybrid_query(question, history)

    def _handle_rag_query(self, question, history) -> Dict:
        """Use existing RAG pipeline."""
        chunks = self.rag.retrieve_chunks(question)
        result = self.rag.process_query(question, chunks, history)
        result["source"] = "rag"
        return result

    def _handle_hybrid_query(self, question, history) -> Dict:
        """Combine database + RAG."""
        # Get structured data
        db_result = self.db_handler.handle_query(question)

        # Get contextual chunks
        chunks = self.rag.retrieve_chunks(question, top_k=3)

        # Combine in prompt
        combined_prompt = self._build_hybrid_prompt(
            question, db_result["answer"], chunks
        )

        answer = self.rag.llm.invoke(combined_prompt)

        return {
            "answer": answer,
            "confidence": "high",
            "source": "hybrid",
            "metadata": {
                "db_indicators": db_result["metadata"]["total_indicators"],
                "rag_chunks": len(chunks)
            }
        }
```

**Acceptance Criteria**:
- [ ] Correctly routes all query types
- [ ] Database queries return 100% accurate counts
- [ ] RAG queries maintain existing quality
- [ ] Hybrid queries combine both seamlessly
- [ ] Logs route decision and execution time
- [ ] Handles edge cases (empty results, errors)

### Task 3.3: Integration Testing
**Owner**: QA/Backend Developer
**Duration**: 4 hours
**Dependencies**: Hybrid engine complete

**Deliverables**:
- [ ] End-to-end tests for all query types
- [ ] Performance benchmarks
- [ ] Comparison tests (old RAG vs new hybrid)

**Files to Create**:
```
tests/integration/test_hybrid_engine.py
tests/benchmarks/test_query_performance.py
```

**Test Scenarios**:
```python
# Database queries
def test_title_vi_indicators_exact_count():
    result = engine.process_query("What are the indicators for Title VI?")
    assert result["source"] == "database"
    assert result["metadata"]["total_indicators"] == 22
    assert "TVI1" in result["answer"]
    assert "TVI10" in result["answer"]

# RAG queries
def test_conceptual_question():
    result = engine.process_query("What is the purpose of Title VI?")
    assert result["source"] == "rag"
    assert len(result["sources"]) >= 3

# Hybrid queries
def test_hybrid_combines_structure_and_context():
    result = engine.process_query("Explain the Title VI indicators")
    assert result["source"] == "hybrid"
    assert "22 indicators" in result["answer"]
    assert len(result["metadata"]["rag_chunks"]) > 0
```

**Acceptance Criteria**:
- [ ] All 23 sections return correct indicator counts
- [ ] RAG queries maintain < 5s latency
- [ ] Database queries complete in < 200ms
- [ ] No regressions in existing RAG quality
- [ ] Test coverage > 90%

---

## Phase 4: API & Frontend Updates (Days 11-14)

### Task 4.1: Update API Endpoints
**Owner**: Backend Developer
**Duration**: 3 hours
**Dependencies**: Hybrid engine complete

**Deliverables**:
- [ ] Updated `/api/v1/query` endpoint
- [ ] New response schema with source type
- [ ] API documentation updates

**Files to Modify**:
```
backend/api/routes.py
backend/api/service.py
backend/models/schemas.py
```

**Changes**:
```python
# backend/models/schemas.py

class QueryResponse(BaseModel):
    answer: str
    confidence: str
    sources: List[SourceCitation]
    ranked_chunks: Optional[List[SourceCitation]]

    # NEW FIELDS
    source: str  # "database", "rag", or "hybrid"
    metadata: Optional[Dict] = None  # Query-specific metadata
```

**Acceptance Criteria**:
- [ ] API returns source type in response
- [ ] OpenAPI docs updated
- [ ] Backward compatible with existing clients
- [ ] Error responses include helpful messages

### Task 4.2: Frontend Display Updates
**Owner**: Frontend Developer
**Duration**: 4 hours
**Dependencies**: API changes deployed

**Deliverables**:
- [ ] Display query source type (database/RAG/hybrid)
- [ ] Show metadata (indicator counts)
- [ ] Update UI for database responses

**Files to Modify**:
```
frontend/src/components/MessageBubble.tsx
frontend/src/types/index.ts
```

**UI Changes**:
```tsx
// Show source badge
{message.response?.source === "database" && (
  <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
    📊 Database Query
  </span>
)}

// Show metadata
{message.response?.metadata?.total_indicators && (
  <div className="text-sm text-gray-600">
    {message.response.metadata.total_indicators} indicators found
  </div>
)}
```

**Acceptance Criteria**:
- [ ] Source type displayed prominently
- [ ] Database responses show indicator count
- [ ] Hybrid responses indicate both sources used
- [ ] UI remains clean and professional
- [ ] Mobile responsive

### Task 4.3: Add Example Queries
**Owner**: Frontend Developer
**Duration**: 2 hours
**Dependencies**: None

**Deliverables**:
- [ ] Updated common questions
- [ ] Add examples for each query type
- [ ] Tooltips explaining query types

**Files to Modify**:
```
frontend/src/components/SuggestedQuestions.tsx
backend/api/routes.py (common-questions endpoint)
```

**New Examples**:
```typescript
const COMMON_QUESTIONS = [
  // Database queries
  "What are the indicators of compliance for Title VI?",
  "How many indicators are there for ADA?",
  "List all Charter Bus compliance questions",

  // RAG queries
  "What is the purpose of the Charter Bus review area?",
  "Explain Title VI compliance requirements",

  // Hybrid queries
  "What are the Title VI requirements and indicators?",
];
```

**Acceptance Criteria**:
- [ ] At least 2 examples per query type
- [ ] Questions trigger correct routing
- [ ] Tooltips explain what each query type does
- [ ] Examples cover all major sections

---

## Phase 5: Deployment & Validation (Days 15-21)

### Task 5.1: Database Setup on Render
**Owner**: DevOps/Backend Developer
**Duration**: 3 hours
**Dependencies**: None

**Deliverables**:
- [ ] PostgreSQL database on Render
- [ ] Connection pooling configured
- [ ] Environment variables set
- [ ] Database initialized with schema

**Steps**:
1. Create PostgreSQL database on Render
2. Update `render.yaml` with database service
3. Add `DATABASE_URL` to environment
4. Run migrations: `alembic upgrade head`
5. Run ingestion: `python scripts/ingest_db.py`

**render.yaml Updates**:
```yaml
databases:
  - name: cortap-postgres
    databaseName: cortap_compliance
    user: cortap_user
    plan: starter  # $7/month

services:
  - type: web
    name: cortap-rag-backend
    env: python
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: cortap-postgres
          property: connectionString
```

**Acceptance Criteria**:
- [ ] Database accessible from backend service
- [ ] Migrations run successfully
- [ ] Data ingested (23 sections, all indicators)
- [ ] Connection pooling prevents timeouts

### Task 5.2: Staged Rollout
**Owner**: Backend Developer
**Duration**: 4 hours
**Dependencies**: Database deployed

**Deliverables**:
- [ ] Feature flag system
- [ ] Gradual traffic routing
- [ ] Rollback procedure documented

**Implementation**:
```python
# backend/config.py

class Settings(BaseSettings):
    enable_hybrid_queries: bool = True
    hybrid_traffic_percentage: int = 100  # 0-100

# backend/api/routes.py

@router.post("/api/v1/query")
async def query_endpoint(request: QueryRequest):
    # Feature flag check
    if not settings.enable_hybrid_queries:
        # Fall back to old RAG pipeline
        return old_rag_pipeline.process(request)

    # Gradual rollout
    if random.randint(0, 100) > settings.hybrid_traffic_percentage:
        return old_rag_pipeline.process(request)

    # Use hybrid system
    return hybrid_engine.process_query(request)
```

**Rollout Plan**:
- Day 15: Deploy with `hybrid_traffic_percentage=10`
- Day 16: Monitor metrics, increase to 50%
- Day 17: Review errors, increase to 100%
- Day 18: Remove feature flag

**Acceptance Criteria**:
- [ ] Can toggle hybrid system on/off
- [ ] Can control traffic percentage
- [ ] Metrics show both systems running
- [ ] Zero downtime during rollout

### Task 5.3: Validation & Testing
**Owner**: QA Team
**Duration**: 3 days (Days 18-21)
**Dependencies**: Full deployment complete

**Deliverables**:
- [ ] Validation test suite
- [ ] Performance comparison report
- [ ] User acceptance testing results

**Test Plan**:

**1. Accuracy Validation**
- [ ] Test all 23 sections for indicator counts
- [ ] Compare database results to manual count
- [ ] Verify RAG quality maintained
- [ ] Test 50 sample queries across all types

**2. Performance Testing**
- [ ] Measure latency for database queries (target: < 200ms)
- [ ] Measure latency for RAG queries (target: < 5s)
- [ ] Load test: 100 concurrent users
- [ ] Monitor database connection pool

**3. User Acceptance Testing**
- [ ] 10 users test system with real questions
- [ ] Collect feedback on accuracy
- [ ] Measure satisfaction scores
- [ ] Identify edge cases

**Acceptance Criteria**:
- [ ] 100% accuracy for all database queries
- [ ] RAG quality maintained or improved
- [ ] 95th percentile latency < 5s
- [ ] Zero critical bugs
- [ ] User satisfaction > 8/10

---

## Rollback Plan

If issues arise, follow this procedure:

### Level 1: Feature Flag Disable
```bash
# Disable hybrid system instantly
curl -X POST https://cortap-rag-backend.onrender.com/admin/config \
  -d '{"enable_hybrid_queries": false}'
```

### Level 2: Environment Variable
```bash
# Update Render environment variable
ENABLE_HYBRID_QUERIES=false
```

### Level 3: Code Rollback
```bash
# Revert to previous commit
git revert HEAD
git push origin main
# Render auto-deploys previous version
```

### Level 4: Database Restore
```bash
# Restore from backup if data corrupted
pg_restore -d cortap_compliance backup.dump
```

**Decision Criteria**:
- Level 1: Minor issues, < 5% error rate
- Level 2: Moderate issues, 5-10% error rate
- Level 3: Major issues, > 10% error rate or outage
- Level 4: Data integrity issues

---

## Success Metrics

### Primary Metrics
- **Database Query Accuracy**: 100% (vs current 73%)
- **Query Latency**: < 200ms for database, < 5s for RAG
- **User Satisfaction**: > 8/10

### Secondary Metrics
- **RAG Quality**: Maintain current confidence distribution
- **Cost**: Database queries = $0, RAG queries = $0.01
- **Error Rate**: < 1% of queries

### Monitoring Dashboard
```
┌─────────────────────────────────────────┐
│ CORTAP Hybrid Query System              │
├─────────────────────────────────────────┤
│ Queries Today:                    1,250 │
│  - Database:      450 (36%)            │
│  - RAG:           600 (48%)            │
│  - Hybrid:        200 (16%)            │
│                                         │
│ Avg Latency:                            │
│  - Database:       85ms                 │
│  - RAG:          3.2s                   │
│  - Hybrid:       3.5s                   │
│                                         │
│ Accuracy (last 100 queries):            │
│  - Database:     100% ✅                │
│  - RAG:           87% ⚠️                │
│  - Hybrid:        94% ✅                │
└─────────────────────────────────────────┘
```

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| JSON structure doesn't match expected format | Medium | High | Review JSON early, create flexible parser |
| Database performance issues | Low | Medium | Connection pooling, indexing |
| Query routing misclassification | Medium | Medium | Extensive testing, manual review |
| Data migration errors | Low | High | Validate data, backup before migration |
| RAG quality regression | Low | High | A/B testing, metrics monitoring |
| Deployment issues | Medium | Medium | Staged rollout, feature flags |

---

## Team Assignments

### Backend Developer
- Database schema & migrations
- JSON parsing & ingestion
- Query routing logic
- Hybrid engine core
- API updates
- **Estimated Hours**: 40-50 hours

### Frontend Developer
- UI updates for source type display
- Example queries
- User feedback collection
- **Estimated Hours**: 10-15 hours

### QA/Testing
- Integration testing
- Performance benchmarking
- User acceptance testing
- **Estimated Hours**: 15-20 hours

### DevOps
- Database setup on Render
- Environment configuration
- Monitoring setup
- **Estimated Hours**: 8-10 hours

---

## Communication Plan

### Daily Standups
- Progress updates
- Blockers
- Next 24-hour plan

### Weekly Reviews
- Demo completed features
- Metrics review
- Adjust timeline if needed

### Stakeholder Updates
- Day 7: Database + routing complete
- Day 14: Hybrid engine ready for staging
- Day 21: Production rollout complete

---

## Next Steps

1. **Review JSON Structure** (1-2 hours)
   - Share JSON file
   - Confirm schema matches expectations
   - Identify any edge cases

2. **Kick-off Meeting** (1 hour)
   - Review this plan
   - Assign tasks
   - Set up project board

3. **Start Phase 1** (Day 1)
   - Create database schema
   - Set up local PostgreSQL
   - Begin JSON parser

---

**Status**: Plan Ready for Review
**Created**: December 5, 2025
**Version**: 1.0
**Estimated Completion**: December 26, 2025 (3 weeks from start)
