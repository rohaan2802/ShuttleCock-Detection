import argparse  # argparse lets us read command-line options like --model and --conf.
import csv  # csv lets us write per-frame detection/action logs into a .csv file.
import time  # time provides timestamps to compute FPS and elapsed seconds.
from pathlib import Path  # Path gives safe file/folder path handling across OSes.

import cv2  # cv2 (OpenCV) handles webcam capture and drawing text/graphics on frames.
from ultralytics import YOLO  # YOLO class loads the trained model and runs detection.


def parse_args():  # parse_args() collects all user-configurable runtime settings.
    parser = argparse.ArgumentParser(description="Real-time shuttle detection with webcam")  # Create CLI parser with a short help description.
    parser.add_argument(  # Add --model argument so user can choose a custom .pt model file.
        "--model",  # --model is the CLI flag name.
        type=str,  # type=str means this argument must be a text path string.
        default="ShuttleBotRealtime/models/shuttle_yolov8n_best.pt",  # Default model path used when --model is not provided.
        help="Path to trained YOLO model (.pt)",  # Help text shown in --help output.
    )
    parser.add_argument(  # Add --camera-index argument to select webcam source index.
        "--camera-index",  # --camera-index is the CLI flag name for camera selection.
        type=int,  # type=int ensures the value is an integer like 0, 1, or 2.
        default=0,  # default=0 means use the primary/default webcam.
        help="Webcam index (0 for default camera)",  # Help text describing valid usage.
    )
    parser.add_argument(  # Add --conf argument to filter low-confidence detections.
        "--conf",  # --conf is the confidence threshold flag.
        type=float,  # type=float expects decimal values like 0.25 or 0.5.
        default=0.35,  # default=0.35 is a balanced threshold for this project.
        help="Confidence threshold (0 to 1)",  # Help text clarifies valid range.
    )
    parser.add_argument(  # Add --iou argument for Non-Max Suppression overlap threshold.
        "--iou",  # --iou is the NMS IoU threshold flag.
        type=float,  # type=float expects decimal overlap threshold values.
        default=0.5,  # default=0.5 is a common NMS IoU setting.
        help="NMS IoU threshold (0 to 1)",  # Help text clarifies parameter meaning.
    )
    parser.add_argument(  # Add --imgsz argument to control YOLO input resolution.
        "--imgsz",  # --imgsz is the inference image size flag.
        type=int,  # type=int expects integer size like 640.
        default=640,  # default=640 matches typical YOLO training/inference setup.
        help="Inference image size",  # Help text explains what this size controls.
    )
    parser.add_argument(  # Add --x-thresh argument for left/right action sensitivity.
        "--x-thresh",  # --x-thresh is pixel threshold around frame center.
        type=int,  # type=int expects an integer pixel value.
        default=40,  # default=40 means small center errors are tolerated.
        help="Horizontal pixel error threshold for turn decisions",  # Help text explains this control threshold.
    )
    parser.add_argument(  # Add --pick-area-thresh argument for PICK trigger distance.
        "--pick-area-thresh",  # --pick-area-thresh is normalized box-area threshold flag.
        type=float,  # type=float expects decimal area ratio value.
        default=0.08,  # default=0.08 means "pick" when object appears sufficiently large/near.
        help="Normalized bbox area threshold to trigger PICK",  # Help text explains when PICK activates.
    )
    parser.add_argument(  # Add --log-csv argument so user can choose log output path.
        "--log-csv",  # --log-csv is the output log file path flag.
        type=str,  # type=str expects a text file path string.
        default="detection_log.csv",  # default log file name in current working directory.
        help="CSV file path to store frame-wise action logs",  # Help text for CSV logging behavior.
    )
    return parser.parse_args()  # Parse command-line inputs and return them as args object.


def main():  # main() is the entry point containing camera loop and detection logic.
    args = parse_args()  # Read all CLI arguments once at startup.

    model_path = Path(args.model)  # Convert model path string to Path for existence checks and readability.
    if not model_path.exists():  # Validate that the .pt model file actually exists before running.
        raise FileNotFoundError(  # Raise clear error immediately if model path is wrong.
            f"Model file not found: {model_path}\n"  # Show missing path in error message.
            "Place your trained model at this path or pass --model with the correct path."  # Tell user exactly how to fix.
        )

    model = YOLO(str(model_path))  # Load YOLO model from .pt file (Path converted to str for library call).

    cap = cv2.VideoCapture(args.camera_index)  # Open camera stream using selected integer camera index.
    if not cap.isOpened():  # Check if camera opened successfully (permissions/index/camera availability).
        raise RuntimeError(  # Raise clear runtime error if camera cannot be opened.
            f"Could not open camera index {args.camera_index}. "  # Report attempted camera index.
            "Try --camera-index 1 (or 2) if you have multiple cameras."  # Provide practical fix for alternate camera IDs.
        )

    prev_time = time.time()  # Save previous frame timestamp to compute current FPS.
    start_time = prev_time  # Save session start time for elapsed-time logging.
    print("Press 'q' to quit.")  # Console instruction so user knows how to exit.

    log_path = Path(args.log_csv)  # Convert CSV path to Path for safe directory/file handling.
    if log_path.parent != Path("."):  # If user provided a folder path (not just filename), ensure folder exists.
        log_path.parent.mkdir(parents=True, exist_ok=True)  # Create parent directories recursively; ignore if they already exist.

    with log_path.open("w", newline="", encoding="utf-8") as log_file:  # Open CSV file in write mode with UTF-8 and clean newlines.
        writer = csv.writer(log_file)  # Create CSV writer object to append one row per frame.
        writer.writerow(  # Write CSV header row once to label each logged column.
            [
                "timestamp_s",  # Elapsed seconds from session start.
                "frame_index",  # Current frame number.
                "action",  # Action decision text (SEARCH/TURN_LEFT/etc.).
                "detected",  # 1 if shuttle detected, else 0.
                "confidence",  # Confidence score for selected detection.
                "target_cx",  # Detected target center x-coordinate in pixels.
                "target_cy",  # Detected target center y-coordinate in pixels.
                "dx",  # Horizontal error from frame center (target_x - center_x).
                "dy",  # Vertical error from frame center (target_y - center_y).
                "norm_area",  # Normalized bbox area (used as rough closeness estimate).
                "fps",  # Per-frame instantaneous FPS.
            ]
        )
        frame_idx = 0  # Initialize frame counter at zero for logging.

        while True:  # Infinite loop to process live webcam frames until user quits.
            ok, frame = cap.read()  # Read one frame; ok is success flag, frame is image array.
            if not ok:  # Handle camera read failures (disconnected camera, permission issues, etc.).
                print("Warning: Failed to read frame from camera.")  # Warn user about failed frame capture.
                break  # Exit loop if frame capture fails.

            results = model.predict(  # Run YOLO inference on current frame.
                source=frame,  # source=frame passes in-memory image directly (no file needed).
                conf=args.conf,  # conf threshold removes low-confidence detections.
                iou=args.iou,  # iou threshold controls NMS overlap suppression behavior.
                imgsz=args.imgsz,  # imgsz resizes input for model inference speed/accuracy tradeoff.
                device="cpu",  # device="cpu" runs inference on CPU (works without GPU).
                verbose=False,  # verbose=False keeps console output clean per frame.
            )

            result = results[0]  # Get first result because one frame produces one result object.
            annotated = result.plot()  # Create visualization frame with YOLO boxes/labels drawn.

            boxes = result.boxes  # Extract detection boxes object for coordinate/confidence access.
            h, w = annotated.shape[:2]  # Read frame height and width from annotated image array.
            frame_center = (w // 2, h // 2)  # Compute integer center point of frame.
            cv2.circle(annotated, frame_center, 5, (255, 0, 0), -1)  # Draw filled blue dot at frame center for control reference.

            target_text = "No shuttle detected"  # Default on-screen text when no detection exists.
            action_text = "SEARCH"  # Default action when no target is found.
            detected = 0  # Default detection flag for CSV (0 means no target).
            conf_val = 0.0  # Default confidence value used when no target exists.
            cx = -1  # Default target x-center when missing target.
            cy = -1  # Default target y-center when missing target.
            dx = 0  # Default x-error from center when missing target.
            dy = 0  # Default y-error from center when missing target.
            norm_area = 0.0  # Default normalized area when no box exists.
            if boxes is not None and len(boxes) > 0:  # Continue only if at least one box was detected.
                best_idx = int(boxes.conf.argmax().item())  # Pick index of highest-confidence detection.
                x1, y1, x2, y2 = boxes.xyxy[best_idx].tolist()  # Read selected box corners as pixel coordinates.
                cx = int((x1 + x2) / 2)  # Compute target center x from box corner coordinates.
                cy = int((y1 + y2) / 2)  # Compute target center y from box corner coordinates.
                conf_val = float(boxes.conf[best_idx].item())  # Read confidence value for selected target box.
                detected = 1  # Set detection flag to 1 because target was found.
                cv2.circle(annotated, (cx, cy), 6, (0, 255, 255), -1)  # Draw filled yellow dot at detected target center.
                cv2.line(annotated, frame_center, (cx, cy), (0, 255, 255), 2)  # Draw yellow line from frame center to target center.
                dx = cx - frame_center[0]  # Compute horizontal error for turn decisions.
                dy = cy - frame_center[1]  # Compute vertical error (informational for logging/debug).
                target_text = f"Target center: ({cx}, {cy})  Error(dx,dy): ({dx}, {dy})"  # Build overlay text with target/error values.

                bbox_area = max((x2 - x1) * (y2 - y1), 0.0)  # Compute non-negative pixel area of selected bounding box.
                norm_area = bbox_area / float(max(w * h, 1))  # Normalize area by frame area to estimate target closeness robustly.

                if norm_area >= args.pick_area_thresh and abs(dx) <= args.x_thresh:  # If target is close and centered enough, trigger PICK.
                    action_text = "PICK"  # Action for grasp/collect stage.
                elif dx < -args.x_thresh:  # If target is significantly left of center, rotate left.
                    action_text = "TURN_LEFT"  # Action text for left turn command.
                elif dx > args.x_thresh:  # If target is significantly right of center, rotate right.
                    action_text = "TURN_RIGHT"  # Action text for right turn command.
                else:  # Otherwise, target is roughly centered but not close enough.
                    action_text = "FORWARD"  # Move forward toward target.

            current_time = time.time()  # Capture current timestamp for FPS and elapsed-time calculations.
            fps = 1.0 / max(current_time - prev_time, 1e-6)  # Compute FPS safely (protect from divide-by-zero).
            prev_time = current_time  # Update previous timestamp for next frame's FPS.

            cv2.putText(  # Draw FPS text on top-left corner of frame.
                annotated,  # Image to draw onto.
                f"FPS: {fps:.1f}",  # Formatted text with one decimal precision.
                (10, 30),  # Pixel position (x=10, y=30) for text baseline.
                cv2.FONT_HERSHEY_SIMPLEX,  # Built-in OpenCV font style.
                0.8,  # Font scale (text size multiplier).
                (0, 255, 0),  # Text color in BGR format (green).
                2,  # Line thickness in pixels.
                cv2.LINE_AA,  # Anti-aliased line type for smoother text.
            )
            cv2.putText(  # Draw target center/error status text under FPS line.
                annotated,  # Image to draw onto.
                target_text,  # Dynamic text showing detection status and center error.
                (10, 60),  # Pixel position for second text line.
                cv2.FONT_HERSHEY_SIMPLEX,  # Same font for consistency.
                0.6,  # Slightly smaller font for longer text.
                (0, 255, 255),  # Text color in BGR format (yellow).
                2,  # Text thickness.
                cv2.LINE_AA,  # Anti-aliased text rendering.
            )
            cv2.putText(  # Draw selected control action text for simulation logic visualization.
                annotated,  # Image to draw onto.
                f"ACTION: {action_text}",  # Action string formatted with prefix.
                (10, 90),  # Pixel position for third text line.
                cv2.FONT_HERSHEY_SIMPLEX,  # Same font family.
                0.8,  # Font scale for action emphasis.
                (0, 165, 255),  # Text color in BGR format (orange).
                2,  # Text thickness.
                cv2.LINE_AA,  # Anti-aliased text style.
            )

            writer.writerow(  # Write one CSV row containing frame-level telemetry.
                [
                    round(current_time - start_time, 3),  # Elapsed time in seconds since start, rounded to 3 decimals.
                    frame_idx,  # Current frame index.
                    action_text,  # Chosen action command text.
                    detected,  # 1 or 0 detection flag.
                    round(conf_val, 4),  # Confidence rounded to 4 decimals.
                    cx,  # Target center x pixel (or -1 if none).
                    cy,  # Target center y pixel (or -1 if none).
                    dx,  # Horizontal error in pixels.
                    dy,  # Vertical error in pixels.
                    round(norm_area, 6),  # Normalized box area rounded for compact logs.
                    round(fps, 2),  # FPS rounded to 2 decimals.
                ]
            )
            frame_idx += 1  # Increment frame counter after logging current frame.

            cv2.imshow("Shuttle Bot - Real-time Detection", annotated)  # Show the live annotated output window.
            if cv2.waitKey(1) & 0xFF == ord("q"):  # Wait 1 ms for key input and exit if user presses 'q'.
                break  # Break loop to stop streaming and close gracefully.

    cap.release()  # Release webcam resource so other apps can use camera afterward.
    cv2.destroyAllWindows()  # Close all OpenCV GUI windows opened by this script.
    print(f"Saved action log: {log_path.resolve()}")  # Print absolute path of saved CSV log file.


if __name__ == "__main__":  # This condition is True only when script is run directly, not imported as a module.
    main()  # Start the full webcam detection pipeline.
