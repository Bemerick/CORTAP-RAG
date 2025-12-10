# Query Router Enhancement - Historical Audit Support

**Date**: December 10, 2025
**Status**: ✅ Complete

---

## Overview

Extended the CORTAP-RAG query router to support natural language queries about historical FTA audit reviews. The system now routes historical audit queries to the database backend and provides structured data from 29 ingested audit reviews covering 28 transit agencies.

---

## What Was Added

### 1. Historical Query Patterns (`retrieval/query_router.py`)

Added 12 new query patterns to detect historical audit questions:

**Recipient-Specific Queries**:
- "What deficiencies did GNHTD have?"
- "Show me AMTRAN audit results"
- "COLTS review findings"

**Regional Queries**:
- "List all agencies in Region 1"
- "Compare Region 1 vs Region 3"
- "Connecticut agencies"

**Review Area Queries**:
- "Common procurement deficiencies"
- "Legal findings across all agencies"

**Aggregate Queries**:
- "How many total deficiencies?"
- "List all agencies reviewed"

### 2. Database Query Helper (`database/audit_queries.py`)

Created `AuditQueryHelper` class with 6 main query methods:

#### `get_recipient_deficiencies(recipient, fiscal_year=None)`
Get all deficiencies for a specific recipient (by name or acronym).

**Example**:
```python
result = query_recipient_deficiencies('AMTRAN')
# Returns:
{
  "recipient": {
    "name": "Cambria County Transit Authority",
    "acronym": "AMTRAN",
    "city": "Johnstown",
    "state": "PA",
    "region": 3
  },
  "total_deficiencies": 2,
  "deficiencies": [
    {"review_area": "Legal", ...},
    {"review_area": "Procurement", ...}
  ]
}
```

#### `get_regional_deficiencies(region_number, review_area=None)`
Get deficiencies grouped by recipient for a specific region.

**Example**:
```python
result = query_regional_data(region=3)
# Returns deficiencies for all 13 Region 3 agencies
```

#### `get_common_deficiencies(review_area=None, min_occurrences=2)`
Find common deficiency patterns across all recipients.

**Example**:
```python
result = query_common_deficiencies()
# Returns:
{
  "common_deficiencies": [
    {"review_area": "Procurement", "recipient_count": 21, "total_deficiencies": 22},
    {"review_area": "Legal", "recipient_count": 11, "total_deficiencies": 11},
    {"review_area": "Maintenance", "recipient_count": 8, "total_deficiencies": 8}
  ]
}
```

#### `list_all_recipients(region_number=None, state=None)`
List all recipients with review counts, optionally filtered.

**Example**:
```python
result = query_all_recipients(region=3)
# Returns all 13 Region 3 recipients with review counts
```

#### `get_review_summary(recipient, fiscal_year=None)`
Get complete review data including all assessments.

#### `get_aggregate_stats()`
Get system-wide statistics.

**Example**:
```python
result = query_aggregate_stats()
# Returns:
{
  "total_recipients": 28,
  "total_reviews": 29,
  "total_deficiencies": 50,
  "by_region": [...],
  "top_deficiency_areas": [...]
}
```

---

## How It Works

### Query Flow

1. **User asks**: "What deficiencies did GNHTD have?"
2. **Query Router** detects historical pattern → routes to DATABASE backend
3. **Database Helper** searches by acronym/name → retrieves deficiencies
4. **Result returned** with structured data

### Pattern Detection Priority

1. **Historical patterns** (highest priority)
2. **Database patterns** (indicator/question lookups)
3. **RAG patterns** (conceptual questions)
4. **Hybrid patterns** (cross-section comparisons)

### Recipient Lookup

The helper uses flexible matching:
- Case-insensitive
- Matches both full name and acronym
- Partial name matching with LIKE

Examples that all work:
- `query_recipient_deficiencies('GNHTD')`
- `query_recipient_deficiencies('gnhtd')`
- `query_recipient_deficiencies('Greater New Haven')`

---

## Database Coverage

### Current Data (as of Dec 10, 2025)

```
Total Recipients:    28 agencies
Total Reviews:       29 FY2023 reviews
Total Deficiencies:  50 across 5 review areas
Total Assessments:   667 (23 areas × 29 reviews)

By Region:
  - Region 1: 15 agencies, 14 deficiencies
  - Region 3: 13 agencies, 36 deficiencies

Top Deficiency Areas:
  1. Procurement (22 deficiencies, 21 agencies affected)
  2. Legal (11 deficiencies, 11 agencies)
  3. Maintenance (8 deficiencies, 8 agencies)
  4. Title VI (7 deficiencies, 6 agencies)
  5. Charter Bus (1 deficiency, 1 agency)
```

### Geographic Coverage

**Region 1** (15 agencies):
- Connecticut: 5 agencies (GBT, GNHTD, NTD, NVCOG, ETD)
- Massachusetts: 4 agencies (LRTA, MEVA, MTA, SRTA)
- Maine: 5 agencies (AVCOG, BSOOB, Bangor, GPTD, KVRTA)
- New Hampshire: 1 agency (Nashua Transit)

**Region 3** (13 agencies):
- Pennsylvania: 6 agencies (AMTRAN, COLTS, LCTA, MCTA, PART, SCTA)
- Virginia: 4 agencies (CSPDC, GRTC, PAT, Radford Transit)
- Delaware: 2 agencies (DRPA, DRBA)
- West Virginia: 1 agency (NRTA)

---

## Testing Results

### Query Router Tests

All query types correctly routed:

```
✅ "What deficiencies did GNHTD have?" → DATABASE (historical)
✅ "Show me AMTRAN audit results" → DATABASE (historical)
✅ "List all agencies in Region 1" → DATABASE (historical)
✅ "Common procurement deficiencies" → DATABASE (historical)
✅ "Compare Region 1 vs Region 3" → DATABASE (historical)
✅ "How many indicators in TVI3?" → DATABASE (compliance indicators)
✅ "What are Charter Bus requirements?" → RAG (conceptual)
```

### Database Query Tests

All query functions tested successfully:

```
✅ get_recipient_deficiencies('GNHTD') → 0 deficiencies (clean review)
✅ get_recipient_deficiencies('AMTRAN') → 2 deficiencies (Legal, Procurement)
✅ get_regional_deficiencies(1) → 10 recipients with deficiency data
✅ get_common_deficiencies() → Top 4 deficiency areas identified
✅ list_all_recipients(region=3) → 13 Region 3 agencies listed
✅ get_aggregate_stats() → System-wide statistics generated
```

---

## API Usage Examples

### Example 1: Agency-Specific Query

```python
from database.audit_queries import query_recipient_deficiencies

# Natural language: "What deficiencies did AMTRAN have?"
result = query_recipient_deficiencies('AMTRAN')

print(f"{result['recipient']['name']} had {result['total_deficiencies']} deficiencies:")
for d in result['deficiencies']:
    print(f"  - {d['review_area']}")
```

### Example 2: Regional Comparison

```python
from database.audit_queries import query_regional_data

# Natural language: "Show me Region 3 deficiencies"
result = query_regional_data(region=3, review_area='Procurement')

print(f"Region {result['region']} Procurement Deficiencies:")
for recipient in result['recipients']:
    print(f"  {recipient['acronym']}: {len(recipient['deficiencies'])} deficiencies")
```

### Example 3: Pattern Analysis

```python
from database.audit_queries import query_common_deficiencies

# Natural language: "What are the most common deficiencies?"
result = query_common_deficiencies(min_occurrences=5)

for item in result['common_deficiencies']:
    print(f"{item['review_area']}: {item['recipient_count']} agencies affected")
```

### Example 4: System Overview

```python
from database.audit_queries import query_aggregate_stats

# Natural language: "Give me overall audit statistics"
stats = query_aggregate_stats()

print(f"Total Recipients: {stats['total_recipients']}")
print(f"Total Deficiencies: {stats['total_deficiencies']}")
print("\nTop Deficiency Areas:")
for area in stats['top_deficiency_areas'][:3]:
    print(f"  {area['review_area']}: {area['count']}")
```

---

## Integration Points

### Current Integration

The query router is already integrated with:
- `/api/query` endpoint (FastAPI backend)
- Frontend chat interface
- Existing compliance indicator queries

### Future Integration (Phase 3)

Will integrate with ChromaDB for hybrid queries:
- "Why is procurement compliance important?" → RAG (narrative text)
- "Show GNHTD deficiencies and explain best practices" → HYBRID (database + RAG)

---

## Files Modified/Created

### Created
1. **`backend/database/audit_queries.py`** (430 lines)
   - `AuditQueryHelper` class with 6 query methods
   - 5 convenience wrapper functions

### Modified
2. **`backend/retrieval/query_router.py`**
   - Added `HISTORICAL_PATTERNS` list (12 patterns)
   - Added `_check_historical_patterns()` method
   - Updated `classify_query()` to check historical patterns first

### Documentation
3. **`QUERY_ROUTER_ENHANCEMENT.md`** (this file)

---

## Known Limitations

1. **No Narrative Text Search Yet**: Only structured data queries supported. Narrative text from reports not yet in ChromaDB (Phase 3).

2. **Single Fiscal Year**: All current data is from FY2023. Query by fiscal year supported but not yet tested with multi-year data.

3. **Acronym Conflicts**: If two agencies share an acronym, queries by acronym may return unexpected results. Use full name for disambiguation.

4. **State Queries Not Fully Optimized**: State abbreviation pattern matches in queries but doesn't always trigger best query strategy.

---

## Next Steps (Phase 3)

1. **Ingest Narrative Text to ChromaDB**
   - Extract narrative sections from `historical_assessments.narrative_text`
   - Create embeddings for semantic search
   - Link chunks back to recipient/review/area

2. **Implement Hybrid Queries**
   - "Explain common procurement deficiencies" → DATABASE + RAG
   - "Show GNHTD results and best practices" → DATABASE + RAG

3. **Add Learning/Improvement Queries**
   - "How to improve audit performance in Legal area?"
   - "What corrective actions worked for procurement deficiencies?"

4. **Frontend Enhancements**
   - Display historical data in UI
   - Add charts/visualizations for regional comparisons
   - Create recipient detail pages

---

## Success Metrics

✅ **Query Router**: 12 new historical patterns added
✅ **Database Helper**: 6 query methods implemented
✅ **Test Coverage**: All query types tested successfully
✅ **Data Coverage**: 28 recipients, 29 reviews, 50 deficiencies
✅ **Integration**: Works with existing query router system

---

**Status**: ✅ Phase 2 Complete - Ready for Phase 3 (ChromaDB Integration)
