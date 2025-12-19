import json
import os
from pathlib import Path

import chromadb
import pandas as pd
from llama_index.core import Document as LIDocument
from llama_index.core import Settings, StorageContext, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.prompts import PromptTemplate
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.chroma import ChromaVectorStore
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
        csv_error = None
        try:
            df = pd.read_csv(path, dtype=str, low_memory=False)
            return f"[Read as CSV]\n{df.to_string(index=False)}"
        except Exception as err:
            csv_error = err
        # Try as plain text
        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                txt = f.read()
            return f"[Read as text]\n{txt}"
        except Exception as text_error:
            print(f"[Unable to parse {path}] Excel engines tried: {tried}. CSV error: {csv_error}. Text error: {text_error}")
            return ""

def collect_documents():
    docs = []
    for fn in os.listdir(ROOT_DIR):
        p = ROOT_DIR / fn
        suffix = p.suffix.lower()
        if suffix == ".csv":
            text = extract_text_from_csv(p)
        elif suffix in {".xls", ".xlsx"}:
            text = extract_text_from_xls(p)
        elif suffix == ".jsonl":
            text = extract_text_from_jsonl(p)
        else:
            continue
        docs.append(LIDocument(text=text))
    docs.extend(build_summary_documents())
    return docs


def extract_text_from_jsonl(path):
    lines = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for raw_line in f:
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                obj = json.loads(raw_line)
                if isinstance(obj, dict):
                    title = obj.get("title")
                    content = obj.get("content")
                    if title and content:
                        lines.append(f"Title: {title}\n{content}")
                    elif content:
                        lines.append(str(content))
                    else:
                        lines.append(json.dumps(obj, ensure_ascii=False))
                else:
                    lines.append(str(obj))
            except json.JSONDecodeError:
                lines.append(raw_line)
    return "\n\n".join(lines)


def build_summary_documents():
    summaries = []
    forecast_summary = build_top_forecast_summary()
    if forecast_summary:
        summaries.append(LIDocument(text=forecast_summary))

    horizon_summary = build_next_weeks_summary()
    if horizon_summary:
        summaries.append(LIDocument(text=horizon_summary))

    top_items_summary = build_top_items_summary()
    if top_items_summary:
        summaries.append(LIDocument(text=top_items_summary))

    return summaries


def build_top_forecast_summary():
    path_csv = ROOT_DIR / "all_items_forecast.csv"
    if not path_csv.exists():
        return None
    try:
        df = pd.read_csv(path_csv)
    except Exception:
        return None
    required_cols = {"Item Name", "PredictedOrders"}
    if not required_cols.issubset(df.columns):
        return None
    top_df = df.sort_values("PredictedOrders", ascending=False).head(10)
    if top_df.empty:
        return None
    lines = [
        "Top forecasted menu items based on predicted orders:",
    ]
    for idx, row in top_df.iterrows():
        item = row.get("Item Name", "Unknown item")
        orders = row.get("PredictedOrders", 0)
        week = row.get("Week", "-")
        date = row.get("Date", "")
        lines.append(f"- {item} • approx {orders:.0f} orders (week {week}, {date})")
    total_orders = df["PredictedOrders"].sum()
    avg_orders = df["PredictedOrders"].mean()
    lines.append(
        f"Total predicted orders across {len(df)} items: {total_orders:.0f}; average per item: {avg_orders:.1f}."
    )
    return "\n".join(lines)


def build_next_weeks_summary():
    path_csv = ROOT_DIR / "next_8_weeks_forecast.csv"
    if not path_csv.exists():
        return None
    try:
        df = pd.read_csv(path_csv)
    except Exception:
        return None
    if "PredictedTotal" not in df.columns:
        return None
    max_row = df.loc[df["PredictedTotal"].idxmax()]
    min_row = df.loc[df["PredictedTotal"].idxmin()]
    lines = [
        "Eight-week demand outlook:",
        f"- Highest volume expected in week {int(max_row['Week'])} of {int(max_row['Year'])}: roughly {max_row['PredictedTotal']:.0f} orders.",
        f"- Quietest week appears to be week {int(min_row['Week'])} of {int(min_row['Year'])}: around {min_row['PredictedTotal']:.0f} orders.",
        f"- Average weekly demand over this horizon: {df['PredictedTotal'].mean():.0f} orders."
    ]
    return "\n".join(lines)


def build_top_items_summary():
    path_jsonl = ROOT_DIR / "top_items_rag.jsonl"
    if not path_jsonl.exists():
        return None
    items = []
    try:
        with open(path_jsonl, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    content = obj.get("content") if isinstance(obj, dict) else None
                    if content:
                        parts = content.split(",")
                        if len(parts) == 2:
                            name = parts[0].split(":")[-1].strip()
                            quantity = parts[1].split(":")[-1].strip()
                            items.append((name, quantity))
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        return None
    if not items:
        return None
    lines = ["Top items by historical demand:"]
    for name, quantity in items[:10]:
        lines.append(f"- {name} • {quantity} orders served")
    return "\n".join(lines)

def build_index():
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
    qa_prompt = PromptTemplate(
        "You are a clever, friendly restaurant receptionist. Answer warmly and naturally using key details from context. "
        "CRITICAL: Never list raw context, file paths, item lists, or metadata. "
        "Weave key information into 1-2 natural sentences only. Keep it brief and conversational. "
        "\n\nGuest: {query_str}\n\nKey info: {context_str}\n\nYour answer:"
    )
    refine_prompt = PromptTemplate(
        "Polish the receptionist's answer. Rules: stay warm, concise (2-3 sentences), never show raw data or lists. "
        "\n\nCurrent: {existing_answer}\n\nNew info: {context_str}\n\nImproved answer:"
    )
    query_engine = index.as_query_engine(
        similarity_top_k=1,
        response_mode="compact",
        text_qa_template=qa_prompt,
        refine_template=refine_prompt,
    )
    print("RAG ready. Ask questions about your CSV/XLS docs. Type 'exit' to quit.\n")
    
    greetings = {"hi", "hii", "hey", "hello", "hello there", "hi there", "hey there", "howdy"}
    
    while True:
        q = input("> ").strip()
        if q.lower() in {"exit", "quit"}:
            break
        
        # Detect simple greetings
        q_clean = q.lower().replace("!", "").replace("?", "")
        if q_clean in greetings or (len(q) < 5 and q_clean in greetings):
            print("\nHello! Welcome to our restaurant. How can I help you today?\n")
            continue
        
        if len(q) < 3:
            print("\nCould you ask me something more specific?\n")
            continue
        try:
            resp = query_engine.query(q)
            text = getattr(resp, "response", None)
            if not text:
                text = getattr(resp, "message", None)
            if not text and hasattr(resp, "get_response_str"):
                text = resp.get_response_str()
            if not text:
                text = str(resp).strip()
            if not text or text.lower() == "empty response":
                text = "I'm not seeing enough details to answer that just yet. Could you try asking in another way?"
            
            # Post-process: if response contains excessive context dumps, truncate it
            if text.count("The item") > 2 or text.count("Item Name") > 0 or text.count(" • ") > 5:
                sentences = text.split(". ")
                if len(sentences) > 2:
                    text = ". ".join(sentences[:2]) + "."
            
            print("\n" + text + "\n")
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
