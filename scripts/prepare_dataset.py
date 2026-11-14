"""Extract the original YOLO dataset to a new directory with a portable config."""
import argparse
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from zipfile import ZipFile


def prepare(archive_path, destination):
    if destination.exists():
        raise FileExistsError(f"Destination already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(archive_path) as archive, TemporaryDirectory(dir=destination.parent) as temporary:
        for member in archive.infolist():
            name = PurePosixPath(member.filename)
            if (
                not name.parts or name.parts[0] != "merged_dataset"
                or ".." in name.parts or "\\" in member.filename or ":" in member.filename
            ):
                raise ValueError(f"Unexpected archive path: {member.filename}")
        archive.extractall(temporary)
        extracted = Path(temporary) / "merged_dataset"
        for split in ("train", "valid", "test"):
            images = {p.stem for p in (extracted / split / "images").glob("*.jpg")}
            labels = {p.stem for p in (extracted / split / "labels").glob("*.txt")}
            if not images or images != labels:
                raise ValueError(f"{split} must contain matching images and labels")
            print(f"{split}: {len(images)} labeled images")
        config = f'path: "{destination.resolve().as_posix()}"\n'
        config += "train: train/images\nval: valid/images\ntest: test/images\nnames:\n  0: shuttle\n"
        (extracted / "data_local.yaml").write_text(config, encoding="utf-8")
        extracted.rename(destination)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    prepare(args.archive, args.destination)
