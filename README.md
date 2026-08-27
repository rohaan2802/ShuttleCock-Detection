# ShuttleCock Detection (ShuttleBot)

**YOLOv8n** shuttlecock detector for an autonomous badminton **service robot** (ShuttleBot): Colab training notebook, exported weights, prediction runs, **real-time webcam** inference with left/right/PICK actions, a simulation script, and robotics design / viva notes for a **Raspberry Pi + Arduino** stack.

**Student ID:** i222327 · **Author:** Mohammad Rohaan · [rohaan2802](https://github.com/rohaan2802)

---

## Table of contents

1. [Project goal](#project-goal)
2. [ML pipeline (notebook)](#ml-pipeline-notebook)
3. [Training artifacts](#training-artifacts)
4. [Real-time detector (`realtime_detect.py`)](#real-time-detector-realtime_detectpy)
5. [Simulation](#simulation)
6. [Robotics context (Pi + Arduino)](#robotics-context-pi--arduino)
7. [Dataset](#dataset)
8. [Repository layout](#repository-layout)
9. [Install and run](#install-and-run)
10. [Viva highlights](#viva-highlights)
11. [Notes](#notes)

---

## Project goal

Detect a **shuttlecock** in camera frames so a court robot can steer and pick it up. Computer vision runs on a class-capable SBC (Raspberry Pi); **PID motor control** and encoders stay on Arduino. This repo is the **detection / ML** side plus design PDFs.

---

## ML pipeline (notebook)

`i222327_ML_FINALPROJECT.ipynb` (Colab + Google Drive):

1. Install Ultralytics + OpenCV; check GPU.  
2. Mount Drive; unzip the merged YOLO dataset.  
3. Inspect train/val/test splits; write dataset YAML.  
4. Fine-tune from `yolov8n.pt`.  
5. Copy `best.pt` → `shuttle_yolov8n_best.pt`.  
6. Predict on test images; log metrics.  
7. Plot box/cls/dfl loss, precision, recall, mAP50, mAP50-95.

---

## Training artifacts

| Path (Drive layout) | Contents |
|---------------------|----------|
| `My Drive/ShuttleBot/runs/shuttle_train_v1/` | `args.yaml`, `results.csv`, `weights/best.pt` |
| `My Drive/ShuttleBot/models/shuttle_yolov8n_best.pt` | Frozen export |
| `ShuttleBotRealtime/models/shuttle_yolov8n_best.pt` | Copy for the realtime script |
| `runs/predict_test_v1/` | Annotated test JPGs (large) |

`results.csv` is epoch-wise: train/val box, cls, dfl losses + P, R, mAP50, mAP50-95.  
`args.yaml` stores Ultralytics hyperparameters from the training run.

---

## Real-time detector (`realtime_detect.py`)

Webcam loop: YOLO detect → choose **action** from bbox vs frame center → overlay + CSV log.

| CLI flag | Default | Meaning |
|----------|---------|---------|
| `--model` | `ShuttleBotRealtime/models/shuttle_yolov8n_best.pt` | Weights |
| `--camera-index` | `0` | OpenCV device |
| `--conf` | `0.35` | Confidence gate |
| `--iou` | `0.5` | NMS IoU |
| `--imgsz` | `640` | Inference size |
| `--x-thresh` | `40` | Pixels from center before LEFT/RIGHT |
| `--pick-area-thresh` | `0.08` | Normalized bbox area → **PICK** (object near) |
| `--log-csv` | `detection_log.csv` | Per-frame log |

Typical actions: **LEFT / RIGHT / FORWARD / PICK / SEARCH** (exact labels in the draw/log loop). FPS is computed with `time`. Quit with the OpenCV window key used in `main()` (usually `q`).

`detection_log.csv` columns include timestamps, detections, and the chosen action (see header after first run).

---

## Simulation

`Simulation.py` — kinematics / collection simulation assets for the robot (pair with the design PDFs). Run after reading the file’s `if __name__` block for required windows or parameters.

---

## Robotics context (Pi + Arduino)

From `ML_A_#01_(Viva_Questions).txt` and the design PDFs:

| Topic | Design choice |
|-------|----------------|
| Why Pi + Arduino | Pi for ML/camera; Arduino for **real-time PID** + encoders |
| Why PID | Straight-line speed, less motor drift |
| Why not Jetson | Cost / power for an academic build |
| Grounding | Common GND between Pi and Arduino |
| Drop zone | Encoders and/or visual markers |
| Claimed detection | ~85–90% indoor with lighting control |
| Future | SLAM, AI accelerator, dock, multi-shuttle |

PDFs in the original repo: Shuttle Bot design/ML reports, mechanical design, assignment briefs, object-detection notes.

---

## Dataset

Note file: Kaggle [shuttle-badminton-photos](https://www.kaggle.com/datasets/ayushsinha731/shuttle-badminton-photos) plus a merged YOLO-format ZIP used in Colab.

---

## Repository layout

```text
ShuttleCock-Detection/
├── i222327_ML_FINALPROJECT.ipynb
├── realtime_detect.py
├── Simulation.py
├── detection_log.csv
├── results.csv
├── args.yaml
├── ML_A_#01_(Viva_Questions).txt
├── My_Drive_ShuttleBot_datasets_DataSet_Link.txt
├── ShuttleBotRealtime/models/shuttle_yolov8n_best.pt
└── My Drive/ShuttleBot/runs/{shuttle_train_v1,predict_test_v1}/
```

---

## Install and run 
 
```bash
pip install ultralytics opencv-python
```
 
Offline predict: 
 
```python
from ultralytics import YOLO
model = YOLO("ShuttleBotRealtime/models/shuttle_yolov8n_best.pt")
model.predict(source="images_or_video", conf=0.25, save=True)
```
 
Webcam: 
 
```bash
python realtime_detect.py --conf 0.35 --x-thresh 40 --pick-area-thresh 0.08
```
 
### Live web page (camera + coordinates only)
 
Dark Gradio UI — no database, no CSV. Uses the trained weights above.
 
```bash
pip install -r webapp/requirements.txt
python webapp/app.py
```
 
Then open `http://127.0.0.1:7860` and allow the camera. Details: [`webapp/README.md`](webapp/README.md).

**Free online host:** [Hugging Face Spaces](https://huggingface.co/new-space) — step-by-step: [`DEPLOY-HF.md`](DEPLOY-HF.md).
 
Retrain: open the notebook; retarget Drive paths for local runs. 

---

## Viva highlights

- Hybrid SBC + MCU: compute vs hard real-time.  
- PID + encoders vs open-loop motors.  
- Lighting and dataset quality dominate mAP.  
- Common ground and regulated 5 V / 12 V rails.  
- Do not clone `predict_test_v1` JPGs if you only need weights.

---

## Notes

Notebook paths assume Colab Drive. For a lean clone keep `models/` and `runs/shuttle_train_v1/weights/`.

---

## Author

**Mohammad Rohaan** — i222327 · [rohaan2802](https://github.com/rohaan2802)
