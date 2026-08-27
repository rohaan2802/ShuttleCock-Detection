# Hosting options (updated)

## Hugging Face message you see

> Gradio and Docker Spaces require a paid plan  
> Static Spaces stay free

That means:

| Option on HF | For this shuttlecock app? |
|--------------|---------------------------|
| **Gradio** / **Docker** | Needs **HF PRO** (paid) |
| **Static** / **Gradio Lite** | Free, but **cannot** run YOLO + webcam server |

So **do not** pick Static / Gradio Lite — the model will not work there.

---

## Free options that work

### 1) Local (best)

Double-click:

`run.bat`

Browser opens on your PC. Camera works here.

### 2) Temporary public link (free, PC must stay on)

Double-click:

`run-share.bat`

Or:

```bash
python webapp/app.py --share
```

Gradio prints a link like `https://xxxxx.gradio.live` — share that.  
It works only while your laptop is running the app.

### 3) Permanent online on Hugging Face

Subscribe to **Hugging Face PRO**, then create a **Gradio** Space (not Static) and upload the `webapp/` files.

---

## Upload list (only if you have Gradio Space / PRO)

From `webapp/`:

- `app.py`
- `requirements.txt`
- `README.md`
- `models/shuttle_yolov8n_best.pt`
