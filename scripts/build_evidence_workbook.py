"""Build the review workbook from repository CSVs and the preserved dataset ZIP."""
import argparse
import csv
import statistics
from collections import Counter
from pathlib import Path
from zipfile import ZipFile

from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "My Drive/ShuttleBot/runs/shuttle_train_v1/results.csv"
LOGS = {
    "Saved session": ROOT / "detection_log.csv",
    "Archived session": ROOT / "archive/original/detection_log.csv",
}
METRICS = {
    "Precision": "metrics/precision(B)",
    "Recall": "metrics/recall(B)",
    "mAP50": "metrics/mAP50(B)",
    "mAP50–95": "metrics/mAP50-95(B)",
}


def records(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def dataset_rows(path):
    with ZipFile(path) as archive:
        names = set(archive.namelist())
        for split in ("train", "valid", "test"):
            prefix = f"merged_dataset/{split}/"
            images = {Path(n).stem for n in names if n.startswith(prefix + "images/") and n.endswith(".jpg")}
            labels = {Path(n).stem for n in names if n.startswith(prefix + "labels/") and n.endswith(".txt")}
            if not images or images != labels:
                raise ValueError(f"{split} has unmatched images or labels")
            boxes = empty = 0
            for name in labels:
                lines = archive.read(f"{prefix}labels/{name}.txt").decode().splitlines()
                count = 0
                for line in lines:
                    fields = line.split()
                    if not fields:
                        continue
                    if len(fields) != 5 or fields[0] != "0":
                        raise ValueError(f"Invalid shuttle label in {split}/{name}")
                    x, y, width, height = map(float, fields[1:])
                    if not (0 <= x <= 1 and 0 <= y <= 1 and 0 < width <= 1 and 0 < height <= 1):
                        raise ValueError(f"Invalid normalized box in {split}/{name}")
                    count += 1
                boxes += count
                empty += count == 0
            yield split, len(images), len(labels), empty, boxes


def add_sheet(book, name, headers, rows):
    sheet = book.create_sheet(name)
    sheet.append(headers)
    for row in rows:
        sheet.append(row)
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    for cell in sheet[1]:
        cell.fill = PatternFill("solid", fgColor="164A45")
        cell.font = Font(color="FFFFFF", bold=True)
        cell.alignment = Alignment(wrap_text=True, vertical="center")
    sheet.row_dimensions[1].height = 32
    for index, column in enumerate(sheet.columns, 1):
        width = max(len(str(cell.value or "")) for cell in column)
        sheet.column_dimensions[get_column_letter(index)].width = min(85, max(16, width + 3))
    return sheet


def build(dataset, output):
    book = Workbook()
    book.remove(book.active)
    add_sheet(book, "Read me", ("Sheet", "Evidence and scope"), [
        ("Splits", "Counts read from the original YOLO ZIP. Empty labels are separate from annotation counts."),
        ("Epoch metrics", "All 50 saved training rows with validation scores, losses and learning rates."),
        ("Validation milestones", "Epoch 1, epoch 50 and the maximum recorded value for each metric."),
        ("Notebook test split", "Saved notebook output, 1,509 images and 1,493 boxes. No new full evaluation."),
        ("Session summary", "Descriptive figures from the two saved sessions. Detection share is not recall."),
        ("Decision counts", "Logged software decisions. PICK rows do not establish physical pickups."),
        ("Frame logs", "Saved CSV rows. FPS statistics describe only those sessions."),
    ])
    add_sheet(book, "Splits", ("Split", "Images", "Label files", "Empty labels", "Boxes"), dataset_rows(dataset))

    training = records(TRAIN)
    keys = list(training[0])
    epoch_sheet = add_sheet(book, "Epoch metrics", keys, (
        [int(row["epoch"]), *(float(row[key]) for key in keys[1:])] for row in training
    ))
    chart = LineChart()
    chart.title = "Saved validation scores by epoch"
    chart.x_axis.title = "Epoch"
    chart.y_axis.title = "Score"
    chart.add_data(Reference(epoch_sheet, min_row=1, min_col=6, max_col=9, max_row=51), titles_from_data=True)
    chart.set_categories(Reference(epoch_sheet, min_col=1, min_row=2, max_row=51))
    chart.width, chart.height = 25, 11
    epoch_sheet.add_chart(chart, "Q2")

    def milestones():
        for label, key in METRICS.items():
            peak = max(training, key=lambda row: float(row[key]))
            yield label, float(training[0][key]), float(training[-1][key]), int(peak["epoch"]), float(peak[key])

    add_sheet(book, "Validation milestones", ("Metric", "Epoch 1", "Epoch 50", "Peak epoch", "Peak value"), milestones())
    add_sheet(book, "Notebook test split", ("Images", "Boxes", *METRICS), [(1509, 1493, .829, .624, .708, .358)])

    summary, counts, frame_rows = [], {}, []
    actions = ("SEARCH", "TURN_LEFT", "TURN_RIGHT", "FORWARD", "PICK")
    for label, path in LOGS.items():
        frames = records(path)
        hits = [row for row in frames if row["detected"] == "1"]
        summary.append((label, len(frames), len(hits), len(hits)/len(frames),
                        statistics.median(float(row["fps"]) for row in frames),
                        statistics.median(float(row["confidence"]) for row in hits)))
        counts[label] = Counter(row["action"] for row in frames)
        frame_rows.extend((label, float(row["timestamp_s"]), int(row["frame_index"]), row["action"],
            int(row["detected"]), *(float(row[key]) for key in ("confidence", "target_cx", "target_cy",
                                                               "dx", "dy", "norm_area", "fps")))
            for row in frames)
    sheet = add_sheet(book, "Session summary", ("Session", "Frames", "Detected frames", "Detection share",
                                                "Median FPS", "Median detected confidence"), summary)
    for row in sheet.iter_rows(min_row=2, min_col=4, max_col=4):
        row[0].number_format = "0.00%"
    decisions = add_sheet(book, "Decision counts", ("Decision", *LOGS), (
        (action, *(counts[label][action] for label in LOGS)) for action in actions
    ))
    chart = BarChart()
    chart.title = "Logged guidance decisions"
    chart.y_axis.title = "Frames"
    chart.add_data(Reference(decisions, min_row=1, min_col=2, max_col=3, max_row=6), titles_from_data=True)
    chart.set_categories(Reference(decisions, min_col=1, min_row=2, max_row=6))
    decisions.add_chart(chart, "E2")
    add_sheet(book, "Frame logs", ("Session", "Timestamp (s)", "Frame", "Action", "Detected", "Confidence",
                                  "Center x", "Center y", "dx", "dy", "Normalized area", "FPS"), frame_rows)
    book.save(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "docs/shuttlebot-evidence.xlsx")
    args = parser.parse_args()
    build(args.dataset, args.output)

