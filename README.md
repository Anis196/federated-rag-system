# Federated RAG-Based Prediction & Insights System

A comprehensive **Retrieval-Augmented Generation (RAG)** system combining Python AI/ML backend with Spring Boot API gateway and React frontend for intelligent document analysis and semantic search.

## 🏗️ System Architecture

```
┌─────────────────────────┐
│   React Frontend        │
│   (Vite + TypeScript)   │ Port 5173 (dev) / 8080 (prod)
└────────────┬────────────┘
             │
┌────────────▼────────────┐
│ Spring Boot Gateway     │
│ (REST API + Static)     │ Port 8080
└────────────┬────────────┘
             │
┌────────────▼────────────┐
│  Python RAG Service     │
│  (FastAPI + Ollama)     │ Port 11435
└─────────────────────────┘
  ├─ ChromaDB (Vector Store)
  ├─ LLamaIndex (RAG Orchestration)
  ├─ Ollama (LLM Inference)
  └─ Embeddings (nomic-embed-text)
```

## 📋 Project Structure

```
federated-rag-system/
├── python-rag-service/          # Python FastAPI RAG service
│   ├── main.py                  # Entry point
│   ├── requirements.txt          # Python dependencies
│   ├── rag_storage/             # Persistent vector embeddings
│   ├── docs/                    # Documentation
│   └── archived_*.py            # Legacy code files
│
├── backend/                     # Spring Boot REST gateway
│   ├── pom.xml                  # Maven configuration
│   ├── src/                     # Java source code
│   ├── target/                  # Build output
│   ├── docs/                    # Documentation
│   └── README.md
│
├── frontend/                    # React TypeScript frontend
│   ├── src/                     # React source code
│   ├── public/                  # Static assets
│   ├── package.json             # NPM dependencies
│   ├── vite.config.ts           # Vite build config
│   ├── docs/                    # Documentation
│   └── README.md
│
├── .gitignore                   # Git ignore rules
└── README.md                    # This file
```

## 🚀 Quick Start

### Prerequisites
- **Python 3.9+**
- **Java 17+**
- **Node.js 18+** (for frontend development)
- **Ollama** installed and running (models auto-download)

### Option 1: Full Stack (Recommended)

**Terminal 1 - Python RAG Service:**
```powershell
cd python-rag-service
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```
Service available at: `http://localhost:11435`

**Terminal 2 - Spring Boot Backend:**
```powershell
cd backend
mvn -DskipTests package
java -jar target/springboot-rag-chat-0.0.1-SNAPSHOT.jar
```
Available at: `http://localhost:8080`

**Terminal 3 - React Frontend (Optional - for development):**
```powershell
cd frontend
npm install
npm run dev
```
Dev server at: `http://localhost:5173`

**Then open browser:**
```
http://localhost:8080
```

### Option 2: Python Service Only (Quick Testing)
```powershell
cd python-rag-service
python main.py
```
Test with: `curl http://localhost:11435/health`

## 📚 Documentation

Each component has detailed documentation in its `docs/` folder:

### Python RAG Service
- [Architecture](python-rag-service/docs/ARCHITECTURE.md) - System design and components
- [Components](python-rag-service/docs/COMPONENTS.md) - Detailed component breakdown
- [API Reference](python-rag-service/docs/API_REFERENCE.md) - REST endpoint documentation
- [Data Ingestion](python-rag-service/docs/DATA_INGESTION.md) - How to add and process data

### Spring Boot Backend
- [Architecture](backend/docs/ARCHITECTURE.md) - System design
- [Components](backend/docs/COMPONENTS.md) - Component details

### React Frontend
- [Architecture](frontend/docs/ARCHITECTURE.md) - Frontend design
- [Components](frontend/docs/COMPONENTS.md) - Component details

## 🔄 Data Flow

```
1. User enters query in React Chat Interface
2. Frontend sends HTTP POST to Spring Boot (/api/rag/chat)
3. Spring Boot proxies request to Python FastAPI (/rag_query)
4. Python service:
   - Searches ChromaDB vector store for relevant documents
   - Uses LLamaIndex for context retrieval
   - Generates response using Ollama LLM
   - Returns JSON answer
5. Response flows back through Spring Boot to frontend
6. Frontend displays AI-generated answer
```

## ⚙️ Configuration

### Python Service
Edit `python-rag-service/main.py`:
```python
DATA_DIR = Path(__file__).parent          # Where to scan for data files
DATA_POLL_INTERVAL = 5                    # Scan interval (seconds)
DATA_EXTS = {".csv", ".xls", ".xlsx"}    # Supported file types
```

### Spring Boot Backend
Edit `backend/src/main/resources/application.properties`:
```properties
server.port=8080
rag.python.url=http://localhost:11435/rag_query
```

### React Frontend
Create `frontend/.env.local`:
```
VITE_API_URL=http://localhost:8080
VITE_RAG_ENDPOINT=/api/rag/chat
```

## 📦 Supported Data Formats

| Format | Extension | Use Case |
|--------|-----------|----------|
| CSV | `.csv` | Tabular data (products, forecasts) |
| Excel | `.xlsx`, `.xls` | Spreadsheet data |
| JSONL | `.jsonl` | Line-delimited JSON |
| Text | `.txt` | Plain text documents |

Add data files to `python-rag-service/` root directory. Service auto-indexes every 5 seconds.

## 🤖 LLM Models

- **Embedding Model:** `nomic-embed-text` (~500MB)
- **LLM Model:** `tinyllama` (~1.5GB)
- **Auto-downloaded** on first run via Ollama

Both models run locally for privacy and no API costs.

## 📊 Key Features

✅ **Semantic Search** - Find relevant documents using embeddings
✅ **Vector Store** - Persistent ChromaDB for fast retrieval
✅ **Local LLM** - Ollama-powered AI responses (no API keys)
✅ **REST API** - Spring Boot gateway for easy integration
✅ **React UI** - Modern, responsive chat interface
✅ **Auto-Indexing** - Automatically detects and indexes new data files
✅ **Type-Safe** - TypeScript frontend + Spring Boot backend
✅ **Production-Ready** - Scalable architecture

## 🔌 API Endpoints

### Python Service (Port 11435)

**GET** `/health`
```bash
curl http://localhost:11435/health
```
Response: `{"status": "ok"}`

**POST** `/rag_query`
```bash
curl -X POST http://localhost:11435/rag_query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the top items?", "k": 3}'
```

### Spring Boot Gateway (Port 8080)

**POST** `/api/rag/chat`
```bash
curl -X POST http://localhost:8080/api/rag/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the top items?"}'
```

## 🛠️ Development

### Backend Development
```powershell
cd backend
mvn spring-boot:run
```

### Frontend Development
```powershell
cd frontend
npm run dev
```

### Python Service Development
```powershell
cd python-rag-service
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 11435
```

## 📝 File Naming Convention

- `main.py` - Current production code
- `archived__*.py` - Legacy/backup versions (not used)

## 🐛 Troubleshooting

### Port Already in Use
```powershell
# Find process using port 11435 (Python service)
netstat -ano | findstr :11435

# Kill process (replace PID with process ID)
taskkill /PID <PID> /F
```

### Ollama Not Running
```bash
# Start Ollama service
ollama serve
```

### Modules Not Found (Python)
```bash
cd python-rag-service
pip install -r requirements.txt
```

### React Build Issues
```bash
cd frontend
npm install
npm run build
```

## 📄 License

[Add your license here]

## 👥 Authors

[Add author information]

## 🤝 Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## 📞 Support

For issues, questions, or contributions, please open an issue on GitHub.

---

**Ready to use?** Start with the [Quick Start](#-quick-start) section above!
