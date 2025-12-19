# Python RAG Service - Data Ingestion Guide

## Supported File Formats

| Format | Extension | Parser | Notes |
|--------|-----------|--------|-------|
| CSV | `.csv` | pandas.read_csv | Recommended for tabular data |
| Excel | `.xls` | pandas.read_excel | Legacy Excel format |
| Excel | `.xlsx` | pandas.read_excel | Modern Excel format |
| JSONL | `.jsonl` | Line-by-line JSON | One JSON object per line |
| Plain Text | `.txt` | Raw text reading | Simple text files |

## How Data Ingestion Works

### 1. **Automatic Discovery**
The service automatically scans the `Python-RAG-Service/` directory every 5 seconds (configurable) for new or updated files.

### 2. **File Processing**
When a file is detected:
1. Extracts text content based on file type
2. Splits content into chunks
3. Generates embeddings using `nomic-embed-text` model
4. Stores vectors in ChromaDB
5. Indexes in LLamaIndex

### 3. **Persistent Storage**
- Embeddings stored in `rag_storage/` directory
- Survives service restarts
- Re-indexed on updates

## Adding Data Files

### Step 1: Prepare Your Data
Choose your format (CSV, XLSX, JSONL, or TXT)

### Step 2: Place Files
Copy files to the `Python-RAG-Service/` root directory:
```
Python-RAG-Service/
├── main.py
├── requirements.txt
├── your_data.csv          ← Add here
├── your_data.xlsx         ← Add here
├── your_data.jsonl        ← Add here
└── rag_storage/
```

### Step 3: Wait for Indexing
Service automatically detects and indexes files within 5 seconds.

Check logs for confirmation:
```
[INFO] Indexing: your_data.csv
[INFO] Successfully indexed: your_data.csv
```

### Step 4: Query Your Data
Use the `/rag_query` endpoint to search and retrieve information from your data.

## CSV Format Example

**file.csv:**
```csv
ID,Name,Description
1,Item A,High-quality product
2,Item B,Budget-friendly option
3,Item C,Premium choice
```

## JSONL Format Example

**file.jsonl:**
```json
{"id": 1, "name": "Item A", "description": "High-quality product"}
{"id": 2, "name": "Item B", "description": "Budget-friendly option"}
{"id": 3, "name": "Item C", "description": "Premium choice"}
```

## Excel Format Example

**file.xlsx:**
```
| ID | Name   | Description              |
|----|--------|--------------------------|
| 1  | Item A | High-quality product     |
| 2  | Item B | Budget-friendly option   |
| 3  | Item C | Premium choice           |
```

## Plain Text Format Example

**file.txt:**
```
Item A: High-quality product with excellent durability
Item B: Budget-friendly option for cost-conscious customers
Item C: Premium choice featuring advanced features
```

## Configuration

Edit `main.py` to customize ingestion behavior:

```python
# Supported file extensions
DATA_EXTS = {".csv", ".xls", ".xlsx", ".jsonl", ".txt"}

# Poll interval in seconds
DATA_POLL_INTERVAL = 5

# Data directory
DATA_DIR = ROOT_DIR  # Scans all files in service root directory
```

## Troubleshooting

### Files Not Being Indexed
- **Check:** Are files in the correct directory?
- **Check:** Is file extension supported?
- **Check:** Is Ollama service running?
- **Solution:** Restart the service and check logs

### Embedding Generation Failed
- **Error:** "Ollama service unavailable"
- **Solution:** Ensure Ollama is running: `ollama serve`

### Query Returns No Results
- **Cause:** Files not yet indexed
- **Solution:** Wait 2-5 minutes for initial indexing on first run
- **Check:** Verify files exist and are readable

## Best Practices

1. **Use consistent formatting** - Standardize column names across files
2. **Include metadata** - Add timestamps, categories, or tags to rows
3. **Keep files organized** - Use descriptive file names
4. **Monitor indexing** - Check logs for successful ingestion
5. **Backup data** - Keep original files backed up separately
