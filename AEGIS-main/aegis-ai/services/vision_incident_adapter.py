import os
import datetime
from typing import Any, Dict, Optional
from services.incident_detection import process_incident

# Event mapping configuration
EVENT_TYPE_MAPPING = {
    "POSSIBLE_ROAD_INCIDENT": "ROAD_ACCIDENT",
    "POSSIBLE_FIRE_EVENT": "FIRE",
    "POSSIBLE_CROWD_EVENT": "CROWD_EVENT"
}


def vision_event_to_incident(
    event_result: Dict[str, Any],
    camera_metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Converts a deterministic vision event into a system-compatible incident.
    - Preserves null coordinates when genuinely missing.
    - Never fabricates casualties or road blockage.
    - Maps POSSIBLE_ROAD_INCIDENT -> ROAD_ACCIDENT.
    - Maps POSSIBLE_FIRE_EVENT -> FIRE.
    - Maps POSSIBLE_CROWD_EVENT -> CROWD_EVENT.
    - Reuses centralized incident ID generation and validation from services/incident_detection.py.
    """
    if not isinstance(event_result, dict):
        return {
            "incident_created": False,
            "incident": None,
            "reason": "Invalid event input structure: expected dictionary."
        }

    event_type = event_result.get("event_type")
    
    if event_type == "NO_SIGNIFICANT_EVENT":
        vision_context = {
            "event_type": "NO_SIGNIFICANT_EVENT",
            "event_score": event_result.get("event_score", 0),
            "frames_analyzed": event_result.get("frames_analyzed", 0)
        }
        if camera_metadata and "camera_id" in camera_metadata:
            vision_context["camera_id"] = camera_metadata["camera_id"]
        return {
            "incident_created": False,
            "incident": None,
            "vision_context": vision_context,
            "reason": "No significant vision event detected; no incident was created."
        }
        
    if event_type not in EVENT_TYPE_MAPPING:
        return {
            "incident_created": False,
            "incident": None,
            "reason": f"Unsupported or unknown vision event type: '{event_type}'."
        }

    mapped_type = EVENT_TYPE_MAPPING[event_type]

    # Extract coordinates from metadata
    latitude = None
    longitude = None
    if camera_metadata:
        latitude = camera_metadata.get("latitude")
        longitude = camera_metadata.get("longitude")

    # Extract counts
    object_summary = event_result.get("object_summary", {})
    vehicles_count = 0
    if mapped_type == "ROAD_ACCIDENT" and object_summary:
        vehicles_count = int(object_summary.get("vehicles", 0))

    # Construct raw incident data for standard verification
    raw_incident = {
        "incident_type": mapped_type,
        "latitude": latitude,
        "longitude": longitude,
        "casualties": 0,  # Factual safety rule: never infer casualties
        "fire": mapped_type == "FIRE",
        "road_blocked": False,  # Factual safety rule: never assume road blockage
        "vehicles": vehicles_count,
        "source": "VISION"
    }

    try:
        # Run validations and normalization using the centralized detection module
        processed = process_incident(raw_incident, allow_null_coords=True)
    except ValueError as e:
        return {
            "incident_created": False,
            "incident": None,
            "reason": f"Incident validation failed: {str(e)}"
        }

    # Construct vision context metadata
    vision_context = {
        "event_type": event_type,
        "event_score": event_result.get("event_score"),
        "frames_analyzed": event_result.get("frames_analyzed")
    }
    if camera_metadata and "camera_id" in camera_metadata:
        vision_context["camera_id"] = camera_metadata["camera_id"]

    return {
        "incident_created": True,
        "incident": processed,
        "vision_context": vision_context,
        "reason": "Vision event converted into a structured incident using deterministic mapping."
    }
