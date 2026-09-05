"""Export the desktop checkpoint to a self-contained browser ONNX model."""
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from model_config import MODEL_PATH, BROWSER_MODEL, BROWSER_IMAGE_SIZE

def main():
    from ultralytics import YOLO
    import onnx
    model = YOLO(str(MODEL_PATH))
    if len(model.names) != 1:
        raise ValueError("The browser decoder expects the single-class shuttlecock model.")
    exported = Path(model.export(format="onnx", imgsz=BROWSER_IMAGE_SIZE, batch=1,
        dynamic=False, simplify=False, opset=17, nms=False, device="cpu"))
    graph = onnx.load(str(exported))
    onnx.checker.check_model(graph)
    BROWSER_MODEL.parent.mkdir(parents=True, exist_ok=True)
    onnx.save_model(graph, str(BROWSER_MODEL), save_as_external_data=False)
    metadata = {"source": str(MODEL_PATH.relative_to(MODEL_PATH.parents[2])).replace('\\', '/'),
        "source_sha256": hashlib.sha256(MODEL_PATH.read_bytes()).hexdigest(),
        "onnx_sha256": hashlib.sha256(BROWSER_MODEL.read_bytes()).hexdigest(),
        "image_size": BROWSER_IMAGE_SIZE, "classes": model.names,
        "input": "RGB float32 NCHW / 255, letterbox padding 114", "opset": 17}
    BROWSER_MODEL.with_suffix('.json').write_text(json.dumps(metadata, indent=2)+'\n', encoding='utf-8')
    print(f"Browser model saved: {BROWSER_MODEL}")

if __name__ == '__main__':
    main()
