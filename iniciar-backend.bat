@echo off
cd /d "%~dp0backend"
set DEBUG=true
set PYTHONIOENCODING=utf-8
set APP_ENV=development
set ENABLE_DEMO_AUTH=true
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
pause

