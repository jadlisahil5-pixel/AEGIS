from typing import Any, Dict, Optional
from services.vision_incident_adapter import vision_event_to_incident
from services.orchestrator import orchestrate_emergency


def process_vision_incident_to_orchestrator(
    event_result: Dict[str, Any],
    camera_metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Coordinates the Vision Incident -> Orchestrator pipeline.
    1. Converts a vision event to a structured incident.
    2. If no incident is created, returns a response with incident_created = False.
    3. If created, runs the structured incident through the existing emergency orchestrator.
    """
    adapter_res = vision_event_to_incident(event_result, camera_metadata)

    if not adapter_res.get("incident_created", False):
        return {
            "incident_created": False,
            "incident": None,
            "severity": None,
            "command": None,
            "ambulance": None,
            "ambulance_status": "SKIPPED",
            "hospital": None,
            "hospital_status": "SKIPPED",
            "agents_called": [],
            "agents_skipped": [],
            "resource_coordination": None,
            "reasoning": None,
            "decision_trace": [],
            "orchestration_status": "RESOURCE_UNAVAILABLE",
            "pipeline_status": "NO_INCIDENT_CREATED",
            "reason": adapter_res.get("reason", "Vision event did not meet the criteria for incident creation.")
        }

    incident = adapter_res["incident"]

    # Run through the existing orchestrator
    orchestration_res = orchestrate_emergency(incident, allow_null_coords=True)

    # Return unified response
    return {
        "incident_created": True,
        "incident": orchestration_res["incident"],
        "severity": orchestration_res["severity"],
        "command": orchestration_res["command"],
        "ambulance": orchestration_res["ambulance"],
        "ambulance_status": orchestration_res["ambulance_status"],
        "hospital": orchestration_res["hospital"],
        "hospital_status": orchestration_res["hospital_status"],
        "agents_called": orchestration_res["agents_called"],
        "agents_skipped": orchestration_res["agents_skipped"],
        "resource_coordination": orchestration_res["resource_coordination"],
        "reasoning": orchestration_res["reasoning"],
        "decision_trace": orchestration_res["decision_trace"],
        "orchestration_status": orchestration_res["orchestration_status"],
        "pipeline_status": "COMPLETED",
        "reason": "Vision-generated incident successfully coordinated through emergency orchestrator."
    }
