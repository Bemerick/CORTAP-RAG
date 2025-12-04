# Testing & Validation Guide

## Pre-deployment Testing Checklist

### 1. Ingestion Validation

**Test**: Verify all 38 PDFs are processed
```bash
cd backend
python3 ingest.py
```

**Expected Output**:
- ✅ Found 38 PDF files to process
- ✅ Processing each file shows progress
- ✅ Successfully processed 38 documents
- ✅ Total documents indexed: 38

**Validation**:
```bash
# Check health endpoint
curl http://localhost:8000/api/v1/health
```
Should show `"database_ready": true`

---

### 2. API Endpoint Testing

**Test 1: Common Questions**
```bash
curl http://localhost:8000/api/v1/common-questions
```
Expected: JSON array with 5 common questions

**Test 2: Query Endpoint**
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What are ADA paratransit eligibility requirements?"}'
```

Expected Response Structure:
```json
{
  "answer": "Based on the provided sources...",
  "confidence": "medium",
  "sources": [...],
  "ranked_chunks": [...]
}
```

**Validation Criteria**:
- ✅ Response returns in < 5 seconds
- ✅ Answer contains [Source N] citations
- ✅ Confidence is one of: low, medium, high
- ✅ Sources array has 1-3 items
- ✅ ranked_chunks has up to 5 items with scores

---

### 3. Comprehensive Query Test Suite

Test one question from each category:

#### ADA General
```
Question: "What are the key ADA requirements for fixed route service?"
Expected: Information about accessibility features, announcements, priority seating
Validate: Sources from "ADA_General" category
```

#### ADA Complementary Paratransit
```
Question: "What are the eligibility requirements for paratransit service?"
Expected: Functional eligibility criteria, certification process
Validate: Sources from "ADA_Complementary_Paratransit" category
```

#### Disadvantaged Business Enterprise
```
Question: "How should DBE goals be established?"
Expected: Goal-setting methodology, market area analysis
Validate: Sources from "Disadvantaged_Business_Enterprise" category
```

#### Financial Management
```
Question: "What financial management systems are required?"
Expected: Accounting standards, financial controls, audit requirements
Validate: Sources from "Financial_Management_and_Capacity" category
```

#### Procurement
```
Question: "What are the procurement thresholds for different methods?"
Expected: Micro-purchase, small purchase, sealed bids, competitive proposals
Validate: Sources from "Procurement" category
```

#### Title VI
```
Question: "What are Title VI compliance obligations?"
Expected: Non-discrimination requirements, equity analysis
Validate: Sources from "Title_VI" category
```

#### Safety
```
Question: "What are the safety management requirements?"
Expected: Safety plans, SMS requirements, incident reporting
Validate: Sources from safety-related chunks
```

---

### 4. Accuracy Validation

**Methodology**:
1. For each test question, verify the answer accuracy by:
   - Reading the source chunks provided
   - Confirming the answer is based ONLY on provided sources
   - Checking that citations ([Source N]) are accurate
   - Validating no hallucinated information

**Acceptance Criteria**:
- ✅ **AC11**: 90% of questions retrieve relevant chunk in top-3 results
- ✅ **AC12**: Zero hallucinations (all info from source docs)
- ✅ **AC13**: Citations match quoted text

**Red Flags**:
- ❌ Answer includes information not in sources
- ❌ [Source N] references don't match actual sources
- ❌ Confidence rating doesn't match answer quality
- ❌ Relevant chunks ranked below irrelevant ones

---

### 5. Performance Testing

**Latency Test**:
```bash
# Time 10 sequential queries
time for i in {1..10}; do
  curl -X POST http://localhost:8000/api/v1/query \
    -H "Content-Type: application/json" \
    -d '{"question": "What are ADA requirements?"}' > /dev/null 2>&1
done
```

**Expected**:
- ✅ **AC7**: P95 latency < 5 seconds
- Average: 2-4 seconds per query

**Load Test** (Optional):
Use Apache Bench or similar:
```bash
ab -n 50 -c 5 -p query.json -T application/json http://localhost:8000/api/v1/query
```

---

### 6. Frontend UI Testing

**Manual QA Checklist**:

**Chat Functionality**:
- ✅ User can type and send questions
- ✅ Messages appear in correct order (user right, assistant left)
- ✅ Loading indicator shows while processing
- ✅ Auto-scroll to bottom on new messages

**Common Questions**:
- ✅ Displayed when chat is empty
- ✅ Clicking populates input field
- ✅ Question is submitted correctly

**Confidence Display**:
- ✅ Badge appears on assistant messages
- ✅ Colors: Green (high), Yellow (medium), Red (low)
- ✅ Badge text: "HIGH CONFIDENCE", "MEDIUM CONFIDENCE", "LOW CONFIDENCE"

**Source Citations**:
- ✅ "View Sources" button appears
- ✅ Expandable/collapsible sources section
- ✅ Shows all ranked chunks with scores
- ✅ Category names are readable (underscores replaced with spaces)
- ✅ Excerpts are truncated appropriately

**Responsive Design**:
- ✅ Mobile layout works (< 768px width)
- ✅ Tablet layout works (768px - 1024px)
- ✅ Desktop layout works (> 1024px)

**Error Handling**:
- ✅ Backend offline: Shows error message
- ✅ Network error: Displays friendly error
- ✅ Empty input: Send button disabled

---

### 7. Edge Cases & Error Scenarios

**Test 1: Empty Database**
- Clear ChromaDB, query API
- Expected: Error or "no results" message

**Test 2: Very Long Question**
- Submit 500+ character question
- Expected: Graceful handling, no errors

**Test 3: Out-of-Domain Question**
- Ask: "What's the weather today?"
- Expected: "I couldn't find relevant information..." response

**Test 4: Special Characters**
- Include quotes, symbols in question
- Expected: No parsing errors

---

### 8. Deployment Validation (Render)

**Pre-deploy**:
1. ✅ Environment variables set in Render dashboard
2. ✅ `OPENAI_API_KEY` configured
3. ✅ Disk storage mounted for ChromaDB

**Post-deploy**:
1. Check backend health: `https://your-app.onrender.com/api/v1/health`
2. Test query endpoint via frontend
3. Verify ingestion ran on first deploy
4. Check logs for errors

---

### 9. Tuning Parameters (If Needed)

If accuracy is poor, adjust in `backend/config.py`:

**Increase retrieval breadth**:
```python
top_k_retrieval: int = 10  # From 5
```

**Adjust hybrid weights**:
```python
semantic_weight: float = 0.8  # More semantic
keyword_weight: float = 0.2   # Less keyword
```

**Change embedding model** (cheaper):
```python
embedding_model: str = "text-embedding-3-small"
```

**After changes**: Re-run ingestion and re-test

---

## Test Results Template

**Date**: ________
**Tester**: ________

| Test Category | Pass/Fail | Notes |
|--------------|-----------|-------|
| Ingestion (38 PDFs) | ☐ | |
| API Health Check | ☐ | |
| Query Endpoint | ☐ | |
| ADA Questions | ☐ | |
| Procurement Questions | ☐ | |
| DBE Questions | ☐ | |
| Title VI Questions | ☐ | |
| Financial Questions | ☐ | |
| Accuracy (no hallucinations) | ☐ | |
| Latency < 5s | ☐ | |
| Source citations accurate | ☐ | |
| UI responsive | ☐ | |
| Common questions work | ☐ | |
| Confidence badges display | ☐ | |

**Overall Status**: ☐ PASS ☐ FAIL

**Issues Found**:
1. _____________________
2. _____________________

**Recommendations**:
_____________________
