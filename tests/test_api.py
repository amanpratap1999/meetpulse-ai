import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from src.database import Base, get_db
from src.main import app

# In-memory SQLite for testing using StaticPool to share connection across threads/sessions
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"
    assert "llm_mode" in data

def test_create_meeting_and_extract_action_items(client):
    transcript = """
    Alice: We need to finalize the quarterly budget report.
    Bob: I will prepare the financial slides by Friday.
    Charlie: I'll review the cloud infrastructure costs before next Tuesday.
    """
    payload = {
        "title": "Q3 Planning Session",
        "transcript": transcript
    }
    response = client.post("/meetings", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["title"] == "Q3 Planning Session"
    assert len(data["action_items"]) >= 2
    
    # Check item details
    items = data["action_items"]
    tasks_text = " ".join([item["task"] for item in items])
    assert "slides" in tasks_text.lower() or "financial" in tasks_text.lower()

def test_get_meeting_by_id(client):
    transcript = "Dave: I will deploy the staging database by tomorrow."
    post_res = client.post("/meetings", json={"title": "Staging Deployment", "transcript": transcript})
    meeting_id = post_res.json()["id"]

    get_res = client.get(f"/meetings/{meeting_id}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["id"] == meeting_id
    assert data["title"] == "Staging Deployment"
    assert len(data["action_items"]) >= 1

def test_get_meeting_not_found(client):
    response = client.get("/meetings/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_semantic_search_action_items(client):
    # Ingest two different meetings
    m1 = client.post("/meetings", json={
        "title": "Security Meeting",
        "transcript": "Eve: I will conduct penetration testing on the authentication gateway by Thursday."
    })
    m2 = client.post("/meetings", json={
        "title": "Marketing Sync",
        "transcript": "Frank: I will draft the social media launch campaign by Friday."
    })
    assert m1.status_code == 201
    assert m2.status_code == 201

    # Search for security
    search_res = client.get("/action-items/search?q=penetration testing authentication")
    assert search_res.status_code == 200
    data = search_res.json()
    assert data["total_results"] >= 1
    # Top result should be related to security
    top_result = data["results"][0]
    assert "penetration" in top_result["task"].lower() or "authentication" in top_result["task"].lower()
    assert top_result["relevance_score"] > 0.0

def test_invalid_transcript_validation(client):
    # Too short transcript
    response = client.post("/meetings", json={"title": "Short", "transcript": "hi"})
    assert response.status_code == 422
