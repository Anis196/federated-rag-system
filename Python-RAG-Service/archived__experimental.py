import json
import os
import shutil
import threading
import time
from pathlib import Path

import chromadb
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from llama_index.core import Document as LIDocument, Settings, StorageContext
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.chroma import ChromaVectorStore
from pydantic import BaseModel

# ---------- Configuration ----------
ROOT_DIR = Path(__file__).parent
PERSIST_DIR = ROOT_DIR / "rag_storage"
DATA_DIR = ROOT_DIR
DATA_EXTS = {".csv", ".xls", ".xlsx", ".jsonl"}
DATA_POLL_INTERVAL = 5  # seconds
SIMILARITY_THRESHOLD = 0.30  # confidence cutoff for fallback

# ---------- File Reading ----------
def extract_text_from_file(p):
    import pandas as pd
    ext = p.suffix.lower()

    if ext == ".jsonl":
        return extract_text_from_jsonl(p)

    try:
        if ext in [".xls", ".xlsx"]:
            df = pd.read_excel(p, dtype=str)
            return df.to_string(index=False)
        elif ext == ".csv":
            df = pd.read_csv(p, dtype=str)
            return df.to_string(index=False)
        else:
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
    except Exception:
        return ""

def extract_text_from_jsonl(path: Path) -> str:
    lines = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            try:
                obj = json.loads(line.strip())
                lines.append(obj.get("content", str(obj)))
            except:
                lines.append(line.strip())
    return "\n".join(lines)


# ---------- Document Loader ----------
def collect_documents():
    docs = []
    for fn in os.listdir(DATA_DIR):
        p = DATA_DIR / fn
        if p.suffix.lower() in DATA_EXTS:
            text = extract_text_from_file(p)
            if text.strip():
                docs.append(LIDocument(text=text))
    return docs


# ---------- Monitor for file changes ----------
def get_files_snapshot():
    return {(f.name, f.stat().st_mtime) for f in DATA_DIR.iterdir() if f.suffix.lower() in DATA_EXTS}


# ---------- RAG Engine ----------
class IndexManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._index = None
        self._last_snapshot = None

        self._setup_llm()
        self._start_indexing()
        self._start_monitor()

    def _setup_llm(self):
        Settings.llm = Ollama(
            model="tinyllama",
            request_timeout=120,
            temperature=0.1,
            system_prompt=(
                "You are a friendly restaurant assistant. "
                "Keep responses short, warm, helpful, and human. "
                "Never show raw CSV, system text, or technical details."
            )
        )
        Settings.embed_model = OllamaEmbedding(model_name="nomic-embed-text")
        Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=64)

    def _start_indexing(self):
        with self._lock:
            docs = collect_documents()

            shutil.rmtree(PERSIST_DIR, ignore_errors=True)

            chroma_client = chromadb.PersistentClient(path=str(PERSIST_DIR / "chroma"))
            collection = chroma_client.get_or_create_collection("edi_rag")

            vector_store = ChromaVectorStore(chroma_collection=collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)

            from llama_index.core import VectorStoreIndex
            self._index = VectorStoreIndex.from_documents(docs, storage_context=storage_context)

            self._index.storage_context.persist(persist_dir=str(PERSIST_DIR))
            self._last_snapshot = get_files_snapshot()

    def _start_monitor(self):
        threading.Thread(target=self._monitor_files, daemon=True).start()

    def _monitor_files(self):
        while True:
            time.sleep(DATA_POLL_INTERVAL)
            if get_files_snapshot() != self._last_snapshot:
                print("[Live ingestion] Updating index...")
                self._start_indexing()

    # ---------- NEW: General chatbot response ----------
    def _general_chat(self, query):
        response = Settings.llm.complete(
            f"Respond as a warm restaurant assistant. User asked: '{query}'. Be simple and natural."
        )
        return response.text.strip()

    # ---------- Main query pipeline ----------
    def query(self, q: str) -> str:
        q_lower = q.lower()

        # Greetings
        if q_lower in {"hi", "hello", "hey", "good morning", "good evening"}:
            return "Hello! How can I help today?"

        retriever = self._index.as_retriever(similarity_top_k=1)
        nodes = retriever.retrieve(q)

        if not nodes or float(nodes[0].score or 0) < SIMILARITY_THRESHOLD:
            return self._general_chat(q)

        # Category safety check (desserts example)
        dessert_terms = {"sweet", "dessert", "ice cream", "cake", "chocolate", "gulab", "rasgulla"}
        dataset_text = nodes[0].get_text().lower()

        if dessert_terms & set(q_lower.split()) and not any(term in dataset_text for term in dessert_terms):
            return (
                "I don’t see any dessert items in our stored menu data yet. "
                "But if you're craving something sweet, gulab jamun, rasmalai, or a warm brownie are always great choices!"
            )

        # Actual RAG response
        response = Settings.llm.complete(
            f"Use this information to give a friendly answer (but do NOT list raw data):\n\n"
            f"Context: {nodes[0].text[:400]}\n\nUser asked: {q}"
        )
        return response.text.strip()


# ---------- API Layer ----------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

index_manager = IndexManager()


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    answer: str
    query: str
    timestamp: str


@app.post("/rag_query", response_model=QueryResponse)
async def rag_query(request: Request):
    body = await request.json()
    user_query = body.get("query", "").strip()

    if not user_query:
        return JSONResponse(status_code=400, content={"error": "Missing query input"})

    answer = index_manager.query(user_query)

    from datetime import datetime
    return QueryResponse(answer=answer, query=user_query, timestamp=datetime.utcnow().isoformat() + "Z")


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    print("[SYSTEM] Running RAG Chatbot on http://127.0.0.1:11435")
    uvicorn.run(app, host="127.0.0.1", port=11435)
# ---------- Allergy-aware response processing (example) ----------