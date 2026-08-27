# Shuttlecock live web detector

Point your webcam at a shuttlecock. The page draws a box and shows coordinates only.

No database. Nothing is saved to disk or Excel.

## Run locally

From the **repo root** (`ShuttleCock-Detection`):

```bash
pip install -r webapp/requirements.txt
python webapp/app.py
```

Open **http://127.0.0.1:7860** and allow camera access.

Model path used:

`ShuttleBotRealtime/models/shuttle_yolov8n_best.pt`

## Notes

- Use good indoor light for best results.
- If the camera is blank, check browser permission for this site.
- CPU-only machines may run a few frames per second — that is normal.
