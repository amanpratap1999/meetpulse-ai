# System Architecture — Meeting Notes → Action Items API

## 1. System Overview

The **Meeting Notes → Action Items API** is a production-grade FastAPI microservice designed to transform unstructured, multi-speaker conversational transcripts into structured, queryable action items and provide semantic vector search across all historical action items.

### Core Problem Solved:
In typical engineering and business workflows, action items discussed during meetings are lost, forgotten, or buried across disparate documents. This service automates the end-to-end extraction pipeline:
1. Validates and ingests raw transcripts.
2. Extracts structured deliverables, designated owners, deadlines, and confidence scores using LLMs.
3. Indexes action item deliverables into a vector similarity store.
4. Exposes an instant semantic search endpoint (`GET /action-items/search?q=...`) to query past commitments.

---

## 2. Architecture & Data Flow

```
+-------------------------------------------------------------------------------+
|                                Client Request                                 |
|               (POST /meetings  or  GET /action-items/search)                  |
+---------------------------------------+---------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
|                            FastAPI Gateway Layer                              |
|   - Pydantic Input Validation (schemas.py)                                    |
|   - Structured Request Logging & Error Sanitization (main.py)                 |
+-------------------+---------------------------------------+-------------------+
                    |                                       |
    [Ingestion Flow] v                       [Search Flow]  v
+---------------------------------------+  +------------------------------------+
|         LLM Client Layer              |  |         Vector Search Engine       |
|  - Dual Mode (Live Groq/OpenAI | Mock)|  |  - Query Vectorization             |
|  - JSON Schema Strict Extraction      |  |  - Cosine Similarity across Embeds |
+-------------------+-------------------+  +-----------------+------------------+
                    |                                        |
                    +-------------------+--------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
|                       Relational Storage (SQLAlchemy ORM)                     |
|                                                                               |
|   +-------------------+    1:N    +--------------------+   1:1  +-------------+
|   |     meetings      | --------> |    action_items    | -----> | embeddings  |
|   +-------------------+           +--------------------+        +-------------+
|   | id (PK)           |           | id (PK)            |        | id (PK)     |
|   | title             |           | meeting_id (FK)    |        | action_item |
|   | transcript        |           | task               |        | vector_json |
|   | created_at        |           | owner              |        | text_chunk  |
|   +-------------------+           | due_date           |        +-------------+
|                                   | status, confidence |                      |
|                                   +--------------------+                      |
+-------------------------------------------------------------------------------+
```

---

## 3. Database Schema

The service relies on a normalized 3-table relational design:

1. **`meetings`**:
   - Stores raw meeting records and metadata.
   - Cascades deletions to associated action items.
2. **`action_items`**:
   - Stores discrete deliverables identified from the transcript.
   - Contains explicit attributes: `task` (description), `owner` (responsible person), `due_date` (deadline), `status` (`pending`, `completed`), and `confidence` score.
3. **`embeddings`**:
   - Stores dense float vectors for each action item.
   - Vectors are stored as serialized JSON arrays of normalized floats, making the vector layer 100% portable across SQLite and PostgreSQL.

---

## 4. Extraction & Retrieval Design

### LLM Structured Extraction
- Prompts use explicit system personas demanding valid JSON matching the `TranscriptExtractionResult` Pydantic schema.
- Zero free-form markdown or chatter is accepted; any parsing anomalies trigger graceful fallbacks.
- **Dual-Mode Engine:** An integrated deterministic rule-based extractor operates when `MOCK_LLM=true` (or when no API key is set), allowing full offline test execution and automated CI. Setting `MOCK_LLM=false` with a valid `LLM_API_KEY` seamlessly delegates to Groq's high-speed inference engine (`llama-3.3-70b-versatile`) or OpenAI endpoints.

### Semantic Vector Lookup (RAG)
- Incoming search queries (e.g. `budget slides`) are converted to dense vector embeddings.
- Stored vectors are scored using cosine similarity:
  $$\text{sim}(\mathbf{u}, \mathbf{v}) = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\| \|\mathbf{v}\|}$$
- Results are ranked descending by relevance score, paired with meeting metadata, and returned via `GET /action-items/search`.

---

## 5. Architectural Tradeoffs & Decisions

| Decision | Alternative Considered | Rationale & Tradeoff |
|---|---|---|
| **SQLite + Local Cosine Search** | PostgreSQL + pgvector in Docker | Maximizes local Windows developer velocity with zero container or daemon dependencies. Clean SQLAlchemy abstraction allows 1-line `.env` switch to PostgreSQL for cloud deployment. |
| **JSON Array Embedding Storage** | Dedicated Vector DB (Pinecone, Qdrant) | Eliminates external cloud network dependencies and cost for foundational service; keeps relational consistency atomic in a single database transaction. |
| **Dual-Mode LLM Client** | Live-Only API calls | Enables full continuous integration (CI) and local testing without incurring API costs or blocking development when keys are not yet configured. |

---

## 6. Security, Resilience & Rollback

- **Secret Isolation:** API keys and credentials reside exclusively in `.env` (ignored in `.gitignore`).
- **Error Sanitization:** A custom global exception handler catches internal errors and returns sanitized JSON responses (`{"error": "Internal server error"}`), preventing raw stack traces from exposing system internals.
- **Rollback Path:** Database migrations and SQLite file backups (`meetings.db`) allow instantaneous point-in-time state recovery.
