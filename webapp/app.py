"""
Live shuttlecock detection — camera only, no database, no file logging.
Works locally and on Hugging Face Spaces.
"""

from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

import cv2
import gradio as gr
import numpy as np
from ultralytics import YOLO

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

_CANDIDATES = [
    HERE / "models" / "shuttle_yolov8n_best.pt",
    ROOT / "ShuttleBotRealtime" / "models" / "shuttle_yolov8n_best.pt",
]

_model: YOLO | None = None
_device: str = "cpu"
_use_half: bool = False
_infer_lock = threading.Lock()
_last_annotated: np.ndarray | None = None
_last_coords: str = ""

# Speed-first defaults (web path is slower than raw OpenCV desktop).
INFER_IMGSZ = 320
MAX_FRAME_SIDE = 480
STREAM_EVERY_SEC = 0.05
BOX_COLOR = (45, 212, 191)
TEXT_COLOR = (248, 250, 252)

MESSAGE_VISIBLE_SEC = 5.0

MSG_NO_SHUTTLE = "No detection of shuttle"
MSG_WAIT_CAMERA = "Waiting for camera… Allow access when the browser asks."
MSG_MODEL_MISSING = (
    "Detection model is missing. Refresh the page, or contact the site owner."
)
MSG_MODEL_FAIL = "Could not start the detector. Refresh the page and try again."
MSG_DETECT_FAIL = "Detection failed on this frame. Check lighting and try again."

STOP_TRACKS_JS = """
() => {
  const root = document.querySelector("#cam-engine");
  if (root) {
    const stopBtn = Array.from(root.querySelectorAll("button")).find((b) => {
      const t = (
        (b.textContent || "") +
        (b.getAttribute("aria-label") || "") +
        (b.getAttribute("title") || "")
      ).toLowerCase();
      return t.includes("stop") || !!b.querySelector('[title="stop recording"]');
    });
    if (stopBtn) stopBtn.click();
  }
  document.querySelectorAll("video").forEach((video) => {
    const stream = video.srcObject;
    if (!stream) return;
    stream.getTracks().forEach((track) => track.stop());
    video.srcObject = null;
  });
}
"""

# Gradio webcam needs an internal "Record" click to stream frames — do it automatically.
AUTO_START_STREAM_JS = """
() => {
  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const textOf = (el) =>
    (
      (el.textContent || "") +
      " " +
      (el.getAttribute("aria-label") || "") +
      " " +
      (el.getAttribute("title") || "")
    ).toLowerCase();

  (async () => {
    for (let i = 0; i < 60; i++) {
      const root = document.querySelector("#cam-engine");
      if (!root) {
        await sleep(120);
        continue;
      }

      const accessBtn = Array.from(root.querySelectorAll("button")).find((b) =>
        textOf(b).includes("access webcam")
      );
      if (accessBtn) {
        accessBtn.click();
        await sleep(450);
      }

      const recordBtn = Array.from(root.querySelectorAll("button")).find((b) => {
        if (b.querySelector('[title="stop recording"]')) return false;
        if (b.querySelector('[title="start recording"]')) return true;
        const t = textOf(b);
        return t.includes("record") && !t.includes("stop");
      });
      if (recordBtn) {
        recordBtn.click();
        return;
      }

      // Already streaming
      if (root.querySelector('[title="stop recording"]')) return;
      await sleep(150);
    }
  })();
}
"""

IDLE_HTML = """
<div class="idle-stage">
  <div class="idle-orb" aria-hidden="true"></div>
  <p class="idle-kicker">Live detector</p>
  <h2 class="idle-title">Shuttlecock Detection</h2>
  <p class="idle-copy">Tap Access webcam — live detection and coordinates start automatically. No Record button needed.</p>
</div>
"""


def resolve_model_path() -> Path:
    for path in _CANDIDATES:
        if path.is_file():
            return path
    raise FileNotFoundError(MSG_MODEL_MISSING)


def load_model() -> YOLO:
    global _model, _device, _use_half
    if _model is not None:
        return _model

    try:
        import torch

        if torch.cuda.is_available():
            _device = "0"
            _use_half = True
        else:
            _device = "cpu"
            _use_half = False
            # Keep CPU inference responsive for webcam loop.
            torch.set_num_threads(max(1, min(4, (os.cpu_count() or 2))))
    except Exception:
        _device = "cpu"
        _use_half = False

    cv2.setNumThreads(2)
    _model = YOLO(str(resolve_model_path()))
    try:
        _model.fuse()
    except Exception:
        pass

    # Warm up so the first real frame is not the slowest.
    warm = np.zeros((INFER_IMGSZ, INFER_IMGSZ, 3), dtype=np.uint8)
    _model.predict(
        source=warm,
        imgsz=INFER_IMGSZ,
        conf=0.25,
        verbose=False,
        device=_device,
        half=_use_half,
        max_det=5,
    )
    return _model


def shrink_frame(frame: np.ndarray) -> np.ndarray:
    h, w = frame.shape[:2]
    side = max(h, w)
    if side <= MAX_FRAME_SIDE:
        return frame
    scale = MAX_FRAME_SIDE / float(side)
    return cv2.resize(
        frame,
        (max(1, int(w * scale)), max(1, int(h * scale))),
        interpolation=cv2.INTER_AREA,
    )


def draw_boxes_rgb(frame_rgb: np.ndarray, boxes) -> tuple[np.ndarray, str]:
    """Lightweight draw (faster than Ultralytics result.plot())."""
    out = frame_rgb
    lines: list[str] = []
    if boxes is None or len(boxes) == 0:
        return out, ""

    # Copy once only when we need to draw.
    out = frame_rgb.copy()
    xyxy = boxes.xyxy.cpu().numpy()
    confs = boxes.conf.cpu().numpy()
    for i, (row, conf) in enumerate(zip(xyxy, confs), start=1):
        x1, y1, x2, y2 = (int(v) for v in row)
        cv2.rectangle(out, (x1, y1), (x2, y2), BOX_COLOR, 2)
        cx = (x1 + x2) * 0.5
        cy = (y1 + y2) * 0.5
        label = f"{conf * 100:.0f}%"
        cv2.putText(
            out,
            label,
            (x1, max(16, y1 - 6)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            TEXT_COLOR,
            2,
            cv2.LINE_AA,
        )
        lines.append(
            f"#{i}  center ({cx:.0f}, {cy:.0f})  "
            f"box ({x1}, {y1}) → ({x2}, {y2})  "
            f"{conf * 100:.0f}%"
        )
    return out, "\n".join(lines)


def status_html(message: str) -> str:
    if not message:
        return ""
    return f'<div class="status-banner" role="status">{message}</div>'


def detect(frame, confidence: float, miss_since: float | None, running: bool):
    """Fast path: shrink frame, small imgsz, drop backlog frames, light drawing."""
    global _last_annotated, _last_coords

    if not running:
        return gr.update(), "", gr.update(), miss_since, gr.update()

    if frame is None:
        return (
            gr.update(),
            "",
            status_html(MSG_WAIT_CAMERA),
            None,
            gr.update(active=True),
        )

    # If previous inference is still running, keep last result (no queue pile-up).
    if not _infer_lock.acquire(blocking=False):
        if _last_annotated is not None:
            return _last_annotated, _last_coords, gr.update(), miss_since, gr.update()
        return gr.update(), "", gr.update(), miss_since, gr.update()

    try:
        try:
            model = load_model()
        except FileNotFoundError as exc:
            return frame, "", status_html(str(exc)), None, gr.update(active=True)
        except Exception:
            return frame, "", status_html(MSG_MODEL_FAIL), None, gr.update(active=True)

        try:
            conf = min(0.9, max(0.15, float(confidence)))
            small = shrink_frame(frame)
            # Gradio webcam frames are RGB; Ultralytics accepts ndarray RGB/BGR.
            result = model.predict(
                source=small,
                conf=conf,
                imgsz=INFER_IMGSZ,
                verbose=False,
                device=_device,
                half=_use_half,
                max_det=5,
                agnostic_nms=True,
            )[0]
            boxes = result.boxes
            found = boxes is not None and len(boxes) > 0
            annotated, coords = draw_boxes_rgb(small, boxes)
            _last_annotated = annotated
            _last_coords = coords if found else ""
        except Exception:
            return frame, "", status_html(MSG_DETECT_FAIL), None, gr.update(active=True)

        if found:
            return annotated, coords, "", None, gr.update()

        if miss_since is None:
            return (
                annotated,
                "",
                status_html(MSG_NO_SHUTTLE),
                time.time(),
                gr.update(active=True),
            )

        return annotated, "", gr.update(), miss_since, gr.update()
    finally:
        _infer_lock.release()


CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

:root {
  --bg0: #070b12;
  --bg1: #0e1624;
  --bg2: #152033;
  --line: #243247;
  --text: #e8eef7;
  --muted: #93a4bd;
  --accent: #2dd4bf;
  --accent-2: #38bdf8;
  --danger: #fb7185;
  --radius: 18px;
  --shadow: 0 18px 50px rgba(0, 0, 0, 0.45);
}

html, body {
  background:
    radial-gradient(1200px 600px at 10% -10%, rgba(45, 212, 191, 0.16), transparent 55%),
    radial-gradient(900px 500px at 100% 0%, rgba(56, 189, 248, 0.12), transparent 50%),
    var(--bg0) !important;
}

.gradio-container {
  max-width: 920px !important;
  width: min(920px, 100%) !important;
  margin: 0 auto !important;
  padding: 0.75rem !important;
  font-family: "Outfit", system-ui, sans-serif !important;
  color: var(--text) !important;
}

footer, .svelte-1ipelgc { display: none !important; }

.app-shell {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.hero-card, .stage-card, .panel-card {
  background: linear-gradient(180deg, rgba(21, 32, 51, 0.92), rgba(14, 22, 36, 0.96));
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 1rem 1.1rem;
}

.hero-card h1 {
  margin: 0;
  font-size: clamp(1.35rem, 4.2vw, 1.9rem);
  font-weight: 700;
  letter-spacing: -0.03em;
  background: linear-gradient(90deg, #f8fafc, #99f6e4 55%, #7dd3fc);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.hero-card p {
  margin: 0.35rem 0 0;
  color: var(--muted);
  font-size: clamp(0.9rem, 2.6vw, 1rem);
  line-height: 1.45;
}

.stage-card {
  padding: 0.65rem;
  position: relative;
  overflow: hidden;
}

.stage-stack {
  position: relative;
  min-height: clamp(240px, 52vh, 480px);
}

/* Webcam engine streams in the background; Gradio Record UI is auto-clicked and hidden. */
#cam-engine {
  position: absolute !important;
  width: 2px !important;
  height: 2px !important;
  overflow: hidden !important;
  opacity: 0 !important;
  pointer-events: none !important;
  z-index: 0 !important;
}

#cam-engine .button-wrap {
  opacity: 0 !important;
  pointer-events: none !important;
}

#main-stage {
  position: relative !important;
  z-index: 2;
}

#main-stage video,
#main-stage img,
#main-stage .image-container {
  width: 100% !important;
  max-height: min(68vh, 560px) !important;
  object-fit: contain !important;
  border-radius: 14px !important;
  background: #05080f !important;
}

.idle-stage {
  position: relative;
  min-height: clamp(240px, 52vh, 480px);
  display: grid;
  place-content: center;
  text-align: center;
  padding: 1.5rem 1rem;
  border-radius: 14px;
  background:
    linear-gradient(145deg, rgba(45, 212, 191, 0.08), transparent 40%),
    linear-gradient(180deg, #101a2a, #0b1320);
  border: 1px dashed rgba(45, 212, 191, 0.35);
}

.idle-orb {
  width: 84px;
  height: 84px;
  margin: 0 auto 1rem;
  border-radius: 50%;
  background: radial-gradient(circle at 30% 30%, #5eead4, #0f766e 70%);
  box-shadow: 0 0 0 10px rgba(45, 212, 191, 0.12), 0 12px 40px rgba(45, 212, 191, 0.35);
  animation: pulse 2.4s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.06); opacity: 0.88; }
}

.idle-kicker {
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  font-size: 0.72rem;
  color: var(--accent);
  font-weight: 600;
}

.idle-title {
  margin: 0.35rem 0;
  font-size: clamp(1.25rem, 4vw, 1.7rem);
  font-weight: 700;
}

.idle-copy {
  margin: 0 auto;
  max-width: 28rem;
  color: var(--muted);
  font-size: 0.95rem;
  line-height: 1.45;
}

.controls-row {
  display: flex !important;
  flex-wrap: wrap;
  gap: 0.65rem !important;
  align-items: stretch !important;
}

.controls-row > * {
  flex: 1 1 160px;
}

button.access-btn, button.stop-btn {
  min-height: 48px !important;
  border-radius: 14px !important;
  font-family: "Outfit", system-ui, sans-serif !important;
  font-weight: 700 !important;
  font-size: 1rem !important;
  letter-spacing: 0.01em !important;
  transition: transform 0.15s ease, box-shadow 0.15s ease, filter 0.15s ease !important;
}

button.access-btn {
  background: linear-gradient(135deg, #14b8a6, #0ea5e9) !important;
  color: #042f2e !important;
  border: none !important;
  box-shadow: 0 10px 28px rgba(20, 184, 166, 0.35) !important;
}

button.stop-btn {
  background: linear-gradient(135deg, #fb7185, #f43f5e) !important;
  color: #fff !important;
  border: none !important;
  box-shadow: 0 10px 28px rgba(244, 63, 94, 0.28) !important;
}

button.access-btn:hover, button.stop-btn:hover {
  transform: translateY(-1px) scale(1.01);
  filter: brightness(1.05);
}

button.access-btn:active, button.stop-btn:active {
  transform: translateY(0) scale(0.99);
}

.status-banner {
  margin-top: 0.35rem;
  padding: 0.85rem 1rem;
  border-radius: 12px;
  background: rgba(251, 113, 133, 0.12);
  border: 1px solid rgba(251, 113, 133, 0.35);
  color: #fecdd3;
  font-size: clamp(0.92rem, 2.8vw, 1.05rem);
  font-weight: 600;
  text-align: center;
  animation: fadeIn 0.25s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

.coords-box textarea {
  font-family: "JetBrains Mono", ui-monospace, monospace !important;
  font-size: 0.86rem !important;
  line-height: 1.45 !important;
}

input[type="range"] {
  accent-color: var(--accent) !important;
}

@media (max-width: 640px) {
  .gradio-container { padding: 0.45rem !important; }
  .hero-card, .stage-card, .panel-card { padding: 0.8rem; border-radius: 14px; }
  .controls-row > * { flex: 1 1 100%; }
  #main-stage video, #main-stage img {
    max-height: min(58vh, 420px) !important;
  }
}

@media (min-width: 1024px) {
  .gradio-container { padding: 1.25rem !important; }
}

@media (prefers-reduced-motion: reduce) {
  .idle-orb, button.access-btn, button.stop-btn, .status-banner {
    animation: none !important;
    transition: none !important;
  }
}
"""

theme = gr.themes.Base(
    primary_hue="teal",
    secondary_hue="slate",
    neutral_hue="slate",
    font=gr.themes.GoogleFont("Outfit"),
    font_mono=gr.themes.GoogleFont("JetBrains Mono"),
).set(
    body_background_fill="#070b12",
    body_background_fill_dark="#070b12",
    block_background_fill="#0e1624",
    block_background_fill_dark="#0e1624",
    block_border_color="#243247",
    block_label_text_color="#e8eef7",
    body_text_color="#e8eef7",
    button_primary_background_fill="#14b8a6",
    button_primary_background_fill_hover="#2dd4bf",
    button_primary_text_color="#042f2e",
    border_color_primary="#243247",
    input_background_fill="#101a2a",
)


def build_app() -> gr.Blocks:
    with gr.Blocks(title="Shuttlecock Detection", theme=theme, css=CUSTOM_CSS) as blocks:
        running = gr.State(False)
        miss_since = gr.State(None)

        with gr.Column(elem_classes=["app-shell"]):
            gr.HTML(
                """
                <div class="hero-card">
                  <h1>Shuttlecock Detection</h1>
                  <p>One tap starts live detection. Coordinates update as the shuttlecock moves — no Record button.</p>
                </div>
                """
            )

            with gr.Column(elem_classes=["stage-card", "stage-stack"]):
                idle = gr.HTML(IDLE_HTML, visible=True)
                # Hidden stream source (Gradio requires an internal record click; we auto-press it).
                camera = gr.Image(
                    sources=["webcam"],
                    streaming=True,
                    type="numpy",
                    label="Camera engine",
                    mirror_webcam=True,
                    visible=False,
                    elem_id="cam-engine",
                    show_download_button=False,
                    show_share_button=False,
                    show_fullscreen_button=False,
                    format="jpeg",
                )
                # What the user sees: live annotated frames + moving coordinates.
                stage = gr.Image(
                    type="numpy",
                    label="Live detection",
                    visible=False,
                    interactive=False,
                    elem_id="main-stage",
                    show_download_button=False,
                    show_share_button=False,
                    show_fullscreen_button=False,
                    format="jpeg",
                )

            with gr.Row(elem_classes=["controls-row"]):
                start_btn = gr.Button(
                    "Access webcam",
                    variant="primary",
                    elem_classes=["access-btn"],
                )
                stop_btn = gr.Button(
                    "Stop",
                    variant="stop",
                    visible=False,
                    elem_classes=["stop-btn"],
                )

            status = gr.HTML(value="")
            msg_timer = gr.Timer(value=MESSAGE_VISIBLE_SEC, active=False)

            with gr.Column(elem_classes=["panel-card"]):
                coords = gr.Textbox(
                    label="Live coordinates",
                    lines=3,
                    interactive=False,
                    elem_classes=["coords-box"],
                    placeholder="Coordinates update live when a shuttlecock is found.",
                )
                confidence = gr.Slider(
                    minimum=0.2,
                    maximum=0.7,
                    value=0.35,
                    step=0.05,
                    label="Detection sensitivity",
                    info="Lower finds more. Higher is stricter.",
                )

        def on_start():
            global _last_annotated, _last_coords
            _last_annotated = None
            _last_coords = ""
            return (
                True,
                None,
                gr.update(visible=False),
                gr.update(value=None, visible=True),
                gr.update(value=None, visible=True),
                gr.update(visible=False),
                gr.update(visible=True),
                "",
                "",
            )

        def on_stop():
            global _last_annotated, _last_coords
            _last_annotated = None
            _last_coords = ""
            return (
                False,
                None,
                gr.update(visible=True, value=IDLE_HTML),
                gr.update(value=None, visible=False),
                gr.update(value=None, visible=False),
                gr.update(visible=True),
                gr.update(visible=False),
                "",
                "",
                gr.update(active=False),
            )

        start_btn.click(
            fn=on_start,
            outputs=[
                running,
                miss_since,
                idle,
                camera,
                stage,
                start_btn,
                stop_btn,
                coords,
                status,
            ],
            js=AUTO_START_STREAM_JS,
        )

        stop_btn.click(
            fn=on_stop,
            outputs=[
                running,
                miss_since,
                idle,
                camera,
                stage,
                start_btn,
                stop_btn,
                coords,
                status,
                msg_timer,
            ],
            js=STOP_TRACKS_JS,
        )

        # Never write detection back into the webcam component — that breaks live streaming.
        camera.stream(
            fn=detect,
            inputs=[camera, confidence, miss_since, running],
            outputs=[stage, coords, status, miss_since, msg_timer],
            time_limit=None,
            stream_every=STREAM_EVERY_SEC,
        )

        def clear_status():
            return "", gr.update(active=False)

        msg_timer.tick(fn=clear_status, outputs=[status, msg_timer])

    return blocks


demo = build_app()
demo.queue(max_size=1, default_concurrency_limit=1)


def port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.4)
        return sock.connect_ex((host, port)) == 0


def pids_on_port(port: int) -> list[int]:
    pids: set[int] = set()
    if sys.platform.startswith("win"):
        try:
            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    f"(Get-NetTCPConnection -LocalPort {port} -State Listen "
                    f"-ErrorAction SilentlyContinue).OwningProcess | Select-Object -Unique",
                ],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            for token in result.stdout.split():
                if token.isdigit():
                    pid = int(token)
                    if pid > 0:
                        pids.add(pid)
        except Exception:
            pass
        if not pids:
            try:
                result = subprocess.run(
                    ["netstat", "-ano", "-p", "tcp"],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    check=False,
                )
                needle = f":{port}"
                for line in result.stdout.splitlines():
                    if needle not in line or "LISTENING" not in line.upper():
                        continue
                    parts = line.split()
                    if parts and parts[-1].isdigit():
                        pid = int(parts[-1])
                        if pid > 0:
                            pids.add(pid)
            except Exception:
                pass
    else:
        try:
            result = subprocess.run(
                ["lsof", "-ti", f"tcp:{port}"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            for token in result.stdout.split():
                if token.isdigit():
                    pids.add(int(token))
        except Exception:
            pass
    return sorted(pids)


def free_port(port: int) -> None:
    me = os.getpid()
    for pid in pids_on_port(port):
        if pid == me:
            continue
        try:
            if sys.platform.startswith("win"):
                subprocess.run(
                    ["taskkill", "/F", "/PID", str(pid)],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    check=False,
                )
            else:
                os.kill(pid, signal.SIGTERM)
        except Exception:
            pass

    for _ in range(20):
        if not port_in_use(port):
            return
        time.sleep(0.15)


def pick_port(preferred: int = 7860, fallbacks: int = 15) -> int:
    free_port(preferred)
    if not port_in_use(preferred):
        return preferred

    for offset in range(1, fallbacks + 1):
        candidate = preferred + offset
        free_port(candidate)
        if not port_in_use(candidate):
            return candidate

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


if __name__ == "__main__":
    port = pick_port(7860)
    url = f"http://127.0.0.1:{port}"
    share = ("--share" in sys.argv) or (os.environ.get("GRADIO_SHARE", "").strip() == "1")

    def open_when_ready() -> None:
        for _ in range(80):
            if port_in_use(port):
                webbrowser.open(url)
                return
            time.sleep(0.25)

    threading.Thread(target=open_when_ready, daemon=True).start()
    demo.launch(
        server_name="127.0.0.1",
        server_port=port,
        inbrowser=False,
        show_error=True,
        share=share,
    )
