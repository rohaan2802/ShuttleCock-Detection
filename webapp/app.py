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
from ultralytics import YOLO

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

# Prefer local webapp/models (HF Space), then repo weights path.
_CANDIDATES = [
    HERE / "models" / "shuttle_yolov8n_best.pt",
    ROOT / "ShuttleBotRealtime" / "models" / "shuttle_yolov8n_best.pt",
]

_model: YOLO | None = None

# Continuous no-shuttle before camera stops (avoids flicker on 1–2 frames).
NO_DETECT_BEFORE_STOP_SEC = 2.0
# Status / error text stays visible this long, then clears.
MESSAGE_VISIBLE_SEC = 5.0

MSG_NO_SHUTTLE = "No detection of shuttle"
MSG_WAIT_CAMERA = "Waiting for camera… Allow access when the browser asks."
MSG_MODEL_MISSING = (
    "Detection model is missing. Refresh the page, or contact the site owner."
)
MSG_MODEL_FAIL = "Could not start the detector. Refresh the page and try again."
MSG_DETECT_FAIL = "Detection failed on this frame. Check lighting and try again."

STOP_CAMERA_SCRIPT = """
<script>
(function () {
  document.querySelectorAll("video").forEach(function (video) {
    var stream = video.srcObject;
    if (!stream) return;
    stream.getTracks().forEach(function (track) { track.stop(); });
    video.srcObject = null;
  });
})();
</script>
"""


def resolve_model_path() -> Path:
    for path in _CANDIDATES:
        if path.is_file():
            return path
    raise FileNotFoundError(MSG_MODEL_MISSING)


def load_model() -> YOLO:
    global _model
    if _model is not None:
        return _model
    _model = YOLO(str(resolve_model_path()))
    return _model


def format_coordinates(result) -> str:
    boxes = result.boxes
    lines: list[str] = []
    for i, box in enumerate(boxes, start=1):
        x1, y1, x2, y2 = (float(v) for v in box.xyxy[0].tolist())
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0
        confidence = float(box.conf[0]) * 100.0
        lines.append(
            f"#{i}  center ({cx:.0f}, {cy:.0f})  "
            f"box ({x1:.0f}, {y1:.0f}) → ({x2:.0f}, {y2:.0f})  "
            f"{confidence:.0f}%"
        )
    return "\n".join(lines)


def status_html(message: str, *, stop_camera: bool = False) -> str:
    if not message and not stop_camera:
        return ""
    stop = STOP_CAMERA_SCRIPT if stop_camera else ""
    if not message:
        return stop
    return (
        f'<div class="status-banner">{message}</div>'
        f"{stop}"
    )


def detect(frame, confidence: float, miss_since: float | None, camera_armed: bool):
    """
    Returns:
      annotated image, coordinates, status HTML, miss_since, camera_armed, timer_active
    """
    if not camera_armed:
        return None, "", "", miss_since, False, gr.update()

    if frame is None:
        return (
            None,
            "",
            status_html(MSG_WAIT_CAMERA),
            None,
            True,
            gr.update(active=True),
        )

    try:
        model = load_model()
    except FileNotFoundError as exc:
        return (
            frame,
            "",
            status_html(str(exc), stop_camera=True),
            None,
            False,
            gr.update(active=True),
        )
    except Exception:
        return (
            frame,
            "",
            status_html(MSG_MODEL_FAIL, stop_camera=True),
            None,
            False,
            gr.update(active=True),
        )

    try:
        conf = float(confidence)
        conf = min(0.9, max(0.15, conf))
        results = model.predict(source=frame, conf=conf, imgsz=640, verbose=False)
        result = results[0]
        boxes = result.boxes
        found = boxes is not None and len(boxes) > 0
        annotated_bgr = result.plot()
        annotated = cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB)
    except Exception:
        return (
            frame,
            "",
            status_html(MSG_DETECT_FAIL, stop_camera=True),
            None,
            False,
            gr.update(active=True),
        )

    if found:
        return annotated, format_coordinates(result), "", None, True, gr.update()

    now = time.time()
    started = now if miss_since is None else miss_since
    if now - started < NO_DETECT_BEFORE_STOP_SEC:
        # Still live — keep camera on; no lasting text yet.
        return annotated, "", "", started, True, gr.update()

    # No shuttle for long enough → stop camera + show message for 5s.
    return (
        None,
        "",
        status_html(MSG_NO_SHUTTLE, stop_camera=True),
        None,
        False,
        gr.update(active=True),
    )


CUSTOM_CSS = """
:root {
  --body-bg: #0b0f14;
}
.gradio-container {
  max-width: 1100px !important;
  margin: 0 auto !important;
  font-family: "Segoe UI", system-ui, sans-serif !important;
}
footer { display: none !important; }
.status-banner {
  margin: 0.75rem 0 0;
  padding: 0.9rem 1.1rem;
  border-radius: 10px;
  background: #1a2332;
  border: 1px solid #334155;
  color: #f8fafc;
  font-size: 1.05rem;
  font-weight: 600;
  text-align: center;
}
"""

theme = gr.themes.Base(
    primary_hue="teal",
    secondary_hue="slate",
    neutral_hue="slate",
    font=gr.themes.GoogleFont("DM Sans"),
).set(
    body_background_fill="#0b0f14",
    body_background_fill_dark="#0b0f14",
    block_background_fill="#121821",
    block_background_fill_dark="#121821",
    block_border_color="#1e293b",
    block_label_text_color="#e2e8f0",
    body_text_color="#e2e8f0",
    button_primary_background_fill="#0d9488",
    button_primary_background_fill_hover="#14b8a6",
    button_primary_text_color="#04110f",
    border_color_primary="#334155",
    input_background_fill="#0f172a",
)


def build_app() -> gr.Blocks:
    with gr.Blocks(title="Shuttlecock Detection", theme=theme, css=CUSTOM_CSS) as blocks:
        gr.Markdown(
            """
            # Shuttlecock Detection
            Allow camera access, then hold a shuttlecock in view. Boxes and coordinates update live.
            """
        )

        miss_since = gr.State(None)
        camera_armed = gr.State(True)

        with gr.Row(equal_height=True):
            camera = gr.Image(
                sources=["webcam"],
                streaming=True,
                type="numpy",
                label="Live camera",
                mirror_webcam=True,
            )
            output = gr.Image(label="Detection", type="numpy")

        coords = gr.Textbox(
            label="Coordinates",
            lines=4,
            interactive=False,
            placeholder="Coordinates appear here when a shuttlecock is found.",
        )
        status = gr.HTML(value="")
        msg_timer = gr.Timer(value=MESSAGE_VISIBLE_SEC, active=False)

        confidence = gr.Slider(
            minimum=0.2,
            maximum=0.7,
            value=0.35,
            step=0.05,
            label="Detection sensitivity",
            info="Lower finds more (may include false alerts). Higher is stricter.",
        )
        restart = gr.Button("Start camera again", variant="primary")

        camera.stream(
            fn=detect,
            inputs=[camera, confidence, miss_since, camera_armed],
            outputs=[output, coords, status, miss_since, camera_armed, msg_timer],
            time_limit=None,
            stream_every=0.2,
        )

        def clear_status():
            return "", gr.update(active=False)

        msg_timer.tick(fn=clear_status, outputs=[status, msg_timer])

        def restart_camera():
            return True, None, "", None, ""

        restart.click(
            fn=restart_camera,
            outputs=[camera_armed, miss_since, status, output, coords],
        )

    return blocks


demo = build_app()
demo.queue(max_size=2)


def port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.4)
        return sock.connect_ex((host, port)) == 0


def pids_on_port(port: int) -> list[int]:
    """Return PIDs listening on the given TCP port (Windows + Unix)."""
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
    """Stop whatever is holding the port so launch does not fail."""
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
    """Prefer preferred port (freeing it). If still blocked, use the next free one."""
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
    )
