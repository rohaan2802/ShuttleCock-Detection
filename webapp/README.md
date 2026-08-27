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

From this folder (`webapp/`):

```bash
pip install -r requirements.txt
python app.py
```

Or from the repo root:

```bash
pip install -r webapp/requirements.txt
python webapp/app.py
```

Open **http://127.0.0.1:7860** and allow camera access.

## Deploy (Hugging Face Spaces)

See steps in the repo root `DEPLOY-HF.md`.
