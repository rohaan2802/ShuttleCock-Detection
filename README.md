# ShuttleCock Detection (ShuttleBot)

**YOLOv8n** shuttlecock detector for an autonomous badminton **service robot** (ShuttleBot).

This repository includes:

- Colab / notebook training pipeline
- Trained weights (`shuttle_yolov8n_best.pt`)
- Desktop real-time webcam detector with robot actions + CSV log
- Simulation script
- Robotics design / viva notes (Raspberry Pi + Arduino)
- **Live Gradio web app** — browser webcam, boxes + coordinates only (no database, no Excel/CSV storage)

**Student ID:** i222327 · **Author:** Mohammad Rohaan · [rohaan2802](https://github.com/rohaan2802)  
**GitHub repo:** https://github.com/rohaan2802/ShuttleCock-Detection

---

## Table of contents

1. [What this project does](#1-what-this-project-does)
2. [What we built / updated (changelog)](#2-what-we-built--updated-changelog)
3. [Quick start — which file should I run?](#3-quick-start--which-file-should-i-run)
4. [Requirements](#4-requirements)
5. [Repository layout (every important path)](#5-repository-layout-every-important-path)
6. [Model weights](#6-model-weights)
7. [Live web app (`webapp/`)](#7-live-web-app-webapp)
8. [Ports, browser URL, and port conflicts](#8-ports-browser-url-and-port-conflicts)
9. [Desktop real-time detector (`realtime_detect.py`)](#9-desktop-real-time-detector-realtime_detectpy)
10. [Offline prediction (Python one-liner)](#10-offline-prediction-python-one-liner)
11. [Training notebook (ML pipeline)](#11-training-notebook-ml-pipeline)
12. [Training artifacts](#12-training-artifacts)
13. [Simulation](#13-simulation)
14. [Robotics context (Pi + Arduino)](#14-robotics-context-pi--arduino)
15. [Dataset](#15-dataset)
16. [Hosting / deploy (Hugging Face and free options)](#16-hosting--deploy-hugging-face-and-free-options)
17. [Web app behaviour (UI rules)](#17-web-app-behaviour-ui-rules)
18. [Speed / performance notes](#18-speed--performance-notes)
19. [Troubleshooting](#19-troubleshooting)
20. [Viva highlights](#20-viva-highlights)
21. [Notes](#21-notes)
22. [Author](#22-author)

---

## 1) What this project does

Detect a **shuttlecock** in camera frames so a court robot can steer and pick it up.

| Layer | Where it runs | Role |
|-------|----------------|------|
| Computer vision (YOLO) | PC / Raspberry Pi | Find shuttlecock + coordinates |
| Motor / PID / encoders | Arduino | Real-time motion control |
| This GitHub repo | Detection + ML + web demo | Soft side + design docs |

Two ways to run detection on a PC:

| Mode | Entry | Saves data? | Robot actions? |
|------|--------|-------------|----------------|
| **Desktop OpenCV** | `realtime_detect.py` | Yes → `detection_log.csv` | Yes (LEFT/RIGHT/PICK/…) |
| **Browser web app** | `run.bat` / `webapp/app.py` | **No** DB / Excel / CSV | **No** — boxes + coordinates only |

---

## 2) What we built / updated (changelog)

Work added on top of the original ShuttleBot ML project:

### Live Gradio web page (`webapp/`)

- Live webcam detection in the browser
- Shows **bounding box** + **live coordinates**
- **No database**, no Excel, no CSV logging from the web UI
- Dark interactive theme (Outfit + JetBrains Mono), responsive layout
- Single-screen flow:
  - **Access webcam** → auto-starts live detection (no manual Gradio “Record” click)
  - **Stop** → camera off, detection cleared, idle screen returns
- Status / error messages show for **5 seconds**, then clear
- If shuttle is **not** found → camera **stays on**; message: `No detection of shuttle` (5s)
- Port helper: prefers **7860**, frees it if busy, otherwise next free port; browser opens automatically
- Speed optimizations for web path:
  - Inference size **320**
  - Max frame side **480px**
  - Drop backlog frames (no queue pile-up)
  - Lightweight OpenCV drawing (not heavy `result.plot()`)
  - JPEG encode, small Gradio queue
  - Model fuse + warmup

### Helper launchers

| File | Purpose |
|------|---------|
| `run.bat` | Local web app (auto browser) |
| `run-share.bat` | Local web app + temporary public Gradio link |
| `webapp/run.bat` | Same as local web app, from inside `webapp/` |
| `DEPLOY-HF.md` | Hosting notes (HF PRO wall, Static/Lite warning, free options) |

### Docs

- Root `README.md` (this file) — full project + web app guide
- `webapp/README.md` — Space frontmatter + short run notes
- `DEPLOY-HF.md` — deploy / hosting reality check

---

## 3) Quick start — which file should I run?

| Goal | What to run | How |
|------|-------------|-----|
| **Browser live demo (recommended for UI)** | `run.bat` | Double-click in repo root |
| Same, from terminal | `webapp/app.py` | `python webapp/app.py` |
| Share a **temporary** public link | `run-share.bat` | Double-click (PC must stay on) |
| Fastest desktop OpenCV loop + CSV + robot actions | `realtime_detect.py` | See [§9](#9-desktop-real-time-detector-realtime_detectpy) |
| Train / retrain model | `i222327_ML_FINALPROJECT.ipynb` | Open in Colab / Jupyter |
| Robot simulation | `Simulation.py` | `python Simulation.py` |
| Deploy online permanently | HF **Gradio** Space (needs PRO) or keep local/`--share` | See [§16](#16-hosting--deploy-hugging-face-and-free-options) |

### First-time setup (web app)

Open PowerShell in the repo root:

```powershell
cd C:\Users\CodeTech\Desktop\ShuttleCock-Detection
python -m pip install -r webapp\requirements.txt
```

Then either:

```powershell
.\run.bat
```

or:

```powershell
python webapp\app.py
```

Browser should open to `http://127.0.0.1:7860` (or another free port — see [§8](#8-ports-browser-url-and-port-conflicts)).

> On this machine `pip` alone may not be on PATH. Prefer `python -m pip …`.

### First-time setup (desktop detector)

```powershell
cd C:\Users\CodeTech\Desktop\ShuttleCock-Detection
python -m pip install ultralytics opencv-python
python realtime_detect.py --conf 0.35 --x-thresh 40 --pick-area-thresh 0.08
```

---

## 4) Requirements

### Software

| Item | Notes |
|------|--------|
| **Python** | 3.10–3.12 recommended; 3.14 may work but wheels can be newer/fragile |
| **pip** | Use `python -m pip` |
| **Webcam** | Built-in or USB; browser must allow camera for web app |
| **OS** | Windows tested (`run.bat`); Linux/macOS: run `python webapp/app.py` |

### Python packages

**Web app** (`webapp/requirements.txt`):

- `gradio` (UI)
- `ultralytics` (YOLO)
- `opencv-python-headless`
- `numpy`
- `torch` (CPU index URL in requirements for lighter install)

**Desktop script:**

- `ultralytics`
- `opencv-python` (GUI window)

### Hardware

- CPU is enough for demo (few FPS on web is normal)
- NVIDIA GPU optional (web app auto-uses CUDA if available)

---

## 5) Repository layout (every important path)

```text
ShuttleCock-Detection/
├── README.md                          ← Full documentation (this file)
├── DEPLOY-HF.md                       ← Hosting / Hugging Face notes
├── run.bat                            ← Start local web app + open browser
├── run-share.bat                      ← Web app + temporary public Gradio URL
│
├── webapp/                            ← LIVE BROWSER DETECTOR
│   ├── app.py                         ← Gradio app (main web entry)
│   ├── requirements.txt               ← Web dependencies
│   ├── README.md                      ← Short notes + HF Space YAML header
│   ├── run.bat                        ← Launch from webapp folder
│   └── models/
│       └── shuttle_yolov8n_best.pt    ← Weights copy for web / HF upload
│
├── realtime_detect.py                 ← Desktop OpenCV detector + actions + CSV
├── Simulation.py                      ← Robot simulation
├── detection_log.csv                  ← Log from realtime_detect.py runs
├── results.csv / args.yaml            ← Training metrics / hyperparameters
│
├── i222327_ML_FINALPROJECT.ipynb      ← Colab training notebook
├── i222327_ML_FINALPROJECT.ipynb - Colab.pdf
│
├── ShuttleBotRealtime/
│   └── models/
│       └── shuttle_yolov8n_best.pt    ← Weights for desktop realtime script
│
├── My Drive/ShuttleBot/...            ← Training / predict artifacts (large)
│
├── ML A #01 (Viva Questions).txt
├── Shuttle Bot Design Report.pdf
├── Shuttle Bot ML Design.pdf
├── Mechanical_Design_of_Service_Robot_for_Shuttlecock.pdf
├── Object Detection Models Explained.pdf
├── slides.pdf / assignment PDFs / demo video assets
└── .gradio/                           ← Local Gradio cache (auto-created; safe to ignore)
```

### File purpose cheat-sheet

| File / folder | Purpose | Run? |
|---------------|---------|------|
| `webapp/app.py` | Browser live detection UI | Yes — primary web entry |
| `run.bat` | Windows launcher for web app | Yes — easiest |
| `run-share.bat` | Web app + `*.gradio.live` share link | Yes — temporary public demo |
| `webapp/requirements.txt` | Install web stack | `python -m pip install -r …` |
| `webapp/models/*.pt` | Model for web / Space upload | Used automatically |
| `ShuttleBotRealtime/models/*.pt` | Model for desktop script | Used by `realtime_detect.py` |
| `realtime_detect.py` | Fast desktop OpenCV + actions + CSV | Yes |
| `Simulation.py` | Simulation | Yes |
| `i222327_ML_FINALPROJECT.ipynb` | Train / evaluate | In Colab/Jupyter |
| `DEPLOY-HF.md` | How (not) to host on HF | Read only |
| Design / viva PDFs & txt | Course docs | Read only |
| `detection_log.csv` | Output of desktop detector | Generated |
| `.gradio/` | Gradio runtime cache | Do not commit / ignore |

---

## 6) Model weights

Primary trained file:

`shuttle_yolov8n_best.pt` (YOLOv8n fine-tuned for shuttlecock)

Present in:

1. `webapp/models/shuttle_yolov8n_best.pt` — used by the web app first  
2. `ShuttleBotRealtime/models/shuttle_yolov8n_best.pt` — used by `realtime_detect.py` / fallback for web  

Web app search order (in `webapp/app.py`):

1. `webapp/models/shuttle_yolov8n_best.pt`  
2. `ShuttleBotRealtime/models/shuttle_yolov8n_best.pt`  

Size is roughly **~6 MB** — fine for Git and for uploading to a Space (if you have Gradio hosting).

---

## 7) Live web app (`webapp/`)

### What it is

A **Gradio** webpage that:

1. Opens your webcam in the browser  
2. Runs YOLO on frames  
3. Draws boxes on **one live view**  
4. Updates **coordinates** as the shuttle moves  
5. Does **not** store anything (no DB, Excel, CSV)

### How to run (Windows)

**Option A — double-click (easiest)**

1. Open folder: `ShuttleCock-Detection`  
2. Double-click `run.bat`  
3. Wait for browser  
4. Click **Access webcam**  
5. Allow camera permission if the browser asks  
6. Hold a shuttlecock in view  
7. Click **Stop** when finished  

**Option B — terminal**

```powershell
cd C:\Users\CodeTech\Desktop\ShuttleCock-Detection
python -m pip install -r webapp\requirements.txt
python webapp\app.py
```

**Option C — from `webapp/` folder**

```powershell
cd C:\Users\CodeTech\Desktop\ShuttleCock-Detection\webapp
.\run.bat
```

**Option D — temporary public link**

```powershell
cd C:\Users\CodeTech\Desktop\ShuttleCock-Detection
.\run-share.bat
```

Or:

```powershell
python webapp\app.py --share
```

Terminal prints a URL like `https://xxxxxxxx.gradio.live`.  
Anyone can open it **only while your PC keeps the app running**.

### Environment flag (optional)

```powershell
$env:GRADIO_SHARE="1"
python webapp\app.py
```

### Web UI controls

| Control | Meaning |
|---------|---------|
| **Access webcam** | Start camera + auto live detection |
| **Stop** | Stop camera, clear detection view, back to idle |
| **Live coordinates** | Updates when shuttle is detected |
| **Detection sensitivity** | Confidence threshold slider (lower = more detections) |

### Web dependencies install (detail)

```powershell
python -m pip install -r webapp\requirements.txt
```

`requirements.txt` pins a CPU PyTorch index for smaller installs on machines without GPU.

---

## 8) Ports, browser URL, and port conflicts

### Default

| Item | Value |
|------|--------|
| Preferred port | **7860** |
| Local URL | `http://127.0.0.1:7860` |
| Bind address | `127.0.0.1` (this PC only) |

### Automatic port behaviour (`webapp/app.py`)

On start the app will:

1. Prefer port **7860**  
2. If something is already listening on 7860 → **kill that listener** (Windows `taskkill` / Unix `SIGTERM`)  
3. If 7860 still cannot be used → try **7861, 7862, …**  
4. Last resort → OS ephemeral free port  
5. Open the system browser to the chosen URL automatically  

So you should **not** get stuck on “Address already in use” for normal local runs.

### If the page does not open

Manually visit:

- `http://127.0.0.1:7860`  
- or check the terminal for the printed Gradio local URL  

### Stop the server

- Close the terminal window running the app, or press `Ctrl+C` in that terminal  
- Or click **Stop** in the UI (stops camera; close terminal to stop the server fully)

### Firewall

Local `127.0.0.1` usually needs no firewall change.  
`--share` / Gradio tunnel needs outbound internet.

---

## 9) Desktop real-time detector (`realtime_detect.py`)

OpenCV window on the desktop (usually **faster** than the browser path).

### Features

- YOLO on webcam frames  
- Chooses robot-style **actions** from bbox vs frame center  
- Overlay text + FPS  
- Writes **`detection_log.csv`**

### Run

```powershell
cd C:\Users\CodeTech\Desktop\ShuttleCock-Detection
python -m pip install ultralytics opencv-python
python realtime_detect.py --conf 0.35 --x-thresh 40 --pick-area-thresh 0.08
```

### CLI flags

| Flag | Default | Meaning |
|------|---------|---------|
| `--model` | `ShuttleBotRealtime/models/shuttle_yolov8n_best.pt` | Weights path |
| `--camera-index` | `0` | OpenCV camera index |
| `--conf` | `0.35` | Confidence threshold |
| `--iou` | `0.5` | NMS IoU |
| `--imgsz` | `640` | Inference size |
| `--x-thresh` | `40` | Pixels from center → LEFT/RIGHT |
| `--pick-area-thresh` | `0.08` | Normalized box area → **PICK** |
| `--log-csv` | `detection_log.csv` | Per-frame log file |

Typical actions: **LEFT / RIGHT / FORWARD / PICK / SEARCH** (see draw/log loop in the script).  
Quit with the OpenCV key used in `main()` (usually `q`).

---

## 10) Offline prediction (Python one-liner)

```python
from ultralytics import YOLO

model = YOLO("ShuttleBotRealtime/models/shuttle_yolov8n_best.pt")
model.predict(source="path/to/images_or_video", conf=0.25, save=True)
```

Annotated outputs are written under Ultralytics `runs/predict/…`.

---

## 11) Training notebook (ML pipeline)

File: `i222327_ML_FINALPROJECT.ipynb` (Colab + Google Drive workflow)

1. Install Ultralytics + OpenCV; check GPU  
2. Mount Drive; unzip merged YOLO dataset  
3. Inspect train/val/test; write dataset YAML  
4. Fine-tune from `yolov8n.pt`  
5. Copy `best.pt` → `shuttle_yolov8n_best.pt`  
6. Predict on test images; log metrics  
7. Plot box/cls/dfl loss, precision, recall, mAP50, mAP50-95  

For local retrain: open the notebook and retarget Drive paths.

PDF export also present: `i222327_ML_FINALPROJECT.ipynb - Colab.pdf`

---

## 12) Training artifacts

| Path | Contents |
|------|----------|
| `My Drive/ShuttleBot/runs/shuttle_train_v1/` | `args.yaml`, `results.csv`, `weights/best.pt` |
| `My Drive/ShuttleBot/models/shuttle_yolov8n_best.pt` | Frozen export (Drive layout) |
| `ShuttleBotRealtime/models/shuttle_yolov8n_best.pt` | Copy for realtime / desktop |
| `webapp/models/shuttle_yolov8n_best.pt` | Copy for web app |
| `runs/predict_test_v1/` (under Drive tree) | Annotated test JPGs (large) |

`results.csv` — epoch-wise train/val losses + P, R, mAP50, mAP50-95  
`args.yaml` — Ultralytics hyperparameters from the training run  

Root copies of `results.csv` / `args.yaml` may also exist for quick reference.

---

## 13) Simulation

`Simulation.py` — kinematics / collection simulation assets for the robot (pair with design PDFs).

```powershell
python Simulation.py
```

Check the file’s `if __name__ == "__main__"` block for windows / parameters.  
Related media: `Simulation_video.avi`, demo MP4 in the repo root.

---

## 14) Robotics context (Pi + Arduino)

From `ML A #01 (Viva Questions).txt` and design PDFs:

| Topic | Design choice |
|-------|----------------|
| Why Pi + Arduino | Pi for ML/camera; Arduino for **real-time PID** + encoders |
| Why PID | Straighter motion, less motor drift |
| Why not Jetson | Cost / power for academic build |
| Grounding | Common GND between Pi and Arduino |
| Drop zone | Encoders and/or visual markers |
| Claimed detection | ~85–90% indoor with lighting control |
| Future | SLAM, AI accelerator, dock, multi-shuttle |

PDFs: Shuttle Bot design/ML reports, mechanical design, assignment briefs, object-detection notes, slides.

---

## 15) Dataset

Note file: `My_Drive_ShuttleBot_datasets_DataSet_Link.txt`  
Kaggle source referenced in project notes: [shuttle-badminton-photos](https://www.kaggle.com/datasets/ayushsinha731/shuttle-badminton-photos) plus a merged YOLO-format ZIP used in Colab.

---

## 16) Hosting / deploy (Hugging Face and free options)

Full short guide: [`DEPLOY-HF.md`](DEPLOY-HF.md)

### Hugging Face reality (important)

On **Create new Space**, HF may show:

> Gradio and Docker Spaces require a paid plan  
> Static Spaces stay free

| HF option | Use for this YOLO webcam app? |
|-----------|-------------------------------|
| **Gradio** (Python server) | Yes — but often needs **HF PRO** |
| **Docker** | Possible — also paid plan on HF |
| **Static / Gradio Lite** | **NO** — cannot run PyTorch YOLO server |

**Do not** pick Static → Gradio Lite. It will not run this detector.

### Free options that actually work

| Option | Cost | Notes |
|--------|------|--------|
| `run.bat` local | Free | Best reliability |
| `run-share.bat` / `--share` | Free | Temporary `*.gradio.live`; PC must stay on |
| Google Colab + Gradio share | Free | Temporary session |
| Permanent HF Gradio Space | Paid (PRO) | Upload `webapp/` files |

### If you have HF Gradio (PRO) — upload these

From `webapp/`:

- `app.py`  
- `requirements.txt`  
- `README.md` (keeps Space YAML header)  
- `models/shuttle_yolov8n_best.pt`  

Live URL shape:

`https://huggingface.co/spaces/YOUR_USERNAME/shuttlecock-detection`

### Why not Vercel / Netlify?

Those are static/serverless hosts. This app needs a long-running Python process + PyTorch. **Not supported.**

---

## 17) Web app behaviour (UI rules)

| Situation | Behaviour |
|-----------|-----------|
| Click **Access webcam** | Camera starts; live detection starts automatically (internal Gradio Record is auto-clicked and hidden) |
| Shuttle visible | Box drawn; **coordinates update live** as it moves |
| Shuttle not visible | Camera **stays on**; `No detection of shuttle` for **5 seconds**, then message clears |
| Errors / waiting messages | Shown for **5 seconds**, then disappear |
| Click **Stop** | Camera stopped; detection image cleared; idle screen returns |
| Storage | Nothing saved (no DB / Excel / CSV from web UI) |

---

## 18) Speed / performance notes

### Desktop (`realtime_detect.py`)

- Direct OpenCV loop — usually **fastest** on the same PC  
- Default `imgsz=640`

### Web (`webapp/app.py`)

Browser path is inherently heavier (encode frames, send to Python, return JPEG). Optimizations already in code:

| Setting | Value | Why |
|---------|-------|-----|
| `INFER_IMGSZ` | `320` | Faster YOLO |
| `MAX_FRAME_SIDE` | `480` | Smaller images over the wire |
| `STREAM_EVERY_SEC` | `0.05` | Snappier stream attempts |
| Frame drop lock | on | Skip backlog instead of lagging |
| Drawing | light OpenCV boxes | Avoid slow `result.plot()` |
| Queue | `max_size=1` | No piled-up frames |
| Warmup + `fuse()` | on | First real frames faster |

Expect: web ≤ desktop FPS. Good indoor light helps both.

---

## 19) Troubleshooting

| Problem | Fix |
|---------|-----|
| `pip` not recognized | Use `python -m pip install …` |
| Browser blank / no camera | Allow camera permission for `127.0.0.1` |
| Port busy | App auto-frees **7860**; or close old `python webapp\app.py` / `run.bat` |
| Very slow web FPS | Normal vs desktop; use `realtime_detect.py` for max speed; ensure only one app instance |
| Model missing error | Ensure `webapp/models/shuttle_yolov8n_best.pt` or `ShuttleBotRealtime/models/…` exists |
| HF only shows Static / Gradio Lite | Cannot host this app there for free; use local or `--share` or HF PRO Gradio |
| Share link dead | Your PC stopped the app or lost internet |
| Python 3.14 package errors | Install Python 3.11/3.12 and recreate venv if needed |
| Old UI still showing | Stop old server (`Ctrl+C`) and run `run.bat` again |

### Manual free port 7860 (Windows PowerShell)

Usually not needed (app does this), but:

```powershell
Get-NetTCPConnection -LocalPort 7860 -ErrorAction SilentlyContinue |
  Select-Object -ExpandProperty OwningProcess -Unique |
  ForEach-Object { taskkill /F /PID $_ }
```

---

## 20) Viva highlights

- Hybrid SBC + MCU: compute vs hard real-time  
- PID + encoders vs open-loop motors  
- Lighting and dataset quality dominate mAP  
- Common ground and regulated 5 V / 12 V rails  
- Web demo is for visualization/coordinates only — robot actions live in `realtime_detect.py` / Pi stack  
- Do not clone huge `predict_test_v1` JPGs if you only need weights  

---

## 21) Notes

- Notebook paths assume Colab Drive. For a lean clone keep the `.pt` weights under `ShuttleBotRealtime/models/` and `webapp/models/`.  
- Web UI intentionally does **not** log to CSV (desktop script does).  
- Gradio “Record” is an internal stream switch; the web app auto-triggers it so users only use **Access webcam** / **Stop**.  

---

## 22) Author

**Mohammad Rohaan** — i222327 · [rohaan2802](https://github.com/rohaan2802)  
Repository: https://github.com/rohaan2802/ShuttleCock-Detection
