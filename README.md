# CORTAP-RAG: FTA Compliance Assistant

A Retrieval-Augmented Generation (RAG) application for querying FTA (Federal Transit Administration) compliance documentation.

## Features

- 🔍 **Intelligent Search**: Hybrid search combining semantic embeddings and keyword matching
- 💬 **Chat Interface**: Clean, intuitive Q&A interface with conversation history
- 📊 **Confidence Scoring**: Transparent confidence ratings for each answer
- 📚 **Source Citations**: Full traceability with ranked source documents
- ⚡ **Fast Retrieval**: Sub-5 second query responses
- 🎯 **Common Questions**: Pre-loaded frequently asked compliance questions
- 🧠 **Contextual Awareness**: Maintains conversation context across multiple questions

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **LangChain** - RAG orchestration
- **ChromaDB** - Vector database for embeddings
- **OpenAI** - GPT-4 for generation, text-embedding-3-large for embeddings
- **BM25** - Keyword-based retrieval

### Frontend
- **React 18** with TypeScript
- **Tailwind CSS** - Styling
- **React Query** - API state management
- **React Markdown** - Response rendering

## Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- OpenAI API key

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file:
```bash
cp .env.example .env
```

4. Edit `.env` and add your OpenAI API key:
```
OPENAI_API_KEY=your_key_here
CHROMA_DB_PATH=./chroma_db
ENVIRONMENT=development
```

5. Run ingestion to process the full FTA guide:
```bash
python ingest_full_guide.py
```

Note: This processes the entire 767-page FTA manual and creates 1,442 intelligent chunks. Takes ~15 minutes.

6. Start the backend server:
```bash
python main.py
```

Backend will run at http://localhost:8000

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create `.env` file:
```bash
cp .env.example .env
```

4. Start development server:
```bash
npm run dev
```

Frontend will run at http://localhost:3000

## Usage

1. Start both backend and frontend servers
2. Open http://localhost:3000 in your browser
3. Click a suggested question or type your own
4. View answers with confidence scores and source citations
5. Expand "View Sources" to see ranked document chunks
6. Ask follow-up questions - the system maintains conversation context automatically

## Project Structure

```
CORTAP-RAG/
├── backend/
│   ├── api/              # FastAPI routes and service layer
│   ├── ingestion/        # PDF processing and embedding generation
│   ├── retrieval/        # Hybrid search and RAG pipeline
│   ├── models/           # Pydantic schemas
│   ├── config.py         # Configuration management
│   ├── main.py           # FastAPI app entry point
│   └── ingest.py         # CLI ingestion script
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── services/     # API client
│   │   ├── types/        # TypeScript types
│   │   └── App.tsx       # Main app component
│   └── index.html
├── docs/
│   └── guide/chunks/     # 38 pre-chunked PDF files
└── render.yaml           # Render.com deployment config
```

## API Endpoints

- `POST /api/v1/query` - Submit a question with optional conversation history
  - Request body: `{ "question": "string", "conversation_history": [{"role": "user|assistant", "content": "string"}] }`
- `GET /api/v1/common-questions` - Get suggested questions
- `GET /api/v1/health` - Health check
- `GET /docs` - Swagger API documentation

## Deployment

### Render.com

1. Push code to GitHub
2. Connect repository to Render
3. Render will auto-detect `render.yaml`
4. Set `OPENAI_API_KEY` environment variable in Render dashboard
5. Deploy!

Both frontend and backend will deploy automatically.

## Configuration

### Retrieval Tuning

Edit `backend/config.py`:

```python
# Retrieval settings
top_k_retrieval: int = 5           # Number of chunks to retrieve
semantic_weight: float = 0.7        # Semantic search weight
keyword_weight: float = 0.3         # BM25 keyword weight

# Model settings
embedding_model: str = "text-embedding-3-large"
llm_model: str = "gpt-4-turbo-preview"
```

### Common Questions

Add questions in `backend/config.py`:

```python
common_questions: list = [
    {"question": "Your question here?", "category": "Category_Name"},
]
```

## Testing

### Manual Testing

Run test queries covering all compliance categories:
- ADA General
- ADA Complementary Paratransit
- Disadvantaged Business Enterprise
- Financial Management
- Procurement
- Title VI
- Safety
- Charter Service
- School Bus
- Drug and Alcohol Testing

### Backend Tests

```bash
cd backend
pytest
```

## Troubleshooting

**No results returned?**
- Verify ChromaDB has documents: Check `/api/v1/health` endpoint
- Re-run ingestion: `python ingest.py`

**Slow queries?**
- Check OpenAI API rate limits
- Reduce `top_k_retrieval` in config

**CORS errors?**
- Verify backend URL in frontend `.env`
- Check CORS settings in `backend/main.py`

**Answers referencing wrong topics?**
- This is now fixed with conversation history tracking
- If issues persist, refresh the page to clear conversation context

## License

MIT

## Support

For issues or questions, contact the development team.
