# Python RAG Service - API Reference

## Endpoints

### GET `/health`
**Purpose:** Health check to verify service is running

**Response (200):**
```json
{
  "status": "ok"
}
```

**Usage:**
```bash
curl http://localhost:11435/health
```

---

### POST `/rag_query`
**Purpose:** Query the RAG system with semantic search and AI-generated responses

**Request (JSON):**
```json
{
  "query": "What are the top items?",
  "k": 3
}
```

**Request (Form Data):**
```
query=What are the top items?
```

**Response (200):**
```json
{
  "answer": "Based on the data, the top items are...",
  "query": "What are the top items?",
  "timestamp": 1700000000.123
}
```

**Status Codes:**
- `200` - Success
- `400` - Invalid query or missing parameters
- `503` - Index not ready or Ollama service unavailable

**Example using curl:**
```bash
curl -X POST http://localhost:11435/rag_query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the top items?", "k": 3}'
```

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama service URL |
| `FASTAPI_PORT` | `11435` | FastAPI server port |

---

## Error Handling

### Service Not Ready
```json
{
  "error": "Index not yet initialized",
  "status": 503
}
```
**Solution:** Wait for initial document indexing (2-5 minutes on first run)

### Query Error
```json
{
  "error": "Query must not be empty",
  "status": 400
}
```
**Solution:** Provide a non-empty query string
