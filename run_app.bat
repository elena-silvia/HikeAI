@echo off
title RoMountainAgent Web App
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" app_server.py
) else (
    python app_server.py
)
pause
