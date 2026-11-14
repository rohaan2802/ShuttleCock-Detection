<div align="center">

# ShuttleCock Detection

**Live shuttlecock localization for ShuttleBot using YOLOv8n, ONNX, and browser-side inference.**

[![Browser](https://img.shields.io/badge/Live%20detector-ONNX-2358a1?logo=googlechrome&logoColor=white&style=for-the-badge)](https://rohaan2802.github.io/ShuttleCock-Detection/)
[![Model](https://img.shields.io/badge/Model-YOLOv8n-265d69?logo=pytorch&logoColor=white&style=for-the-badge)](docs/models/shuttle.json)
[![Dataset](https://img.shields.io/badge/Dataset-YOLO-345e88?logo=databricks&logoColor=white&style=for-the-badge)](#dataset)
[![Tests](https://img.shields.io/badge/Checks-Decoder-375d43?logo=nodedotjs&logoColor=white&style=for-the-badge)](tests/detection.test.js)
[![Gallery](https://img.shields.io/badge/Gallery-24%20figures-564693?logoColor=white&style=for-the-badge)](#screenshots)

[![Camera and image modes](https://img.shields.io/badge/Input-Camera%20%26%20images-156358?logo=googlechrome&logoColor=white&style=for-the-badge)](#detector-workflow)
[![Inference code](https://img.shields.io/badge/Code-Browser%20inference-28495a?logo=javascript&logoColor=white&style=for-the-badge)](docs/app.js)
[![Training notebook](https://img.shields.io/badge/Notebook-Training%20%26%20evaluation-8c512f?logo=jupyter&logoColor=white&style=for-the-badge)](i222327_ML_FINALPROJECT.ipynb)
[![Simulation video](https://img.shields.io/badge/Video-ShuttleBot%20simulation-375b78?logo=youtube&logoColor=white&style=for-the-badge)](docs/videos/simulation-demo.mp4)

</div>

## Live Links

| What | Link |
| --- | --- |
| Repository | [https://github.com/rohaan2802/ShuttleCock-Detection](https://github.com/rohaan2802/ShuttleCock-Detection) |
| GitHub Pages | [https://rohaan2802.github.io/ShuttleCock-Detection/](https://rohaan2802.github.io/ShuttleCock-Detection/) |
| Dataset reference | [https://www.kaggle.com/datasets/ayushsinha731/shuttle-badminton-photos](https://www.kaggle.com/datasets/ayushsinha731/shuttle-badminton-photos) |

## Contents

- [Overview](#overview)
- [Detector Workflow](#detector-workflow)
- [What’s Inside](#whats-inside)
- [Project Breakdown](#project-breakdown)
- [Dataset](#dataset)
- [Setup](#setup)
- [Results](#results)
- [Project Evidence](#project-evidence)
- [CSV and Code Reference](#csv-and-code-reference)
- [Limitations](#limitations)
- [About the Author](#about-the-author)
- [Folder Structure](#folder-structure)
- [Screenshots](#screenshots)

## Overview

A single-class YOLOv8n model locates badminton shuttlecocks for the ShuttleBot robotics project. The browser loads its ONNX export and WebAssembly runtime from this site. Live camera frames and the bundled test image are processed on the device, and the camera starts only on request.

## Detector Workflow

Run `python app.py web`, then choose an input in the detector panel.

| Input | What it does |
| --- | --- |
| **Start camera** | Runs inference continuously on the selected camera. Use Pause, Stop camera, or Reset session to control the stream. |
| **Try test image** | Analyzes a bundled, unannotated test frame so a reviewer can see real boxes and coordinates immediately. |
| **Choose a local image** | Opens a JPEG, PNG or WebP image up to 20 MB. The browser decodes the file and runs inference on the device. |

Move the confidence slider to see which boxes pass the threshold. In still-image mode the detector runs the model once, then decodes the cached predictions again as you adjust the threshold. The browser shows milliseconds for a still image and processing FPS for the camera. Use **Save snapshot** to save the annotated frame locally.

The target center is measured in original frame pixels with the origin at the upper-left. Mirror preview changes how the frame is drawn, while telemetry still uses the original frame. The [sample provenance](docs/samples/source.txt) identifies the frame in the original test split. See the [browser controller](docs/app.js), [decoder](docs/detection.js), and [ONNX metadata](docs/models/shuttle.json).

## What’s Inside

The browser detector is in docs/. The desktop runner adds robot guidance and CSV logging. The Gradio app runs inference in Python. Training artifacts, the original reports and the simulation video document the wider project.

| File | Purpose |
| --- | --- |
| [docs/index.html](docs/index.html) | Pages entry point and live detector |
| [docs/app.js](docs/app.js) | Camera and local image inputs, cached predictions, model session and overlays |
| [docs/detection.js](docs/detection.js) | Letterboxing, normalized RGB tensor and box decoding |
| [docs/models/shuttle.onnx](docs/models/shuttle.onnx) | Browser model |
| [app.py](app.py) | Local launcher |
| [realtime_detect.py](realtime_detect.py) | Desktop detection, robot guidance and CSV logging |
| [webapp/app.py](webapp/app.py) | Gradio detector |
| [i222327_ML_FINALPROJECT.ipynb](i222327_ML_FINALPROJECT.ipynb) | Training and evaluation notebook |
| [My Drive/ShuttleBot/runs/shuttle_train_v1/results.csv](My%20Drive/ShuttleBot/runs/shuttle_train_v1/results.csv) | Saved epoch metrics |
| [tests/verify_export.py](tests/verify_export.py) | PyTorch and ONNX output parity |
| [archive/README.md](archive/README.md) | Original versions and dataset audit |

## Project Breakdown

The camera frame is resized with preserved aspect ratio into a padded 320 × 320 RGB tensor. The model produces 2,100 candidates. The decoder filters by confidence, suppresses overlapping detections, and maps the boxes back to the original frame. The UI shows the highest-confidence target center in camera pixels. The original training run used 640-pixel inputs for 50 epochs.

## Dataset

The preserved YOLO archive contains 14,991 images and matching label files: 10,816 training, 2,666 validation, and 1,509 test images. The full ZIP is supplied separately. Its original configuration contains a Kaggle path, so use the extraction helper for a portable local configuration.

See the [dataset manifest](archive/README.md#dataset) and [preparation helper](scripts/prepare_dataset.py).


### Reassemble the dataset ZIP

1. Download `ShuttleCock_YOLO_Dataset.zip.part01` and `ShuttleCock_YOLO_Dataset.zip.part02`. Keep both files in `ShuttleCock-Detection_Release`, next to the cloned repo.
2. Open PowerShell in the `ShuttleCock-Detection` repo and run:

   ```powershell
   python scripts/join_dataset.py ../ShuttleCock-Detection_Release ../ShuttleCock_YOLO_Dataset.zip
   ```

3. Wait for **Verified dataset ZIP**. The script joins the parts in order, verifies the original SHA-256, and saves `ShuttleCock_YOLO_Dataset.zip` next to the repo.
4. Extract the ZIP normally. To create a portable `data_local.yaml` for training, run:

   ```powershell
   python scripts/prepare_dataset.py ../ShuttleCock_YOLO_Dataset.zip ../ShuttleCock_YOLO_Dataset
   ```

[Download plain-text instructions](docs/dataset-reassembly.txt).

## Setup

Run the web launcher from the repository root and open localhost. Choose Start camera or Try test image for camera-free inference. The browser app requires JavaScript and WebAssembly, and camera access requires HTTPS or localhost.

```powershell
python app.py web --no-browser
# Open http://localhost:8000
npm test
```

For the desktop path, install `requirements-desktop.txt` and run `python app.py desktop --help`. For Gradio, install `webapp/requirements.txt` and run `python app.py gradio`. To rebuild the browser model and compare exports, install `requirements-export.txt` and run `python app.py export` followed by `python tests/verify_export.py`. See the [deployment guide](DEPLOY.md). For saved-video inference, run `python Simulation.py path/to/video.mp4` after installing the desktop requirements. Run `python scripts/build_figures.py` with OpenCV, ONNX Runtime, Matplotlib, NumPy and Pillow to rebuild the gallery.

## Results

The original epoch-50 validation history records precision 0.74647, recall 0.60796, mAP50 0.64776, and mAP50–95 0.29328. These saved scores describe the training run. The ONNX export was checked against PyTorch on three repository images, with maximum absolute raw-tensor difference 0.00048828125. The still-image demo runs the same browser model as the live camera.

- [Saved epoch metrics](My%20Drive/ShuttleBot/runs/shuttle_train_v1/results.csv)
- [Original simulation video](docs/videos/simulation-demo.mp4)
- [Shuttle Bot ML design](Shuttle%20Bot%20ML%20Design.pdf)

### How to read the scores

Precision measures how many predicted positives are correct. Recall measures how many annotated positives were found. mAP50 uses an intersection-over-union threshold of 0.50, while mAP50–95 averages over stricter thresholds as well. The difference between those scores matters for small objects, where moving a predicted box by a few pixels can substantially reduce overlap.

The browser smoke test covers deployment wiring and model execution on an example image. The training metrics summarize a separate validation run.

## Project Evidence

[Download the Excel workbook](docs/shuttlebot-evidence.xlsx) for all 50 training epochs, validation milestones, annotation counts, and both desktop frame logs. The workbook includes filters and charts. The original [epoch CSV](My%20Drive/ShuttleBot/runs/shuttle_train_v1/results.csv) and [desktop CSV](detection_log.csv) remain available for inspection.

### Dataset and annotation audit

The YOLO ZIP contains one class, `0 = shuttle`. Each image has a matching text file. A populated row stores class, center x, center y, width and height in normalized coordinates. Empty files contribute zero annotated boxes.

| Split | Images / label files | Empty labels | Annotated boxes |
| --- | ---: | ---: | ---: |
| Train | 10,816 | 385 | 10,680 |
| Validation | 2,666 | 96 | 2,612 |
| Test | 1,509 | 53 | 1,493 |
| Total | 14,991 | 534 | 14,785 |

The archive does not establish whether related frames from the same recording were grouped when splitting the data. See the [dataset audit](archive/README.md#dataset) for the ZIP checksum and portable extraction commands.

### Training, test results and model export

The recorded run fine-tuned pretrained YOLOv8n for 50 epochs with input size 640, batch size 16, seed 0 and automatic optimizer selection. The browser model uses an RGB input tensor of shape `[1, 3, 320, 320]`. Its output shape is `[1, 5, 2100]`, containing four box values and one class score per candidate. The browser reverses letterbox padding and scaling, clips boxes to the frame, and applies non-max suppression at IoU 0.50. The default confidence threshold is 0.35.

| Validation metric | Epoch 1 | Epoch 50 | Recorded peak |
| --- | ---: | ---: | --- |
| Precision | 0.39654 | 0.74647 | 0.76121 at epoch 44 |
| Recall | 0.18951 | 0.60796 | 0.60796 at epoch 50 |
| mAP50 | 0.15138 | 0.64776 | 0.64803 at epoch 49 |
| mAP50–95 | 0.05306 | 0.29328 | 0.29328 at epoch 50 |

The notebook's saved test evaluation reports **0.829 precision, 0.624 recall, 0.708 mAP50 and 0.358 mAP50–95** across **1,509 images and 1,493 annotated instances**. These scores belong to that saved test run. The browser parity checks used selected images, so full browser-resolution test-set accuracy remains unmeasured.

### Desktop guidance and saved frame logs

The desktop runner picks the highest-confidence detection and computes the center, signed pixel offset from frame center and normalized bounding-box area. It defaults to confidence 0.35, overlap threshold 0.50, input size 640, horizontal tolerance 40 px and pick area threshold 0.08.

| Decision | Condition |
| --- | --- |
| SEARCH | No box passes the detector threshold. |
| PICK | The selected box covers at least 8% of the frame and is within 40 px of horizontal center. |
| TURN_LEFT / TURN_RIGHT | The selected box center falls outside the horizontal tolerance. |
| FORWARD | The box is centered and below the pick area threshold. |

#### Saved session comparison

| Saved session | Rows | Detected rows | Median FPS | SEARCH / LEFT / RIGHT / FORWARD / PICK |
| --- | ---: | ---: | ---: | --- |
| Repository log | 3,153 | 56 | 5.30 | 3,097 / 27 / 19 / 9 / 1 |
| Archived log | 1,992 | 950 | 5.50 | 1,042 / 344 / 342 / 222 / 42 |

The logs store elapsed time, frame index, action, confidence, center pixels, signed offsets, normalized area and instantaneous FPS. They lack frame-by-frame ground truth and matched recording conditions, so detection counts describe the individual sessions. PICK records a software decision. The chassis, Raspberry Pi, camera and servo mechanism are described in the design report, and physical actuation remains unverified.

### Review the project end to end

1. Open the bundled test image and inspect the score, box and center coordinates.
2. Raise the confidence cutoff above the detected score. The overlay drops that candidate using the cached output.
3. Compare the notebook test metrics with the training history and desktop logs in the Excel workbook.
4. Watch the simulation to see the proposed motion sequence. The desktop CSV records software decisions during camera sessions.

### Reports, simulation and implementation

| Evidence | What it covers |
| --- | --- |
| [Robot design report](Shuttle%20Bot%20Design%20Report.pdf) | Proposed chassis, power, camera, Raspberry Pi and servo-based collection. |
| [ML design notes](Shuttle%20Bot%20ML%20Design.pdf) | Detection task, model options, proposed data acquisition and camera integration. |
| [Project slides](slides.pdf) | Dataset, preprocessing, training and evaluation summary. |
| [Training notebook](i222327_ML_FINALPROJECT.ipynb) | Colab training, checkpoint selection, test metrics and prediction workflow. |
| [Colab PDF](i222327_ML_FINALPROJECT.ipynb%20-%20Colab.pdf) | Readable export of the notebook. |
| [Simulation video](docs/videos/simulation-demo.mp4) | Recorded demonstration of the proposed robot workflow. |
| [Desktop runner](realtime_detect.py) | Webcam loop, guidance thresholds and frame logging. |
| [Browser controller](docs/app.js) and [decoder](docs/detection.js) | Camera and still-image state, ONNX inference, box recovery and overlay rendering. |
| [Export parity check](tests/verify_export.py) | Numerical comparison of PyTorch and ONNX tensors on selected images. |

The dataset release uses two files, approximately 1.50 GB and 654 MB. Join both by following the [dataset reconstruction instructions](archive/README.md#dataset). To regenerate the workbook, install `openpyxl` and run the [workbook builder](scripts/build_evidence_workbook.py) from the repository root.

```powershell
python scripts/build_evidence_workbook.py ../ShuttleCock_YOLO_Dataset.zip
```

## CSV and Code Reference

### Reading the CSV files

| File | Rows | Contents |
| --- | ---: | --- |
| [Training results](My%20Drive/ShuttleBot/runs/shuttle_train_v1/results.csv) | 50 | One row per epoch, with training and validation losses, validation scores, elapsed training time and learning rates for three parameter groups. |
| [Desktop session](detection_log.csv) | 3,153 | One row per processed webcam frame, including the detector output and selected guidance action. |
| [Archived desktop session](archive/original/detection_log.csv) | 1,992 | An earlier capture using the same column layout. |
| [Evidence workbook](docs/shuttlebot-evidence.xlsx) | 8 sheets | Split audit, epoch history, milestones, saved test scores and both frame logs in filterable sheets. |

In the training CSV, `train/*_loss` and `val/*_loss` record box localization, classification and distribution focal loss (DFL). The `metrics/*(B)` columns are bounding-box validation metrics. The `lr/pg0` through `lr/pg2` columns save optimizer learning rates. Read the metrics by epoch to trace progress, and use the workbook's peak-epoch table to compare each metric separately.

In the desktop logs, `timestamp_s` is elapsed session time and `frame_index` starts at zero. `detected` is 0 or 1. When it is 0, center coordinates use `-1`, and confidence, offsets and normalized area are zero. Filter to detected rows when analyzing target positions or confidence. `target_cx` and `target_cy` are frame pixels, `dx` and `dy` are signed offsets from the frame center, and `norm_area` is box area divided by frame area. `fps` is the desktop loop's per-frame estimate. A row describes one frame, so repeated action labels can belong to the same continuous event.

### Follow the code from input to output

| File | Role in the pipeline |
| --- | --- |
| [Launcher](app.py) | Serves the Pages folder over localhost or dispatches to desktop, Gradio, and export entry points. |
| [Browser controller](docs/app.js) | Starts and stops the source, reuses the WASM model session, renders overlays and handles snapshot downloads. The still-image path caches the raw output for threshold changes. |
| [Browser decoder](docs/detection.js) | Calculates letterbox padding, builds the normalized RGB tensor, maps boxes into original frame pixels, and suppresses overlapping detections. |
| [Desktop runner](realtime_detect.py) | Takes camera frames through Ultralytics YOLO, selects the strongest box, calculates a guidance action and writes CSV rows. Use `--log-csv` with a fresh path to preserve the saved sample log. |
| [Export script](scripts/export_browser_model.py) | Exports the canonical checkpoint to ONNX and writes input metadata and model checksums. |
| [Numerical parity check](tests/verify_export.py) | Reads selected saved inputs, runs the PyTorch and ONNX models, and compares raw tensors within tolerance. |
| [Browser checks](tests/browser_review.py) | Exercises themes, responsive navigation, gallery, still-image detection and simulated camera behavior. |

For local inference, start with `python app.py web` from the repo folder. The HTML file also supports a direct preview for project content, theme and gallery. The local server supplies the JavaScript modules and model files used by the detector.

## Limitations

Small and fast-moving shuttlecocks, clutter, lighting and motion blur can reduce confidence. Accuracy on one saved evaluation set cannot establish performance on every court or camera. WebAssembly speed depends on the device. The browser shows boxes and coordinates. Robot commands and CSV logging belong to the desktop application.

## Folder Structure

```text
docs/                     Pages app, ONNX, WASM, gallery, video
ShuttleBotRealtime/       Canonical PyTorch checkpoint
My Drive/ShuttleBot/      Saved training and evaluation artifacts
webapp/                   Gradio application
scripts/                  Export, dataset preparation, figure generation
tests/                    Decoder and model checks
archive/                  Earlier submission variants
```

## Screenshots

[1](#1-onnx-detection-on-a-test-image) · [2](#2-the-letterboxed-model-input) · [3](#3-detector-output-and-coordinates) · [4](#4-precision-and-recall) · [5](#5-mean-average-precision) · [6](#6-bounding-box-loss)

[7](#7-classification-loss) · [8](#8-distribution-focal-loss) · [9](#9-training-label-distribution) · [10](#10-precision-recall-curve) · [11](#11-f1-confidence-curve) · [12](#12-precision-confidence-curve)

[13](#13-normalized-confusion-matrix) · [14](#14-evaluation-confusion-counts) · [15](#15-evaluation-labels) · [16](#16-evaluation-predictions) · [17](#17-aspect-ratio-preserving-resize) · [18](#18-rgb-input-conversion)

[19](#19-confidence-and-box-decoding) · [20](#20-suppressing-overlapping-candidates) · [21](#21-browser-runtime-initialization) · [22](#22-dataset-split-counts) · [23](#23-final-validation-metrics) · [24](#24-checkpoint-export-parity)

### 1. ONNX detection on a test image

<p align="left"><a href="docs/figures/full/01_onnx_detection_on_a_test_image.png"><img src="docs/figures/preview/01_onnx_detection_on_a_test_image.webp" width="900" alt="ONNX detection on a test image"></a></p>

The original browser export predicts this box on a repository sample. The label shows its actual confidence.

### 2. The letterboxed model input

<p align="left"><a href="docs/figures/full/02_the_letterboxed_model_input.png"><img src="docs/figures/preview/02_the_letterboxed_model_input.webp" width="900" alt="The letterboxed model input"></a></p>

The same sample is resized with its aspect ratio intact, padded to 320 × 320, then normalized for inference.

### 3. Detector output and coordinates

<p align="left"><a href="docs/figures/full/03_detector_output_and_coordinates.png"><img src="docs/figures/preview/03_detector_output_and_coordinates.webp" width="900" alt="Detector output and coordinates"></a></p>

The highest-confidence candidate is mapped back into original image coordinates.

### 4. Precision and recall

<p align="left"><a href="docs/figures/full/04_precision_and_recall.png"><img src="docs/figures/preview/04_precision_and_recall.webp" width="900" alt="Precision and recall"></a></p>

The original validation history records how precision and recall changed across training.

### 5. Mean average precision

<p align="left"><a href="docs/figures/full/05_mean_average_precision.png"><img src="docs/figures/preview/05_mean_average_precision.webp" width="900" alt="Mean average precision"></a></p>

mAP at IoU 0.50 and mAP averaged across IoU 0.50 to 0.95 measure different localization strictness.

### 6. Bounding box loss

<p align="left"><a href="docs/figures/full/06_bounding_box_loss.png"><img src="docs/figures/preview/06_bounding_box_loss.webp" width="900" alt="Bounding box loss"></a></p>

Training and validation loss from the original 50-epoch run.

### 7. Classification loss

<p align="left"><a href="docs/figures/full/07_classification_loss.png"><img src="docs/figures/preview/07_classification_loss.webp" width="900" alt="Classification loss"></a></p>

Training and validation loss from the original 50-epoch run.

### 8. Distribution focal loss

<p align="left"><a href="docs/figures/full/08_distribution_focal_loss.png"><img src="docs/figures/preview/08_distribution_focal_loss.webp" width="900" alt="Distribution focal loss"></a></p>

Training and validation loss from the original 50-epoch run.

### 9. Training label distribution

<p align="left"><a href="docs/figures/full/09_training_label_distribution.png"><img src="docs/figures/preview/09_training_label_distribution.webp" width="900" alt="Training label distribution"></a></p>

Saved training-run plot showing label locations and box sizes.

### 10. Precision recall curve

<p align="left"><a href="docs/figures/full/10_precision_recall_curve.png"><img src="docs/figures/preview/10_precision_recall_curve.webp" width="900" alt="Precision recall curve"></a></p>

Saved threshold trade-off from the CPU evaluation artifacts.

### 11. F1 confidence curve

<p align="left"><a href="docs/figures/full/11_f1_confidence_curve.png"><img src="docs/figures/preview/11_f1_confidence_curve.webp" width="900" alt="F1 confidence curve"></a></p>

Saved evaluation curve summarizes precision and recall at different confidence thresholds.

### 12. Precision confidence curve

<p align="left"><a href="docs/figures/full/12_precision_confidence_curve.png"><img src="docs/figures/preview/12_precision_confidence_curve.webp" width="900" alt="Precision confidence curve"></a></p>

Precision changes as low-confidence candidates are removed.

### 13. Normalized confusion matrix

<p align="left"><a href="docs/figures/full/13_normalized_confusion_matrix.png"><img src="docs/figures/preview/13_normalized_confusion_matrix.webp" width="900" alt="Normalized confusion matrix"></a></p>

The evaluation artifact summarizes class and background results as proportions.

### 14. Evaluation confusion counts

<p align="left"><a href="docs/figures/full/14_evaluation_confusion_counts.png"><img src="docs/figures/preview/14_evaluation_confusion_counts.webp" width="900" alt="Evaluation confusion counts"></a></p>

The raw matrix uses counts and includes the background category.

### 15. Evaluation labels

<p align="left"><a href="docs/figures/full/15_evaluation_labels.png"><img src="docs/figures/preview/15_evaluation_labels.webp" width="900" alt="Evaluation labels"></a></p>

The saved test mosaic shows the annotated boxes used for comparison.

### 16. Evaluation predictions

<p align="left"><a href="docs/figures/full/16_evaluation_predictions.png"><img src="docs/figures/preview/16_evaluation_predictions.webp" width="900" alt="Evaluation predictions"></a></p>

The matching evaluation mosaic shows model predictions and confidence labels.

### 17. Aspect ratio preserving resize

<p align="left"><a href="docs/figures/full/17_aspect_ratio_preserving_resize.png"><img src="docs/figures/preview/17_aspect_ratio_preserving_resize.webp" width="900" alt="Aspect ratio preserving resize"></a></p>

The browser keeps its letterbox scale and padding for coordinate restoration.

### 18. RGB input conversion

<p align="left"><a href="docs/figures/full/18_rgb_input_conversion.png"><img src="docs/figures/preview/18_rgb_input_conversion.webp" width="900" alt="RGB input conversion"></a></p>

The browser transforms RGBA pixels into normalized planar RGB.

### 19. Confidence and box decoding

<p align="left"><a href="docs/figures/full/19_confidence_and_box_decoding.png"><img src="docs/figures/preview/19_confidence_and_box_decoding.webp" width="900" alt="Confidence and box decoding"></a></p>

The decoder reads the candidate score and converts model-space boxes back into frame pixels.

### 20. Suppressing overlapping candidates

<p align="left"><a href="docs/figures/full/20_suppressing_overlapping_candidates.png"><img src="docs/figures/preview/20_suppressing_overlapping_candidates.webp" width="900" alt="Suppressing overlapping candidates"></a></p>

Candidates are ranked by confidence and compared with already selected boxes.

### 21. Browser runtime initialization

<p align="left"><a href="docs/figures/full/21_browser_runtime_initialization.png"><img src="docs/figures/preview/21_browser_runtime_initialization.webp" width="900" alt="Browser runtime initialization"></a></p>

The live detector loads the local ONNX model and runs it with the vendored WebAssembly runtime.

### 22. Dataset split counts

<p align="left"><a href="docs/figures/full/22_dataset_split_counts.png"><img src="docs/figures/preview/22_dataset_split_counts.webp" width="900" alt="Dataset split counts"></a></p>

Counts are taken from the preserved YOLO training archive. Each image has a corresponding text label.

### 23. Final validation metrics

<p align="left"><a href="docs/figures/full/23_final_validation_metrics.png"><img src="docs/figures/preview/23_final_validation_metrics.webp" width="900" alt="Final validation metrics"></a></p>

Epoch 50 values are from the training validation history and are separate from local inference checks.

### 24. Checkpoint export parity

<p align="left"><a href="docs/figures/full/24_checkpoint_export_parity.png"><img src="docs/figures/preview/24_checkpoint_export_parity.webp" width="900" alt="Checkpoint export parity"></a></p>

The verification script compares raw CPU ONNX predictions to the PyTorch checkpoint within numeric tolerance.

## About the Author

Mohammad Rohaan developed ShuttleBot’s vision workflow as part of a machine learning and robotics project. His work spans fine-tuning a YOLOv8n detector, examining validation and test results, and connecting detections to desktop guidance rules. The browser demo makes the same trained checkpoint accessible through an ONNX export.

- **Training and evaluation** — [Colab notebook](i222327_ML_FINALPROJECT.ipynb) and [evidence workbook](docs/shuttlebot-evidence.xlsx)
- **Browser inference and robotics integration** — [browser controller](docs/app.js) and [desktop guidance code](realtime_detect.py)
- **Profile** — [Mohammad Rohaan on GitHub](https://github.com/rohaan2802)
