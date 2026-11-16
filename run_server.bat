@echo off
title JARVIS Microservices & RESTful API
cd /d "%~dp0"
echo ============================================================
echo  Starting JARVIS FastAPI & WebSocket Microservices Server
echo ============================================================
echo.
echo Activating local environment...
call .\jarvis_env\Scripts\activate.bat
echo Launching Uvicorn ASGI Server on http://127.0.0.1:8000...
python -m uvicorn server:app --host 127.0.0.1 --port 8000 --reload
if errorlevel 1 (
    echo.
    echo [ERROR] Server exited unexpectedly. Check details above.
    pause
)
