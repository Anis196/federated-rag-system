import os
from pathlib import Path
import pandas as pd

from llama_index.core import Document as LIDocument, VectorStoreIndex
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import StorageContext, Settings

import chromadb
from ollama._types import ResponseError

# Directory where your files are
ROOT_DIR = Path(__file__).parent
PERSIST_DIR = ROOT_DIR / "rag_storage"


def extract_text_from_csv(path):
    df = pd.read_csv(path, dtype=str, low_memory=False)
    return df.to_string(index=False)

def extract_text_from_xls(path):
    from pathlib import Path
    import pandas as pd
    ext = Path(path).suffix.lower()
    tried = []
    xls = None
    # Try xlrd first for .xls
    if ext == ".xls":
        try:
            xls = pd.ExcelFile(path, engine="xlrd")
            tried.append("xlrd")
        except Exception:
            xls = None
    # Try openpyxl fallback (for modern .xls/.xlsx)
    if xls is None:
        try:
            xls = pd.ExcelFile(path, engine="openpyxl")
            tried.append("openpyxl")
        except Exception:
            xls = None
            tried.append("openpyxl_fail")
    # Try as CSV if failed as Excel
    if xls is not None:
        parts = []
        for sheet in xls.sheet_names:
            try:
                df = pd.read_excel(path, sheet_name=sheet, dtype=str, engine=xls.engine)
                parts.append(f"=== Sheet: {sheet} ===\n{df.to_string(index=False)}")
            except Exception as e:
                parts.append(f"[Error reading sheet {sheet}: {e}]")
        return "\n\n".join(parts)
    else:
        # Try as CSV
        try:
            df = pd.read_csv(path, dtype=str, low_memory=False)
            return f"[Read as CSV]\n{df.to_string(index=False)}"
        except Exception as e_csv:
            pass
        # Try as plain text
        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                txt = f.read()
            return f"[Read as text]\n{txt}"
        except Exception as e_text:
            print(f"[Unable to parse {path}] Excel engines tried: {tried}. CSV error: {e_csv}. Text error: {e_text}")
            return ""

def collect_documents():
    docs = []
    for fn in os.listdir(ROOT_DIR):
        p = ROOT_DIR / fn
        if p.suffix.lower() == ".csv":
            text = extract_text_from_csv(p)
        elif p.suffix.lower() in {".xls", ".xlsx"}:
            text = extract_text_from_xls(p)
        else:
            continue
        docs.append(LIDocument(text=text, metadata={"source": str(p)}))
    return docs

def build_index():
    from pathlib import Path
    import shutil
    Settings.llm = Ollama(
        model="tinyllama",
        request_timeout=120.0,
        temperature=0.1,
        system_prompt=(
            "You are a clever, friendly restaurant receptionist. "
            "Greet warmly and speak in a natural, casual tone. "
            "Never show context lists, raw numbers, metadata, or technical details directly to guests. "
            "Instead, summarize and recommend what is best, popular, or smartly paired, using your own words—just as a great receptionist would. "
            "Do not mention 'context' or cite sources. Just offer helpful, cheerful, brief, and action-oriented advice as if talking to a customer."
        )
    )
    Settings.embed_model = OllamaEmbedding(model_name="nomic-embed-text")
    Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=64)

    docstore_path = PERSIST_DIR / "docstore.json"
    chroma_dir = PERSIST_DIR / "chroma"
    # Only attempt load if persist dir, docstore.json, AND chroma dir exist
    if PERSIST_DIR.exists() and docstore_path.exists() and chroma_dir.exists():
        try:
            chroma_client = chromadb.PersistentClient(path=str(chroma_dir))
            chroma_collection = chroma_client.get_or_create_collection("edi_rag")
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store, persist_dir=str(PERSIST_DIR))
            return VectorStoreIndex.from_vector_store(vector_store, storage_context=storage_context)
        except Exception as e:
            print(f"[Index load error: {e}] Rebuilding index...")
            shutil.rmtree(PERSIST_DIR, ignore_errors=True)
    # Always rebuild if any required file missing or load failed
    docs = collect_documents()
    shutil.rmtree(PERSIST_DIR, ignore_errors=True)
    chroma_client = chromadb.PersistentClient(path=str(PERSIST_DIR / "chroma"))
    chroma_collection = chroma_client.get_or_create_collection("edi_rag")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)  # NO persist_dir here
    index = VectorStoreIndex.from_documents(docs, storage_context=storage_context, show_progress=True)
    index.storage_context.persist(persist_dir=str(PERSIST_DIR))
    return index

def interactive_query(index):
    query_engine = index.as_query_engine(similarity_top_k=2, response_mode="compact")
    print("RAG ready. Ask questions about your CSV/XLS docs. Type 'exit' to quit.\n")
    while True:
        q = input("> ").strip()
        if q.lower() in {"exit", "quit"}:
            break
        try:
            resp = query_engine.query(q)
            print("\n" + str(resp) + "\n")
        except ResponseError as ollama_err:
            print("\n[Ollama LLM error] Your local model crashed or was interrupted!\n"
                  "Please try a simpler question, restart ollama, or close other apps to free RAM/VRAM.\n"
                  f"Ollama says: {ollama_err}\n\n")
        except Exception as e:
            print(f"\n[Unexpected error during LLM query] {e}\n")

def main():
    print("Building/loading index over all data files ...")
    index = build_index()
    interactive_query(index)

if __name__ == "__main__":
    main()
