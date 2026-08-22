import os
import cv2
from typing import Any, Dict, Optional

def validate_video_file(path: str) -> Dict[str, Any]:
    """
    Validate if a video file exists, can be opened by OpenCV,
    and contains readable video content.
    """
    if not path:
        return {"valid": False, "error_detail": "Empty file path provided."}
    
    if not os.path.exists(path):
        return {"valid": False, "error_detail": f"File does not exist."}
        
    if not os.path.isfile(path):
        return {"valid": False, "error_detail": f"Path is not a file."}

    cap = cv2.VideoCapture(path)
    try:
        if not cap.isOpened():
            return {"valid": False, "error_detail": "Cannot open video file via cv2.VideoCapture."}
            
        ret, frame = cap.read()
        if not ret or frame is None:
            return {"valid": False, "error_detail": "Video file is corrupt, empty, or unreadable."}
            
        return {"valid": True, "error_detail": None}
    except Exception as exc:
        return {"valid": False, "error_detail": f"Unexpected error opening video: {str(exc)}"}
    finally:
        cap.release()


def get_video_metadata(path: str) -> Dict[str, Any]:
    """
    Safely extract video metadata using OpenCV.
    Returns width, height, fps, frame_count, and duration in seconds.
    """
    validation = validate_video_file(path)
    if not validation["valid"]:
        return {
            "filename": os.path.basename(path) if path else "unknown",
            "readable": False,
            "width": None,
            "height": None,
            "fps": None,
            "frame_count": None,
            "duration_seconds": None,
            "error_detail": validation["error_detail"]
        }

    cap = cv2.VideoCapture(path)
    try:
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = float(cap.get(cv2.CAP_PROP_FPS))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        duration = 0.0
        if fps > 0:
            duration = round(frame_count / fps, 2)

        return {
            "filename": os.path.basename(path),
            "readable": True,
            "width": width,
            "height": height,
            "fps": round(fps, 2),
            "frame_count": frame_count,
            "duration_seconds": duration,
            "error_detail": None
        }
    except Exception as exc:
        return {
            "filename": os.path.basename(path),
            "readable": False,
            "width": None,
            "height": None,
            "fps": None,
            "frame_count": None,
            "duration_seconds": None,
            "error_detail": f"Failed extracting metadata: {str(exc)}"
        }
    finally:
        cap.release()


def read_video_frames(path: str, max_frames: int = 10) -> Dict[str, Any]:
    """
    Sequentially read up to max_frames frames without loading the entire video into memory.
    Guarantees resource release on success or failure.
    """
    validation = validate_video_file(path)
    if not validation["valid"]:
        return {
            "readable": False,
            "frames_read": 0,
            "max_frames_requested": max_frames,
            "error_detail": validation["error_detail"]
        }

    cap = cv2.VideoCapture(path)
    try:
        frames_read = 0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        while frames_read < max_frames:
            ret, frame = cap.read()
            if not ret or frame is None:
                break
            frames_read += 1
            
        return {
            "readable": True,
            "frames_read": frames_read,
            "max_frames_requested": max_frames,
            "frame_dimensions": {"width": width, "height": height} if frames_read > 0 else None,
            "error_detail": None
        }
    except Exception as exc:
        return {
            "readable": False,
            "frames_read": 0,
            "max_frames_requested": max_frames,
            "error_detail": f"Error during frame extraction: {str(exc)}"
        }
    finally:
        cap.release()
