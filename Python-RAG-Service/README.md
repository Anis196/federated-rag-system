# Python RAG Service

FastAPI-based Retrieval-Augmented Generation service using LlamaIndex, ChromaDB, and Ollama for intelligent document search and response generation.

## Features

- **Real-time Document Ingestion** - Automatically detects and indexes new CSV, Excel, and JSONL files
- **Vector Search** - Uses ChromaDB for semantic search across documents
- **LLM Integration** - Powered by Ollama (tinyllama model)
- **Fallback Responses** - Graceful handling when relevant context isn't found
- **REST API** - FastAPI endpoints for health checks and RAG queries

## Prerequisites

- **Python 3.9+**
- **Ollama** - Running locally (pulls tinyllama and nomic-embed-text models on first run)

## Installation

```powershell
cd "A:\Aniss\EDI\Implementation Paper FINAL\EDI_RAG_Implem"
python -m venv .venv
.\.venv\Scripts\activate
pip install fastapi uvicorn chromadb llama-index ollama pandas openpyxl xlrd
```

## Quick Start

```powershell
python rag_edi_expanded.py
```

Wait for:
```
Uvicorn running on http://127.0.0.1:11435 (Press CTRL+C to quit)
```

On first run, it will:
1. Pull required Ollama models (~1-2 GB)
2. Parse all CSV/XLS/XLSX/JSONL files in the directory
3. Generate embeddings (~2-5 minutes for first run)
4. Build the vector index

## API Endpoints

### GET `/health`
Health check.

**Response:**
```json
{"status": "ok"}
```

### POST `/rag_query`
Query the RAG system.

**Request (JSON):**
```json
{
  "query": "What are the top items?"
}
```

**Request (Form):**
```
query=What are the top items?
```

**Response:**
```json
{
  "answer": "Based on the data, the top items are...",
  "query": "What are the top items?",
  "timestamp": 1700000000.123
}
```

## Configuration

Edit `rag_edi_expanded.py` to customize:

```python
ROOT_DIR = Path(__file__).parent                    # Data directory
PERSIST_DIR = ROOT_DIR / "rag_storage"              # Index storage
DATA_DIR = ROOT_DIR                                 # Ingestion directory
DATA_EXTS = {".csv", ".xls", ".xlsx", ".jsonl"}     # File types
DATA_POLL_INTERVAL = 5                              # Check interval (seconds)
```

### Ollama Models

Models are pulled on first run. To pre-download or customize:

```bash
ollama pull tinyllama
ollama pull nomic-embed-text
```

To use a different model, edit `rag_edi_expanded.py`:

```python
Settings.llm = Ollama(model="your-model-name", ...)
Settings.embed_model = OllamaEmbedding(model_name="your-embed-model")
```

## Data Formats

### CSV
```
item,week,forecast
Item A,1,150
Item B,1,120
```

### Excel
Automatically reads all sheets as separate documents.

### JSONL
```json
{"title": "Item A Forecast", "content": "Week 1: 150 units..."}
{"content": "Item B analysis..."}
```

## How It Works

1. **Ingestion** - Reads CSV/XLS/JSONL files from `DATA_DIR`
2. **Parsing** - Converts files to text documents
3. **Chunking** - Splits documents into 512-token chunks with 64-token overlap
4. **Embedding** - Generates vector embeddings using `nomic-embed-text`
5. **Storage** - Persists vectors to ChromaDB
6. **Query** - User query is embedded and searched for top-2 similar documents
7. **Generation** - LLM generates response grounded in retrieved context

## Query Pipeline

```
User Query
    ↓
Embed query vector (nomic-embed-text)
    ↓
Search ChromaDB for top-2 similar chunks
    ↓
If relevance > 0.15:
    Generate RAG response (tinyllama with context)
Else:
    Generate fallback response (no context)
    ↓
Return answer + timestamp
```

## Monitoring

Watch the terminal for logs:
- `[Live ingestion] Data files changed; rebuilding index...` - Index is rebuilding
- `Generating embeddings: 100%|...` - Embedding progress
- Request/response logs for API calls

## Troubleshooting

### "Ollama Error: The model stopped or ran out of resources"

Ollama is overloaded or crashed. Restart it:
```bash
# Kill Ollama and restart
# On Windows: taskkill /IM ollama.exe /F
# Then restart Ollama application
```

### Index not building / "Index not ready"

First run takes time to pull models and generate embeddings. Wait 5-10 minutes. Check the terminal for progress bars.

### "Could not find data files" / No embeddings generated

Ensure CSV/XLS/JSONL files are in the same directory as `rag_edi_expanded.py`:

```powershell
ls *.csv, *.xlsx  # List data files
```

### Port 11435 already in use

Change the port in the last line:
```python
uvicorn.run(app, host="127.0.0.1", port=11436)  # Use 11436 instead
```

## Performance Tips

- **First run**: Expect 5-10 minutes for model download + embedding generation
- **Subsequent queries**: 2-10 seconds depending on Ollama performance
- **Large documents**: Consider splitting into smaller files for better indexing

## Integration with Spring Boot

The Spring Boot backend at `http://localhost:8080` forwards chat requests to this service:

```
Browser → Spring (/api/rag/chat)
       ↓
       → Python (/rag_query)
       ↓
Browser ← Response
```

See `springboot-rag-chat/README.md` for full setup.

## File Structure

```
EDI_RAG_Implem/
├── *.csv, *.xlsx, *.jsonl    # Data files to ingest
├── rag_edi_expanded.py       # Main service (this file)
├── rag_storage/              # Persisted index (auto-created)
│   ├── chroma/               # Vector database
│   ├── docstore.json         # Documents
│   └── index_store.json      # Index metadata
└── .venv/                    # Python virtual environment
```

## License & Attribution

Uses:
- **LlamaIndex** - Document indexing
- **ChromaDB** - Vector store
- **Ollama** - Local LLM
- **FastAPI** - Web framework
