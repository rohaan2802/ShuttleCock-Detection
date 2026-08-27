# Deploy live demo — Lightning AI Studio (recommended free cloud)

You want a **public link** that can **sleep when idle** and **wake again when someone opens the link**.

| Option | Auto wake on click? | PC must stay on? | Use? |
|--------|---------------------|------------------|------|
| **Lightning AI Studio** (serverless / auto-start) | **Yes** (after short wake delay) | No | **Best choice** |
| Gradio `--share` / `run-share.bat` | No | **Yes** | Easy temporary share |
| Google Colab + ngrok/share | **No** (notebook dies; must re-run by hand) | No | Short GPU tests only |
| Render | Yes (cold start) | No | You said no |
| Hugging Face Gradio Space | Yes | No | Needs PRO on your account |

---

## Why Lightning (not Colab / Gradio share)

- **Colab:** session ends on idle → old link does **not** auto-start again.  
- **Gradio share:** free and easy, but **your PC must stay on**; if PC sleeps/off, link dies.  
- **Lightning Studio:** can sleep when unused, then **auto-wake when a visitor hits the public URL** (small delay first time).

Your model is **YOLOv8n** + webcam — fits free **CPU** Studio if you keep the optimized webapp settings (already in `webapp/app.py`: imgsz 320, frame drop, etc.).

---

## Step-by-step — Lightning AI

### 1) Account

1. Open **https://lightning.ai**  
2. Sign up / log in (GitHub login is fine)

### 2) Create a free CPU Studio

1. **New Studio** → choose free **CPU**  
2. Wait until the Studio terminal is ready  

### 3) Clone this project

In the Studio terminal:

```bash
cd ~
git clone https://github.com/rohaan2802/ShuttleCock-Detection.git
cd ShuttleCock-Detection
python -m pip install -r webapp/requirements.txt
```

### 4) Start the Gradio app

```bash
python webapp/app.py
```

App listens on **port 7860**.

### 5) Expose a public URL (important)

1. In the Studio UI, open **Port viewer** / **Ports** plugin (or “Expose port”)  
2. Expose **7860**  
3. Copy the **public HTTPS URL** Lightning gives you  

That URL is what you share (portfolio / friends).

### 6) Enable sleep + auto wake (serverless)

In Lightning docs this is called **serverless** / **auto start** for web apps:

1. Find the setting for your exposed app / Studio: **Auto start** / **serverless**  
2. Turn **ON** so that:
   - idle → Studio **sleeps** (saves free quota)  
   - someone opens the public link → Studio **wakes**, then Gradio loads  

First visit after sleep can take **~30–90 seconds**. Later requests are faster while it stays awake.

> Exact UI labels move sometimes; look for: *Auto start*, *Serverless*, *Sleep when inactive*, *Wake on request*.  
> Official: https://lightning.ai/docs/platform/build/host-web-apps/expose-web-apps

### 7) Keep the process running inside the Studio

After wake, Gradio must start again. Options:

**A) Simple (manual after wake):**  
When Studio wakes, open terminal and run `python webapp/app.py` again.

**B) Better — startup command / plugin:**  
Use Lightning’s **API builder** / app plugin (if available on your plan) and set start command:

```bash
cd ~/ShuttleCock-Detection && python webapp/app.py
```

So wake → command runs → port 7860 serves the app.

**C) Background in Studio terminal:**

```bash
cd ~/ShuttleCock-Detection
nohup python webapp/app.py > /tmp/shuttle-gradio.log 2>&1 &
```

Combine with auto-start if Lightning re-runs a startup script on wake.

---

## Gradio share (still useful)

On your PC:

```bat
run-share.bat
```

or:

```bash
python webapp/app.py --share
```

- Free public `*.gradio.live` link  
- **PC must stay on and awake**  
- Link expires (~72 hours)  
- **No** cloud auto-wake  

Use this for quick demos when you are at the laptop.

---

## Google Colab (only temporary)

Use only if you need a short GPU test. It will **not** meet “sleep then auto-start on click”.

Rough flow:

1. New Colab notebook  
2. Clone repo + `pip install -r webapp/requirements.txt`  
3. `!python webapp/app.py --share`  
4. Use the printed Gradio link until the runtime disconnects  

When Colab disconnects, that link dies until you run the notebook again.

---

## Checklist after Lightning deploy

- [ ] Public URL opens Gradio UI  
- [ ] **Access webcam** works (browser camera permission)  
- [ ] Detection + live coordinates update  
- [ ] Leave idle until Studio sleeps  
- [ ] Open the same URL again → wakes (wait once) → app works  

---

## If wake works but Gradio is blank

Studio woke but `app.py` was not running:

```bash
cd ~/ShuttleCock-Detection
python webapp/app.py
```

Then re-check port **7860** is still exposed.

---

## Summary

| Goal | Do this |
|------|---------|
| Live link + sleep + **auto wake on click** | **Lightning AI Studio** + expose **7860** + auto-start/serverless |
| Quick share from laptop | **`run-share.bat`** |
| Short GPU experiment | Colab + `--share` (not permanent) |
| Render / HF free Gradio | Skip (Render you don’t want; HF needs PRO) |
