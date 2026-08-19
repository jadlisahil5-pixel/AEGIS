from typing import Any, Dict
from services.incident_detection import process_incident

def predict_severity(incident: Dict[str, Any], allow_null_coords: bool = False) -> Dict[str, Any]:
    """
    Deterministically predict incident severity level, score, factors, and generate a natural reason.
    Reuses process_incident for validation/normalization without side effects on incident ID or counter.
    """
    if not isinstance(incident, dict):
        raise ValueError("Incident must be a dictionary")

    # Create a copy and insert dummy validation-only values for missing non-critical API fields (incident_id, timestamp)
    # to reuse process_incident's validation/normalization logic without generating new IDs/timestamps in memory.
    incident_copy = incident.copy()
    if "incident_id" not in incident_copy:
        incident_copy["incident_id"] = "INC-VALIDATION"
    if "timestamp" not in incident_copy:
        incident_copy["timestamp"] = "2026-08-15T12:00:00"

    # Call process_incident to perform all validation/normalization rules
    normalized = process_incident(incident_copy, allow_null_coords=allow_null_coords)

    # Calculate score
    score = 0
    factors = []
    reason_phrases = []

    # 1. Casualties
    casualties = normalized.get("casualties", 0)
    if casualties == 0:
        pass
    elif casualties == 1:
        score += 1
        factors.append("1 casualty")
        reason_phrases.append("1 casualty")
    elif 2 <= casualties <= 3:
        score += 2
        factors.append(f"{casualties} casualties")
        reason_phrases.append("multiple casualties")
    elif 4 <= casualties <= 5:
        score += 3
        factors.append(f"{casualties} casualties")
        reason_phrases.append("multiple casualties")
    else:  # >= 6
        score += 4
        factors.append(f"{casualties} casualties")
        reason_phrases.append("multiple casualties")

    # 2. Fire (+2)
    if normalized.get("fire", False):
        score += 2
        factors.append("fire detected")
        reason_phrases.append("fire")

    # 3. Road block (+1)
    if normalized.get("road_blocked", False):
        score += 1
        factors.append("road blockage")
        reason_phrases.append("road blockage")

    # 4. Multiple vehicles (+1)
    vehicles = normalized.get("vehicles", 0)
    if vehicles >= 2:
        score += 1
        factors.append("multiple vehicles")
        reason_phrases.append("multiple vehicles")

    # Severity Mapping
    if score >= 7:
        severity = "CRITICAL"
    elif score >= 5:
        severity = "HIGH"
    elif score >= 3:
        severity = "MEDIUM"
    else:
        severity = "LOW"

    # Generate explanation
    if not reason_phrases:
        reason = f"No casualties or hazards detected indicate a low-severity emergency."
    else:
        if len(reason_phrases) == 1:
            phrase_str = reason_phrases[0]
        elif len(reason_phrases) == 2:
            phrase_str = f"{reason_phrases[0]} combined with {reason_phrases[1]}"
        else:
            first = reason_phrases[0]
            rest = reason_phrases[1:]
            if len(rest) == 1:
                phrase_str = f"{first} combined with {rest[0]}"
            else:
                rest_str = ", ".join(rest[:-1]) + f", and {rest[-1]}"
                phrase_str = f"{first} combined with {rest_str}"

        phrase_str_cap = phrase_str[0].upper() + phrase_str[1:]

        # Verb: singular if only 1 item and not "multiple casualties", otherwise plural
        if len(reason_phrases) == 1 and casualties <= 1:
            verb = "indicates"
        else:
            verb = "indicate"

        if severity == "LOW":
            suffix = "low-severity emergency"
        elif severity == "MEDIUM":
            suffix = "medium-severity emergency"
        elif severity == "HIGH":
            suffix = "high-severity emergency"
        else:
            suffix = "critical emergency"

        reason = f"{phrase_str_cap} {verb} a {suffix}."

    result = {
        "severity": severity,
        "score": score,
        "factors": factors,
        "reason": reason
    }

    # Preserve input incident ID if originally provided
    if "incident_id" in incident:
        result["incident_id"] = incident["incident_id"]

    return result
