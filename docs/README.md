# CORTAP-RAG Documentation

## Quick Navigation

### Getting Started
- **[../README.md](../README.md)** - Main project README with setup instructions
- **[../QUICKSTART.md](../QUICKSTART.md)** - Fast local development setup
- **[../TESTING.md](../TESTING.md)** - Testing procedures and validation

### Project Overview
- **[../PROJECT_SUMMARY.md](../PROJECT_SUMMARY.md)** - Complete implementation summary, features, and status
- **[../IMPLEMENTATION_SUMMARY.md](../IMPLEMENTATION_SUMMARY.md)** - Detailed technical implementation notes

### Architecture & Planning

#### Hybrid RAG+Database System (NEW)
- **[HYBRID_ARCHITECTURE.md](HYBRID_ARCHITECTURE.md)** - Complete architectural design for combining PostgreSQL with RAG
- **[HYBRID_IMPLEMENTATION_PLAN.md](HYBRID_IMPLEMENTATION_PLAN.md)** - 3-week implementation plan with detailed tasks

### Data
- **guide/** - FTA Compliance Guide PDFs and JSON structure
  - `Fiscal-Year-2025-Contractor-Manual_0.pdf` - Complete 767-page FTA guide
  - `guide_structure.json` - Structured data (sections, questions, indicators)

### Sprint Artifacts
- **sprint-artifacts/** - Technical specifications and planning documents
  - `tech-spec-cortap-rag.md` - Original technical specification

---

## What's New

### Version 1.2.0 (December 5, 2025)

**Hybrid Architecture Planned**: To address the 73% accuracy limitation for indicator counting queries, we've designed a hybrid system that combines:

1. **PostgreSQL Database** for structured queries (100% accuracy)
   - "What are the indicators for Title VI?" → SQL lookup
   - Fast (< 200ms), deterministic, $0 cost

2. **RAG System** for conceptual queries (maintains flexibility)
   - "What is the purpose of Title VI?" → Semantic search + LLM
   - Contextual understanding, open-ended answers

3. **Hybrid Queries** combining both
   - "Explain Title VI indicators" → Database list + RAG context
   - Best of both worlds

**Documentation Created**:
- ✅ Architecture design ([HYBRID_ARCHITECTURE.md](HYBRID_ARCHITECTURE.md))
- ✅ Implementation plan ([HYBRID_IMPLEMENTATION_PLAN.md](HYBRID_IMPLEMENTATION_PLAN.md))

**Next Steps**:
1. Review JSON guide structure
2. Implement database schema
3. Build query router
4. Deploy hybrid system

Expected timeline: 3 weeks

---

## Document Descriptions

### HYBRID_ARCHITECTURE.md
**Purpose**: Complete architectural design for the hybrid RAG+Database system

**Contents**:
- Problem statement and motivation
- High-level system design with diagrams
- PostgreSQL schema design
- Query routing logic
- Implementation components (code examples)
- Data ingestion pipeline
- Query examples for all types
- Performance expectations
- Testing strategy
- Monitoring approach

**Audience**: Developers, architects, technical stakeholders

**Read this if**: You need to understand how the hybrid system works or want to contribute to implementation

---

### HYBRID_IMPLEMENTATION_PLAN.md
**Purpose**: Step-by-step implementation guide with tasks, timelines, and acceptance criteria

**Contents**:
- 5-phase implementation plan (21 days)
- Detailed task breakdowns with time estimates
- Code templates and examples
- Testing procedures
- Deployment strategy with staged rollout
- Risk assessment
- Team assignments
- Success metrics

**Audience**: Development team, project managers, QA

**Read this if**: You're implementing the hybrid system or managing the project

---

## Key Concepts

### Current System (RAG)
```
User Question
    ↓
Semantic Search (ChromaDB)
    ↓
Retrieve Top-K Chunks
    ↓
GPT-4 Answer Generation
    ↓
Response
```

**Strengths**: Flexible, handles conceptual questions well
**Limitations**: 73% accuracy for structured data (indicator counts)

### Hybrid System (Planned)
```
User Question
    ↓
Query Router (classify)
    ↓
    ├─→ [Database] → SQL Query → 100% Accuracy
    ├─→ [RAG] → Semantic Search → Contextual Answer
    └─→ [Hybrid] → Both → Combined Response
```

**Strengths**: 100% accuracy for structured queries + maintains RAG flexibility
**Trade-offs**: Additional complexity, requires database maintenance

---

## Development Workflow

### To Work on Hybrid System:

1. **Read the architecture**: [HYBRID_ARCHITECTURE.md](HYBRID_ARCHITECTURE.md)
2. **Review the plan**: [HYBRID_IMPLEMENTATION_PLAN.md](HYBRID_IMPLEMENTATION_PLAN.md)
3. **Set up database**: Follow Phase 1 tasks
4. **Implement**: Follow phases sequentially
5. **Test**: Use testing strategy from architecture doc
6. **Deploy**: Follow deployment plan with feature flags

### To Understand Current System:

1. **Main README**: [../README.md](../README.md)
2. **Project Summary**: [../PROJECT_SUMMARY.md](../PROJECT_SUMMARY.md)
3. **Tech Spec**: [sprint-artifacts/tech-spec-cortap-rag.md](sprint-artifacts/tech-spec-cortap-rag.md)

---

## FAQ

### Why add a database when RAG works?
RAG achieves 73% accuracy for indicator counting because:
- Chunks overlap, causing duplicates
- LLM extraction is non-deterministic
- Token costs are high for simple lookups

Database gives 100% accuracy, instant responses, and $0 cost for structured queries.

### Will this break existing functionality?
No. The hybrid system:
- Keeps existing RAG for conceptual questions
- Adds database for structured queries
- Uses feature flags for safe rollout
- Has complete rollback plan

### What if the JSON structure changes?
The ingestion pipeline is designed to be flexible:
- Parser handles variations
- Validation catches errors
- Re-ingestion takes < 5 minutes

### How much does this cost?
- **Development**: 3 weeks (40-50 dev hours)
- **Infrastructure**: +$7/month (Render PostgreSQL starter)
- **Ongoing**: Database queries = $0, RAG queries = $0.01 (no change)

### When will this be ready?
Following the implementation plan: 3 weeks from start date.

---

## Contributing

When adding new documentation:

1. **Update this README** with links and descriptions
2. **Use clear headings** and navigation
3. **Include code examples** where helpful
4. **Add diagrams** for complex concepts
5. **Keep it actionable** - readers should know what to do next

---

## Questions?

- **Architecture questions**: See [HYBRID_ARCHITECTURE.md](HYBRID_ARCHITECTURE.md)
- **Implementation questions**: See [HYBRID_IMPLEMENTATION_PLAN.md](HYBRID_IMPLEMENTATION_PLAN.md)
- **General questions**: See [../README.md](../README.md)
- **Testing questions**: See [../TESTING.md](../TESTING.md)

---

**Last Updated**: December 5, 2025
