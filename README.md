# ShuttleCock Detection

YOLOv8-based shuttlecock detection for an autonomous badminton court service robot (ShuttleBot), including trained weights, prediction runs, real-time inference, simulation assets, and robotics design reports.

## Overview

Course / project repository combining computer vision and robotics systems design:

- Fine-tune Ultralytics YOLOv8n on shuttlecock imagery
- Export best weights for offline and real-time detection
- Document mechanical / ML design and viva answers for a Raspberry Pi + Arduino service robot

Student ID on artifacts: i222327.

## Highlights

| Component | Detail |
|-----------|--------|
| Detector | Ultralytics YOLOv8n |
| Best weights | `My Drive/ShuttleBot/models/shuttle_yolov8n_best.pt` (also `ShuttleBotRealtime/models/`) |
| Training run | `My Drive/ShuttleBot/runs/shuttle_train_v1/` (`args.yaml`, `results.csv`, `weights/best.pt`) |
| Predictions | `My Drive/ShuttleBot/runs/predict_test_v1/` (annotated test frames) |
| Notebook | `i222327_ML_FINALPROJECT.ipynb` |
| Real-time script | `realtime_detect.py` |
| Simulation | `Simulation.py` |
| Detection log | `detection_log.csv` |
| Dataset note | `My Drive/ShuttleBot/datasets/DataSet Link.txt` |
| Viva notes | `ML A #01 (Viva Questions).txt` |

## ML Pipeline (notebook)

1. Install ultralytics and OpenCV; confirm GPU
2. Mount Google Drive; extract merged YOLO dataset ZIP
3. Inspect splits; create / verify dataset YAML
4. Train from `yolov8n.pt`
5. Copy `best.pt` to `shuttle_yolov8n_best.pt`
6. Run prediction on test images; validate metrics
7. Plot training curves (loss, precision, recall, mAP)

`shuttle_train_v1/results.csv` stores epoch-wise box/cls/dfl losses plus precision, recall, mAP50, and mAP50-95.

## Robotics Context

Assignment PDFs, design reports, and viva notes describe a hybrid Raspberry Pi + Arduino shuttle-collection robot (Pi for camera / ML, Arduino for PID motor control). This README focuses on the detection / ML side.

## Notable Files

```
ShuttleCock-Detection/
├── i222327_ML_FINALPROJECT.ipynb
├── realtime_detect.py
├── Simulation.py
├── detection_log.csv
├── ML A #01 (Viva Questions).txt
├── Asg-1-Shuttle Bot-Robotics-Sp 2026.pdf
├── A#01_Sec_A.pdf
├── 787410299-Robotics-Assignment-1.pdf
├── Shuttle Bot ML Design.pdf
├── Shuttle Bot Design Report.pdf
├── Mechanical_Design_of_Service_Robot_for_Shuttlecock.pdf
├── Object Detection Models Explained.pdf
├── ShuttleBotRealtime/models/shuttle_yolov8n_best.pt
└── My Drive/ShuttleBot/
    ├── datasets/DataSet Link.txt
    ├── models/shuttle_yolov8n_best.pt
    └── runs/
        ├── shuttle_train_v1/
        └── predict_test_v1/
```

The repository is large mainly because of prediction JPGs under `predict_test_v1/`.

## Tech Stack

Python 3 · PyTorch (via Ultralytics) · YOLOv8 · OpenCV · NumPy · Matplotlib · pandas · Google Colab

## Getting Started

```bash
pip install ultralytics opencv-python
```

```python
from ultralytics import YOLO

model = YOLO("My Drive/ShuttleBot/models/shuttle_yolov8n_best.pt")
model.predict(source="path/to/images_or_video", conf=0.25, save=True)
```

```bash
python realtime_detect.py
```

Retrain with `i222327_ML_FINALPROJECT.ipynb` (update Drive / dataset paths for local runs).

## Notes

- Notebook paths assume the original Colab + Google Drive layout.
- For a lean clone, keep `models/` and `runs/shuttle_train_v1/weights/`; omit `predict_test_v1` images if needed.

## Author

Mohammad Rohaan — i222327 · [rohaan2802](https://github.com/rohaan2802)
