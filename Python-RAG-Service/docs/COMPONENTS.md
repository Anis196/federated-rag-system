# Python RAG Service - Component Details

## Components Breakdown

### 1. Data Extraction Module
**File:** `python-rag-service/main.py`

**Functions:**
- `extract_text_from_file(path)` - Extracts text from CSV, XLS, XLSX, TXT
- `extract_text_from_jsonl(path)` - Parses JSONL format

**How it works:**
1. Detects file type by extension
2. Uses pandas for Excel/CSV parsing
3. Falls back to plain text reading
4. Returns formatted string content

**Used by:** Document ingestion pipeline

---

### 2. Document Ingestion Engine
**File:** `python-rag-service/main.py`

**Key Variables:**
- `documents` - List of indexed documents
- `index` - LLamaIndex VectorStoreIndex
- `query_engine` - Query interface

**Process:**
1. Scans `DATA_DIR` for new files
2. Extracts text from each file
3. Creates LLamaIndex Document objects
4. Generates embeddings via Ollama
5. Stores vectors in ChromaDB
6. Runs in background thread (`document_watcher` thread)

**Used by:** Continuous document monitoring

---

### 3. Vector Store (ChromaDB)
**Library:** chromadb

**Configuration:**
```python
chroma_client = chromadb.PersistentClient(path=PERSIST_DIR / "chroma")
vector_store = ChromaVectorStore(client=chroma_client, collection_name="rag_documents")
```

**Purpose:**
- Stores embeddings as vectors
- Enables semantic similarity search
- Persists data across restarts

**Used by:** Query engine for retrieval

---

### 4. Embedding Model (Ollama)
**Model:** `nomic-embed-text`

**Library:** llama_index.embeddings.ollama

**Purpose:** Converts text to vector embeddings

**Auto-downloaded on first run (~500MB)**

---

### 5. LLM (Ollama)
**Model:** `tinyllama`

**Library:** llama_index.llms.ollama

**Purpose:** Generates natural language responses

**Auto-downloaded on first run (~1.5GB)**

---

### 6. FastAPI REST API
**Endpoints:**
- `GET /health` - Health check
- `POST /rag_query` - RAG query endpoint

**CORS Middleware:** Allows requests from Spring Boot frontend

**Used by:** Spring Boot backend

---

### 7. Background Document Watcher
**Thread:** `document_watcher_thread`

**Interval:** Every `DATA_POLL_INTERVAL` seconds

**Function:** Monitors for new/updated files and re-indexes them

**Used by:** Real-time document ingestion

---

## Dependencies

| Library | Purpose |
|---------|---------|
| fastapi | Web framework |
| uvicorn | ASGI server |
| chromadb | Vector store |
| llama-index | RAG orchestration |
| ollama | LLM provider |
| pandas | Data parsing |
| openpyxl, xlrd | Excel support |
| pydantic | Data validation |
