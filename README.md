# Meeting Notes → Action Items API (Project 0)

> **Autonomous AI/ML Portfolio — Foundation Service**  
> Ingest meeting transcripts, extract structured action items via LLMs (Groq / OpenAI compatible), index embeddings, and query them with semantic vector search.

---

## Quickstart (Run Cold in 60 Seconds)

### Option A: 1-Click Windows Launch (PowerShell)
```powershell
.\run_local.ps1
```
*(Or double-click `run_local.bat`)*

### Option B: Manual Setup
1. **Create and activate a virtual environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
2. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```
3. **Run the server:**
   ```powershell
   uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
   ```

Open your browser to:
- **Interactive Swagger Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## Running Tests & Benchmark Evaluation

### 1. Run Automated Unit & Integration Tests
```powershell
.\venv\Scripts\pytest -v tests/
```

### 2. Run the 16-Transcript Evaluation Benchmark
```powershell
.\venv\Scripts\python eval/run_eval.py
```
This evaluates the extraction accuracy against ground-truth items and writes a detailed metric report to `docs/eval-results.md`.

---

## API Endpoints & Examples

### 1. Health Check
```bash
curl -X GET http://127.0.0.1:8000/health
```
**Response:**
```json
{
  "status": "ok",
  "database": "connected",
  "llm_provider": "groq",
  "llm_mode": "mock",
  "version": "0.1.0"
}
```

### 2. Ingest Transcript & Extract Action Items
```bash
curl -X POST http://127.0.0.1:8000/meetings \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Weekly Engineering Sync",
    "transcript": "Alice: We need to ship the auth update. Bob: I will deploy the Redis caching cluster by Friday. Charlie: I will review the pull request by tomorrow morning."
  }'
```
**Response:**
```json
{
  "id": 1,
  "title": "Weekly Engineering Sync",
  "transcript": "...",
  "created_at": "2026-09-08T12:00:00",
  "action_items": [
    {
      "id": 1,
      "meeting_id": 1,
      "task": "deploy the Redis caching cluster",
      "owner": "Bob",
      "due_date": "by friday",
      "status": "pending",
      "confidence": 0.95
    },
    {
      "id": 2,
      "meeting_id": 1,
      "task": "review the pull request",
      "owner": "Charlie",
      "due_date": "by tomorrow morning",
      "status": "pending",
      "confidence": 0.95
    }
  ]
}
```

### 3. Semantic Vector Search (RAG Lookup)
```bash
curl -X GET "http://127.0.0.1:8000/action-items/search?q=caching+database"
```
**Response:**
```json
{
  "query": "caching database",
  "total_results": 1,
  "results": [
    {
      "id": 1,
      "meeting_id": 1,
      "meeting_title": "Weekly Engineering Sync",
      "task": "deploy the Redis caching cluster",
      "owner": "Bob",
      "due_date": "by friday",
      "status": "pending",
      "relevance_score": 0.7421
    }
  ]
}
```

---

## Connecting a Live LLM API Key

The service includes a built-in mock mode (`MOCK_LLM=true`) so everything functions offline out of the box.

To activate live extraction with **Groq** (or OpenAI):
1. Open `.env`.
2. Enter your API key:
   ```env
   MOCK_LLM=false
   LLM_PROVIDER=groq
   LLM_API_KEY=gsk_your_actual_groq_key_here
   LLM_MODEL=llama-3.3-70b-versatile
   ```
3. Restart the server. Your requests will now call Groq for live LLM extraction.

---

## Directory Structure
```
project-0-meeting-agent/
├── .env.example
├── .gitignore
├── ARCHITECTURE.md
├── BUILD_LOG.md
├── DECISIONS.md
├── Dockerfile
├── docker-compose.yml
├── README.md
├── requirements.txt
├── run_local.bat
├── run_local.ps1
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── llm_client.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   └── vector_store.py
├── tests/
│   └── test_api.py
├── eval/
│   ├── dataset.json
│   └── run_eval.py
└── docs/
    └── eval-results.md
```
