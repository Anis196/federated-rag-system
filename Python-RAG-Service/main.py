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

# Import the core logic from rag_edi.py by duplicating the ingestion/RAG logic here (no import)
from llama_index.core import Document as LIDocument
from llama_index.core import Settings, StorageContext
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.chroma import ChromaVectorStore
from pydantic import BaseModel


# --- Settings ---
ROOT_DIR = Path(__file__).parent
PERSIST_DIR = ROOT_DIR / "rag_storage"
DATA_DIR = ROOT_DIR  # You may change to another folder for real-time ingestion
DATA_EXTS = {".csv", ".xls", ".xlsx", ".jsonl"}
DATA_POLL_INTERVAL = 5  # seconds


# --- Data Extraction (robust CSV/XLS/text loader) ---
def extract_text_from_file(p):
    import pandas as pd
    ext = p.suffix.lower()
    tried = []
    xls = None
    if ext == ".jsonl":
        return extract_text_from_jsonl(p)
    # Excel first
    if ext == ".xls":
        try:
            xls = pd.ExcelFile(p, engine="xlrd")
            tried.append("xlrd")
        except Exception:
            xls = None
    if xls is None and ext in {".xls", ".xlsx"}:
        try:
            xls = pd.ExcelFile(p, engine="openpyxl")
            tried.append("openpyxl")
        except Exception:
            xls = None
            tried.append("openpyxl_fail")
    if xls is not None:
        parts = []
        for sheet in xls.sheet_names:
            try:
                df = pd.read_excel(p, sheet_name=sheet, dtype=str, engine=xls.engine)
                parts.append(f"=== Sheet: {sheet} ===\n{df.to_string(index=False)}")
            except Exception as e:
                parts.append(f"[Error reading sheet {sheet}: {e}]")
        return "\n\n".join(parts)
    # Try as CSV
    try:
        if ext == ".csv":
            df = pd.read_csv(p, dtype=str, low_memory=False)
            return f"[Read as CSV]\n{df.to_string(index=False)}"
    except Exception:
        pass
    # Try as plain text
    try:
        with open(p, encoding="utf-8", errors="ignore") as f:
            txt = f.read()
        return f"[Read as text]\n{txt}"
    except Exception:
        return ""


def extract_text_from_jsonl(path: Path) -> str:
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


# --- Summary Placeholder (fixes the NameError) ---
def build_summary_documents():
    """
    Placeholder for future summarization logic.
    Right now, it returns an empty list to keep indexing stable.
    """
    return []


# --- Document Loader ---
def collect_documents():
    docs = []
    for fn in os.listdir(DATA_DIR):
        p = DATA_DIR / fn
        if p.suffix.lower() in DATA_EXTS:
            text = extract_text_from_file(p)
            if text and text.strip():
                # Do not include file path metadata to avoid leaking sources into model context
                docs.append(LIDocument(text=text))
    docs.extend(build_summary_documents())
    return docs


# --- Change Monitoring (Ingestion) ---
def get_files_snapshot():
    return {(f.name, f.stat().st_mtime) for f in DATA_DIR.iterdir() if f.suffix.lower() in DATA_EXTS}


class IndexManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._last_snapshot = None
        self._index = None
        self._start_indexing()
        self._start_monitor()

    def _start_indexing(self):
        with self._lock:
            self._build_index()

    def _build_index(self):
        Settings.llm = Ollama(
            model="tinyllama",
            request_timeout=120.0,
            temperature=0.1,
            system_prompt=(
                "You are a friendly and intelligent restaurant assistant. "
                "Respond in a conversational, warm, and helpful tone. "
                "CRITICAL RULES: "
                "1. Never show raw data, CSV content, metadata, file paths, or debug text. "
                "2. Summarize extracted data in natural language with bullet points only when necessary. "
                "3. Keep responses concise and readable (2-3 sentences ideally). "
                "4. Structure responses as: Greeting → Helpful answer → Personalized suggestion → Friendly closing. "
                "5. Always prioritize clarity and relevance over data exposure. "
                "6. Be warm and conversational, never robotic or overly formal."
            ),
        )
        Settings.embed_model = OllamaEmbedding(model_name="nomic-embed-text")
        Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=64)
        # Always rebuild for simplicity (real world might optimize more)
        shutil.rmtree(PERSIST_DIR, ignore_errors=True)
        docs = collect_documents()
        chroma_client = chromadb.PersistentClient(path=str(PERSIST_DIR / "chroma"))
        chroma_collection = chroma_client.get_or_create_collection("edi_rag")
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        from llama_index.core import VectorStoreIndex
        index = VectorStoreIndex.from_documents(docs, storage_context=storage_context, show_progress=True)
        index.storage_context.persist(persist_dir=str(PERSIST_DIR))
        self._index = index
        self._last_snapshot = get_files_snapshot()

    def _start_monitor(self):
        t = threading.Thread(target=self._monitor_files, daemon=True)
        t.start()

    def _monitor_files(self):
        while True:
            time.sleep(DATA_POLL_INTERVAL)
            snap = get_files_snapshot()
            if snap != self._last_snapshot:
                print("[Live ingestion] Data files changed; rebuilding index...")
                self._start_indexing()

    def query(self, q: str) -> str:
        from llama_index.core.prompts import PromptTemplate
        from ollama._types import ResponseError
        import re
        try:
            q = q.strip()
            
            # ---- Step 1: Detect simple greetings and casual messages
            greetings = {"hi", "hii", "hey", "hello", "hello there", "hi there", "hey there", "howdy", "good morning", "good afternoon", "good evening"}
            q_lower_clean = q.lower().replace("!", "").replace("?", "")
            if q_lower_clean in greetings or (len(q) < 5 and q_lower_clean in greetings):
                return "Hello! Welcome User. How can I help you today? Feel free to ask about our menu items, recommendations, or anything else!"

            # ---- Step 2: Check if query is too short for meaningful retrieval
            if len(q) < 3:
                return "Could you please ask me something more specific?"
            
            # ---- Step 3: Classify query type (order/menu/forecast vs general discussion)
            order_keywords = {"order", "menu", "item", "dish", "food", "curry", "biryani", "naan", "papadum", 
                             "forecast", "demand", "sale", "popular", "best-seller", "price", "cost", 
                             "week", "predict", "trend", "top items", "availability", "served"}
            q_lower = q.lower()
            is_order_related = any(keyword in q_lower for keyword in order_keywords)
            
            # ---- Step 4: Retrieve only embeddings first (no generation yet)
            retriever = self._index.as_retriever(similarity_top_k=1)
            retrieved_nodes = retriever.retrieve(q)

            # ---- Step 5: Detect if the query matches memory meaningfully
            no_context = (
                not retrieved_nodes or
                all(float(node.score or 0) < 0.15 for node in retrieved_nodes)
            )

            if no_context:
                # If order/menu related but no data found, say so explicitly
                if is_order_related:
                    return f"I don't have information about that in our system. Our menu and order data might not include what you're looking for, or it could be temporarily unavailable. Please ask our staff directly for more details!"
                
                # Otherwise, respond as a normal chatbot for general discussions
                fallback_llm = Settings.llm
                response = fallback_llm.complete(
                    f"""
You are a friendly restaurant assistant. Respond conversationally and warmly.

Structure your response as:
1. Warm greeting
2. Natural, helpful answer to their question
3. A friendly closing suggestion

The guest said: "{q}"

Respond naturally without mentioning data, files, or systems. Keep it brief and warm.
""".strip()
                )
                return response.text.strip()

            # ---- Step 6: Standard RAG pipeline with strict templates
            qa_prompt = PromptTemplate(
                "You are a friendly restaurant assistant. Follow this structure:\n"
                "1. Start with a warm greeting\n"
                "2. Provide a concise, helpful answer using key details from context\n"
                "3. Add a personalized suggestion or recommendation\n"
                "4. End with a friendly closing\n\n"
                "CRITICAL: Never list raw context, metadata, file paths, or database dumps.\n"
                "Summarize data naturally in conversational language.\n"
                "Use bullet points only if essential. Keep response brief and readable.\n\n"
                "Guest question: {query_str}\n\nContext data: {context_str}\n\nYour response:"
            )

            refine_prompt = PromptTemplate(
                "Refine this response to be more conversational and structured:\n"
                "- Start with a warm greeting if missing\n"
                "- Summarize key insights naturally (no raw data)\n"
                "- Add a personalized suggestion\n"
                "- End with a friendly closing\n"
                "- Keep it brief and warm\n\n"
                "Current response: {existing_answer}\n\nAdditional context: {context_str}\n\nRefined response:"
            )

            qe = self._index.as_query_engine(
                similarity_top_k=1,
                response_mode="compact",
                text_qa_template=qa_prompt,
                refine_template=refine_prompt,
            )

            resp = qe.query(q)
            text = getattr(resp, "response", None) or str(resp)
            
            # Post-process: CRITICAL - detect and clean any raw data leakage
            # Check for CSV/raw data markers (numbers, dates, category patterns)
            raw_csv_pattern = r"\d{4}-\d{2}-\d{2}|Main\s*-\s*(?:Curry|Biryani)|^\d+\.\d+"
            has_raw_data = len(re.findall(raw_csv_pattern, text)) > 2
            
            if has_raw_data:
                # Aggressive cleanup: extract meaningful content only
                text = self._extract_meaningful_response(text, q)
            elif text.count("Item Name") > 0 or text.count("Title:") > 0:
                # Extract and reformat menu items if present
                text = self._clean_and_format_response(text, q)
            elif text.count("This dish") > 3 or text.count("which means") > 2 or text.count("typically consists") > 2:
                # Detect overly verbose/repetitive descriptions
                text = self._compress_verbose_response(text, q)
            elif text.count("The item") > 2 or text.count(" • ") > 5:
                # Truncate responses that look like data dumps
                sentences = text.split(". ")
                if len(sentences) > 2:
                    text = ". ".join(sentences[:2]) + "."
            
            return text

        except ResponseError as ollama_err:
            return (
                "[Ollama Error] The model stopped or ran out of resources. "
                "Try restarting Ollama or freeing memory.\n"
                f"Details: {ollama_err}"
            )

        except Exception as e:
            return f"[Unexpected Error During Query] {e}"
    
    def _clean_and_format_response(self, text: str, query: str) -> str:
        """Clean raw context dumps and format responses following structured guidelines."""
        import re
        
        # Check if this is a top items query
        if "top" in query.lower() and ("item" in query.lower() or "10" in query or "five" in query or "best" in query or "popular" in query):
            # Extract item names and quantities
            lines = text.split("\n")
            items = []
            
            for line in lines:
                # Match patterns like "Item Name, Quantity: Name, Number"
                match = re.search(r"(?:Item Name,\s*)?Quantity:\s*([^,]+),\s*(\d+)", line)
                if match:
                    item_name = match.group(1).strip()
                    quantity = match.group(2).strip()
                    items.append((item_name, quantity))
                # Also try simpler pattern with name and number
                elif "," in line and any(char.isdigit() for char in line):
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 2 and parts[-1].isdigit():
                        items.append((parts[0], parts[-1]))
            
            if items:
                # Format as structured, friendly response
                response = "Great question! Here are our most popular dishes right now:\n\n"
                for i, (name, qty) in enumerate(items[:10], 1):
                    # Clean up the name
                    name = re.sub(r"^(Plain|Prwan|Plains)\s*", "", name).strip()
                    response += f"• {name}\n"
                
                response += f"\nThese items have been customer favorites with strong demand. "
                response += "Would you like a recommendation based on spice level or cuisine type?"
                return response.strip()
        
        # Check for recommendation queries
        if any(word in query.lower() for word in ["recommend", "suggest", "best", "popular", "trending"]):
            # Format as friendly recommendation response
            response = "Perfect! Based on what's trending right now:\n\n"
            
            # Extract key dishes from the text if present
            dishes = re.findall(r"\b([A-Z][a-z]+ (?:Curry|Biryani|Naan|Bhajee|Chaat|Masala|Tikka)[a-zA-Z]*)\b", text)
            
            if dishes:
                unique_dishes = list(dict.fromkeys(dishes))[:5]  # Get unique, limit to 5
                for dish in unique_dishes:
                    response += f"• {dish} is getting great feedback\n"
                response += f"\nThese are currently among our guests' favorites. "
            else:
                response = "Based on recent trends, our guests are loving our curry and biryani selections. "
            
            response += "Which cuisine or spice level appeals to you?"
            return response.strip()
        
        # For other queries, clean up raw metadata and structure nicely
        text = re.sub(r"Item Name,\s*Quantity:\s*", "", text)
        text = re.sub(r"Title:\s*\w+\s*", "", text)
        text = re.sub(r"\[Read as CSV\]", "", text)
        text = re.sub(r"===.*?===", "", text)
        text = re.sub(r"\n\n+", "\n", text)  # Remove excessive newlines
        
        # Limit to first few sentences and ensure friendly tone
        sentences = text.split(". ")
        if len(sentences) > 3:
            text = ". ".join(sentences[:3]) + "."
        
        # Add friendly prefix if missing
        if not text.lower().startswith(("great", "perfect", "sure", "absolutely", "yes", "hi", "hello")):
            text = f"Based on our data: {text}"
        
        return text.strip()

    def _extract_meaningful_response(self, text: str, query: str) -> str:
        """Extract meaningful content from responses containing raw CSV data."""
        import re
        
        # Remove raw CSV patterns (dates, numbers-only lines, metadata)
        lines = text.split("\n")
        cleaned_lines = []
        
        for line in lines:
            # Skip pure CSV lines (dates, pure numbers, category tags)
            if re.match(r"^\s*\d{4}-\d{2}-\d{2}\s*$", line):
                continue  # Skip date lines
            if re.match(r"^\s*[\d.]+\s*$", line):
                continue  # Skip number-only lines
            if re.match(r"^\s*(Main|Drink|Other)\s*-.*$", line):
                continue  # Skip category lines
            if re.match(r"^\s*\d+\s*$", line):
                continue  # Skip ID lines
            
            # Keep meaningful lines (dish names, descriptions, questions)
            if line.strip() and len(line.strip()) > 3:
                # Clean up formatting
                line = re.sub(r"^\d+\.\s*", "", line)  # Remove numbering
                line = re.sub(r"\s{2,}", " ", line)    # Normalize spaces
                cleaned_lines.append(line.strip())
        
        if not cleaned_lines:
            # Fallback: generate generic response for allergy/special needs queries
            if "allerg" in query.lower() or "spic" in query.lower():
                return "I'd recommend dishes like Cauliflower Bhajee, Chapati, or mild curries on request. Always tell our staff about your allergy so we can prepare it safely!"
            elif "suggest" in query.lower() or "recommend" in query.lower():
                return "Let me know what cuisine you prefer — I can suggest mild, vegetarian, or other options!"
            else:
                return "Sorry, I'm having trouble retrieving that info. Please ask our staff for details!"
        
        # Reconstruct meaningful response
        text = " ".join(cleaned_lines)
        
        # If still looks like raw data, truncate aggressively
        if len(text) > 300 or text.count(".") > 5:
            sentences = text.split(". ")
            text = ". ".join(sentences[:2]) + "."
        
        # Add friendly wrapper if not already conversational
        if not any(text.lower().startswith(w) for w in ["i'd", "great", "perfect", "sure", "here", "based"]):
            if "allerg" in query.lower() or "spic" in query.lower():
                text = f"For your allergy concern: {text}"
            elif "recommend" in query.lower():
                text = f"Here are some great options: {text}"
        
        return text.strip()
    

        """Compress overly verbose responses into concise, natural format."""
        import re
        
        # Extract dish names from the verbose text
        # Look for numbered lists like "1. Aloo Chaat - " or dish descriptions
        dish_pattern = r"^\d+\.\s+([A-Za-z\s]+?)(?:\s*-\s*|\s*:)"
        dishes = []
        
        for line in text.split("\n"):
            match = re.match(dish_pattern, line)
            if match:
                dish_name = match.group(1).strip()
                # Clean up prefixes like "This dish is"
                if dish_name and len(dish_name) > 0:
                    dishes.append(dish_name)
        
        if not dishes:
            # If pattern matching fails, try to extract from "X. Name - description" format
            lines = text.split("\n")
            for line in lines:
                if re.match(r"^\d+\.", line):
                    # Extract name before first dash or colon
                    parts = re.split(r"\s*[-:]", line, 1)
                    if len(parts) > 0:
                        name = re.sub(r"^\d+\.\s*", "", parts[0]).strip()
                        if name and len(name) > 2:
                            dishes.append(name)
        
        # Limit to top recommendations (5-7 dishes)
        dishes = list(dict.fromkeys(dishes))[:7]  # Remove duplicates and limit
        
        if dishes:
            # Create a concise, friendly response
            response = "Great! Here are some fantastic options trending this week:\n\n"
            for i, dish in enumerate(dishes, 1):
                response += f"• {dish}\n"
            
            response += "\nThese dishes are getting wonderful feedback from our guests! "
            response += "Each brings authentic flavors and quality ingredients. "
            response += "Would you like to know more about any specific dish or need dietary recommendations?"
            
            return response.strip()
        
        # Fallback: Clean up and shorten the original text
        # Remove repeated phrases
        text = re.sub(r"This dish is also known as.*?means\s*\"[^\"]*\"\.", "", text)
        text = re.sub(r"It\'s a popular.*?with\s+", "It features ", text)
        text = re.sub(r"which typically consists of.*?and\s+", "made with ", text)
        
        # Keep only first 3 items if still too long
        lines = text.split("\n")
        if len(lines) > 5:
            text = "\n".join(lines[:5])
        
        # Ensure conversational tone
        if not text.lower().startswith(("great", "perfect", "sure", "here")):
            text = f"Here are some great options: {text}"
        
        return text.strip()
    
app = FastAPI()

# Allow local frontend dev server and Spring Boot origin during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

index_manager = IndexManager()


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    answer: str
    query: str
    timestamp: str  # ISO format timestamp


@app.post("/rag_query", response_model=QueryResponse)
async def rag_query(request: Request):
    """Accept JSON or form-encoded requests.

    - JSON: {"query": "..."}
    - form: message=... OR query=...
    """
    try:
        content_type = request.headers.get("content-type", "")
        query_text = None
        if "application/json" in content_type:
            body = await request.json()
            # accept either 'query' or 'message'
            query_text = body.get("query") or body.get("message")
        elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
            form = await request.form()
            query_text = form.get("query") or form.get("message")
        else:
            # Try parsing JSON as fallback
            try:
                body = await request.json()
                query_text = body.get("query") or body.get("message")
            except Exception:
                query_text = None

        if not query_text:
            return JSONResponse(status_code=400, content={"detail": "Missing 'query' or 'message' field"})

        answer = index_manager.query(query_text)
        from datetime import datetime
        timestamp = datetime.utcnow().isoformat() + "Z"
        return QueryResponse(answer=answer, query=query_text, timestamp=timestamp)
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    print("[INFO] Starting RAG service on http://127.0.0.1:11435")
    uvicorn.run(app, host="127.0.0.1", port=11435)