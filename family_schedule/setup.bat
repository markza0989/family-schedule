@echo off
REM One-time setup: creates a virtual environment and installs dependencies.
cd /d "%~dp0"

echo Creating virtual environment...
python -m venv .venv
if errorlevel 1 (
  echo.
  echo ERROR: Python was not found. Install it from https://www.python.org/downloads/
  echo Make sure to tick "Add python.exe to PATH" during installation.
  pause
  exit /b 1
)

echo Installing dependencies...
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\pip install -r requirements.txt

echo.
echo Setup complete. You can now run start-server.bat
pause
