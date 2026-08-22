from typing import Any, Dict, Optional
from services.data_loader import get_ambulances
from services.hospital_agent import haversine_distance

def recommend_ambulance(
    latitude: Optional[float],
    longitude: Optional[float],
    severity: Optional[str] = None,
    required_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Recommend the best ambulance based on location, severity, and required type.
    Uses deterministic type matching with fallbacks and distance ranking.
    """
    if latitude is None or longitude is None:
        return {
            "ambulance": None,
            "type": None,
            "eta_minutes": None,
            "distance_km": None,
            "available": False,
            "reason": "Ambulance recommendation requires valid location coordinates."
        }
    ambulances = get_ambulances()
    if not ambulances:
        return {
            "ambulance": None,
            "type": None,
            "eta_minutes": None,
            "distance_km": None,
            "available": False,
            "reason": "No ambulance data available."
        }

    # Normalize inputs
    severity = (severity or "").upper()
    required_type = (required_type or "").upper()

    # Determine the preferred ambulance type
    if required_type in ["ALS", "BLS", "TRAUMA"]:
        pref_type = required_type
    else:
        # Map from severity if required_type is not specified or invalid
        if severity == "CRITICAL":
            pref_type = "TRAUMA"
        elif severity == "HIGH":
            pref_type = "ALS"
        elif severity in ["MEDIUM", "LOW"]:
            pref_type = "BLS"
        else:
            pref_type = "BLS"  # Default fallback preferred type

    eligible_ambulances = []

    for amb in ambulances:
        amb_id = amb.get("ambulance_id")
        amb_type = (amb.get("type") or "BLS").upper()
        status = (amb.get("status") or "UNKNOWN").upper()
        
        # Parse numeric and boolean values defensively
        def safe_float(val) -> Optional[float]:
            if val is None:
                return None
            try:
                return float(val)
            except (ValueError, TypeError):
                return None

        def safe_int(val, default=0) -> int:
            if val is None:
                return default
            try:
                return int(val)
            except (ValueError, TypeError):
                return default

        amb_lat = safe_float(amb.get("latitude"))
        amb_lon = safe_float(amb.get("longitude"))
        fuel = safe_int(amb.get("fuel_percent"), default=0)
        crew = safe_int(amb.get("crew_size"), default=0)
        driver = amb.get("driver_id")
        paramedic = amb.get("paramedic_id")

        # Hard filters:
        # 1. Location must be valid
        if amb_lat is None or amb_lon is None:
            continue

        # 2. General availability: status must be AVAILABLE
        if status != "AVAILABLE":
            continue

        # 3. Fuel check: fuel must be > 10%
        if fuel <= 10:
            continue

        # 4. Crew check: crew_size >= 2, driver and paramedic must be present
        if crew < 2 or not driver or not paramedic:
            continue

        # Calculate distance
        dist = haversine_distance(latitude, longitude, amb_lat, amb_lon)

        # Calculate Type Match Score (Exact Match: 10, Secondary: 5, Least: 1)
        type_match_score = 1
        if amb_type == pref_type:
            type_match_score = 10
        else:
            # Fallback rules
            if pref_type == "TRAUMA":
                if amb_type == "ALS":
                    type_match_score = 5
                elif amb_type == "BLS":
                    type_match_score = 1
            elif pref_type == "ALS":
                if amb_type == "TRAUMA":
                    type_match_score = 5
                elif amb_type == "BLS":
                    type_match_score = 1
            elif pref_type == "BLS":
                if amb_type == "ALS":
                    type_match_score = 5
                elif amb_type == "TRAUMA":
                    type_match_score = 1

        eligible_ambulances.append({
            "ambulance_id": amb_id,
            "type": amb.get("type"),  # Keep original casing for output
            "type_normalized": amb_type,
            "distance_km": round(dist, 2),
            "fuel_percent": fuel,
            "type_match_score": type_match_score
        })

    if not eligible_ambulances:
        return {
            "ambulance": None,
            "type": None,
            "eta_minutes": None,
            "distance_km": None,
            "available": False,
            "reason": "No available ambulances found matching operational criteria (status AVAILABLE, fuel > 10%, adequate crew)."
        }

    # Rank: type_match_score DESC, distance_km ASC, fuel_percent DESC
    eligible_ambulances.sort(key=lambda x: (-x["type_match_score"], x["distance_km"], -x["fuel_percent"]))
    best = eligible_ambulances[0]

    # Calculate DEMO ETA: distance_km * 1.5 + 2
    eta = round(best["distance_km"] * 1.5 + 2.0)

    # Build response reason with clear explanation of match type and demo ETA disclaimer
    matched_type = best["type_normalized"]
    is_fallback = matched_type != pref_type
    
    # Capitalize for readability in reason string
    pref_title = pref_type.title() if pref_type != "ALS" and pref_type != "BLS" else pref_type
    matched_title = best["type"].title() if matched_type != "ALS" and matched_type != "BLS" else best["type"]

    if is_fallback:
        reason_type = f"No {pref_title} ambulance was available; {matched_title} ambulance selected as fallback."
    else:
        reason_type = f"Nearest available {matched_title} ambulance selected."

    reason = (
        f"{reason_type} Estimated ETA is {eta} minutes based on a simplified travel-speed/dispatch assumption "
        f"({best['distance_km']} km distance)."
    )

    return {
        "ambulance": best["ambulance_id"],
        "type": best["type"],
        "eta_minutes": eta,
        "distance_km": best["distance_km"],
        "available": True,
        "reason": reason
    }
