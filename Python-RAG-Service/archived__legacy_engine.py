import json
import os
import shutil
import threading
import time
from pathlib import Path
from typing import Optional

import chromadb
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from llama_index.core import Document as LIDocument
from llama_index.core import Settings, StorageContext
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.chroma import ChromaVectorStore
from pydantic import BaseModel


# ------------------ PATHS / FILE SETTINGS ------------------

ROOT_DIR = Path(__file__).parent
PERSIST_DIR = ROOT_DIR / "rag_storage"
DATA_DIR = ROOT_DIR
DATA_EXTS = {".csv", ".xls", ".xlsx", ".jsonl"}
DATA_POLL_INTERVAL = 5


# ------------------ CSV → NATURAL LANGUAGE CLEANER ------------------

def preprocess_menu_csv(text: str) -> str:
    """
    Convert spreadsheet-like rows into clean conversational menu descriptions.
    Keeps human-friendly data only.
    """
    import re

    lines = text.split("\n")
    processed = []

    for line in lines:
        if not line.strip():
            continue

        # Ignore headers
        if any(h in line.lower() for h in ["date", "timestamp", "qty", "quantity", "forecast", "index"]):
            continue

        parts = [p.strip() for p in line.split(",")]
        item = parts[0]

        spicy_ref = ["spicy", "hot", "karahi", "hari", "mirch"]
        veg_ref = ["paneer", "veg", "vegetable", "cauliflower", "soya","bhajee","aloo"]

        notes = []
        if any(v in item.lower() for v in veg_ref):
            notes.append("Vegetarian")
        if any(s in item.lower() for s in spicy_ref):
            notes.append("Usually spicy")
        else:
            notes.append("Mild available")

        processed.append(f"{item}: {', '.join(notes)}.")

    # dedupe
    processed = list(dict.fromkeys(processed))
    return "\n".join(processed)


# ------------------ FILE LOADERS ------------------

def extract_text_from_file(p: Path) -> str:
    import pandas as pd
    ext = p.suffix.lower()

    if ext == ".jsonl":
        return extract_text_from_jsonl(p)

    try:
        if ext in [".xls", ".xlsx"]:
            df = pd.read_excel(p, dtype=str)
            return df.to_string(index=False)
    except:
        pass

    try:
        if ext == ".csv":
            df = pd.read_csv(p, dtype=str)
            return df.to_string(index=False)
    except:
        pass

    try:
        return open(p, encoding="utf-8", errors="ignore").read()
    except:
        return ""


def extract_text_from_jsonl(file_path: Path) -> str:
    lines = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
                lines.append(obj.get("text", str(obj)))
            except:
                lines.append(line)
    return "\n".join(lines)


# ------------------ DOCUMENT LOADING ------------------

def collect_documents():
    docs = []
    for fname in os.listdir(DATA_DIR):
        p = DATA_DIR / fname
        if p.suffix.lower() in DATA_EXTS:
            raw = extract_text_from_file(p)
            cleaned = preprocess_menu_csv(raw)
            if cleaned.strip():
                docs.append(LIDocument(text=cleaned))
    return docs


def get_files_snapshot():
    return {(f.name, f.stat().st_mtime) for f in DATA_DIR.iterdir() if f.suffix.lower() in DATA_EXTS}


# ------------------ INDEX MANAGER ------------------

class IndexManager:
    def __init__(self):
        self._index = None
        self._lock = threading.Lock()
        self._last_snapshot = None
        self._start_indexing()
        self._start_monitor()

    def _start_indexing(self):
        with self._lock:
            self._build_index()

    def _build_index(self):

        SYSTEM_PROMPT = (
            "You are a warm and polite restaurant receptionist. "
            "You speak naturally, briefly (1–3 sentences), and helpfully. "
            "Never mention technical things like databases, CSV files, vectors, or context. "
            "If someone mentions allergies or spice concerns, prioritize mild recommendations. "
            "Avoid lists unless necessary. Just talk like a friendly staff member."
        )

        Settings.llm = Ollama(
            model="mistral:instruct",
            temperature=0.25,
            top_p=0.92,
            repeat_penalty=1.06,
            request_timeout=200,
            system_prompt=SYSTEM_PROMPT,
        )

        Settings.embed_model = OllamaEmbedding(model_name="nomic-embed-text")
        Settings.node_parser = SentenceSplitter(chunk_size=500, chunk_overlap=60)

        shutil.rmtree(PERSIST_DIR, ignore_errors=True)
        docs = collect_documents()

        client = chromadb.PersistentClient(str(PERSIST_DIR / "db"))
        collection = client.get_or_create_collection("menu")

        vector_store = ChromaVectorStore(chroma_collection=collection)
        storage_ctx = StorageContext.from_defaults(vector_store=vector_store)

        from llama_index.core import VectorStoreIndex
        self._index = VectorStoreIndex.from_documents(docs, storage_context=storage_ctx)
        self._index.storage_context.persist(str(PERSIST_DIR))
        self._last_snapshot = get_files_snapshot()

    def _start_monitor(self):
        threading.Thread(target=self._watch, daemon=True).start()

    def _watch(self):
        while True:
            time.sleep(DATA_POLL_INTERVAL)
            if get_files_snapshot() != self._last_snapshot:
                print("[RAG] Menu updated → rebuilding index...")
                self._start_indexing()

    def query(self, q: str) -> str:
        if not self._index:
            return "Just a moment, still loading the menu."

        from llama_index.core.prompts import PromptTemplate

        retriever = self._index.as_retriever(similarity_top_k=2)
        matches = retriever.retrieve(q)

        if not matches:
            return "I don't see that item, but I'm happy to suggest something similar."

        prompt = PromptTemplate(
            "Guest question: {query_str}\n"
            "Useful menu info:\n{context_str}\n\n"
            "Respond politely and conversationally in under 3 sentences:"
        )

        qe = self._index.as_query_engine(
            similarity_top_k=2,
            response_mode="tree_summarize",
            text_qa_template=prompt
        )

        return str(qe.query(q)).strip()


# ------------------ FASTAPI API ------------------

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

index_manager = IndexManager()


class QueryReq(BaseModel):
    query: str


class QueryResp(BaseModel):
    answer: str
    timestamp: str


@app.post("/rag_query", response_model=QueryResp)
async def rag_query(req: QueryReq):
    from datetime import datetime
    reply = index_manager.query(req.query)
    return QueryResp(answer=reply, timestamp=datetime.utcnow().isoformat() + "Z")


@app.get("/health")
def health():
    return {"status": "ready"}


if __name__ == "__main__":
    print("🚀 Assistant running on http://127.0.0.1:11435")
    uvicorn.run(app, host="127.0.0.1", port=11435)
