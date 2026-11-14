"""Reassemble the two published dataset parts and verify the original ZIP hash."""
import argparse
import hashlib
from pathlib import Path

NAME = "ShuttleCock_YOLO_Dataset.zip"
EXPECTED = "ebe15d48d331ff76ad2b6aae1415a01cd5423fbebee997eada765e44060718ef"


def join(parts_dir, output):
    parts = [parts_dir / f"{NAME}.part{index:02d}" for index in (1, 2)]
    if output.exists():
        raise FileExistsError(output)
    digest = hashlib.sha256()
    target = output.open("xb")
    try:
        with target:
            for part in parts:
                with part.open("rb") as source:
                    while chunk := source.read(8 * 1024 * 1024):
                        target.write(chunk)
                        digest.update(chunk)
        if digest.hexdigest() != EXPECTED:
            raise ValueError("Reconstructed ZIP has an unexpected SHA-256")
    except Exception:
        if output.exists():
            output.unlink()
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("parts_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    join(args.parts_dir, args.output)
    print(f"Verified dataset ZIP: {args.output}")
