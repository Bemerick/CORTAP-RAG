# Hybrid RAG + Database Architecture

## Overview

This document outlines the architectural design for combining **structured database queries** with **RAG (Retrieval-Augmented Generation)** to optimize for both accuracy and flexibility in querying the FTA Compliance Guide.

## Problem Statement

### Current Limitations
The existing pure-RAG approach struggles with structured queries:
- **Indicator counting**: Returns 16/22 indicators (73% accuracy) due to chunk overlap and LLM extraction variability
- **Duplicate detection**: Even with post-processing, duplicates appear across chunks
- **Consistency**: Same query can return different counts due to LLM non-determinism
- **Performance**: High token costs for queries that could be simple database lookups

### When RAG Excels vs. When Database Excels

**RAG Strengths**:
- ✅ Conceptual/explanatory questions ("What is the purpose of Title VI?")
- ✅ Open-ended queries ("Explain ADA compliance requirements")
- ✅ Contextual understanding ("How does this relate to...?")
- ✅ Semantic similarity matching

**Database Strengths**:
- ✅ Structured data retrieval ("List all indicators for Title VI")
- ✅ Exact counts ("How many indicators are there?")
- ✅ Enumeration ("What are the compliance questions?")
- ✅ Deterministic results (same query = same answer every time)

## Solution: Hybrid Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────┐
│                     User Question                        │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
         ┌────────────────────┐
         │   Query Router     │ ◄── Classifies query type
         │  (Smart Routing)   │
         └────────┬───────────┘
                  │
         ┌────────┴────────┐
         │                 │
    ┌────▼─────┐     ┌────▼──────┐      ┌──────────┐
    │ Database │     │    RAG    │      │  Hybrid  │
    │  Query   │     │   Query   │      │  Query   │
    └────┬─────┘     └────┬──────┘      └────┬─────┘
         │                │                   │
         │                │              ┌────┴─────┐
         │                │              │          │
         │                │         ┌────▼────┐ ┌──▼─────┐
         │                │         │ Database│ │  RAG   │
         │                │         └────┬────┘ └──┬─────┘
         │                │              │          │
         └────────────────┴──────────────┴──────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ Response Merger │
                 └────────┬────────┘
                          │
                          ▼
                   Final Answer
```

## Database Schema Design

### PostgreSQL Tables

```sql
-- Compliance sections (e.g., Title VI, ADA, Charter Bus)
CREATE TABLE compliance_sections (
    id SERIAL PRIMARY KEY,
    section_code VARCHAR(50) UNIQUE NOT NULL,  -- e.g., "Title_VI", "ADA_General"
    section_name VARCHAR(255) NOT NULL,         -- e.g., "Title VI"
    description TEXT,
    review_area VARCHAR(255),                   -- e.g., "Civil Rights"
    page_range VARCHAR(50),                     -- e.g., "11-1 to 11-15"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Compliance questions within each section
CREATE TABLE compliance_questions (
    id SERIAL PRIMARY KEY,
    section_id INTEGER REFERENCES compliance_sections(id) ON DELETE CASCADE,
    question_code VARCHAR(50) NOT NULL,         -- e.g., "TVI1", "TVI2"
    question_text TEXT NOT NULL,                -- Full question text
    question_order INTEGER,                     -- Order within section
    basic_requirement TEXT,                     -- Basic requirement description
    page_number INTEGER,                        -- Page in guide
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(section_id, question_code)
);

-- Indicators of compliance (the structured lists under each question)
CREATE TABLE compliance_indicators (
    id SERIAL PRIMARY KEY,
    question_id INTEGER REFERENCES compliance_questions(id) ON DELETE CASCADE,
    letter CHAR(1) NOT NULL,                    -- e.g., "a", "b", "c"
    indicator_text TEXT NOT NULL,               -- Full indicator description
    indicator_order INTEGER,                    -- Order within question
    source_page INTEGER,                        -- Page where indicator appears
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(question_id, letter)
);

-- Index for fast lookups
CREATE INDEX idx_section_code ON compliance_sections(section_code);
CREATE INDEX idx_question_code ON compliance_questions(question_code);
CREATE INDEX idx_section_questions ON compliance_questions(section_id);
CREATE INDEX idx_question_indicators ON compliance_indicators(question_id);
```

### Example Data

```sql
-- Example: Title VI section
INSERT INTO compliance_sections (section_code, section_name, description, review_area, page_range)
VALUES ('Title_VI', 'Title VI', 'Civil Rights compliance for transit agencies', 'Civil Rights', '11-1 to 11-15');

-- Example: TVI3 question
INSERT INTO compliance_questions (section_id, question_code, question_text, question_order, page_number)
VALUES (
    1,
    'TVI3',
    'Does the recipient notify the public of its rights under Title VI?',
    3,
    11-3
);

-- Example: Indicators under TVI3
INSERT INTO compliance_indicators (question_id, letter, indicator_text, indicator_order, source_page)
VALUES
    (1, 'a', 'Does the recipient disseminate the required Title VI Notice to the public as described in its Title VI Program?', 1, 11-3),
    (1, 'b', 'Does the published and posted Title VI Notice include all three of the required elements?', 2, 11-3);
```

## Query Routing Logic

### Classification Rules

```python
def classify_query_route(question: str) -> QueryRoute:
    """
    Determine optimal query execution path.

    Returns: "database", "rag", or "hybrid"
    """
    question_lower = question.lower()

    # DATABASE ROUTE - Structured queries
    database_patterns = [
        # Indicator queries
        ("what are the indicators", "database"),
        ("indicators of compliance for", "database"),
        ("list all indicators", "database"),
        ("how many indicators", "database"),

        # Question queries
        ("what are the questions", "database"),
        ("list all questions", "database"),
        ("compliance questions for", "database"),

        # Count queries
        ("how many", "database"),
        ("count of", "database"),
        ("total number", "database"),
    ]

    # RAG ROUTE - Conceptual/explanatory queries
    rag_patterns = [
        ("what is the purpose", "rag"),
        ("explain", "rag"),
        ("why is", "rag"),
        ("how does", "rag"),
        ("describe", "rag"),
        ("what should i know", "rag"),
    ]

    # HYBRID ROUTE - Queries needing both structure + context
    hybrid_patterns = [
        ("requirements and indicators", "hybrid"),
        ("explain the indicators", "hybrid"),
        ("what are the requirements", "hybrid"),  # Needs both lists + explanation
    ]

    # Check patterns in priority order
    for pattern, route in hybrid_patterns:
        if pattern in question_lower:
            return route

    for pattern, route in database_patterns:
        if pattern in question_lower:
            return route

    for pattern, route in rag_patterns:
        if pattern in question_lower:
            return route

    # Default to RAG for unknown query types
    return "rag"
```

## Implementation Components

### 1. Database Service Layer

```python
# backend/database/compliance_db.py

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from typing import List, Dict, Optional

class ComplianceDB:
    """Service layer for structured compliance data queries."""

    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)

    def get_indicators_by_section(self, section_code: str) -> Dict[str, any]:
        """
        Get all indicators for a compliance section.

        Returns:
            {
                "section_name": "Title VI",
                "total_indicators": 22,
                "questions": [
                    {
                        "question_code": "TVI3",
                        "question_text": "Does the recipient...",
                        "indicators": [
                            {"letter": "a", "text": "..."},
                            {"letter": "b", "text": "..."}
                        ]
                    }
                ]
            }
        """
        with Session(self.engine) as session:
            # Query section
            section = session.execute(
                select(ComplianceSection)
                .where(ComplianceSection.section_code == section_code)
            ).scalar_one_or_none()

            if not section:
                return None

            # Query questions with indicators
            questions = session.execute(
                select(ComplianceQuestion)
                .where(ComplianceQuestion.section_id == section.id)
                .order_by(ComplianceQuestion.question_order)
            ).scalars().all()

            result = {
                "section_name": section.section_name,
                "section_code": section.section_code,
                "total_indicators": 0,
                "questions": []
            }

            for question in questions:
                indicators = session.execute(
                    select(ComplianceIndicator)
                    .where(ComplianceIndicator.question_id == question.id)
                    .order_by(ComplianceIndicator.indicator_order)
                ).scalars().all()

                question_data = {
                    "question_code": question.question_code,
                    "question_text": question.question_text,
                    "indicators": [
                        {
                            "letter": ind.letter,
                            "text": ind.indicator_text,
                            "page": ind.source_page
                        }
                        for ind in indicators
                    ]
                }

                result["questions"].append(question_data)
                result["total_indicators"] += len(indicators)

            return result

    def search_sections(self, search_term: str) -> List[Dict]:
        """Search for compliance sections by name or keyword."""
        with Session(self.engine) as session:
            sections = session.execute(
                select(ComplianceSection)
                .where(ComplianceSection.section_name.ilike(f"%{search_term}%"))
            ).scalars().all()

            return [
                {
                    "section_code": s.section_code,
                    "section_name": s.section_name,
                    "description": s.description
                }
                for s in sections
            ]
```

### 2. Hybrid Query Engine

```python
# backend/retrieval/hybrid_query_engine.py

from typing import Dict, List
from .rag_pipeline import RAGPipeline
from database.compliance_db import ComplianceDB
from .query_router import classify_query_route

class HybridQueryEngine:
    """Orchestrates database + RAG queries."""

    def __init__(self, db: ComplianceDB, rag: RAGPipeline):
        self.db = db
        self.rag = rag

    def process_query(self, question: str, conversation_history: List = None) -> Dict:
        """
        Route query to appropriate backend(s) and combine results.
        """
        # Classify query
        route = classify_query_route(question)

        if route == "database":
            return self._handle_database_query(question)

        elif route == "rag":
            return self._handle_rag_query(question, conversation_history)

        else:  # hybrid
            return self._handle_hybrid_query(question, conversation_history)

    def _handle_database_query(self, question: str) -> Dict:
        """Pure database query for structured data."""
        # Extract section name from question
        section_code = self._extract_section_from_question(question)

        if not section_code:
            return {
                "answer": "I couldn't identify which compliance section you're asking about. Please specify (e.g., 'Title VI', 'ADA', 'Charter Bus').",
                "confidence": "low",
                "source": "database",
                "error": "section_not_found"
            }

        # Query database
        data = self.db.get_indicators_by_section(section_code)

        if not data:
            return {
                "answer": f"No data found for section: {section_code}",
                "confidence": "low",
                "source": "database",
                "error": "no_data"
            }

        # Format response
        answer = self._format_indicator_response(data)

        return {
            "answer": answer,
            "confidence": "high",  # Database = deterministic = high confidence
            "source": "database",
            "metadata": {
                "section_code": data["section_code"],
                "total_indicators": data["total_indicators"],
                "query_type": "structured"
            }
        }

    def _handle_rag_query(self, question: str, history: List) -> Dict:
        """Pure RAG query for conceptual questions."""
        # Use existing RAG pipeline
        chunks = self.rag.retrieve_chunks(question)
        result = self.rag.process_query(question, chunks, history)
        result["source"] = "rag"
        return result

    def _handle_hybrid_query(self, question: str, history: List) -> Dict:
        """Combine database structure with RAG context."""
        # Get structured data from database
        section_code = self._extract_section_from_question(question)
        db_data = self.db.get_indicators_by_section(section_code)

        # Get contextual explanation from RAG
        chunks = self.rag.retrieve_chunks(question, top_k=3)

        # Combine in LLM prompt
        combined_prompt = f"""
You have access to both structured compliance data and contextual information.

STRUCTURED DATA (from database):
{self._format_indicator_response(db_data)}

CONTEXTUAL INFORMATION (from guide):
{self.rag.build_context(chunks)}

Question: {question}

Provide a comprehensive answer that combines the structured indicator list with explanatory context from the guide.
"""

        # Generate combined answer
        answer = self.rag.llm.invoke(combined_prompt)

        return {
            "answer": answer,
            "confidence": "high",
            "source": "hybrid",
            "metadata": {
                "db_indicators": db_data["total_indicators"],
                "rag_chunks": len(chunks)
            }
        }

    def _extract_section_from_question(self, question: str) -> Optional[str]:
        """Extract compliance section from natural language question."""
        # Map common names to section codes
        section_map = {
            "title vi": "Title_VI",
            "title 6": "Title_VI",
            "civil rights": "Title_VI",
            "ada": "ADA_General",
            "americans with disabilities": "ADA_General",
            "charter bus": "Charter_Bus",
            "school bus": "School_Bus",
            "dbe": "Disadvantaged_Business_Enterprise",
            "procurement": "Procurement",
            # ... add all 23 sections
        }

        question_lower = question.lower()
        for keyword, code in section_map.items():
            if keyword in question_lower:
                return code

        return None

    def _format_indicator_response(self, data: Dict) -> str:
        """Format database results as readable text."""
        answer_parts = [
            f"There are {data['total_indicators']} indicators of compliance for {data['section_name']}:\n"
        ]

        for question in data["questions"]:
            answer_parts.append(f"\n**{question['question_code']}. {question['question_text']}**")
            for indicator in question["indicators"]:
                answer_parts.append(f"{indicator['letter']}. {indicator['text']}")

        return "\n".join(answer_parts)
```

### 3. API Endpoint Updates

```python
# backend/api/routes.py

from fastapi import APIRouter, Depends
from models.schemas import QueryRequest, QueryResponse
from database.compliance_db import ComplianceDB
from retrieval.hybrid_query_engine import HybridQueryEngine

router = APIRouter()

# Singleton instances
hybrid_engine = None

def get_hybrid_engine() -> HybridQueryEngine:
    global hybrid_engine
    if hybrid_engine is None:
        db = ComplianceDB(database_url=settings.database_url)
        rag = RAGPipeline(openai_api_key=settings.openai_api_key)
        hybrid_engine = HybridQueryEngine(db=db, rag=rag)
    return hybrid_engine

@router.post("/api/v1/query", response_model=QueryResponse)
async def query_endpoint(
    request: QueryRequest,
    engine: HybridQueryEngine = Depends(get_hybrid_engine)
):
    """
    Hybrid query endpoint - routes to database, RAG, or both.
    """
    result = engine.process_query(
        question=request.question,
        conversation_history=request.conversation_history
    )

    return QueryResponse(**result)
```

## Data Ingestion Pipeline

### JSON to Database Loader

```python
# backend/ingestion/load_json_to_db.py

import json
from pathlib import Path
from database.compliance_db import ComplianceDB
from sqlalchemy.orm import Session

def ingest_json_guide(json_path: Path, db: ComplianceDB):
    """
    Parse JSON guide structure and load into PostgreSQL.

    Expected JSON structure:
    {
        "sections": [
            {
                "section_code": "Title_VI",
                "section_name": "Title VI",
                "description": "...",
                "questions": [
                    {
                        "question_code": "TVI1",
                        "question_text": "...",
                        "indicators": [
                            {"letter": "a", "text": "..."},
                            {"letter": "b", "text": "..."}
                        ]
                    }
                ]
            }
        ]
    }
    """
    # Load JSON
    with open(json_path, 'r') as f:
        data = json.load(f)

    with Session(db.engine) as session:
        for section_data in data["sections"]:
            # Insert section
            section = ComplianceSection(
                section_code=section_data["section_code"],
                section_name=section_data["section_name"],
                description=section_data.get("description"),
                review_area=section_data.get("review_area"),
                page_range=section_data.get("page_range")
            )
            session.add(section)
            session.flush()  # Get section.id

            # Insert questions and indicators
            for q_idx, question_data in enumerate(section_data.get("questions", []), 1):
                question = ComplianceQuestion(
                    section_id=section.id,
                    question_code=question_data["question_code"],
                    question_text=question_data["question_text"],
                    question_order=q_idx,
                    basic_requirement=question_data.get("basic_requirement"),
                    page_number=question_data.get("page_number")
                )
                session.add(question)
                session.flush()  # Get question.id

                # Insert indicators
                for i_idx, indicator_data in enumerate(question_data.get("indicators", []), 1):
                    indicator = ComplianceIndicator(
                        question_id=question.id,
                        letter=indicator_data["letter"],
                        indicator_text=indicator_data["text"],
                        indicator_order=i_idx,
                        source_page=indicator_data.get("page")
                    )
                    session.add(indicator)

        session.commit()
        print(f"✅ Loaded {len(data['sections'])} sections into database")

# CLI script
if __name__ == "__main__":
    import sys
    json_file = sys.argv[1] if len(sys.argv) > 1 else "docs/guide/guide_structure.json"

    db = ComplianceDB(database_url=settings.database_url)
    ingest_json_guide(Path(json_file), db)
```

## Query Examples

### Example 1: Database Query
**Question**: "What are the indicators of compliance for Title VI?"

**Route**: Database

**Query**:
```sql
SELECT
    cq.question_code,
    cq.question_text,
    ci.letter,
    ci.indicator_text
FROM compliance_sections cs
JOIN compliance_questions cq ON cs.id = cq.section_id
JOIN compliance_indicators ci ON cq.id = ci.question_id
WHERE cs.section_code = 'Title_VI'
ORDER BY cq.question_order, ci.indicator_order;
```

**Response**:
```
There are 22 indicators of compliance for Title VI:

**TVI1. Did the recipient prepare and submit a Title VI Program?**
a. Did the recipient develop and submit a Title VI Program in FTA's TrAMS?
b. If the recipient submitted a Title VI Program and FTA has issued...

**TVI2. Does the recipient provide meaningful access to Limited English Proficient (LEP) persons?**
a. Has the recipient assessed whether the population of its service area...
b. Has the recipient translated vital documents...

... (all 10 questions with 22 total indicators)
```

**Confidence**: High (deterministic database result)

### Example 2: RAG Query
**Question**: "What is the purpose of Title VI compliance?"

**Route**: RAG

**Process**:
1. Semantic search retrieves chunks about Title VI purpose/overview
2. LLM generates explanation from context

**Response**:
```
Title VI of the Civil Rights Act of 1964 ensures that no person is excluded from
participation in, denied benefits of, or subjected to discrimination under any
program receiving Federal financial assistance on the basis of race, color, or
national origin. For transit agencies, this means...

[Source 1] [Source 2] [Source 3]
```

**Confidence**: High (contextual sources available)

### Example 3: Hybrid Query
**Question**: "Explain the Title VI indicators and their requirements"

**Route**: Hybrid

**Process**:
1. Database retrieves all 22 indicators (structured)
2. RAG retrieves contextual chunks about requirements
3. LLM combines both into comprehensive answer

**Response**:
```
Title VI compliance involves 22 indicators organized across 10 review areas.
These indicators ensure recipients meet civil rights obligations:

**Program Submission (TVI1)**
a. Recipients must develop and submit a Title VI Program in FTA's TrAMS
b. Programs must be updated every 3 years or when significant changes occur

This requirement ensures that transit agencies formally document their civil
rights compliance procedures...

[Continues with all indicators + contextual explanations]

[Database: 22 indicators] [RAG: 3 sources]
```

**Confidence**: High (both structured data + contextual explanation)

## Performance Expectations

### Query Latency
- **Database queries**: 50-100ms (SQL lookup)
- **RAG queries**: 2-4s (embedding + LLM)
- **Hybrid queries**: 2-5s (SQL + embedding + LLM)

### Accuracy
- **Database**: 100% accuracy for structured data
- **RAG**: 70-90% for conceptual questions
- **Hybrid**: 95%+ for questions needing both

### Cost
- **Database queries**: $0 (no LLM)
- **RAG queries**: ~$0.01 per query
- **Hybrid queries**: ~$0.01-0.02 per query

## Migration Path

### Phase 1: Database Setup (Week 1)
1. ✅ Design PostgreSQL schema
2. ✅ Create migration scripts
3. ✅ Parse JSON guide into database
4. ✅ Validate data integrity

### Phase 2: Query Router (Week 1-2)
1. ✅ Implement classification logic
2. ✅ Build database service layer
3. ✅ Test routing accuracy
4. ✅ Add logging/metrics

### Phase 3: Hybrid Engine (Week 2)
1. ✅ Integrate database + RAG
2. ✅ Build response merger
3. ✅ Update API endpoints
4. ✅ Test all query types

### Phase 4: Frontend Updates (Week 2-3)
1. ✅ Display source type (database/RAG/hybrid)
2. ✅ Show database metadata (indicator counts)
3. ✅ Update UI for hybrid responses
4. ✅ Add query examples

### Phase 5: Testing & Deployment (Week 3)
1. ✅ End-to-end testing
2. ✅ Performance benchmarking
3. ✅ Deploy to staging
4. ✅ Production rollout

## Configuration

### Environment Variables
```env
# Existing
OPENAI_API_KEY=sk-...
CHROMA_DB_PATH=/data/chroma_db

# New for hybrid system
DATABASE_URL=postgresql://user:pass@localhost:5432/cortap_compliance
QUERY_ROUTING_ENABLED=true
DEFAULT_QUERY_ROUTE=auto  # auto, database, rag, hybrid
```

### Feature Flags
```python
# config.py
class Settings(BaseSettings):
    # Existing settings
    openai_api_key: str
    chroma_db_path: str

    # New hybrid settings
    database_url: str
    enable_hybrid_queries: bool = True
    default_query_route: str = "auto"  # auto, database, rag, hybrid
    force_route: Optional[str] = None  # Override routing for testing
```

## Testing Strategy

### Unit Tests
```python
# tests/test_query_router.py
def test_database_route_detection():
    assert classify_query_route("What are the indicators for Title VI?") == "database"
    assert classify_query_route("How many indicators are there?") == "database"

def test_rag_route_detection():
    assert classify_query_route("What is the purpose of ADA?") == "rag"
    assert classify_query_route("Explain Charter Bus requirements") == "rag"

def test_hybrid_route_detection():
    assert classify_query_route("What are the requirements and indicators?") == "hybrid"
```

### Integration Tests
```python
# tests/test_hybrid_engine.py
def test_database_query_accuracy():
    engine = HybridQueryEngine(db, rag)
    result = engine.process_query("What are the indicators for Title VI?")
    assert result["metadata"]["total_indicators"] == 22
    assert result["source"] == "database"
    assert result["confidence"] == "high"

def test_rag_query_contextual():
    result = engine.process_query("What is Title VI?")
    assert result["source"] == "rag"
    assert len(result["sources"]) > 0

def test_hybrid_query_combines():
    result = engine.process_query("Explain Title VI indicators")
    assert result["source"] == "hybrid"
    assert "22 indicators" in result["answer"]
```

## Monitoring & Metrics

### Key Metrics to Track
```python
# Routing distribution
metrics.counter("query_route.database")
metrics.counter("query_route.rag")
metrics.counter("query_route.hybrid")

# Performance
metrics.histogram("query_latency.database")
metrics.histogram("query_latency.rag")
metrics.histogram("query_latency.hybrid")

# Accuracy (user feedback)
metrics.counter("query_feedback.helpful")
metrics.counter("query_feedback.not_helpful")
```

## Rollback Plan

If hybrid system has issues:

1. **Feature flag**: Set `enable_hybrid_queries=false` to fall back to pure RAG
2. **API versioning**: Keep old `/api/v1/query` endpoint, add `/api/v2/query` for hybrid
3. **Gradual rollout**: Route 10% → 50% → 100% of traffic to hybrid system
4. **Database backup**: Maintain PostgreSQL dumps for easy restoration

## Future Enhancements

1. **Caching**: Redis cache for common database queries
2. **Search indexing**: Elasticsearch for fuzzy section name matching
3. **Multi-language**: Store indicators in multiple languages
4. **Versioning**: Track guide versions and changes over time
5. **Audit trail**: Log all queries and responses for compliance

---

**Status**: Architecture Design Complete
**Next Step**: Review JSON structure and begin implementation
**Owner**: Development Team
**Last Updated**: December 5, 2025
