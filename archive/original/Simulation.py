from ultralytics import YOLO

# Load your trained model
model = YOLO("shuttle_yolov8n_best.pt")

# Run on video
results = model.predict(
    source="test-vid.mp4",  # or 0 for webcam
    save=True,                 # saves output video automatically
    conf=0.25                  # confidence threshold
)