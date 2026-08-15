@echo off
echo Starting OmniAI Backend...
start cmd /k "cd backend && call venv\Scripts\activate.bat && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo Starting OmniAI Frontend...
cd frontend
"D:\Kamran Projects\flutter\bin\flutter.bat" run -d edge
pause
