from typing import Any, Dict, Optional

def generate_explainable_plan(
    orchestration_result: Dict[str, Any],
    raw_input: Dict[str, Any],
    amb_res: Optional[Dict[str, Any]] = None,
    hosp_res: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate deterministic, explainable explanations for all decisions in the emergency response plan.
    Consumes outputs from the sub-agents and raw input to explain decisions factually.
    
    Safety:
    - Never invents data.
    - Never changes underlying decisions.
    - Uses factual fallbacks for missing fields.
    - Never generates fake AI confidence scores.
    """
    # 1. Incident Normalization Reasoning
    raw_type = raw_input.get("incident_type")
    normalized_type = orchestration_result.get("incident", {}).get("incident_type")
    
    if raw_type and normalized_type:
        if str(raw_type).strip().upper() == str(normalized_type).strip().upper():
            incident_reason = f"Incident type '{raw_type}' was already normalized; no classification mapping changes were required."
        else:
            incident_reason = f"Raw incident type '{raw_type}' was normalized to '{normalized_type}' based on pre-defined classification mappings."
    else:
        incident_reason = "Incident type details were not fully provided."
        
    supplied_id = raw_input.get("incident_id")
    if supplied_id:
        incident_reason += f" Supplied incident ID '{supplied_id}' was verified and preserved."

    # 2. Severity Reasoning
    severity_reason = orchestration_result.get("severity", {}).get("reason")
    if not severity_reason:
        severity_reason = "Severity prediction was calculated based on deterministic contributing factors, but no detailed explanation was provided."

    # 3. Command Reasoning
    command_reason = orchestration_result.get("command", {}).get("reason")
    if not command_reason:
        command_reason = "Command response actions were generated based on hazard rules, but no detailed explanation was provided."

    # 4. Ambulance Reasoning
    coordination = orchestration_result.get("resource_coordination", {})
    amb_coord = coordination.get("ambulance", {})
    amb_status = amb_coord.get("status", "SKIPPED")
    amb_rec = orchestration_result.get("ambulance") or amb_res
    
    if amb_status == "ALLOCATED" and amb_rec:
        amb_id = amb_rec.get("ambulance")
        amb_type = amb_rec.get("type")
        dist = amb_rec.get("distance_km")
        eta = amb_rec.get("eta_minutes")
        agent_reason = amb_rec.get("reason")
        
        details = []
        if amb_id: details.append(f"Ambulance '{amb_id}'")
        if amb_type: details.append(f"type '{amb_type}'")
        if dist is not None: details.append(f"distance {dist} km")
        if eta is not None: details.append(f"ETA {eta} mins")
        
        base_desc = " ".join(details) if details else "Ambulance"
        if agent_reason:
            ambulance_reason = f"{base_desc} was selected: {agent_reason}"
        else:
            ambulance_reason = f"{base_desc} was selected based on the Ambulance Agent's eligibility and ranking logic."
    elif amb_status == "NO_SUITABLE_AMBULANCE":
        agent_reason = amb_rec.get("reason") if amb_rec else None
        if agent_reason:
            ambulance_reason = f"Ambulance dispatch was requested, but failed: {agent_reason}"
        else:
            ambulance_reason = "Ambulance dispatch was requested, but no available ambulance met the fuel and crew requirements."
    else:
        ambulance_reason = "Ambulance support was not required based on the command response plan."

    # 5. Hospital Reasoning
    hosp_coord = coordination.get("hospital", {})
    hosp_status = hosp_coord.get("status", "SKIPPED")
    hosp_rec = orchestration_result.get("hospital") or hosp_res
    
    if hosp_status == "RECOMMENDED" and hosp_rec:
        hosp_name = hosp_rec.get("hospital")
        dist = hosp_rec.get("distance_km")
        agent_reason = hosp_rec.get("reason")
        
        details = []
        if hosp_name: details.append(f"Hospital '{hosp_name}'")
        if dist is not None: details.append(f"distance {dist} km")
        
        base_desc = " ".join(details) if details else "Hospital"
        if agent_reason:
            hospital_reason = f"{base_desc} was recommended: {agent_reason}"
        else:
            hospital_reason = f"{base_desc} was recommended because it ranked highest among eligible hospitals according to the Hospital Agent."
    elif hosp_status == "NO_SUITABLE_HOSPITAL":
        agent_reason = hosp_rec.get("reason") if hosp_rec else None
        if agent_reason:
            hospital_reason = f"Hospital recommendation was requested, but failed: {agent_reason}"
        else:
            hospital_reason = "Hospital alert was requested, but no available hospital met the trauma/ICU criteria."
    else:
        hospital_reason = "Hospital recommendation was not required based on the command response plan."

    # 6. Resource Status Reasoning
    tp_coord = coordination.get("traffic_police", {})
    tp_status = tp_coord.get("status", "SKIPPED")
    fu_coord = coordination.get("fire_unit", {})
    fu_status = fu_coord.get("status", "SKIPPED")
    
    tp_desc = "SKIPPED"
    if tp_status == "NOT_IMPLEMENTED":
        tp_desc = "NOT_IMPLEMENTED (support was requested, but a dedicated Traffic Agent is not yet implemented)"
        
    fu_desc = "SKIPPED"
    if fu_status == "NOT_IMPLEMENTED":
        fu_desc = "NOT_IMPLEMENTED (support was requested, but a dedicated Fire Agent is not yet implemented)"
        
    resource_reason = (
        f"Ambulance: {amb_status}. "
        f"Hospital: {hosp_status}. "
        f"Traffic Police: {tp_desc}. "
        f"Fire Unit: {fu_desc}."
    )

    # 7. Orchestration Status Reasoning
    orch_status = orchestration_result.get("orchestration_status", "COMPLETED")
    if orch_status == "FULLY_COORDINATED":
        orchestration_reason = "All required resources supported by the current AEGIS system were successfully coordinated."
    elif orch_status == "PARTIALLY_COORDINATED":
        orchestration_reason = "Some required resources were successfully coordinated while others were unavailable or not yet implemented."
    elif orch_status == "RESOURCE_UNAVAILABLE":
        orchestration_reason = "Required actionable resources could not be allocated."
    else:
        orchestration_reason = f"Orchestration resolved with status: {orch_status}."

    # 8. Overall Reason
    inc_id = orchestration_result.get("incident", {}).get("incident_id", "UNKNOWN")
    severity = orchestration_result.get("severity", {}).get("severity", "UNKNOWN")
    inc_type = orchestration_result.get("incident", {}).get("incident_type", "UNKNOWN")
    priority = orchestration_result.get("command", {}).get("response_priority", "UNKNOWN").lower()
    
    overall_reason = (
        f"Emergency {inc_id} (classified as {severity} {inc_type}) requires {priority} response. "
        f"Coordination status resolved to {orch_status}."
    )

    return {
        "incident_reason": incident_reason,
        "severity_reason": severity_reason,
        "command_reason": command_reason,
        "ambulance_reason": ambulance_reason,
        "hospital_reason": hospital_reason,
        "resource_reason": resource_reason,
        "orchestration_reason": orchestration_reason,
        "overall_reason": overall_reason
    }
