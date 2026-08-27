@echo off
title Shuttlecock Detection (public link)
cd /d "%~dp0"

echo Starting with a temporary public Gradio link...
echo Your PC must stay on while others use the link.
echo.

python "%~dp0webapp\app.py" --share
if errorlevel 1 (
  echo.
  echo Failed to start. Try:  python -m pip install -r webapp\requirements.txt
  pause
)
