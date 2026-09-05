"""One canonical trained checkpoint for all ShuttleBot entry points."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT / "ShuttleBotRealtime" / "models" / "shuttle_yolov8n_best.pt"
BROWSER_MODEL = ROOT / "docs" / "models" / "shuttle.onnx"
BROWSER_IMAGE_SIZE = 320
