# Spring Boot RAG Chat Application

A full-stack RAG (Retrieval-Augmented Generation) chat application combining a React frontend, Spring Boot backend, and Python FastAPI service with Ollama + ChromaDB.

## Architecture

```
Client (Browser) 
    ↓
Spring Boot (8080) - Frontend + API Gateway
    ↓
Python FastAPI (11435) - RAG Service
    ↓
Ollama + ChromaDB - LLM + Vector Store
```

## Prerequisites

- **Java 17+** (for Spring Boot)
- **Python 3.9+** (for RAG service)
- **Node.js 18+** (for frontend build)
- **Ollama** running locally on default port (usually 11434)

## Quick Start

### 1. Start Python RAG Service

```powershell
cd "A:\Aniss\EDI\Implementation Paper FINAL\EDI_RAG_Implem"
python rag_edi_expanded.py
```

Wait for: `Uvicorn running on http://127.0.0.1:11435`

The service will build embeddings on startup (~2-5 minutes first run).

### 2. Build & Start Spring Boot

```powershell
cd "A:\Aniss\EDI\Implementation Paper FINAL\springboot-rag-chat"
mvn -DskipTests package
java -jar target\springboot-rag-chat-0.0.1-SNAPSHOT.jar
```

Wait for: `Tomcat started on port 8080`

### 3. Open in Browser

Visit: `http://localhost:8080`

Type a question and press Send. The response will appear in the chat.

## Troubleshooting

### "Failed to fetch" or no response showing

**Check 1: Is Python running?**
```powershell
curl http://127.0.0.1:11435/health
```
Should return: `{"status":"ok"}`

**Check 2: Is Spring reaching Python?**
Look in the Spring Boot console for logs like:
```
[RagChatController] Python response body: {answer:"...", timestamp:...}
```

**Check 3: Windows Firewall blocking port 11435?**
Temporarily disable to test:
```powershell
netsh advfirewall set allprofiles state off
# Re-enable after testing:
netsh advfirewall set allprofiles state on
```

**Check 4: Browser DevTools**
- Open DevTools (F12)
- Network tab → filter for `/api/rag/chat` POST
- Click the request → Response tab
- You should see `{"response": "...", "conversationId": "", "timestamp": ...}`

If Response is empty/null, the issue is in Spring or Python.

### Index not ready

If you see "[Index not ready]..." message, embeddings are still building. Wait 2-5 minutes.

### Connection aborted error in Spring logs

This can occur if responses are delayed. It's not critical — the UI should still show the response once it arrives.

## Development

### Frontend only (hot reload)

```powershell
cd frontend
npm ci
npm run dev
```

Then visit `http://localhost:5173` (dev server proxies to Spring at 8080).

### Backend only (faster rebuild)

After code changes:
```powershell
mvn -DskipTests package -Dskip.npm=true
java -jar target\springboot-rag-chat-0.0.1-SNAPSHOT.jar
```

## API Endpoints

- `GET /` - Serves the React frontend
- `POST /api/rag/chat` - Send a message to the RAG system
  - Request: `{ "message": "your question" }`
  - Response: `{ "response": "answer", "conversationId": "", "timestamp": ... }`

## Configuration

### Spring Boot

Edit `src/main/resources/application.properties`:
- `rag.python.url` - URL of Python RAG service (default: `http://localhost:11435/rag_query`)

### Python RAG Service

Edit `rag_edi_expanded.py`:
- `ROOT_DIR` - Data directory (default: script directory)
- `DATA_EXTS` - File extensions to ingest (CSV, XLS, XLSX, JSONL)
- `DATA_POLL_INTERVAL` - Seconds to check for file changes (default: 5)

## File Structure

```
springboot-rag-chat/
├── frontend/          # React + Vite
│   ├── src/
│   │   ├── components/ui/animated-ai-chat.tsx  # Chat UI
│   │   ├── hooks/useChatMessages.ts            # Message state
│   │   └── services/chatApi.ts                 # API calls
│   └── package.json
├── src/main/
│   ├── java/.../api/RagChatController.java     # Spring API
│   └── resources/application.properties
└── pom.xml
```

## Example Query

Send from the UI:
```
"What are the top items this week?"
```

Response (from RAG system):
```
"Based on the forecast data, the top items this week are: Item A (150 units), Item B (120 units), ..."
```

## Notes

- Chat history is in-memory; refreshing clears messages.
- The RAG index rebuilds whenever data files in the Python directory change.
- Responses can take 5-30 seconds depending on Ollama performance.

## Support

Check Spring Boot console and Python terminal for detailed logs.
