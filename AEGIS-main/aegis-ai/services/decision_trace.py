from typing import Any, Dict, List
from datetime import datetime, timezone

def build_decision_trace(orchestration_result: Dict[str, Any], raw_input: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Build a deterministic, structured decision trace to audit all major decisions.
    
    Safety:
    - Never invents data.
    - Never changes underlying decisions.
    - Uses factual fallbacks for missing fields.
    - Uses actual UTC timestamp of record creation.
    """
    trace: List[Dict[str, Any]] = []
    
    incident = orchestration_result.get("incident", {})
    severity = orchestration_result.get("severity", {})
    command = orchestration_result.get("command", {})
    coordination = orchestration_result.get("resource_coordination", {})
    reasoning = orchestration_result.get("reasoning", {})
    
    inc_id = incident.get("incident_id", "UNKNOWN")
    
    def get_timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    # 1. INCIDENT_CLASSIFICATION
    raw_type = raw_input.get("incident_type")
    normalized_type = incident.get("incident_type")
    if raw_type and normalized_type:
        if str(raw_type).strip().upper() == str(normalized_type).strip().upper():
            inc_factors = ["incident type already normalized"]
        else:
            inc_factors = ["incident_type normalization mapping"]
    else:
        inc_factors = ["incident type details missing"]
        
    trace.append({
        "decision_id": f"DEC-{inc_id}-01",
        "decision_type": "INCIDENT_CLASSIFICATION",
        "source_agent": "IncidentDetection",
        "inputs": {"incident_type": raw_type},
        "factors": inc_factors,
        "decision": normalized_type,
        "reason": reasoning.get("incident_reason", ""),
        "timestamp": get_timestamp()
    })

    # 2. SEVERITY_CLASSIFICATION
    sev_factors = severity.get("factors", [])
    trace.append({
        "decision_id": f"DEC-{inc_id}-02",
        "decision_type": "SEVERITY_CLASSIFICATION",
        "source_agent": "SeverityEngine",
        "inputs": {
            "casualties": incident.get("casualties"),
            "fire": incident.get("fire"),
            "road_blocked": incident.get("road_blocked"),
            "vehicles": incident.get("vehicles")
        },
        "factors": sev_factors,
        "decision": severity.get("severity"),
        "reason": severity.get("reason", ""),
        "timestamp": get_timestamp()
    })

    # 3. COMMAND_RESPONSE
    trace.append({
        "decision_id": f"DEC-{inc_id}-03",
        "decision_type": "COMMAND_RESPONSE",
        "source_agent": "CommandAgent",
        "inputs": {
            "incident_type": normalized_type,
            "severity": severity.get("severity"),
            "casualties": incident.get("casualties"),
            "fire": incident.get("fire"),
            "road_blocked": incident.get("road_blocked")
        },
        "factors": [
            f"required_actions: {command.get('required_actions', [])}",
            f"required_resources: {command.get('required_resources', [])}"
        ],
        "decision": command.get("response_priority"),
        "reason": command.get("reason", ""),
        "timestamp": get_timestamp()
    })

    # 4. AMBULANCE_SELECTION
    amb_coord = coordination.get("ambulance", {})
    amb_status = amb_coord.get("status", "SKIPPED")
    amb_rec = orchestration_result.get("ambulance")
    
    amb_inputs = {
        "latitude": incident.get("latitude"),
        "longitude": incident.get("longitude"),
        "severity": severity.get("severity"),
        "required_type": raw_input.get("required_type") or raw_input.get("ambulance_type")
    }
    
    if amb_status == "ALLOCATED" and amb_rec:
        amb_id = amb_rec.get("ambulance")
        amb_factors = []
        if "ambulance" in amb_rec: amb_factors.append(f"ambulance_id: {amb_rec['ambulance']}")
        if "type" in amb_rec: amb_factors.append(f"type: {amb_rec['type']}")
        if "distance_km" in amb_rec: amb_factors.append(f"distance_km: {amb_rec['distance_km']}")
        if "eta_minutes" in amb_rec: amb_factors.append(f"eta_minutes: {amb_rec['eta_minutes']}")
        amb_decision = amb_id
    elif amb_status == "NO_SUITABLE_AMBULANCE":
        amb_factors = ["no available ambulance matching operational criteria"]
        amb_decision = None
    else:
        amb_factors = ["ambulance support not required"]
        amb_decision = None
        
    trace.append({
        "decision_id": f"DEC-{inc_id}-04",
        "decision_type": "AMBULANCE_SELECTION",
        "source_agent": "AmbulanceAgent",
        "inputs": amb_inputs,
        "factors": amb_factors,
        "decision": amb_decision,
        "reason": reasoning.get("ambulance_reason", ""),
        "timestamp": get_timestamp()
    })

    # 5. HOSPITAL_SELECTION
    hosp_coord = coordination.get("hospital", {})
    hosp_status = hosp_coord.get("status", "SKIPPED")
    hosp_rec = orchestration_result.get("hospital")
    
    # Reconstruct exact HospitalAgent input resolution logic
    severity_level = severity.get("severity")
    casualties = incident.get("casualties") or 0
    requires_trauma = False
    requires_icu = False
    if severity_level == "CRITICAL" and casualties >= 4:
        requires_trauma = True
        requires_icu = True
    if "requires_trauma" in raw_input and raw_input["requires_trauma"] is not None:
        requires_trauma = bool(raw_input["requires_trauma"])
    if "requires_icu" in raw_input and raw_input["requires_icu"] is not None:
        requires_icu = bool(raw_input["requires_icu"])
        
    hosp_inputs = {
        "latitude": incident.get("latitude"),
        "longitude": incident.get("longitude"),
        "severity": severity_level,
        "requires_trauma": requires_trauma,
        "requires_icu": requires_icu
    }
    
    if hosp_status == "RECOMMENDED" and hosp_rec:
        hosp_name = hosp_rec.get("hospital")
        hosp_factors = []
        if "hospital" in hosp_rec: hosp_factors.append(f"hospital_name: {hosp_rec['hospital']}")
        if "distance_km" in hosp_rec: hosp_factors.append(f"distance_km: {hosp_rec['distance_km']}")
        for fld in ["available", "trauma_capable", "icu_available"]:
            if fld in hosp_rec:
                hosp_factors.append(f"{fld}: {hosp_rec[fld]}")
        hosp_decision = hosp_name
    elif hosp_status == "NO_SUITABLE_HOSPITAL":
        hosp_factors = ["no open emergency capacity hospital found matching requirements"]
        hosp_decision = None
    else:
        hosp_factors = ["hospital recommendation not required"]
        hosp_decision = None
        
    trace.append({
        "decision_id": f"DEC-{inc_id}-05",
        "decision_type": "HOSPITAL_SELECTION",
        "source_agent": "HospitalAgent",
        "inputs": hosp_inputs,
        "factors": hosp_factors,
        "decision": hosp_decision,
        "reason": reasoning.get("hospital_reason", ""),
        "timestamp": get_timestamp()
    })

    # 6. RESOURCE_COORDINATION
    trace.append({
        "decision_id": f"DEC-{inc_id}-06",
        "decision_type": "RESOURCE_COORDINATION",
        "source_agent": "Orchestrator",
        "inputs": {
            "required_resources": command.get("required_resources", [])
        },
        "factors": [
            f"Ambulance status: {coordination.get('ambulance', {}).get('status')}",
            f"Hospital status: {coordination.get('hospital', {}).get('status')}",
            f"Traffic Police status: {coordination.get('traffic_police', {}).get('status')}",
            f"Fire Unit status: {coordination.get('fire_unit', {}).get('status')}"
        ],
        "decision": {
            "ambulance": coordination.get("ambulance", {}).get("status"),
            "hospital": coordination.get("hospital", {}).get("status"),
            "traffic_police": coordination.get("traffic_police", {}).get("status"),
            "fire_unit": coordination.get("fire_unit", {}).get("status")
        },
        "reason": reasoning.get("resource_reason", ""),
        "timestamp": get_timestamp()
    })

    # 7. ORCHESTRATION_STATUS
    trace.append({
        "decision_id": f"DEC-{inc_id}-07",
        "decision_type": "ORCHESTRATION_STATUS",
        "source_agent": "Orchestrator",
        "inputs": {
            "ambulance_status": coordination.get("ambulance", {}).get("status"),
            "hospital_status": coordination.get("hospital", {}).get("status"),
            "traffic_police_status": coordination.get("traffic_police", {}).get("status"),
            "fire_unit_status": coordination.get("fire_unit", {}).get("status")
        },
        "factors": [
            f"Required resources: {command.get('required_resources', [])}",
            f"Orchestration status: {orchestration_result.get('orchestration_status')}"
        ],
        "decision": orchestration_result.get("orchestration_status"),
        "reason": reasoning.get("orchestration_reason", ""),
        "timestamp": get_timestamp()
    })

    return trace
