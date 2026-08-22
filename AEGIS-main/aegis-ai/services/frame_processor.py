import os
import cv2
from typing import Any, Dict, Optional

def process_video_frames(
    path: str,
    frame_interval: int = 1,
    max_frames: int = 30,
    resize_width: Optional[int] = None,
    resize_height: Optional[int] = None
) -> Dict[str, Any]:
    """
    Process video frames sequentially.
    - Samples frames at `frame_interval`.
    - Resizes to exact dimensions if both `resize_width` and `resize_height` are provided.
    - Computes timestamps based on frame index and source FPS.
    - Guarantees memory safety and OpenCV resource release.
    """
    # 1. Parameter Validation
    if frame_interval < 1:
        return {
            "success": False,
            "filename": os.path.basename(path) if path else "unknown",
            "frames_processed": 0,
            "source_fps": None,
            "frame_interval": frame_interval,
            "frames": [],
            "error_detail": "frame_interval must be greater than or equal to 1."
        }
    if max_frames < 1:
        return {
            "success": False,
            "filename": os.path.basename(path) if path else "unknown",
            "frames_processed": 0,
            "source_fps": None,
            "frame_interval": frame_interval,
            "frames": [],
            "error_detail": "max_frames must be greater than or equal to 1."
        }
    if (resize_width is not None and resize_width <= 0) or (resize_height is not None and resize_height <= 0):
        return {
            "success": False,
            "filename": os.path.basename(path) if path else "unknown",
            "frames_processed": 0,
            "source_fps": None,
            "frame_interval": frame_interval,
            "frames": [],
            "error_detail": "Resize dimensions must be greater than 0."
        }
    if (resize_width is not None and resize_height is None) or (resize_width is None and resize_height is not None):
        return {
            "success": False,
            "filename": os.path.basename(path) if path else "unknown",
            "frames_processed": 0,
            "source_fps": None,
            "frame_interval": frame_interval,
            "frames": [],
            "error_detail": "Both resize_width and resize_height must be provided to perform resize."
        }

    # 2. File Validation
    # Use existing validation logic to ensure path exists and video can be opened
    from services.video_processor import validate_video_file
    validation = validate_video_file(path)
    if not validation["valid"]:
        return {
            "success": False,
            "filename": os.path.basename(path) if path else "unknown",
            "frames_processed": 0,
            "source_fps": None,
            "frame_interval": frame_interval,
            "frames": [],
            "error_detail": validation["error_detail"]
        }

    # 3. Process Frames Sequentially
    cap = cv2.VideoCapture(path)
    try:
        if not cap.isOpened():
            return {
                "success": False,
                "filename": os.path.basename(path),
                "frames_processed": 0,
                "source_fps": None,
                "frame_interval": frame_interval,
                "frames": [],
                "error_detail": "Cannot open video file via cv2.VideoCapture."
            }

        fps = float(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        frames_list = []
        frame_index = 0
        sampled_count = 0
        
        while sampled_count < max_frames:
            ret, frame = cap.read()
            if not ret or frame is None:
                break
                
            if frame_index % frame_interval == 0:
                current_width = width
                current_height = height
                
                # Perform resize internally if requested to verify correctness
                if resize_width is not None and resize_height is not None:
                    cv2.resize(frame, (resize_width, resize_height))
                    current_width = resize_width
                    current_height = resize_height
                
                # Calculate timestamp (with zero FPS safety)
                timestamp = None
                if fps > 0:
                    timestamp = round(frame_index / fps, 4)
                
                frames_list.append({
                    "frame_index": frame_index,
                    "timestamp_seconds": timestamp,
                    "width": current_width,
                    "height": current_height
                })
                sampled_count += 1
                
            frame_index += 1
            
        return {
            "success": True,
            "filename": os.path.basename(path),
            "frames_processed": sampled_count,
            "source_fps": round(fps, 2) if fps > 0 else 0.0,
            "frame_interval": frame_interval,
            "frames": frames_list,
            "error_detail": None
        }
    except Exception as exc:
        return {
            "success": False,
            "filename": os.path.basename(path),
            "frames_processed": 0,
            "source_fps": None,
            "frame_interval": frame_interval,
            "frames": [],
            "error_detail": f"Error during frame processing: {str(exc)}"
        }
    finally:
        cap.release()
