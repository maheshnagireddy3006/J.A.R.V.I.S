@echo off
title JARVIS Test Suite Runner
cd /d "%~dp0"
echo ============================================================
echo  Executing JARVIS Automated Unit & Integration Tests
echo ============================================================
echo.
call .\jarvis_env\Scripts\activate.bat
pytest -v
pause
