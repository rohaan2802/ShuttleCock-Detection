# Lightweight image for free Render (512MB). YOLOv8n + Gradio webcam demo.
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1

WORKDIR /app

# System libs for OpenCV headless
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --extra-index-url https://download.pytorch.org/whl/cpu \
    -r requirements.txt

COPY app.py .
COPY models/shuttle_yolov8n_best.pt ./models/shuttle_yolov8n_best.pt
COPY README.md .

# Render sets $PORT
EXPOSE 10000
CMD ["python", "app.py"]
