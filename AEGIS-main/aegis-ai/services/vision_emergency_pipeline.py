from typing import Any, Dict, Optional
from services.video_processor import get_video_metadata
from services.yolo_detector import detect_video_frames
from services.event_interpreter import interpret_detections
from services.vision_incident_adapter import vision_event_to_incident
from services.orchestrator import orchestrate_emergency
from services.severity_engine import predict_severity
from services.command_agent import generate_response_plan


def process_vision_incident_to_command(
    event_result: Dict[str, Any],
    camera_metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Coordinates the Phase 6.1 Vision Incident -> Severity -> Command pipeline.
    1. Converts a vision event to a structured incident.
    2. If no incident is created, returns a NO_INCIDENT_CREATED status response.
    3. If created, predicts incident severity using the existing Severity Engine.
    4. Generates a response plan using the existing Command Agent.
    5. Returns a unified nested dictionary.
    """
    # 1. Convert vision event to structured incident
    adapter_res = vision_event_to_incident(event_result, camera_metadata)

    if not adapter_res.get("incident_created", False):
        return {
            "incident_created": False,
            "incident": None,
            "severity": None,
            "command": None,
            "pipeline_status": "NO_INCIDENT_CREATED",
            "reason": adapter_res.get("reason", "Vision event did not meet the criteria for incident creation.")
        }

    incident = adapter_res["incident"]

    # 2. Predict severity using the existing Severity Engine
    severity_res = predict_severity(incident, allow_null_coords=True)

    # 3. Generate response plan using the existing Command Agent
    severity_level = severity_res["severity"]
    command_res = generate_response_plan(incident, severity_level, allow_null_coords=True)

    # 4. Construct unified response
    return {
        "incident_created": True,
        "incident": incident,
        "severity": severity_res,
        "command": command_res,
        "pipeline_status": "COMPLETED",
        "reason": "Vision-generated incident successfully processed through Severity Engine and Command Agent."
    }


def process_video_to_emergency(
    video_path: str,
    filename: str,
    camera_metadata: Optional[Dict[str, Any]] = None,
    frame_interval: int = 1,
    max_frames: int = 30,
    confidence_threshold: float = 0.25,
    resize_width: Optional[int] = None,
    resize_height: Optional[int] = None
) -> Dict[str, Any]:
    """
    Runs the complete E2E Vision -> Emergency Response pipeline.
    1. Validates the video file.
    2. Performs frame processing, sampling, and YOLO object detection.
    3. Interprets YOLO detections into a vision event.
    4. Deterministically maps the vision event to a structured incident.
    5. Coordinates the incident through the standard Multi-Agent Orchestrator.
    """
    # 1. Fetch metadata for validation/source_fps
    meta = get_video_metadata(video_path)
    if not meta.get("readable", False):
        raise ValueError(meta.get("error_detail") or "Invalid or unreadable video file.")

    source_fps = meta.get("fps", 0.0)

    # 2. Run object detection (sampling + YOLO)
    yolo_res = detect_video_frames(
        path=video_path,
        frame_interval=frame_interval,
        max_frames=max_frames,
        confidence_threshold=confidence_threshold,
        resize_width=resize_width,
        resize_height=resize_height
    )

    if not yolo_res.get("success", False):
        raise ValueError(yolo_res.get("error_detail") or "Failed to detect objects in video.")

    # 3. Interpret YOLO detections
    event_res = interpret_detections(yolo_res["detections"])

    # 4. Map event to structured incident
    adapter_res = vision_event_to_incident(event_res, camera_metadata)

    if not adapter_res.get("incident_created", False):
        return {
            "success": True,
            "incident_created": False,
            "pipeline_status": "NO_INCIDENT_CREATED",
            "reason": adapter_res.get("reason", "No significant event was detected.")
        }

    incident = adapter_res["incident"]

    # 5. Run incident through the standard Multi-Agent Orchestrator
    orchestration_res = orchestrate_emergency(incident, allow_null_coords=True)

    # 6. Build final response
    return {
        "success": True,
        "video": {
            "filename": filename,
            "frames_processed": yolo_res["frames_processed"],
            "source_fps": source_fps
        },
        "vision_event": event_res,
        "incident_created": True,
        "incident": incident,
        "emergency_response": {
            "severity": orchestration_res["severity"],
            "command": orchestration_res["command"],
            "ambulance": orchestration_res["ambulance"],
            "ambulance_status": orchestration_res["ambulance_status"],
            "hospital": orchestration_res["hospital"],
            "hospital_status": orchestration_res["hospital_status"],
            "resource_coordination": orchestration_res["resource_coordination"],
            "orchestration_status": orchestration_res["orchestration_status"]
        },
        "reasoning": orchestration_res["reasoning"],
        "decision_trace": orchestration_res["decision_trace"],
        "pipeline_status": "COMPLETED",
        "reason": "Vision input was processed through the complete AEGIS emergency response pipeline."
    }
