"""Build publication figures from saved training artifacts and real ONNX output."""
from pathlib import Path
import csv
import json
import textwrap

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import onnxruntime as ort
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "My Drive/ShuttleBot/runs"
DEST = ROOT / "docs/figures"
PAPER, INK, ACCENT = "#f0f4fd", "#142641", "#224d8f"
items = []
FONT_DIR = Path(matplotlib.get_data_path()) / "fonts/ttf"


def add(title, caption, category, artwork):
    stem = f"{len(items)+1:02d}_" + title.lower().replace(" ", "_").replace("-", "_")
    canvas = Image.new("RGB", (1440, 900), PAPER)
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, 1440, 12), fill=ACCENT)
    draw.text((34, 29), category.upper(), font=ImageFont.truetype(str(FONT_DIR / "DejaVuSans-Bold.ttf"), 24), fill=ACCENT)
    draw.text((34, 59), title, font=ImageFont.truetype(str(FONT_DIR / "DejaVuSans-Bold.ttf"), 47), fill=INK)
    artwork = artwork.resize(ImageOps.contain(artwork, (1372, 678)).size, Image.Resampling.LANCZOS)
    x, y = (1440-artwork.width)//2, 124 + (678-artwork.height)//2
    canvas.paste(artwork.convert("RGB"), (x, y))
    draw.multiline_text((34, 815), textwrap.fill(caption, 106), spacing=6,
                        font=ImageFont.truetype(str(FONT_DIR / "DejaVuSans.ttf"), 24), fill=INK, stroke_width=1)
    canvas.save(DEST / f"full/{stem}.png")
    canvas.resize((960, 600), Image.Resampling.LANCZOS).save(DEST / f"preview/{stem}.webp", quality=97)
    items.append(dict(stem=stem, title=title, caption=caption, category=category))


def excerpt(title, caption, category, lines):
    panel = Image.new("RGB", (1372, 650), "#dfeaff")
    size = min(36, 2020 // max(map(len, lines)), 465 // len(lines))
    ImageDraw.Draw(panel).multiline_text((28, 29), "\n".join(lines), spacing=9,
        font=ImageFont.truetype(str(FONT_DIR / "DejaVuSansMono.ttf"), size), fill=INK, stroke_width=1)
    add(title, caption, category, panel)


def excerpt_source(title, caption, path, prefix, count):
    lines = (ROOT / path).read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith(prefix))
    lines = [part for line in lines[start:start+count] for part in textwrap.wrap(
        line, width=85, replace_whitespace=False, subsequent_indent="    ") or [""]]
    excerpt(title, caption, "Implementation", lines)


def artifact(title, caption, folder, filename):
    with Image.open(RUN / folder / filename) as img:
        artwork = img.convert("RGB")
        if img.format == "PNG":
            blank = Image.new("RGB", artwork.size, artwork.getpixel((0, 0)))
            bounds = ImageChops.difference(artwork, blank).getbbox()
            if bounds:
                artwork = artwork.crop(bounds)
            artwork = ImageOps.expand(artwork, border=18, fill="white")
        add(title, caption, "Training evidence", artwork)


def chart(title, caption, labels, keys, ylabel):
    with (RUN / "shuttle_train_v1/results.csv").open() as stream:
        rows = list(csv.DictReader(stream))
    fig, ax = plt.subplots(figsize=(13.72, 6.78), dpi=100, layout="constrained")
    for label, key in zip(labels, keys):
        ax.plot([int(row["epoch"]) for row in rows], [float(row[key]) for row in rows],
                linewidth=3.2, label=label)
    ax.set(xlabel="Epoch", ylabel=ylabel)
    ax.tick_params(labelsize=19)
    ax.xaxis.label.set_size(18)
    ax.yaxis.label.set_size(18)
    ax.spines[["right","top"]].set_visible(False)
    ax.set_facecolor("#f6f9ff")
    ax.grid(color="#577aae", alpha=.30)
    ax.legend(fontsize=19)
    for label in (*ax.get_xticklabels(), *ax.get_yticklabels()):
        label.set_fontweight("semibold")
    fig.canvas.draw()
    add(title, caption, "Training evidence", Image.fromarray(np.asarray(fig.canvas.buffer_rgba()).copy()))
    plt.close(fig)


def inference():
    source = ROOT / "docs/samples/test-shuttle.jpg"
    frame = cv2.imread(str(source))
    h, w = frame.shape[:2]
    scale = min(320/w, 320/h)
    nw, nh = round(w*scale), round(h*scale)
    left, top = round((320-nw)/2-.1), round((320-nh)/2-.1)
    padded = np.full((320, 320, 3), 114, dtype=np.uint8)
    padded[top:top+nh, left:left+nw] = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), (nw, nh))
    session = ort.InferenceSession(str(ROOT / "docs/models/shuttle.onnx"), providers=["CPUExecutionProvider"])
    tensor = np.ascontiguousarray(padded.transpose(2,0,1)[None], dtype=np.float32)/255
    output = session.run(None, {session.get_inputs()[0].name: tensor})[0][0]
    j = output[4].argmax()
    x, y, bw, bh, score = output[:,j]
    assert score >= .35
    a = (round((x-bw/2-left)/scale), round((y-bh/2-top)/scale))
    b = (round((x+bw/2-left)/scale), round((y+bh/2-top)/scale))
    # Keep the original context and give the small predicted box an enlarged inset.
    raw_frame = frame.copy()
    cv2.rectangle(frame, a, b, (20, 245, 210), 3)
    cv2.putText(frame, f"Shuttle {score:.0%}", (max(0, a[0]-8), max(22, a[1]-8)),
                cv2.FONT_HERSHEY_SIMPLEX, .7, (30, 240, 200), 2, cv2.LINE_AA)
    px, py = (a[0]+b[0])//2, (a[1]+b[1])//2
    radius = max(34, round(max(b[0]-a[0], b[1]-a[1]) * .85))
    left_crop, top_crop = max(0, px-radius), max(0, py-radius)
    crop = raw_frame[top_crop:min(h, py+radius), left_crop:min(w, px+radius)]
    inset = cv2.resize(crop, (515, 515), interpolation=cv2.INTER_CUBIC)
    fx, fy = 515/crop.shape[1], 515/crop.shape[0]
    cv2.rectangle(inset, (round((a[0]-left_crop)*fx), round((a[1]-top_crop)*fy)),
                  (round((b[0]-left_crop)*fx), round((b[1]-top_crop)*fy)), (20, 245, 210), 4)
    comparison = Image.new("RGB", (1372, 650), "#dbe6f7")
    original = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    original = original.resize(ImageOps.contain(original, (805, 595)).size, Image.Resampling.LANCZOS)
    original_x = 20 + (810-original.width)//2
    comparison.paste(original, (original_x, 46))
    comparison.paste(Image.fromarray(cv2.cvtColor(inset, cv2.COLOR_BGR2RGB)), (828, 46))
    label_font = ImageFont.truetype(str(FONT_DIR / "DejaVuSans-Bold.ttf"), 25)
    labels = ImageDraw.Draw(comparison)
    labels.text((original_x, 8), "Full test frame", font=label_font, fill=INK)
    labels.text((828, 8), "Enlarged detection", font=label_font, fill=INK)
    add("ONNX detection on a test image", "The original browser export predicts this box on a repository sample. The label shows its actual confidence.",
        "Inference", comparison)
    add("The letterboxed model input", "The same sample is resized with its aspect ratio intact, padded to 320 × 320, then normalized for inference.",
        "Inference", Image.fromarray(padded).resize((590,590)))
    excerpt("Detector output and coordinates", "The highest-confidence candidate is mapped back into original image coordinates.", "Inference",
            [f"Image size       {w} × {h}", f"Tensor input     {tensor.shape}",
             f"Raw output       {(1,*output.shape)}", f"Top confidence   {score:.4f}",
             f"Box corners      {a} to {b}", f"Box center       {((a[0]+b[0])/2,(a[1]+b[1])/2)}"])


def build():
    inference()
    chart("Precision and recall", "The original validation history records how precision and recall changed across training.",
          ["Precision","Recall"], ["metrics/precision(B)","metrics/recall(B)"], "Validation score")
    chart("Mean average precision", "mAP at IoU 0.50 and mAP averaged across IoU 0.50 to 0.95 measure different localization strictness.",
          ["mAP50","mAP50–95"], ["metrics/mAP50(B)","metrics/mAP50-95(B)"], "Validation score")
    for loss, label in [("box","Bounding box loss"),("cls","Classification loss"),("dfl","Distribution focal loss")]:
        chart(label,"Training and validation loss from the original 50-epoch run.",
              ["Training","Validation"],[f"train/{loss}_loss",f"val/{loss}_loss"], "Loss")
    for title, caption, folder, file in [
        ("Training label distribution","Saved training-run plot showing label locations and box sizes.","shuttle_train_v1","labels.jpg"),
        ("Precision recall curve","Saved threshold trade-off from the CPU evaluation artifacts.","val_test_cpu_v3","BoxPR_curve.png"),
        ("F1 confidence curve","Saved evaluation curve summarizes precision and recall at different confidence thresholds.","val_test_cpu_v3","BoxF1_curve.png"),
        ("Precision confidence curve","Precision changes as low-confidence candidates are removed.","val_test_cpu_v3","BoxP_curve.png"),
        ("Normalized confusion matrix","The evaluation artifact summarizes class and background results as proportions.","val_test_cpu_v3","confusion_matrix_normalized.png"),
        ("Evaluation confusion counts","The raw matrix uses counts and includes the background category.","val_test_cpu_v3","confusion_matrix.png"),
        ("Evaluation labels","The saved test mosaic shows the annotated boxes used for comparison.","val_test_cpu_v3","val_batch0_labels.jpg"),
        ("Evaluation predictions","The matching evaluation mosaic shows model predictions and confidence labels.","val_test_cpu_v3","val_batch0_pred.jpg"),
    ]:
        artifact(title,caption,folder,file)
    excerpt_source("Aspect ratio preserving resize","The browser keeps its letterbox scale and padding for coordinate restoration.",
                   "docs/detection.js","export function letterbox",4)
    excerpt_source("RGB input conversion","The browser transforms RGBA pixels into normalized planar RGB.",
                   "docs/detection.js","export function rgbTensor",5)
    excerpt_source("Confidence and box decoding","The decoder reads the candidate score and converts model-space boxes back into frame pixels.",
                   "docs/detection.js","  for (let i=0; i<n",6)
    excerpt_source("Suppressing overlapping candidates","Candidates are ranked by confidence and compared with already selected boxes.",
                   "docs/detection.js","  candidates.sort",7)
    excerpt_source("Browser runtime initialization","The live detector loads the local ONNX model and runs it with the vendored WebAssembly runtime.",
                   "docs/app.js","function session()",8)
    excerpt("Dataset split counts","Counts are taken from the preserved YOLO training archive. Each image has a corresponding text label.",
            "Training evidence",["Training images       10,816","Validation images      2,666",
                                 "Test images            1,509","Total                 14,991","Class                 shuttle"])
    excerpt("Final validation metrics","Epoch 50 values are from the training validation history and are separate from local inference checks.",
            "Training evidence",["Precision     0.74647","Recall        0.60796","mAP50         0.64776","mAP50-95      0.29328"])
    excerpt_source("Checkpoint export parity","The verification script compares raw CPU ONNX predictions to the PyTorch checkpoint within numeric tolerance.",
                   "tests/verify_export.py","    with torch.no_grad()",7)
    assert len(items)==24
    (DEST/"gallery.json").write_text(json.dumps(items,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")


if __name__ == "__main__":
    build()

