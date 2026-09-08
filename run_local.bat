@echo off
echo ==========================================
echo  Starting Meeting Notes -^> Action Items API
echo ==========================================

if not exist venv (
    echo Creating Python virtual environment...
    python -m venv venv
    call .\venv\Scripts\pip install -r requirements.txt
)

if not exist .env (
    echo Creating .env from .env.example...
    copy .env.example .env
)

echo Starting FastAPI server at http://127.0.0.1:8000
echo Swagger UI: http://127.0.0.1:8000/docs
echo Health Check: http://127.0.0.1:8000/health

call .\venv\Scripts\uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
pause
