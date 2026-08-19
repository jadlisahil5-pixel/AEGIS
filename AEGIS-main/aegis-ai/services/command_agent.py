from typing import Any, Dict
from services.incident_detection import process_incident

def generate_response_plan(incident: Dict[str, Any], severity: str, allow_null_coords: bool = False) -> Dict[str, Any]:
    """
    Deterministically generate a response plan (priority, actions, resource categories, reason)
    based on the incident type, severity, and hazards.
    Reuses process_incident only for validation/normalization without side effects.
    """
    if not isinstance(incident, dict):
        raise ValueError("Incident must be a dictionary")
    if not isinstance(severity, str):
        raise ValueError("Severity must be a string")

    severity = severity.strip().upper()
    if severity not in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
        raise ValueError(f"Invalid severity level: '{severity}'")

    # Create a copy and insert dummy validation-only values for missing non-critical API fields (incident_id, timestamp)
    # to reuse process_incident's validation/normalization logic without side effects.
    incident_copy = incident.copy()
    if "incident_id" not in incident_copy:
        incident_copy["incident_id"] = "INC-VALIDATION"
    if "timestamp" not in incident_copy:
        incident_copy["timestamp"] = "2026-08-15T12:00:00"

    # Call process_incident to perform all validation/normalization rules
    normalized = process_incident(incident_copy, allow_null_coords=allow_null_coords)

    # Extract variables
    incident_type = normalized["incident_type"]
    casualties = normalized["casualties"]
    fire = normalized["fire"]
    road_blocked = normalized["road_blocked"]
    vehicles = normalized["vehicles"]

    required_actions = []

    # 1. Severity-based action rules
    if severity == "CRITICAL":
        required_actions.append("IMMEDIATE_RESPONSE")

    # 2. Incident Type specific rules
    if incident_type == "ROAD_ACCIDENT":
        if casualties > 0 or severity in {"HIGH", "CRITICAL"}:
            required_actions.append("DISPATCH_AMBULANCE")
            required_actions.append("ALERT_HOSPITAL")
        required_actions.append("ALERT_TRAFFIC_POLICE")
        if severity in {"HIGH", "CRITICAL"}:
            required_actions.append("MANAGE_TRAFFIC")

    elif incident_type == "FIRE":
        required_actions.append("REQUEST_FIRE_RESPONSE")
        required_actions.append("ALERT_POLICE")
        if casualties > 0:
            required_actions.append("DISPATCH_AMBULANCE")
            required_actions.append("ALERT_HOSPITAL")

    elif incident_type == "MEDICAL_EMERGENCY":
        required_actions.append("DISPATCH_AMBULANCE")
        required_actions.append("ALERT_HOSPITAL")

    elif incident_type == "TRAFFIC_INCIDENT":
        required_actions.append("ALERT_TRAFFIC_POLICE")
        required_actions.append("MANAGE_TRAFFIC")

    elif incident_type in {"INDUSTRIAL_ACCIDENT", "BUILDING_COLLAPSE", "DISASTER"}:
        required_actions.append("ALERT_POLICE")
        if severity in {"HIGH", "CRITICAL"}:
            required_actions.append("REQUEST_FIRE_RESPONSE")  # for search & rescue
        if casualties > 0:
            required_actions.append("DISPATCH_AMBULANCE")
            required_actions.append("ALERT_HOSPITAL")

    elif incident_type == "WOMEN_SAFETY":
        required_actions.append("ALERT_POLICE")
        if casualties > 0:
            required_actions.append("DISPATCH_AMBULANCE")
            required_actions.append("ALERT_HOSPITAL")

    else:  # OTHER or default
        required_actions.append("ALERT_POLICE")
        if casualties > 0:
            required_actions.append("DISPATCH_AMBULANCE")
            required_actions.append("ALERT_HOSPITAL")

    # 3. Parameter-based rules (safety overrides)
    if casualties > 0:
        if "DISPATCH_AMBULANCE" not in required_actions:
            required_actions.append("DISPATCH_AMBULANCE")
        if "ALERT_HOSPITAL" not in required_actions:
            required_actions.append("ALERT_HOSPITAL")

    if casualties >= 4:
        if "PRIORITIZE_MEDICAL_RESPONSE" not in required_actions:
            required_actions.append("PRIORITIZE_MEDICAL_RESPONSE")

    if fire:
        if "REQUEST_FIRE_RESPONSE" not in required_actions:
            required_actions.append("REQUEST_FIRE_RESPONSE")

    if road_blocked:
        if "CREATE_EMERGENCY_CORRIDOR" not in required_actions:
            required_actions.append("CREATE_EMERGENCY_CORRIDOR")
        if "ALERT_TRAFFIC_POLICE" not in required_actions:
            required_actions.append("ALERT_TRAFFIC_POLICE")

    # Clean up duplicate actions while preserving order
    seen = set()
    cleaned_actions = []
    for act in required_actions:
        if act not in seen:
            seen.add(act)
            cleaned_actions.append(act)

    # 4. Map actions to resource categories
    resource_candidates = [
        ("AMBULANCE", {"DISPATCH_AMBULANCE", "ALERT_MEDICAL_RESPONSE"}),
        ("HOSPITAL", {"ALERT_HOSPITAL", "PRIORITIZE_MEDICAL_RESPONSE"}),
        ("TRAFFIC_POLICE", {"ALERT_TRAFFIC_POLICE", "MANAGE_TRAFFIC", "CREATE_EMERGENCY_CORRIDOR"}),
        ("FIRE_UNIT", {"REQUEST_FIRE_RESPONSE"}),
        ("POLICE", {"ALERT_POLICE"})
    ]

    required_resources = []
    for resource, action_triggers in resource_candidates:
        if any(act in cleaned_actions for act in action_triggers):
            required_resources.append(resource)

    # Priority mapping
    priority_map = {
        "LOW": "ROUTINE",
        "MEDIUM": "PRIORITY",
        "HIGH": "URGENT",
        "CRITICAL": "IMMEDIATE"
    }
    response_priority = priority_map[severity]

    # 5. Explanations Builder (Deterministic Reason)
    type_str = incident_type.replace("_", " ").lower()

    descriptors = []
    if casualties == 1:
        descriptors.append("1 casualty")
    elif casualties > 1:
        descriptors.append(f"{casualties} casualties")

    if fire:
        descriptors.append("fire")

    if road_blocked:
        descriptors.append("road blockage")

    if not descriptors:
        desc_str = "no major hazards"
    elif len(descriptors) == 1:
        desc_str = descriptors[0]
    elif len(descriptors) == 2:
        desc_str = f"{descriptors[0]} and {descriptors[1]}"
    else:
        desc_str = ", ".join(descriptors[:-1]) + f", and {descriptors[-1]}"

    reason = f"{severity.capitalize()} {type_str} with {desc_str} requires {response_priority.lower()} response."

    return {
        "incident_type": incident_type,
        "severity": severity,
        "response_priority": response_priority,
        "required_actions": cleaned_actions,
        "required_resources": required_resources,
        "reason": reason
    }
