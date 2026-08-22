import os
import cv2
from typing import Any, Dict, List, Optional
from ultralytics import YOLO

# Global cached model singleton
_model = None

def load_yolo_model() -> YOLO:
    """
    Load the pretrained YOLO detection model once globally and cache it.
    Attempts yolo11n.pt first, falling back to yolov8n.pt if unsupported.
    """
    global _model
    if _model is None:
        try:
            _model = YOLO("yolo11n.pt")
        except Exception:
            _model = YOLO("yolov8n.pt")
    return _model


def detect_objects(frame: Any, confidence_threshold: float = 0.25) -> List[Dict[str, Any]]:
    """
    Perform object detection on a single OpenCV numpy frame.
    Returns detected class ID, class name, confidence, and bounding box.
    """
    if not (0.0 <= confidence_threshold <= 1.0):
        raise ValueError("Confidence threshold must be between 0.0 and 1.0.")

    model = load_yolo_model()
    # Perform CPU native inference, disabling verbose logging to keep output clean
    results = model(frame, conf=confidence_threshold, verbose=False)
    detections = []
    
    if not results:
        return detections

    result = results[0]
    boxes = result.boxes
    if boxes is not None:
        for box in boxes:
            xyxy = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])
            cls_name = model.names[cls_id]

            detections.append({
                "class_id": cls_id,
                "class_name": cls_name,
                "confidence": round(conf, 4),
                "bbox": {
                    "x1": round(xyxy[0], 2),
                    "y1": round(xyxy[1], 2),
                    "x2": round(xyxy[2], 2),
                    "y2": round(xyxy[3], 2)
                }
            })
    return detections


def detect_video_frames(
    path: str,
    frame_interval: int = 1,
    max_frames: int = 30,
    confidence_threshold: float = 0.25,
    resize_width: Optional[int] = None,
    resize_height: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run YOLO object detection on sequentially sampled video frames.
    - Samples frames at `frame_interval`.
    - Restricts analysis to `max_frames`.
    - Resizes frames when specified.
    - Guarantees memory safety and OpenCV resource release.
    """
    # 1. Parameter Validation
    if frame_interval < 1:
        return {
            "success": False,
            "filename": os.path.basename(path) if path else "unknown",
            "model": None,
            "frames_processed": 0,
            "detections": [],
            "error_detail": "frame_interval must be greater than or equal to 1."
        }
    if max_frames < 1:
        return {
            "success": False,
            "filename": os.path.basename(path) if path else "unknown",
            "model": None,
            "frames_processed": 0,
            "detections": [],
            "error_detail": "max_frames must be greater than or equal to 1."
        }
    if not (0.0 <= confidence_threshold <= 1.0):
        return {
            "success": False,
            "filename": os.path.basename(path) if path else "unknown",
            "model": None,
            "frames_processed": 0,
            "detections": [],
            "error_detail": "confidence_threshold must be between 0.0 and 1.0."
        }
    if (resize_width is not None and resize_width <= 0) or (resize_height is not None and resize_height <= 0):
        return {
            "success": False,
            "filename": os.path.basename(path) if path else "unknown",
            "model": None,
            "frames_processed": 0,
            "detections": [],
            "error_detail": "Resize dimensions must be greater than 0."
        }
    if (resize_width is not None and resize_height is None) or (resize_width is None and resize_height is not None):
        return {
            "success": False,
            "filename": os.path.basename(path) if path else "unknown",
            "model": None,
            "frames_processed": 0,
            "detections": [],
            "error_detail": "Both resize_width and resize_height must be provided together."
        }

    # 2. File Validation
    from services.video_processor import validate_video_file
    validation = validate_video_file(path)
    if not validation["valid"]:
        return {
            "success": False,
            "filename": os.path.basename(path) if path else "unknown",
            "model": None,
            "frames_processed": 0,
            "detections": [],
            "error_detail": validation["error_detail"]
        }

    # 3. Load Model weights
    try:
        model = load_yolo_model()
        model_name = getattr(model, "ckpt_path", None)
        if model_name:
            model_name = os.path.basename(model_name)
        else:
            model_name = "YOLO (pretrained)"
    except Exception as exc:
        return {
            "success": False,
            "filename": os.path.basename(path),
            "model": None,
            "frames_processed": 0,
            "detections": [],
            "error_detail": f"Failed to load YOLO model weights: {str(exc)}"
        }

    # 4. Sequentially process frames
    cap = cv2.VideoCapture(path)
    try:
        if not cap.isOpened():
            return {
                "success": False,
                "filename": os.path.basename(path),
                "model": model_name,
                "frames_processed": 0,
                "detections": [],
                "error_detail": "Cannot open video file via cv2.VideoCapture."
            }

        fps = float(cap.get(cv2.CAP_PROP_FPS))
        
        detection_results = []
        frame_index = 0
        sampled_count = 0

        while sampled_count < max_frames:
            ret, frame = cap.read()
            if not ret or frame is None:
                break

            if frame_index % frame_interval == 0:
                # Perform optional resize
                if resize_width is not None and resize_height is not None:
                    frame = cv2.resize(frame, (resize_width, resize_height))

                # Run object detection
                frame_dets = detect_objects(frame, confidence_threshold=confidence_threshold)

                # Calculate timestamp
                timestamp = None
                if fps > 0:
                    timestamp = round(frame_index / fps, 4)

                detection_results.append({
                    "frame_index": frame_index,
                    "timestamp_seconds": timestamp,
                    "detections": frame_dets
                })
                sampled_count += 1

            frame_index += 1

        return {
            "success": True,
            "filename": os.path.basename(path),
            "model": model_name,
            "frames_processed": sampled_count,
            "detections": detection_results,
            "error_detail": None
        }
    except Exception as exc:
        return {
            "success": False,
            "filename": os.path.basename(path),
            "model": model_name,
            "frames_processed": 0,
            "detections": [],
            "error_detail": f"Error during object detection: {str(exc)}"
        }
    finally:
        cap.release()
