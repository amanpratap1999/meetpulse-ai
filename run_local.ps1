# Local PowerShell runner for Project 0: Meeting Agent
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " Starting Meeting Notes -> Action Items API" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Check if venv exists
if (-not (Test-Path "venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    .\venv\Scripts\python -m pip install -r requirements.txt
}

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "Copying .env.example to .env..." -ForegroundColor Yellow
    Copy-Item .env.example .env
}

Write-Host "Starting FastAPI server on http://127.0.0.1:8000 ..." -ForegroundColor Green
Write-Host "Swagger Docs: http://127.0.0.1:8000/docs" -ForegroundColor Green
Write-Host "Health check: http://127.0.0.1:8000/health" -ForegroundColor Green

.\venv\Scripts\uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
