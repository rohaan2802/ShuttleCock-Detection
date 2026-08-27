# Deploy live demo — Hugging Face Spaces (free)

Best free host for this Gradio + YOLO webcam app.

Your live URL will look like:

`https://huggingface.co/spaces/YOUR_USERNAME/shuttlecock-detection`

---

## 1) Create account

1. Open **https://huggingface.co/join**
2. Sign up (Google / email)
3. Confirm email if asked

---

## 2) Create a Space

1. Open **https://huggingface.co/new-space**
2. Fill:
   - **Space name:** `shuttlecock-detection` (any name is fine)
   - **License:** MIT
   - **Select the SDK:** **Gradio**
   - **Space hardware:** **CPU basic — free**
   - **Visibility:** Public
3. Click **Create Space**

---

## 3) Upload these 4 files

In the new Space → **Files** → **Add file** → **Upload files**  
Upload **everything from the `webapp/` folder** (not the whole GitHub repo):

| File | Required |
|------|----------|
| `app.py` | yes |
| `requirements.txt` | yes |
| `README.md` | yes (has Space settings) |
| `models/shuttle_yolov8n_best.pt` | yes |

Keep the folder name `models` so the path stays `models/shuttle_yolov8n_best.pt`.

After upload, Hugging Face builds the app (often **5–15 minutes** the first time). Status shows at the top of the Space page.

---

## 4) Open the live page

When status is **Running**, open your Space URL and click **Allow** for the camera.

---

## Notes

- Free CPU is slower than a local PC — a few frames per second is normal.
- If the Space sleeps after idle time, open the URL again; it wakes in a minute or two.
- Do **not** use Vercel for this app.

Local files for upload are already in your clone:

`C:\Users\CodeTech\Desktop\ShuttleCock-Detection\webapp\`
