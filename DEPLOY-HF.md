# Deploy live demo — Hugging Face Spaces

## Important: do NOT use Gradio Lite / Static

On **Create new Space** you may see templates under **Static** (including **Gradio Lite**).

| Choice | Use for this project? |
|--------|------------------------|
| **Gradio** (Space SDK = Gradio, Python) | **YES** |
| **Static → Gradio Lite** | **NO** — runs in browser only; YOLO/PyTorch will not work |
| **Static → blank HTML** | **NO** |

You need the real **Gradio** SDK (server Python), not Gradio Lite.

---

## Account

1. Open **https://huggingface.co/join** and sign up  
2. Confirm your email  

---

## Create the Space (correct clicks)

1. Open **https://huggingface.co/new-space**
2. **Space name:** `shuttlecock-detection`
3. **Space SDK:** click **Gradio** (not Static)
4. If it asks for hardware:
   - Prefer **ZeroGPU** if shown (often the free Gradio option), or **CPU basic**
5. **Public** → **Create Space**

If Gradio is locked / asks for PRO:

- Free accounts sometimes only get **Static** templates — Gradio Lite will **not** run this app  
- Options then:
  1. Use **local** `run.bat` (best reliability), or  
  2. Hugging Face **PRO** for Gradio CPU, or  
  3. Create Gradio Space with **ZeroGPU** if your account still allows it (up to 2 on free, when eligible)

---

## Upload files

Space → **Files** → **Upload files**  
Upload from your PC folder:

`C:\Users\CodeTech\Desktop\ShuttleCock-Detection\webapp\`

Required:

- `app.py`
- `requirements.txt`
- `README.md`
- `models/shuttle_yolov8n_best.pt` (keep the `models` folder name)

First build often takes **5–15 minutes**.

Live URL example:

`https://huggingface.co/spaces/YOUR_USERNAME/shuttlecock-detection`

---

## Quick check after deploy

1. Status = **Running**  
2. Open Space → **Allow** camera  
3. Hold a shuttlecock in view  
4. Hold a shuttlecock in view  
5. If nothing is detected, **No detection of shuttle** shows for **5 seconds**, then clears — **camera stays on**

---

## Local (always works, free)

Double-click:

`C:\Users\CodeTech\Desktop\ShuttleCock-Detection\run.bat`
