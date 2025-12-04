# Quick Start Guide

## Initial Setup (One-time)

### 1. Backend Setup

```bash
# Navigate to backend
cd backend

# Install dependencies
pip3 install -r requirements.txt

# Create environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-...
nano .env  # or use your preferred editor

# Run ingestion to load PDFs into ChromaDB
python3 ingest.py
```

**Expected output**: Should process all 38 PDF chunks and confirm ingestion success.

### 2. Frontend Setup

```bash
# Navigate to frontend (from project root)
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env
# Default settings should work for local development
```

## Running the Application

### Terminal 1: Start Backend

```bash
cd backend
python3 main.py
```

Backend runs at: http://localhost:8000
API docs at: http://localhost:8000/docs

### Terminal 2: Start Frontend

```bash
cd frontend
npm run dev
```

Frontend runs at: http://localhost:3000

## Testing the System

### 1. Health Check

Visit http://localhost:8000/api/v1/health

Should return:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database_ready": true
}
```

### 2. Test Questions

Try these questions in the UI at http://localhost:3000:

**ADA Compliance:**
- "What are the ADA paratransit eligibility requirements?"
- "What are the service area requirements for complementary paratransit?"

**Procurement:**
- "What procurement methods are allowed under FTA regulations?"
- "What are the thresholds for different procurement methods?"

**DBE:**
- "What are the DBE program requirements?"
- "How should DBE goals be established?"

**Financial Management:**
- "What financial management systems are required?"
- "What are the requirements for financial capacity?"

**Title VI:**
- "What are Title VI compliance obligations?"
- "What data collection is required for Title VI?"

### 3. Verify Features

✅ **Confidence Badges**: Each answer should show LOW/MEDIUM/HIGH confidence
✅ **Source Citations**: Click "View Sources" to see ranked chunks with scores
✅ **Common Questions**: Buttons should appear when chat is empty
✅ **Response Time**: Should be < 5 seconds per query
✅ **Markdown Formatting**: Answers should render with proper formatting

## Troubleshooting

### "Module not found" errors (Backend)
```bash
cd backend
pip3 install -r requirements.txt
```

### "Cannot find module" errors (Frontend)
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### No documents in database
```bash
cd backend
python3 ingest.py
```

### CORS errors
Check that both backend (port 8000) and frontend (port 3000) are running.

## Next Steps

1. ✅ Verify all 38 PDFs are ingested
2. ✅ Test queries from each compliance category
3. ✅ Validate source citations are accurate
4. 🔧 Tune hybrid search weights if needed (see config.py)
5. 🚀 Deploy to Render.com when ready

## Sample .env Files

**backend/.env**:
```
OPENAI_API_KEY=sk-your-key-here
CHROMA_DB_PATH=./chroma_db
ENVIRONMENT=development
```

**frontend/.env**:
```
VITE_API_URL=http://localhost:8000
```
