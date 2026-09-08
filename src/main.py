import json
import logging
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.database import engine, get_db, Base
from src.models import Meeting, ActionItem, Embedding
from src.schemas import (
    MeetingCreate,
    MeetingResponse,
    ActionItemResponse,
    SearchResponse,
    SearchItemResult,
    HealthResponse,
)
from src.llm_client import extract_action_items
from src.vector_store import get_embedding, search_action_items
from src.config import settings

# Structured logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("meeting_agent")

# Initialize database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Meeting Notes -> Action Items API",
    description="Production-grade FastAPI service extracting structured action items and semantic search over meeting transcripts.",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler (No raw stack traces to client)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error. Please consult logs."}
    )

@app.get("/health", response_model=HealthResponse, tags=["System"])
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint verifying DB connection and LLM configuration.
    """
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = f"unhealthy: {str(e)}"
        
    return HealthResponse(
        status="ok" if db_status == "connected" else "degraded",
        database=db_status,
        llm_provider=settings.LLM_PROVIDER,
        llm_mode="mock" if settings.MOCK_LLM else "live",
        version="0.1.0"
    )

@app.post("/meetings", response_model=MeetingResponse, status_code=201, tags=["Meetings"])
async def create_meeting(payload: MeetingCreate, db: Session = Depends(get_db)):
    """
    Ingest meeting transcript, extract structured action items with LLM, and index embeddings.
    """
    logger.info(f"Processing transcript for meeting: '{payload.title}'")
    
    # 1. Create Meeting record
    meeting = Meeting(
        title=payload.title,
        transcript=payload.transcript
    )
    db.add(meeting)
    db.flush()  # populate meeting.id

    # 2. Extract structured action items via LLM (or mock)
    extraction_result = await extract_action_items(payload.transcript)
    logger.info(f"Extracted {len(extraction_result.action_items)} action items")

    # 3. Save action items and generate embeddings
    created_items: List[ActionItem] = []
    for item_data in extraction_result.action_items:
        action_item = ActionItem(
            meeting_id=meeting.id,
            task=item_data.task,
            owner=item_data.owner,
            due_date=item_data.due_date,
            status="pending",
            confidence=item_data.confidence
        )
        db.add(action_item)
        db.flush()  # populate action_item.id

        # Generate vector embedding for semantic search
        vector = get_embedding(item_data.task)
        embedding_record = Embedding(
            action_item_id=action_item.id,
            text_chunk=item_data.task,
            vector_json=json.dumps(vector)
        )
        db.add(embedding_record)
        created_items.append(action_item)

    db.commit()
    db.refresh(meeting)

    return meeting

@app.get("/meetings/{meeting_id}", response_model=MeetingResponse, tags=["Meetings"])
def get_meeting(meeting_id: int, db: Session = Depends(get_db)):
    """
    Retrieve meeting transcript and extracted action items by meeting ID.
    """
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail=f"Meeting with ID {meeting_id} not found")
    return meeting

@app.get("/action-items/search", response_model=SearchResponse, tags=["Search"])
def search_action_items_endpoint(
    q: str = Query(..., min_length=1, description="Semantic search query across action items"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    RAG lookup: Semantic vector search across action items from past meetings.
    """
    matches = search_action_items(db, query=q, top_k=limit)
    
    results: List[SearchItemResult] = []
    for item, score in matches:
        results.append(
            SearchItemResult(
                id=item.id,
                meeting_id=item.meeting_id,
                meeting_title=item.meeting.title if item.meeting else "Unknown",
                task=item.task,
                owner=item.owner,
                due_date=item.due_date,
                status=item.status,
                relevance_score=round(score, 4)
            )
        )
        
    return SearchResponse(
        query=q,
        total_results=len(results),
        results=results
    )
