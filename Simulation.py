"""Run the canonical detector against a file or camera and save predictions."""
import argparse
from pathlib import Path

from model_config import MODEL_PATH, ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", default=str(ROOT / "docs/videos/simulation-demo.mp4"))
    parser.add_argument("--confidence", type=float, default=0.25)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    if not 0 <= args.confidence <= 1:
        parser.error("--confidence must be between 0 and 1")
    source = int(args.source) if args.source.isdecimal() else args.source
    if isinstance(source, str) and not Path(source).is_file():
        parser.error(f"Video file not found: {source}")
    from ultralytics import YOLO

    predictions = YOLO(str(MODEL_PATH)).predict(
        source=source, save=True, stream=True, conf=args.confidence, device=args.device,
        project=str(ROOT / ".test-output"), name="simulation"
    )
    output = None
    for prediction in predictions:
        output = prediction.save_dir
    print(f"Predictions saved to {output}" if output is not None else "No frames decoded.")


if __name__ == "__main__":
    main()
