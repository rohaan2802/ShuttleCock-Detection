---
title: Shuttlecock Detection
emoji: 🏸
colorFrom: teal
colorTo: slate
sdk: gradio
sdk_version: 4.44.1
app_file: app.py
pinned: false
license: mit
short_description: Live webcam shuttlecock detection with coordinates
---

# Shuttlecock live detector

Point your webcam at a shuttlecock. The page draws a box and shows coordinates only.

No database. Nothing is saved.

## Run locally

**Windows:** double-click `run.bat` in the repo root (or `webapp\run.bat`).  
The browser opens by itself. If port `7860` is busy, it is freed first.

```bash
python app.py
```

From repo root: `python webapp/app.py`

## Deploy (Hugging Face Spaces)

See steps in the repo root `DEPLOY-HF.md`.
