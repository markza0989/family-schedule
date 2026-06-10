@echo off
REM Starts the Family Schedule server. Keep this window open while hosting.
cd /d "%~dp0"
echo Starting Family Schedule server...
echo Family members can open the address shown in SETUP.md on their phones/laptops.
echo Close this window (or press Ctrl+C) to stop hosting.
echo.
.venv\Scripts\python serve.py
pause
