@echo off
title Shuttlecock Detection
cd /d "%~dp0"

echo Starting Shuttlecock Detection...
echo Browser will open automatically.
echo.

python "%~dp0app.py"
if errorlevel 1 (
  echo.
  echo Failed to start. Try:  python -m pip install -r requirements.txt
  pause
)
