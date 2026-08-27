"""
Live shuttlecock detection — camera only, no database, no file logging.
Works locally and on Hugging Face Spaces.
"""

from __future__ import annotations

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


def resolve_model_path() -> Path:
    for path in _CANDIDATES:
        if path.is_file():
            return path
    raise FileNotFoundError(
        "Detection model is missing. Refresh the page, or contact the site owner."
    )


def load_model() -> YOLO:
    global _model
    if _model is not None:
        return _model
    _model = YOLO(str(resolve_model_path()))
    return _model


def format_coordinates(result) -> str:
    boxes = result.boxes
    if boxes is None or len(boxes) == 0:
        return "No shuttlecock in view"

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


def detect(frame, confidence: float):
    if frame is None:
        return None, "Waiting for camera… Allow access when the browser asks."

    try:
        model = load_model()
    except FileNotFoundError as exc:
        return frame, str(exc)
    except Exception:
        return frame, "Could not start the detector. Refresh the page and try again."

    try:
        conf = float(confidence)
        conf = min(0.9, max(0.15, conf))
        results = model.predict(source=frame, conf=conf, imgsz=640, verbose=False)
        result = results[0]
        annotated_bgr = result.plot()
        annotated = cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB)
        return annotated, format_coordinates(result)
    except Exception:
        return frame, "Detection failed on this frame. Check lighting and try again."


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
            lines=5,
            interactive=False,
            placeholder="Coordinates appear here when a shuttlecock is found.",
        )
        confidence = gr.Slider(
            minimum=0.2,
            maximum=0.7,
            value=0.35,
            step=0.05,
            label="Detection sensitivity",
            info="Lower finds more (may include false alerts). Higher is stricter.",
        )

        camera.stream(
            fn=detect,
            inputs=[camera, confidence],
            outputs=[output, coords],
            time_limit=None,
            stream_every=0.2,
        )

    return blocks


demo = build_app()
demo.queue(max_size=2)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
