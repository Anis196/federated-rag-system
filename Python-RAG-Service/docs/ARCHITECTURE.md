# Python RAG Service Architecture

## Overview
FastAPI-based Retrieval-Augmented Generation service that ingests documents, generates embeddings, and provides intelligent search & response generation using LLamaIndex, ChromaDB, and Ollama.

## Core Components

### 1. **Data Ingestion Pipeline**
- **Location:** `main.py` - `extract_text_from_file()`, `extract_text_from_jsonl()`
- **Supported Formats:** CSV, XLS, XLSX, JSONL, TXT
- **Function:** Automatically detects and indexes new files from `DATA_DIR`
- **Frequency:** Polls every `DATA_POLL_INTERVAL` seconds (default: 5s)

### 2. **Vector Store (ChromaDB)**
- **Location:** `main.py` - ChromaVectorStore initialization
- **Purpose:** Stores embeddings and enables semantic search
- **Persistence:** `rag_storage/` directory
- **Model:** `nomic-embed-text` via Ollama

### 3. **LLM Integration (Ollama)**
- **Location:** `main.py` - Ollama class initialization
- **Model:** `tinyllama` (lightweight, fast)
- **Purpose:** Generates responses based on context and queries
- **Port:** Local Ollama instance (auto-downloaded on first run)

### 4. **FastAPI Server**
- **Location:** `main.py` - FastAPI app initialization
- **Port:** 11435 (default)
- **Middleware:** CORS enabled for frontend communication
- **Features:** Real-time health checks, async query handling

## Data Flow

```
User Query (Frontend)
    ↓
Spring Boot Gateway (Port 8080)
    ↓
FastAPI RAG Service (Port 11435)
    ↓
[Vector Search in ChromaDB] + [Query to LLamaIndex]
    ↓
[Semantic Matching] + [Context Retrieval]
    ↓
[LLM Response Generation via Ollama]
    ↓
JSON Response → Spring Boot → Frontend
```

## Key Files

- **main.py** - Entry point, contains all core logic
- **rag_storage/** - Persistent vector index and embeddings
- **requirements.txt** - Python dependencies

## Configuration

Edit `main.py` constants:
```python
ROOT_DIR = Path(__file__).parent
PERSIST_DIR = ROOT_DIR / "rag_storage"
DATA_DIR = ROOT_DIR
DATA_EXTS = {".csv", ".xls", ".xlsx", ".jsonl"}
DATA_POLL_INTERVAL = 5
```
