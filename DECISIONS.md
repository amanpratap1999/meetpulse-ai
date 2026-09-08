# Architectural Decisions Record (ADR) — Project 0

## ADR 001: Local Execution & Database Substitution (SQLite vs Docker/pgvector)
- **Context:** `AGENT_BUILD_SPEC.md` specifies PostgreSQL + pgvector via Docker Compose. The user explicitly requested running locally on Windows without Docker, and providing the API key later.
- **Decision:** Use SQLite as the default local database engine, coupled with a lightweight local vector similarity engine (cosine similarity over embedding arrays using numpy).
- **Tradeoff & Mitigation:** 
  - Allows instant, frictionless local execution on Windows without requiring Docker Desktop or local PostgreSQL service installation.
  - All database models are built using standard SQLAlchemy ORM. Setting `DATABASE_URL=postgresql://user:pass@host/db` in `.env` seamlessly enables PostgreSQL without altering application logic.
  - A valid `docker-compose.yml` and `Dockerfile` are preserved in the repository for production deployment readiness.

## ADR 002: Deterministic Mock LLM Fallback
- **Context:** The user will supply the LLM API key at the end of the build. Development, testing, and evaluation pipelines must run without blockers.
- **Decision:** Implement a dual-mode LLM client:
  - When `MOCK_LLM=true` (or when `LLM_API_KEY` is not provided), a rule-based mock extractor parses meeting transcripts into structured action items deterministically, and a deterministic hash-based/local embedding model generates vector embeddings.
  - When `MOCK_LLM=false` and `LLM_API_KEY` is provided, the client sends structured JSON extraction requests to Groq (or OpenAI-compatible) endpoints.
- **Tradeoff & Mitigation:** Ensures the full test suite and API lifecycle can be verified locally immediately, with zero code rewrites when transitioning to live LLM inference.

## ADR 003: 3-Table Relational Schema Design
- **Context:** Phase 1 requires 3 tables: `meetings`, `action_items`, `embeddings`.
- **Decision:**
  - `meetings`: id, title, transcript, created_at.
  - `action_items`: id, meeting_id (foreign key), task, owner, due_date, status, confidence.
  - `embeddings`: id, action_item_id (foreign key), text_chunk, vector (JSON-serialized float array).
- **Tradeoff:** Clean normalization and decoupled vector storage allowing independent embedding model upgrades.
