from typing import Any, Dict, List, Optional
from services.incident_detection import process_incident
from services.severity_engine import predict_severity
from services.command_agent import generate_response_plan
from services.ambulance_agent import recommend_ambulance
from services.hospital_agent import recommend_hospital
from services.reasoning_engine import generate_explainable_plan
from services.decision_trace import build_decision_trace

def orchestrate_emergency(data: Dict[str, Any], allow_null_coords: bool = False) -> Dict[str, Any]:
    """
    Orchestrate emergency response by invoking and coordinating individual agent services.
    
    Workflow:
    1. Standardize raw input via process_incident.
    2. Pass standardized incident to Severity Engine.
    3. Pass incident + severity to Command Agent to get the response plan.
    4. Determine required resources.
    5. Conditionally invoke Ambulance Agent if 'AMBULANCE' resource is required.
    6. Conditionally invoke Hospital Agent if 'HOSPITAL' resource is required.
    7. Generate and return a unified response.
    """
    if not isinstance(data, dict):
        raise ValueError("Input data must be a dictionary")

    # STEP 1: Process raw incident through Incident Detection.
    standardized_incident = process_incident(data, allow_null_coords=allow_null_coords)
    
    # Extract location and key metrics for subsequent calls
    latitude = standardized_incident["latitude"]
    longitude = standardized_incident["longitude"]
    casualties = standardized_incident.get("casualties", 0)
    
    # STEP 2: Pass standardized incident to Severity Engine.
    severity_result = predict_severity(standardized_incident, allow_null_coords=allow_null_coords)
    severity_level = severity_result["severity"]
    
    # STEP 3: Pass incident + severity to Command Agent.
    command_result = generate_response_plan(standardized_incident, severity_level, allow_null_coords=allow_null_coords)
    required_resources = command_result.get("required_resources", [])
    
    agents_called = ["IncidentDetection", "SeverityEngine", "CommandAgent"]
    agents_skipped = []
    
    # STEP 5: Ambulance Agent coordination
    ambulance_rec = None
    ambulance_status = "SKIPPED"
    ambulance_required = "AMBULANCE" in required_resources
    amb_res = None
    
    if ambulance_required:
        agents_called.append("AmbulanceAgent")
        
        # Read preferred type overrides from the raw data
        required_type = data.get("required_type") or data.get("ambulance_type")
        
        # Call the existing ambulance agent
        amb_res = recommend_ambulance(
            latitude=latitude,
            longitude=longitude,
            severity=severity_level,
            required_type=required_type
        )
        
        if amb_res.get("ambulance") is not None:
            ambulance_rec = amb_res
            ambulance_status = "ALLOCATED"
        else:
            ambulance_status = "NO_SUITABLE_AMBULANCE"
    else:
        agents_skipped.append("AmbulanceAgent")
        
    # STEP 6: Hospital Agent coordination
    hospital_rec = None
    hospital_status = "SKIPPED"
    hospital_required = "HOSPITAL" in required_resources
    hosp_res = None
    
    if hospital_required:
        agents_called.append("HospitalAgent")
        
        # Deterministic medical requirement rules:
        # severity == CRITICAL and casualties >= 4 -> requires_trauma = True, requires_icu = True
        requires_trauma = False
        requires_icu = False
        if severity_level == "CRITICAL" and casualties >= 4:
            requires_trauma = True
            requires_icu = True
            
        # Optional raw input overrides
        if "requires_trauma" in data and data["requires_trauma"] is not None:
            requires_trauma = bool(data["requires_trauma"])
        if "requires_icu" in data and data["requires_icu"] is not None:
            requires_icu = bool(data["requires_icu"])
            
        # Call the existing hospital agent
        hosp_res = recommend_hospital(
            latitude=latitude,
            longitude=longitude,
            severity=severity_level,
            requires_trauma=requires_trauma,
            requires_icu=requires_icu
        )
        
        if hosp_res.get("hospital") is not None:
            hospital_rec = hosp_res
            hospital_status = "RECOMMENDED"
        else:
            hospital_status = "NO_SUITABLE_HOSPITAL"
    else:
        agents_skipped.append("HospitalAgent")
        
    # Determine Statuses for Traffic and Fire (Future/unimplemented handlers)
    traffic_required = "TRAFFIC_POLICE" in required_resources
    traffic_status = "NOT_IMPLEMENTED" if traffic_required else "SKIPPED"
    
    fire_required = "FIRE_UNIT" in required_resources
    fire_status = "NOT_IMPLEMENTED" if fire_required else "SKIPPED"

    # Build the resource_coordination structure
    resource_coordination = {
        "ambulance": {
            "required": ambulance_required,
            "status": ambulance_status,
            "recommendation": ambulance_rec
        },
        "hospital": {
            "required": hospital_required,
            "status": hospital_status,
            "recommendation": hospital_rec
        },
        "traffic_police": {
            "required": traffic_required,
            "status": traffic_status
        },
        "fire_unit": {
            "required": fire_required,
            "status": fire_status
        }
    }
    
    # Deterministic Orchestration Status Resolution
    succeeded_imp = []
    if ambulance_required and ambulance_status == "ALLOCATED":
        succeeded_imp.append("AMBULANCE")
    if hospital_required and hospital_status == "RECOMMENDED":
        succeeded_imp.append("HOSPITAL")
        
    failed_imp = []
    if ambulance_required and ambulance_status == "NO_SUITABLE_AMBULANCE":
        failed_imp.append("AMBULANCE")
    if hospital_required and hospital_status == "NO_SUITABLE_HOSPITAL":
        failed_imp.append("HOSPITAL")
        
    unimplemented_req = []
    for r in required_resources:
        if r not in ("AMBULANCE", "HOSPITAL"):
            unimplemented_req.append(r)
            
    # Calculate overall orchestration status
    if not required_resources:
        orchestration_status = "FULLY_COORDINATED"
    elif unimplemented_req:
        if succeeded_imp:
            # At least one succeeded, but some unimplemented exist
            orchestration_status = "PARTIALLY_COORDINATED"
        elif failed_imp:
            # All implemented required resources failed
            orchestration_status = "RESOURCE_UNAVAILABLE"
        else:
            # Only unimplemented resources required (none implemented required)
            orchestration_status = "PARTIALLY_COORDINATED"
    else:
        # Only implemented required resources
        if not failed_imp:
            orchestration_status = "FULLY_COORDINATED"
        elif succeeded_imp:
            orchestration_status = "PARTIALLY_COORDINATED"
        else:
            orchestration_status = "RESOURCE_UNAVAILABLE"

    res = {
        "incident": standardized_incident,
        "severity": severity_result,
        "command": command_result,
        "ambulance": ambulance_rec,
        "ambulance_status": ambulance_status,
        "hospital": hospital_rec,
        "hospital_status": hospital_status,
        "agents_called": agents_called,
        "agents_skipped": agents_skipped,
        "resource_coordination": resource_coordination,
        "orchestration_status": orchestration_status
    }

    # Generate explanations using reasoning engine
    reasoning = generate_explainable_plan(res, data, amb_res=amb_res, hosp_res=hosp_res)
    res["reasoning"] = reasoning

    # Generate decision trace
    decision_trace = build_decision_trace(res, data)
    res["decision_trace"] = decision_trace

    return res
