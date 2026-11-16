@echo off
title JARVIS Edge-First Ecosystem
cd /d "%~dp0"
echo ============================================================
echo  Starting JARVIS: Edge-First Local Graph-Agent Ecosystem
echo ============================================================
echo.
echo Activating local environment...
call .\jarvis_env\Scripts\activate.bat
echo Launching Jarvis Core HUD Interface...
python main.py
if errorlevel 1 (
    echo.
    echo [ERROR] Jarvis exited unexpectedly. Check details above.
    pause
)
