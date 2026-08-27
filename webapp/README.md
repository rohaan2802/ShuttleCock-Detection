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

# Shuttlecock live detector (webapp)

Point your webcam at a shuttlecock. One screen draws the box and shows **live coordinates**.

- No database  
- Nothing saved to Excel/CSV from this UI  
- **Access webcam** → live detect (no Record click)  
- **Stop** → clear and return to idle  

## Full documentation

**Read the root README for everything** (all files, ports, install, deploy, troubleshooting):

→ [`../README.md`](../README.md)  
→ Hosting notes: [`../DEPLOY-HF.md`](../DEPLOY-HF.md)

## Run locally (short)

From **repo root**:

```bash
python -m pip install -r webapp/requirements.txt
python webapp/app.py
```

Or double-click `run.bat` in the repo root.

- Default URL: `http://127.0.0.1:7860`  
- Port auto-freed / fallback if busy  
- Browser opens automatically  
- Public temp link: `python webapp/app.py --share` or `run-share.bat`

## Model

`models/shuttle_yolov8n_best.pt`  
(fallback: `../ShuttleBotRealtime/models/shuttle_yolov8n_best.pt`)
