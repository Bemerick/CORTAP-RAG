# Tech-Spec: CORTAP-RAG - FTA Audit Compliance Assistant

**Created:** 2025-12-04
**Status:** Completed
**Project:** CORTAP-RAG

---

## Overview

### Problem Statement

FTA (Federal Transit Administration) auditors need to reference a comprehensive 700+ page compliance guide while conducting recipient audits. Currently, finding relevant information requires manual searching through extensive documentation, which is time-consuming and prone to missing critical compliance indicators. With 36 audits planned and different recipient types requiring different compliance criteria, auditors need an intelligent Q&A system that:

- Quickly surfaces relevant compliance information
- Shows confidence and ranks results by relevance
- Provides source citations for audit trail purposes
- Adapts to different recipient types (transit agencies, DBE programs, safety plans, etc.)

### Solution

Build **CORTAP-RAG**: A Retrieval-Augmented Generation (RAG) application that enables natural language queries against the FTA compliance guide. The system will:

1. **Ingest & Index**: Process 38 pre-chunked PDF sections (organized by compliance category) into a vector database
2. **Query Interface**: Provide a clean chat UI where auditors ask compliance questions
3. **Intelligent Retrieval**: Use hybrid search (semantic + keyword) with recipient-type metadata filtering
4. **Ranked Responses**: Return answers with confidence scores, multiple relevant chunks ranked high-to-low
5. **Source Citations**: Include section name, page references, and chunk IDs for audit documentation
6. **Common Questions**: Surface frequently-asked queries as quick-select options

**Future extensibility**: Support for adding lessons learned, highlighting source text in PDFs, and multi-audit session tracking.

### Scope (In/Out)

**IN SCOPE (MVP):**
- ✅ Chat interface for Q&A against FTA guide
- ✅ Ingest 38 PDF chunks with metadata (section category, chunk number)
- ✅ Semantic search using embeddings (OpenAI text-embedding-3-large)
- ✅ Hybrid retrieval (vector + keyword BM25)
- ✅ Response generation with source citations
- ✅ Confidence scoring and ranked results
- ✅ Recipient-type context filtering/boosting
- ✅ Common questions feature (hardcoded initially)
- ✅ Deployment to Render.com (frontend + backend)

**OUT OF SCOPE (Future phases):**
- ❌ User authentication/authorization
- ❌ Multi-user session management
- ❌ Lessons learned database (admin UI for adding content)
- ❌ PDF highlighting/viewer integration
- ❌ Audit tracking or question history per audit
- ❌ Fine-tuning custom models

---

## Context for Development

### Tech Stack

**Frontend:**
- React 18+ with TypeScript
- Tailwind CSS for styling
- React Query for API state management
- Markdown rendering for responses

**Backend:**
- Python 3.11+ with FastAPI
- LangChain for RAG orchestration
- ChromaDB for vector storage (persistent, file-based for Render)
- PyPDF2/pdfplumber for PDF text extraction
- OpenAI API (embeddings + GPT-4 for generation)
- Sentence-transformers for reranking (optional enhancement)

**Deployment:**
- Render.com web services (frontend + backend as separate services)
- ChromaDB persisted to Render disk storage
- Environment variables for API keys

### Codebase Patterns

**Since this is greenfield:**
- Use modular Python architecture: `/ingestion`, `/retrieval`, `/api`, `/models`
- FastAPI dependency injection for DB connections
- Pydantic models for request/response validation
- React component structure: `/components`, `/hooks`, `/services`, `/types`
- API client abstraction in frontend

### Files to Reference

**Existing:**
- `/docs/guide/chunks/*.pdf` - 38 pre-chunked PDF sections
  - Naming pattern: `{Category}_chunk_{N}.pdf`
  - Categories: ADA_General, ADA_Complementary_Paratransit, Procurement, Title_VI, etc.

**To Create:**
- Backend structure in `/backend`
- Frontend structure in `/frontend`
- Docker/config files for Render deployment

### Technical Decisions

**1. Vector Database: ChromaDB**
- **Why**: Lightweight, persistent, works well on Render disk storage, Python-native
- **Alternative considered**: Pinecone (overkill for single-user, costs money)

**2. Embeddings: OpenAI text-embedding-3-large**
- **Why**: Best-in-class semantic understanding, 3072 dimensions, cost-effective
- **Alternative**: text-embedding-3-small (cheaper but less accurate)

**3. LLM: GPT-4-turbo or GPT-4o**
- **Why**: Strong reasoning, good at citing sources, supports structured outputs
- **Alternative**: Claude 3.5 Sonnet (consider if cost becomes issue)

**4. Hybrid Search Strategy**
- **Semantic (70% weight)**: Dense embeddings for conceptual matching
- **Keyword (30% weight)**: BM25 for exact term/acronym matching (FTA terminology)
- **Reranking**: Optional cross-encoder reranker for top-K results

**5. Metadata Schema**
```python
{
  "chunk_id": "ADA_General_chunk_1",
  "category": "ADA_General",
  "chunk_number": 1,
  "file_path": "docs/guide/chunks/ADA_General_chunk_1.pdf",
  "recipient_types": ["transit_agency", "ada_paratransit"],  # Future use
  "page_range": "1-25"  # Extract if possible
}
```

**6. Confidence Scoring Approach**
- Retrieval score (cosine similarity): 0-1
- Rerank score (if used): 0-1
- LLM self-assessment: Prompt GPT to rate answer confidence (low/medium/high)
- Combined: `(retrieval_score * 0.4) + (rerank_score * 0.3) + (llm_confidence * 0.3)`

**7. Common Questions Implementation**
- Phase 1: Hardcoded list in backend config
- Phase 2: Track query frequency, auto-suggest top N
- Store as: `[{"question": "What are ADA paratransit eligibility requirements?", "category": "ADA_Complementary_Paratransit"}]`

---

## Implementation Plan

### Phase 1: Backend RAG Pipeline

**Task 1.1: Project Setup**
- [x] Initialize Python project with Poetry/pip requirements
- [x] Set up FastAPI app structure with `/api/v1` routes
- [x] Configure environment variables (OpenAI API key, ChromaDB path)
- [x] Create Pydantic models for requests/responses

**Task 1.2: PDF Ingestion & Embedding**
- [x] Write script to extract text from 38 PDF chunks
- [x] Parse metadata from filenames (category, chunk_number)
- [x] Generate embeddings using OpenAI API (batch process)
- [x] Store in ChromaDB with metadata
- [x] Create ingestion CLI command: `python ingest.py`

**Task 1.3: Retrieval Pipeline**
- [x] Implement semantic search in ChromaDB (top-K vector results)
- [x] Implement BM25 keyword search (using rank-bm25 library)
- [x] Merge results with hybrid scoring (70/30 weight)
- [x] Add metadata filtering by recipient_type (optional query param)
- [x] Return ranked results with scores

**Task 1.4: RAG Generation**
- [x] Create prompt template with system role: "You are an FTA compliance expert. Answer based ONLY on provided context. Cite sources."
- [x] Build context from top-5 retrieved chunks
- [x] Call GPT-4 with structured output (answer + confidence + sources)
- [x] Format response with citations (chunk_id, category, excerpt)

**Task 1.5: API Endpoints**
- [x] `POST /api/v1/query` - Main Q&A endpoint
  - Request: `{"question": str, "recipient_type": Optional[str]}`
  - Response: `{"answer": str, "confidence": str, "sources": [...], "ranked_chunks": [...]}`
- [x] `GET /api/v1/common-questions` - Return suggested questions
- [x] `GET /api/v1/health` - Healthcheck endpoint

### Phase 2: Frontend Chat Interface

**Task 2.1: React App Setup**
- [x] Create React app with TypeScript + Vite
- [x] Install Tailwind CSS, React Query, axios
- [x] Set up API client service with base URL from env

**Task 2.2: Chat UI Components**
- [x] Create `ChatContainer` component (main layout)
- [x] Create `MessageList` component (scrollable chat history)
- [x] Create `MessageBubble` component (user vs assistant styling)
- [x] Create `InputBar` component (text input + send button)
- [x] Create `SourceCitation` component (expandable source cards)

**Task 2.3: Common Questions Feature**
- [x] Create `SuggestedQuestions` component (chips/buttons)
- [x] Fetch from `/api/v1/common-questions` on load
- [x] Populate input on click

**Task 2.4: Confidence & Ranking Display**
- [x] Add confidence badge to responses (color-coded: green/yellow/red)
- [x] Display ranked chunks in expandable "View Sources" section
- [x] Show category, chunk_id, similarity score per source

**Task 2.5: State Management**
- [x] Use React Query for API calls (caching, loading states)
- [x] Local state for chat history (array of messages)
- [x] Handle loading/error states gracefully

### Phase 3: Deployment & Testing

**Task 3.1: Backend Deployment (Render)**
- [x] Create `Dockerfile` for FastAPI app
- [x] Configure Render web service (Python runtime)
- [x] Set environment variables in Render dashboard
- [x] Mount persistent disk for ChromaDB storage
- [x] Test ingestion script runs on deploy

**Task 3.2: Frontend Deployment (Render)**
- [x] Build React app for production
- [x] Create static site service on Render OR serve from FastAPI
- [x] Configure CORS for API calls
- [x] Set backend API URL in frontend env

**Task 3.3: Integration Testing**
- [x] Test 10 sample queries across all categories
- [x] Verify confidence scores are reasonable
- [x] Check source citations link to correct chunks
- [x] Test recipient_type filtering (if implemented)
- [x] Load test with concurrent queries

**Task 3.4: Accuracy Tuning**
- [x] Evaluate retrieval quality on test question set
- [x] Adjust hybrid search weights if needed
- [x] Experiment with chunk size (re-chunk if poor results)
- [x] Add reranking if precision is low
- [x] Tune prompt for better citation formatting

---

## Acceptance Criteria

### Functional Requirements
- [x] **AC1**: User can ask a natural language question and receive an answer within 5 seconds
- [x] **AC2**: Responses include at least 3 ranked source citations with category and chunk ID
- [x] **AC3**: Confidence score is displayed for each answer (low/medium/high)
- [x] **AC4**: Common questions are visible and clickable to auto-populate query
- [x] **AC5**: System handles questions about all 10 compliance categories (ADA, DBE, Title VI, etc.)
- [x] **AC6**: UI is responsive (mobile + desktop) and uses clean, professional styling

### Non-Functional Requirements
- [x] **AC7**: 95% of queries return results in < 5 seconds (p95 latency)
- [x] **AC8**: System deploys successfully to Render.com with persistent storage
- [x] **AC9**: Ingestion script processes all 38 PDFs without errors
- [x] **AC10**: API is documented with OpenAPI/Swagger UI

### Accuracy Requirements
- [x] **AC11**: On a test set of 20 questions, system retrieves at least 1 relevant chunk in top-3 results (90% recall@3)
- [x] **AC12**: Answers do not hallucinate information not present in source documents (manual validation)
- [x] **AC13**: Citations are accurate (chunk content matches quoted text)

---

## Additional Context

### Dependencies

**Python Packages:**
```
fastapi
uvicorn[standard]
langchain
langchain-openai
chromadb
pydantic
python-multipart
pypdf2 (or pdfplumber)
rank-bm25
python-dotenv
```

**React Packages:**
```
react
react-dom
typescript
@tanstack/react-query
axios
tailwindcss
react-markdown
```

### Testing Strategy

**Backend:**
- Unit tests for retrieval functions (pytest)
- Integration tests for API endpoints (httpx test client)
- Embedding/ingestion smoke tests

**Frontend:**
- Component tests with React Testing Library
- E2E test for full query flow (Playwright optional)

**Manual QA:**
- Test questions covering all 10 categories
- Edge cases: very short questions, questions outside domain
- Citation accuracy spot-checks

### Notes for Implementation

**RAG Accuracy Tuning Levers:**
1. **Chunk size**: Pre-chunked PDFs may not be optimal. Consider re-chunking with overlap if results are poor.
2. **Embedding model**: text-embedding-3-large is strong, but test against 3-small for cost/performance tradeoff.
3. **Retrieval top-K**: Start with K=5 for context, increase if missing relevant info.
4. **Hybrid weights**: 70/30 semantic/keyword is a starting point. Tune based on eval.
5. **Reranking**: Add a cross-encoder (e.g., ms-marco-MiniLM) to rerank top-10 → top-5 if precision is low.
6. **Prompt engineering**: Iteratively refine system prompt to improve citation format and reduce hallucination.
7. **Query expansion**: For short questions, use LLM to expand query before retrieval.
8. **Metadata filtering**: If recipient_type is known, boost or filter chunks by category.

**Future Features to Plan For:**
- **Lessons Learned DB**: Separate ChromaDB collection with admin API for adding entries
- **PDF Highlighting**: Store page numbers and bounding boxes during ingestion, return coordinates with citations
- **Multi-audit Tracking**: Add session/audit_id to queries, store conversation history per audit
- **Analytics Dashboard**: Track query patterns, low-confidence responses, most-used categories

**Render.com Deployment Considerations:**
- Free tier has limited disk (512MB). Use paid tier for ChromaDB persistence.
- Cold start latency: Keep backend warm or use background job to ping.
- Environment variables: Store OpenAI key securely in Render dashboard.

---

## Next Steps

1. **Review this spec** with Bob for approval
2. **Set up repos**: Monorepo vs separate frontend/backend repos
3. **Begin with Task 1.1-1.2**: Backend setup + ingestion pipeline
4. **Validate ingestion**: Ensure all 38 PDFs process correctly before building retrieval
5. **Iterative development**: Build → test → tune accuracy → deploy

**Recommended:** Start implementation in a fresh context to avoid token limits. Run this spec through the `quick-dev` workflow or hand off to a dev agent.

---

**Tech-Spec Complete! 🚀**
