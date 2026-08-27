# Live deploy guide — Shuttlecock Gradio detector

## Your requirement: sleep → click link → auto start again

| Option | Auto-wake on link click? | Verdict |
|--------|---------------------------|---------|
| **Render free** | **YES** (cold start ~30–90s) | **Best match** |
| Google Colab + ngrok/share | **NO** — dead session stays dead | Bad for this |
| Lightning AI Studio | Usually **NO** — studio must be running | Unreliable wake |
| Gradio `--share` / `run-share.bat` | N/A — needs your PC on | Local only |
| Hugging Face Gradio | Needs PRO / gated ZeroGPU | Not free for you |

**Recommendation: Render free Web Service.**

---

## 1) Render (recommended) — auto cold start

### What happens
1. App sleeps after ~15 minutes idle (free tier).  
2. Someone opens your URL.  
3. Render **starts the container again** automatically.  
4. First load can take **30–90 seconds** (torch/YOLO boot). Then it works.

### Setup steps
1. Push this repo to GitHub (already: `rohaan2802/ShuttleCock-Detection`).  
2. Open **https://dashboard.render.com** → Sign up (GitHub login).  
3. **New +** → **Blueprint** → connect `ShuttleCock-Detection`  
   - Or **New Web Service** → Docker → root directory `webapp`  
4. Use:
   - **Runtime:** Docker  
   - **Root Directory:** `webapp`  
   - **Dockerfile Path:** `./Dockerfile`  
5. Plan: **Free**  
6. Deploy.

Public URL looks like:

`https://shuttlecock-detection-xxxx.onrender.com`

### Files used
| File | Role |
|------|------|
| `webapp/Dockerfile` | Image build |
| `webapp/app.py` | Gradio app (`PORT` + `0.0.0.0`) |
| `webapp/requirements.txt` | Deps (CPU torch) |
| `webapp/models/shuttle_yolov8n_best.pt` | Weights |
| `render.yaml` | Optional Blueprint |

### Warning (512MB free RAM)
YOLOv8n + PyTorch is heavy. If the service **crashes / OOM**:
- Use `run-share.bat` for demos, or  
- Upgrade Render RAM, or  
- Keep-alive ping every 10 min so it sleeps less often (optional).

Optional keep-awake (external cron every 10 min):  
`https://cron-job.org` → GET your Render URL `/`

---

## 2) Google Colab + share / ngrok — NOT auto-wake

- Free GPU possible.  
- When Colab disconnects, the public link **dies**.  
- Clicking the old link does **not** restart the notebook.  
- You must open Colab and run cells again.

Use only for short demos while you watch the notebook.

---

## 3) Lightning AI Studio — longer session, not true wake-on-click

- Free CPU Studio can run Gradio and expose a URL.  
- If the Studio is **stopped**, the link usually fails until you start the Studio again.  
- Better than Colab for longer sessions; worse than Render for “click → wake”.

---

## 4) Local temporary public link (always works)

```powershell
cd C:\Users\CodeTech\Desktop\ShuttleCock-Detection
.\run-share.bat
```

PC must stay on. Link may expire (~72h).

---

## Hugging Face reminder

Gradio Spaces need PRO / eligible ZeroGPU on your account. Static / Gradio Lite cannot run this YOLO app.
